from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import json
import uuid
import logging

from celery import Celery
import redis
from sqlalchemy.orm import Session

from ..models.conversation import (
    ConversationContext, CISTCategory, CISTQuestionCandidate,
    AsyncTask, PathPrediction
)
from .question_generator import QuestionGenerator
from .conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


class AsyncProcessor:
    """비동기 질문 생성 및 평가 처리"""
    
    def __init__(self, redis_url: str, openai_api_key: str):
        # Redis 연결
        self.redis_client = redis.Redis.from_url(redis_url)
        
        # Celery 설정
        self.celery_app = Celery(
            'memento_async',
            broker=redis_url,
            backend=redis_url
        )
        
        # 서비스 인스턴스들
        self.question_generator = QuestionGenerator(openai_api_key)
        self.conversation_manager = ConversationManager()
        
        # 캐시 설정
        self.cache_ttl = 3600 * 24  # 24시간
        self.cache_prefix = "memento:cache:"
        
        # Celery 태스크 등록
        self._register_celery_tasks()
    
    def _register_celery_tasks(self):
        """Celery 태스크 등록"""
        
        @self.celery_app.task(name="generate_and_cache_questions")
        def generate_and_cache_questions_task(
            session_id: str,
            cist_category: str,
            conversation_context: str,
            photo_context: Optional[str],
            conversation_history: List[Dict[str, Any]],
            last_ai_response: str
        ):
            """질문 생성 및 캐싱 비동기 태스크"""
            return asyncio.run(
                self._process_question_generation(
                    session_id,
                    CISTCategory(cist_category),
                    conversation_context,
                    photo_context,
                    conversation_history,
                    last_ai_response
                )
            )
        
        @self.celery_app.task(name="evaluate_and_cache_questions")
        def evaluate_and_cache_questions_task(
            session_id: str,
            candidates_data: List[Dict[str, Any]],
            evaluation_context: Dict[str, Any]
        ):
            """질문 평가 및 캐싱 비동기 태스크"""
            return asyncio.run(
                self._process_question_evaluation(
                    session_id,
                    candidates_data,
                    evaluation_context
                )
            )
        
        # 인스턴스 변수로 저장하여 외부에서 접근 가능하게 함
        self.generate_task = generate_and_cache_questions_task
        self.evaluate_task = evaluate_and_cache_questions_task
    
    async def trigger_async_question_generation(
        self,
        session_id: str,
        cist_category: CISTCategory,
        conversation_context: str,
        photo_context: Optional[str],
        conversation_history: List[Dict[str, Any]],
        last_ai_response: str
    ) -> str:
        """비동기 질문 생성 프로세스 시작"""
        
        task_id = str(uuid.uuid4())
        
        try:
            # AsyncTask 정보 저장
            task_info = AsyncTask(
                id=task_id,
                task_type="question_generation",
                session_id=session_id,
                status="pending",
                input_data={
                    "cist_category": cist_category.value,
                    "conversation_context": conversation_context,
                    "photo_context": photo_context,
                    "conversation_history": conversation_history,
                    "last_ai_response": last_ai_response
                },
                created_at=datetime.now()
            )
            
            # Redis에 태스크 정보 저장
            await self._save_task_info(task_info)
            
            # Celery 태스크 시작
            celery_result = self.generate_task.delay(
                session_id,
                cist_category.value,
                conversation_context,
                photo_context,
                conversation_history,
                last_ai_response
            )
            
            # Celery 태스크 ID 업데이트
            task_info.result_data["celery_task_id"] = celery_result.id
            await self._save_task_info(task_info)
            
            logger.info(f"Started async question generation: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to trigger async question generation: {e}")
            raise
    
    async def _process_question_generation(
        self,
        session_id: str,
        cist_category: CISTCategory,
        conversation_context: str,
        photo_context: Optional[str],
        conversation_history: List[Dict[str, Any]],
        last_ai_response: str
    ) -> Dict[str, Any]:
        """질문 생성 프로세스 실행"""
        
        try:
            # 1. 대화 경로 예측
            logger.info("Predicting conversation paths...")
            path_prediction = await self.question_generator.predict_conversation_paths(
                conversation_context,
                photo_context,
                conversation_history,
                last_ai_response
            )
            path_prediction.session_id = session_id
            
            # 2. 질문 후보 생성
            logger.info("Generating question candidates...")
            candidates = await self.question_generator.generate_question_candidates(
                cist_category,
                conversation_context,
                photo_context,
                path_prediction.predicted_paths,
                session_id
            )
            
            # 3. 질문 평가
            logger.info("Evaluating question candidates...")
            evaluation_context = {
                "session_id": session_id,
                "conversation_context": conversation_context,
                "photo_context": photo_context,
                "cist_category": cist_category.value
            }
            
            evaluated_candidates = await self.question_generator.evaluate_question_candidates(
                candidates,
                evaluation_context
            )
            
            # 4. 캐시에 저장
            logger.info("Caching evaluated questions...")
            await self._cache_question_candidates(session_id, cist_category, evaluated_candidates)
            
            # 5. 경로 예측 결과도 캐시에 저장
            await self._cache_path_prediction(session_id, path_prediction)
            
            result = {
                "status": "completed",
                "generated_candidates": len(candidates),
                "evaluated_candidates": len(evaluated_candidates),
                "predicted_paths": len(path_prediction.predicted_paths),
                "cist_category": cist_category.value
            }
            
            logger.info(f"Question generation completed for session {session_id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in question generation process: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _process_question_evaluation(
        self,
        session_id: str,
        candidates_data: List[Dict[str, Any]],
        evaluation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """질문 평가 프로세스 실행"""
        
        try:
            # 후보 데이터를 객체로 변환
            candidates = [
                CISTQuestionCandidate(**data) for data in candidates_data
            ]
            
            # 질문 평가 실행
            evaluated_candidates = await self.question_generator.evaluate_question_candidates(
                candidates,
                evaluation_context
            )
            
            # 캐시에 저장
            cist_category = CISTCategory(evaluation_context["cist_category"])
            await self._cache_question_candidates(session_id, cist_category, evaluated_candidates)
            
            result = {
                "status": "completed",
                "original_candidates": len(candidates),
                "evaluated_candidates": len(evaluated_candidates)
            }
            
            logger.info(f"Question evaluation completed for session {session_id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in question evaluation process: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def get_cached_questions(
        self,
        session_id: str,
        cist_category: CISTCategory,
        conversation_context: str
    ) -> List[CISTQuestionCandidate]:
        """캐시된 질문 후보들 조회"""
        
        try:
            cache_key = f"{self.cache_prefix}questions:{session_id}:{cist_category.value}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                questions_data = json.loads(cached_data)
                questions = [
                    CISTQuestionCandidate(**q_data) for q_data in questions_data
                ]
                
                # 현재 대화 맥락과 관련성이 높은 질문들 필터링
                relevant_questions = self._filter_relevant_questions(
                    questions, conversation_context
                )
                
                logger.info(
                    f"Found {len(relevant_questions)} relevant cached questions "
                    f"for {cist_category} in session {session_id}"
                )
                return relevant_questions
            
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving cached questions: {e}")
            return []
    
    async def _cache_question_candidates(
        self,
        session_id: str,
        cist_category: CISTCategory,
        candidates: List[CISTQuestionCandidate]
    ):
        """질문 후보들을 캐시에 저장"""
        
        try:
            cache_key = f"{self.cache_prefix}questions:{session_id}:{cist_category.value}"
            
            # 기존 캐시된 질문들 가져오기
            existing_data = self.redis_client.get(cache_key)
            existing_questions = []
            
            if existing_data:
                existing_questions = json.loads(existing_data)
            
            # 새로운 질문들 추가
            new_questions_data = [candidate.dict() for candidate in candidates]
            all_questions = existing_questions + new_questions_data
            
            # 중복 제거 (질문 내용 기준)
            unique_questions = []
            seen_questions = set()
            
            for q in all_questions:
                if q["adapted_question"] not in seen_questions:
                    unique_questions.append(q)
                    seen_questions.add(q["adapted_question"])
            
            # 캐시에 저장
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(unique_questions, ensure_ascii=False, default=str)
            )
            
            logger.info(
                f"Cached {len(unique_questions)} questions for {cist_category} "
                f"in session {session_id}"
            )
            
        except Exception as e:
            logger.error(f"Error caching question candidates: {e}")
            raise
    
    async def _cache_path_prediction(
        self,
        session_id: str,
        path_prediction: PathPrediction
    ):
        """경로 예측 결과를 캐시에 저장"""
        
        try:
            cache_key = f"{self.cache_prefix}paths:{session_id}:{path_prediction.current_turn}"
            
            prediction_data = path_prediction.dict()
            
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(prediction_data, ensure_ascii=False, default=str)
            )
            
            logger.info(f"Cached path prediction for session {session_id}, turn {path_prediction.current_turn}")
            
        except Exception as e:
            logger.error(f"Error caching path prediction: {e}")
            raise
    
    def _filter_relevant_questions(
        self,
        questions: List[CISTQuestionCandidate],
        conversation_context: str
    ) -> List[CISTQuestionCandidate]:
        """현재 대화 맥락과 관련성이 높은 질문들 필터링"""
        
        # 관련성 점수 기준으로 정렬
        scored_questions = []
        
        for question in questions:
            # 기본 점수는 overall_score
            relevance_score = question.overall_score
            
            # 대화 맥락과의 키워드 매칭 보너스
            context_keywords = set(conversation_context.lower().split())
            question_keywords = set(question.conversation_context.lower().split())
            
            keyword_overlap = len(context_keywords & question_keywords)
            keyword_bonus = min(keyword_overlap * 0.1, 0.3)  # 최대 0.3 보너스
            
            final_score = relevance_score + keyword_bonus
            scored_questions.append((question, final_score))
        
        # 점수 순으로 정렬하고 상위 질문들 반환
        scored_questions.sort(key=lambda x: x[1], reverse=True)
        
        # 최소 점수 기준 (0.7) 이상인 질문들만 반환
        return [
            question for question, score in scored_questions 
            if score >= 0.7
        ][:5]  # 최대 5개
    
    async def _save_task_info(self, task_info: AsyncTask):
        """태스크 정보를 Redis에 저장"""
        
        try:
            cache_key = f"{self.cache_prefix}task:{task_info.id}"
            
            self.redis_client.setex(
                cache_key,
                3600,  # 1시간
                json.dumps(task_info.dict(), ensure_ascii=False, default=str)
            )
            
        except Exception as e:
            logger.error(f"Error saving task info: {e}")
            raise
    
    async def get_task_status(self, task_id: str) -> Optional[AsyncTask]:
        """태스크 상태 조회"""
        
        try:
            cache_key = f"{self.cache_prefix}task:{task_id}"
            task_data = self.redis_client.get(cache_key)
            
            if task_data:
                task_dict = json.loads(task_data)
                return AsyncTask(**task_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            return None
    
    async def cleanup_expired_cache(self):
        """만료된 캐시 정리"""
        
        try:
            # 만료된 세션 캐시 찾기 및 정리
            pattern = f"{self.cache_prefix}*"
            keys = self.redis_client.keys(pattern)
            
            expired_count = 0
            for key in keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -2:  # 키가 존재하지 않음
                    self.redis_client.delete(key)
                    expired_count += 1
            
            logger.info(f"Cleaned up {expired_count} expired cache entries")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {e}")
    
    async def invalidate_session_cache(self, session_id: str):
        """특정 세션의 캐시 무효화"""
        
        try:
            pattern = f"{self.cache_prefix}*:{session_id}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated cache for session {session_id}: {len(keys)} keys")
            
        except Exception as e:
            logger.error(f"Error invalidating session cache: {e}")
            raise