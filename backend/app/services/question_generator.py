from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid
import json
import asyncio
import logging

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser, JsonOutputParser

from ..models.conversation import (
    ConversationContext, CISTCategory, CISTQuestionCandidate,
    PathPrediction, CIST_MAX_SCORES
)

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """다중 경로 예측 및 CIST 질문 후보 생성"""
    
    def __init__(self, openai_api_key: str):
        # LLM 모델 설정
        self.llm_heavy = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=openai_api_key
        )
        
        self.llm_light = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.6,
            openai_api_key=openai_api_key
        )
        
        # CIST 원본 질문 템플릿
        self.cist_templates = self._load_cist_templates()
        
        # 프롬프트 템플릿들
        self._setup_prompts()
    
    def _load_cist_templates(self) -> Dict[CISTCategory, List[str]]:
        """CIST 원본 질문 템플릿 로드"""
        return {
            CISTCategory.ORIENTATION_TIME: [
                "오늘이 몇 년도인지 말씀해 주세요.",
                "지금이 몇 월인지 알려주세요.",
                "오늘이 며칠인지 말씀해 주세요.",
                "오늘이 무슨 요일인지 알려주세요."
            ],
            CISTCategory.ORIENTATION_PLACE: [
                "지금 계신 이곳이 어디인지 말씀해 주세요."
            ],
            CISTCategory.MEMORY_REGISTRATION: [
                "제가 말하는 문장을 그대로 따라해 주세요: '{sentence}'",
                "다음 단어들을 기억해 주세요: {words}. 잠시 후 다시 물어보겠습니다."
            ],
            CISTCategory.MEMORY_RECALL: [
                "조금 전에 말씀드린 단어들을 기억나는 대로 말씀해 주세요.",
                "앞서 들려드린 문장을 다시 말씀해 주실 수 있나요?"
            ],
            CISTCategory.MEMORY_RECOGNITION: [
                "이 중에서 앞서 말씀드린 단어는 어느 것인가요?",
                "방금 전 들려드린 것과 같은 내용은 어느 것인가요?"
            ],
            CISTCategory.ATTENTION: [
                "제가 말하는 숫자를 거꾸로 말씀해 주세요: {numbers}",
                "다음 단어를 거꾸로 말씀해 주세요: {word}"
            ],
            CISTCategory.EXECUTIVE_FUNCTION: [
                "1분 동안 {category} 종류의 단어를 최대한 많이 말씀해 주세요.",
                "{category}에 속하는 것들을 아는 대로 말씀해 주세요."
            ],
            CISTCategory.LANGUAGE_NAMING: [
                "이 사진에 보이는 {object}의 이름이 무엇인지 말씀해 주세요.",
                "사진 속 {object}를 뭐라고 부르는지 알려주세요."
            ]
        }
    
    def _setup_prompts(self):
        """프롬프트 템플릿 설정"""
        
        # 경로 예측 프롬프트
        self.path_prediction_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            당신은 치매 조기진단을 위한 대화형 AI 시스템의 경로 예측 전문가입니다.
            
            주어진 대화 맥락을 바탕으로 사용자가 다음에 할 수 있는 응답들을 예측하고,
            각 응답에 대한 확률과 그에 따른 대화 흐름을 분석해주세요.
            
            고려사항:
            1. 사용자는 고령층으로 사진을 보며 추억을 회상하는 상황
            2. 자연스러운 대화 흐름 유지가 중요
            3. 사용자의 인지 상태와 감정 상태 고려
            4. 사진과 관련된 기억이나 경험 중심의 응답 예상
            """),
            ("human", """
            대화 맥락:
            사진 정보: {photo_context}
            현재까지 대화: {conversation_history}
            마지막 AI 응답: {last_ai_response}
            
            다음 3-5가지 가능한 사용자 응답 경로를 예측하고, 
            각각에 대한 확률(0-1)과 예상 응답 내용을 JSON 형태로 제공해주세요.
            
            응답 형식:
            {{
                "predicted_paths": [
                    {{
                        "path_id": "path_1",
                        "probability": 0.4,
                        "predicted_response": "예상 사용자 응답",
                        "response_type": "memory_recall|photo_description|emotion_expression|question|general",
                        "reasoning": "이 응답을 예측한 이유"
                    }}
                ]
            }}
            """)
        ])
        
        # 질문 생성 프롬프트
        self.question_generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            당신은 CIST(치매 조기진단 선별검사) 질문을 자연스러운 대화에 녹여내는 전문가입니다.
            
            원본 CIST 질문을 주어진 대화 맥락과 사진 정보에 맞게 자연스럽게 변형해주세요.
            
            변형 원칙:
            1. 의학적 검사 느낌을 최소화하고 일상 대화처럼 만들기
            2. 사진이나 현재 대화 주제와 연관성 있게 변형
            3. 사용자가 부담스러워하지 않을 친근한 톤 사용
            4. 원본 질문의 인지기능 평가 목적은 유지
            """),
            ("human", """
            변형할 CIST 질문 정보:
            카테고리: {cist_category}
            원본 질문: {original_question}
            
            대화 맥락:
            사진 정보: {photo_context}
            현재 대화 흐름: {conversation_context}
            예상 사용자 응답: {predicted_user_response}
            
            다음 3가지 변형된 질문을 생성해주세요:
            
            응답 형식:
            {{
                "adapted_questions": [
                    {{
                        "question": "자연스럽게 변형된 질문",
                        "adaptation_strategy": "변형 전략 설명",
                        "naturalness_score": 0.85,
                        "context_relevance_score": 0.9
                    }}
                ]
            }}
            """)
        ])
        
        # 질문 평가 프롬프트
        self.question_evaluation_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            당신은 CIST 질문의 적절성을 평가하는 전문가입니다.
            
            생성된 질문들을 다음 기준으로 평가해주세요:
            1. 자연스러움 (0-1): 일상 대화처럼 자연스러운가?
            2. 맥락 관련성 (0-1): 현재 대화 맥락에 적절한가?
            3. 난이도 적절성 (0-1): 사용자에게 적절한 난이도인가?
            4. 평가 유효성 (0-1): 원본 CIST 의도를 유지하는가?
            """),
            ("human", """
            평가할 질문들:
            {questions_to_evaluate}
            
            대화 맥락:
            {evaluation_context}
            
            각 질문에 대해 상세한 평가를 해주세요:
            
            응답 형식:
            {{
                "evaluations": [
                    {{
                        "question_id": "question_1",
                        "naturalness_score": 0.85,
                        "context_relevance_score": 0.9,
                        "difficulty_score": 0.8,
                        "evaluation_validity_score": 0.95,
                        "overall_score": 0.875,
                        "pass_threshold": true,
                        "feedback": "평가 의견"
                    }}
                ]
            }}
            """)
        ])
    
    async def predict_conversation_paths(
        self,
        conversation_context: str,
        photo_context: Optional[str],
        conversation_history: List[Dict[str, Any]],
        last_ai_response: str
    ) -> PathPrediction:
        """대화 경로 예측"""
        
        try:
            # 대화 히스토리를 문자열로 변환
            history_str = self._format_conversation_history(conversation_history)
            
            # LLM을 사용한 경로 예측
            chain = self.path_prediction_prompt | self.llm_heavy | JsonOutputParser()
            
            result = await chain.ainvoke({
                "photo_context": photo_context or "사진 정보 없음",
                "conversation_history": history_str,
                "last_ai_response": last_ai_response
            })
            
            # PathPrediction 객체 생성
            prediction = PathPrediction(
                id=str(uuid.uuid4()),
                session_id="",  # 호출하는 곳에서 설정
                current_turn=len(conversation_history),
                predicted_paths=result["predicted_paths"],
                confidence_scores=[path["probability"] for path in result["predicted_paths"]],
                photo_context=photo_context,
                conversation_context=conversation_context,
                created_at=datetime.now()
            )
            
            logger.info(f"Generated {len(prediction.predicted_paths)} conversation paths")
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting conversation paths: {e}")
            raise
    
    async def generate_question_candidates(
        self,
        cist_category: CISTCategory,
        conversation_context: str,
        photo_context: Optional[str],
        predicted_paths: List[Dict[str, Any]],
        session_id: str
    ) -> List[CISTQuestionCandidate]:
        """CIST 질문 후보 생성"""
        
        candidates = []
        original_questions = self.cist_templates[cist_category]
        
        try:
            # 각 원본 질문과 예측 경로 조합으로 후보 생성
            for original_question in original_questions:
                for path in predicted_paths:
                    
                    # 질문 생성
                    chain = self.question_generation_prompt | self.llm_heavy | JsonOutputParser()
                    
                    result = await chain.ainvoke({
                        "cist_category": cist_category.value,
                        "original_question": original_question,
                        "photo_context": photo_context or "사진 정보 없음",
                        "conversation_context": conversation_context,
                        "predicted_user_response": path["predicted_response"]
                    })
                    
                    # 생성된 질문들을 후보로 변환
                    for adapted_q in result["adapted_questions"]:
                        candidate = CISTQuestionCandidate(
                            id=str(uuid.uuid4()),
                            session_id=session_id,
                            category=cist_category,
                            original_question=original_question,
                            adapted_question=adapted_q["question"],
                            context_relevance_score=adapted_q["context_relevance_score"],
                            naturalness_score=adapted_q["naturalness_score"],
                            difficulty_score=0.0,  # 평가 단계에서 설정
                            overall_score=0.0,     # 평가 단계에서 설정
                            photo_context=photo_context,
                            conversation_context=conversation_context,
                            created_at=datetime.now()
                        )
                        candidates.append(candidate)
            
            logger.info(f"Generated {len(candidates)} question candidates for {cist_category}")
            return candidates
            
        except Exception as e:
            logger.error(f"Error generating question candidates: {e}")
            raise
    
    async def evaluate_question_candidates(
        self,
        candidates: List[CISTQuestionCandidate],
        evaluation_context: Dict[str, Any]
    ) -> List[CISTQuestionCandidate]:
        """질문 후보 평가"""
        
        try:
            # 평가를 위한 데이터 준비
            questions_data = [
                {
                    "question_id": candidate.id,
                    "question": candidate.adapted_question,
                    "category": candidate.category.value,
                    "original": candidate.original_question
                }
                for candidate in candidates
            ]
            
            # LLM을 사용한 질문 평가
            chain = self.question_evaluation_prompt | self.llm_heavy | JsonOutputParser()
            
            result = await chain.ainvoke({
                "questions_to_evaluate": json.dumps(questions_data, ensure_ascii=False),
                "evaluation_context": json.dumps(evaluation_context, ensure_ascii=False)
            })
            
            # 평가 결과를 후보 객체에 반영
            evaluation_map = {
                eval_result["question_id"]: eval_result 
                for eval_result in result["evaluations"]
            }
            
            evaluated_candidates = []
            for candidate in candidates:
                if candidate.id in evaluation_map:
                    eval_data = evaluation_map[candidate.id]
                    
                    candidate.difficulty_score = eval_data["difficulty_score"]
                    candidate.overall_score = eval_data["overall_score"]
                    
                    # 임계값 통과한 후보만 유지
                    if eval_data["pass_threshold"]:
                        evaluated_candidates.append(candidate)
            
            logger.info(
                f"Evaluated {len(candidates)} candidates, "
                f"{len(evaluated_candidates)} passed threshold"
            )
            return evaluated_candidates
            
        except Exception as e:
            logger.error(f"Error evaluating question candidates: {e}")
            raise
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        """대화 히스토리를 문자열로 포맷"""
        formatted = []
        for msg in history[-10:]:  # 최근 10개 메시지만 사용
            speaker = "사용자" if msg.get("message_type") == "user" else "AI"
            content = msg.get("content", "")
            formatted.append(f"{speaker}: {content}")
        
        return "\n".join(formatted)
    
    async def generate_light_response(
        self,
        user_message: str,
        conversation_context: str,
        photo_context: Optional[str]
    ) -> str:
        """실시간 응답을 위한 가벼운 LLM 사용"""
        
        light_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            당신은 고령층 사용자와 사진을 보며 추억을 나누는 친근한 AI입니다.
            사용자의 메시지에 따뜻하고 공감적으로 응답해주세요.
            
            응답 가이드라인:
            1. 친근하고 존중하는 톤 사용
            2. 사용자의 감정과 기억에 공감
            3. 추가 대화를 유도하는 자연스러운 질문 포함
            4. 2-3문장으로 간결하게 응답
            """),
            ("human", """
            사진 맥락: {photo_context}
            대화 맥락: {conversation_context}
            사용자 메시지: {user_message}
            
            따뜻하고 자연스러운 응답을 해주세요.
            """)
        ])
        
        try:
            chain = light_prompt | self.llm_light
            
            response = await chain.ainvoke({
                "photo_context": photo_context or "사진을 함께 보고 있습니다",
                "conversation_context": conversation_context,
                "user_message": user_message
            })
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating light response: {e}")
            return "네, 말씀해 주신 내용이 정말 흥미롭네요. 더 자세히 들려주시겠어요?"