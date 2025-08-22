from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid
import json
import logging

from ..models.conversation import (
    ConversationState, ConversationContext, ConversationMessage,
    CISTCategory, ResponseType, ConversationSession
)
from .conversation_manager import ConversationManager
from .question_generator import QuestionGenerator
from .async_processor import AsyncProcessor

logger = logging.getLogger(__name__)


class ConversationService:
    """WebSocket 기반 실시간 대화 처리 서비스"""
    
    def __init__(
        self, 
        openai_api_key: str, 
        redis_url: str = "redis://localhost:6379"
    ):
        self.conversation_manager = ConversationManager()
        self.question_generator = QuestionGenerator(openai_api_key)
        self.async_processor = AsyncProcessor(redis_url, openai_api_key)
        
        # 세션 저장소 (실제로는 데이터베이스 사용)
        self.sessions: Dict[str, ConversationContext] = {}
    
    async def start_conversation_session(
        self,
        user_id: str,
        photo_ids: List[str],
        session_metadata: Dict[str, Any] = None
    ) -> ConversationContext:
        """대화 세션 시작"""
        
        session_id = str(uuid.uuid4())
        
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            current_state=ConversationState.INIT,
            photo_ids=photo_ids,
            conversation_history=[],
            cist_progress={category: False for category in CISTCategory},
            cist_scores={}
        )
        
        # 메모리에 저장 (실제로는 데이터베이스 저장)
        self.sessions[session_id] = context
        
        # 초기 상태를 사진 기반 대화로 전환
        self.conversation_manager.transition_state(
            context, 
            ConversationState.PHOTO_BASED_CHAT,
            "Session started"
        )
        
        logger.info(f"Started conversation session: {session_id} for user: {user_id}")
        return context
    
    async def process_user_message(
        self,
        session_id: str,
        user_message: str,
        photo_context: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """사용자 메시지 처리 및 응답 생성"""
        
        try:
            # 세션 정보 조회
            context = self.sessions.get(session_id)
            if not context:
                raise ValueError(f"Session not found: {session_id}")
            
            # 턴 수 증가
            context.turn_count += 1
            
            # 사용자 메시지 저장
            user_msg = ConversationMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                user_id=context.user_id,
                message_type="user",
                content=user_message,
                timestamp=datetime.now(),
                photo_id=photo_context,
                metadata=metadata or {}
            )
            context.conversation_history.append(user_msg.dict())
            
            # CIST 질문 삽입 여부 결정
            should_insert, cist_category, decision_reason = self.conversation_manager.should_insert_cist_question(
                context,
                user_message,
                context.conversation_history
            )
            
            logger.info(
                f"CIST insertion decision for session {session_id}: "
                f"insert={should_insert}, category={cist_category}, reason={decision_reason}"
            )
            
            # 응답 생성 및 처리
            if should_insert and cist_category:
                response_data = await self._handle_cist_question_flow(
                    context, cist_category, user_message, photo_context
                )
            else:
                response_data = await self._handle_regular_conversation_flow(
                    context, user_message, photo_context
                )
            
            # 응답 메시지 저장
            ai_msg = ConversationMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                user_id=context.user_id,
                message_type="assistant",
                content=response_data["content"],
                timestamp=datetime.now(),
                metadata=response_data.get("metadata", {}),
                response_type=response_data.get("response_type")
            )
            context.conversation_history.append(ai_msg.dict())
            
            # 컨텍스트 업데이트 시간 갱신
            context.updated_at = datetime.now()
            
            return {
                "success": True,
                "response": response_data,
                "session_info": {
                    "session_id": session_id,
                    "turn_count": context.turn_count,
                    "current_state": context.current_state,
                    "cist_progress": context.cist_progress
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing user message: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": {
                    "content": "죄송합니다. 일시적인 오류가 발생했습니다. 다시 말씀해 주시겠어요?",
                    "response_type": ResponseType.PHOTO_CONVERSATION
                }
            }
    
    async def _handle_cist_question_flow(
        self,
        context: ConversationContext,
        cist_category: CISTCategory,
        user_message: str,
        photo_context: Optional[str]
    ) -> Dict[str, Any]:
        """CIST 질문 삽입 플로우 처리"""
        
        try:
            # 상태를 캐시 대기로 전환
            self.conversation_manager.transition_state(
                context,
                ConversationState.WAITING_CACHE,
                f"Checking cache for {cist_category}"
            )
            
            # 캐시된 질문 조회
            conversation_context = self._build_conversation_context(context.conversation_history)
            cached_questions = await self.async_processor.get_cached_questions(
                context.session_id,
                cist_category,
                conversation_context
            )
            
            if cached_questions:
                # 캐시된 질문 사용
                selected_question = self._select_best_cached_question(
                    cached_questions, user_message, photo_context
                )
                
                # 상태를 CIST 평가로 전환
                self.conversation_manager.transition_state(
                    context,
                    ConversationState.CIST_EVALUATION,
                    f"Using cached question for {cist_category}"
                )
                
                return {
                    "content": selected_question.adapted_question,
                    "response_type": ResponseType.CIST_QUESTION,
                    "metadata": {
                        "cist_category": cist_category.value,
                        "question_source": "cache",
                        "question_id": selected_question.id,
                        "original_question": selected_question.original_question
                    }
                }
            
            else:
                # 캐시된 질문이 없는 경우
                return await self._handle_no_cached_questions(
                    context, cist_category, user_message, photo_context
                )
            
        except Exception as e:
            logger.error(f"Error in CIST question flow: {e}")
            # 오류 시 일반 대화로 폴백
            return await self._generate_fallback_response(context, user_message, photo_context)
    
    async def _handle_no_cached_questions(
        self,
        context: ConversationContext,
        cist_category: CISTCategory,
        user_message: str,
        photo_context: Optional[str]
    ) -> Dict[str, Any]:
        """캐시된 질문이 없는 경우 처리"""
        
        try:
            # 1. 실시간 가벼운 응답 생성
            conversation_context = self._build_conversation_context(context.conversation_history)
            
            light_response = await self.question_generator.generate_light_response(
                user_message,
                conversation_context,
                photo_context
            )
            
            # 2. 비동기 질문 생성 프로세스 시작
            task_id = await self.async_processor.trigger_async_question_generation(
                context.session_id,
                cist_category,
                conversation_context,
                photo_context,
                context.conversation_history[-10:],  # 최근 10개 메시지
                light_response
            )
            
            # 3. 상태를 비동기 처리로 전환
            self.conversation_manager.transition_state(
                context,
                ConversationState.ASYNC_PROCESSING,
                f"Async generation started for {cist_category}"
            )
            
            return {
                "content": light_response,
                "response_type": ResponseType.PHOTO_CONVERSATION,
                "metadata": {
                    "async_task_id": task_id,
                    "pending_cist_category": cist_category.value,
                    "response_source": "light_llm"
                }
            }
            
        except Exception as e:
            logger.error(f"Error handling no cached questions: {e}")
            return await self._generate_fallback_response(context, user_message, photo_context)
    
    async def _handle_regular_conversation_flow(
        self,
        context: ConversationContext,
        user_message: str,
        photo_context: Optional[str]
    ) -> Dict[str, Any]:
        """일반 대화 플로우 처리"""
        
        try:
            conversation_context = self._build_conversation_context(context.conversation_history)
            
            # 가벼운 LLM을 사용한 사진 기반 대화 응답 생성
            response_content = await self.question_generator.generate_light_response(
                user_message,
                conversation_context,
                photo_context
            )
            
            # 상태를 사진 기반 대화로 유지
            if context.current_state != ConversationState.PHOTO_BASED_CHAT:
                self.conversation_manager.transition_state(
                    context,
                    ConversationState.PHOTO_BASED_CHAT,
                    "Regular conversation"
                )
            
            return {
                "content": response_content,
                "response_type": ResponseType.PHOTO_CONVERSATION,
                "metadata": {
                    "conversation_type": "photo_based",
                    "response_source": "light_llm"
                }
            }
            
        except Exception as e:
            logger.error(f"Error in regular conversation flow: {e}")
            return await self._generate_fallback_response(context, user_message, photo_context)
    
    def _select_best_cached_question(
        self,
        cached_questions: List,
        user_message: str,
        photo_context: Optional[str]
    ) -> Any:
        """캐시된 질문 중 가장 적절한 질문 선택"""
        
        if not cached_questions:
            raise ValueError("No cached questions available")
        
        # 현재는 overall_score가 가장 높은 질문 선택
        # 향후 더 정교한 선택 로직 구현 가능
        return max(cached_questions, key=lambda q: q.overall_score)
    
    def _build_conversation_context(self, conversation_history: List[Dict[str, Any]]) -> str:
        """대화 히스토리를 문자열 맥락으로 변환"""
        
        context_parts = []
        
        # 최근 5개 메시지만 사용
        recent_messages = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
        
        for msg in recent_messages:
            speaker = "사용자" if msg.get("message_type") == "user" else "AI"
            content = msg.get("content", "")
            context_parts.append(f"{speaker}: {content}")
        
        return "\n".join(context_parts)
    
    async def _generate_fallback_response(
        self,
        context: ConversationContext,
        user_message: str,
        photo_context: Optional[str]
    ) -> Dict[str, Any]:
        """오류 시 폴백 응답 생성"""
        
        fallback_responses = [
            "네, 말씀해 주신 내용이 정말 흥미롭네요. 더 자세히 들려주시겠어요?",
            "그렇군요. 그때 어떤 기분이셨는지도 궁금하네요.",
            "정말 좋은 추억이시군요. 다른 이야기도 들려주세요.",
            "사진을 보니 그때가 떠오르시나요? 어떤 느낌이신가요?"
        ]
        
        import random
        selected_response = random.choice(fallback_responses)
        
        return {
            "content": selected_response,
            "response_type": ResponseType.PHOTO_CONVERSATION,
            "metadata": {
                "response_source": "fallback"
            }
        }
    
    async def handle_cist_answer(
        self,
        session_id: str,
        cist_category: CISTCategory,
        user_answer: str,
        question_id: str
    ) -> Dict[str, Any]:
        """CIST 질문에 대한 사용자 답변 처리"""
        
        try:
            context = self.sessions.get(session_id)
            if not context:
                raise ValueError(f"Session not found: {session_id}")
            
            # TODO: 실제 CIST 평가 로직 구현
            # 현재는 더미 점수 사용
            import random
            score = random.uniform(0.5, 1.0) * CIST_MAX_SCORES.get(cist_category, 1)
            
            # CIST 진행 상황 업데이트
            self.conversation_manager.update_cist_progress(context, cist_category, score)
            
            # 완료 상태 확인
            completion_status = self.conversation_manager.get_conversation_completion_status(context)
            
            if completion_status["is_complete"]:
                # 모든 CIST 완료 시
                self.conversation_manager.transition_state(
                    context,
                    ConversationState.COMPLETED,
                    "All CIST categories completed"
                )
                
                response_content = (
                    "정말 훌륭하게 대화해주셨네요! "
                    "오늘 나눈 이야기들이 정말 소중한 추억들이었습니다. "
                    "결과 리포트를 확인해보세요."
                )
            else:
                # 일반 대화로 복귀
                self.conversation_manager.transition_state(
                    context,
                    ConversationState.PHOTO_BASED_CHAT,
                    "CIST answer processed, returning to conversation"
                )
                
                response_content = (
                    "네, 감사합니다. 그런데 이 사진을 보니 "
                    "또 다른 추억이 떠오르시나요?"
                )
            
            return {
                "success": True,
                "response": {
                    "content": response_content,
                    "response_type": ResponseType.FOLLOWUP_QUESTION
                },
                "cist_result": {
                    "category": cist_category.value,
                    "score": score,
                    "max_score": CIST_MAX_SCORES.get(cist_category, 1)
                },
                "completion_status": completion_status
            }
            
        except Exception as e:
            logger.error(f"Error handling CIST answer: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 상태 조회"""
        
        context = self.sessions.get(session_id)
        if not context:
            return None
        
        completion_status = self.conversation_manager.get_conversation_completion_status(context)
        
        return {
            "session_id": session_id,
            "user_id": context.user_id,
            "current_state": context.current_state,
            "turn_count": context.turn_count,
            "photo_ids": context.photo_ids,
            "cist_progress": context.cist_progress,
            "cist_scores": context.cist_scores,
            "completion_status": completion_status,
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat()
        }
    
    async def end_conversation_session(self, session_id: str) -> Dict[str, Any]:
        """대화 세션 종료"""
        
        try:
            context = self.sessions.get(session_id)
            if not context:
                raise ValueError(f"Session not found: {session_id}")
            
            # 세션 상태를 완료로 변경
            self.conversation_manager.transition_state(
                context,
                ConversationState.COMPLETED,
                "Session manually ended"
            )
            
            # 최종 상태 정보 생성
            completion_status = self.conversation_manager.get_conversation_completion_status(context)
            
            # 캐시 정리
            await self.async_processor.invalidate_session_cache(session_id)
            
            # 세션 정리 (실제로는 DB에 저장 후 메모리에서 제거)
            final_context = self.sessions.pop(session_id, None)
            
            logger.info(f"Ended conversation session: {session_id}")
            
            return {
                "success": True,
                "session_summary": {
                    "session_id": session_id,
                    "total_turns": final_context.turn_count if final_context else 0,
                    "completion_status": completion_status,
                    "duration_minutes": (
                        (final_context.updated_at - final_context.created_at).total_seconds() / 60
                        if final_context else 0
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Error ending conversation session: {e}")
            return {
                "success": False,
                "error": str(e)
            }