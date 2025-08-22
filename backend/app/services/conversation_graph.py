from typing import Dict, List, Optional, Any, Annotated, TypedDict
from datetime import datetime
import uuid
import logging

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from ..models.conversation import (
    ConversationState, ConversationContext, CISTCategory, 
    ResponseType, CIST_MAX_SCORES
)
from .conversation_manager import ConversationManager
from .question_generator import QuestionGenerator
from .async_processor import AsyncProcessor

logger = logging.getLogger(__name__)


class ConversationGraphState(TypedDict):
    """LangGraph 상태 정의"""
    # 메시지 히스토리
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 세션 정보
    session_id: str
    user_id: str
    turn_count: int
    
    # 대화 상태
    current_state: ConversationState
    
    # 사진 관련
    photo_ids: List[str]
    current_photo_context: Optional[str]
    
    # CIST 관련
    cist_progress: Dict[str, bool]
    cist_scores: Dict[str, float]
    should_insert_cist: bool
    target_cist_category: Optional[str]
    cist_decision_reason: str
    
    # 캐시 관련
    cached_questions_available: bool
    selected_question: Optional[Dict[str, Any]]
    
    # 비동기 작업
    async_task_id: Optional[str]
    
    # 응답 관련
    response_content: str
    response_type: ResponseType
    response_metadata: Dict[str, Any]
    
    # 제어 플래그
    needs_async_processing: bool
    is_session_complete: bool


class ConversationGraph:
    """LangGraph 기반 대화 워크플로우"""
    
    def __init__(
        self, 
        openai_api_key: str, 
        redis_url: str = "redis://localhost:6379"
    ):
        self.conversation_manager = ConversationManager()
        self.question_generator = QuestionGenerator(openai_api_key)
        self.async_processor = AsyncProcessor(redis_url, openai_api_key)
        
        # LangGraph 구성
        self.graph = self._build_graph()
        self.app = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """LangGraph 워크플로우 구성"""
        
        workflow = StateGraph(ConversationGraphState)
        
        # 노드 추가
        workflow.add_node("analyze_input", self._analyze_input_node)
        workflow.add_node("decide_cist_insertion", self._decide_cist_insertion_node)
        workflow.add_node("check_cached_questions", self._check_cached_questions_node)
        workflow.add_node("use_cached_question", self._use_cached_question_node)
        workflow.add_node("generate_light_response", self._generate_light_response_node)
        workflow.add_node("trigger_async_processing", self._trigger_async_processing_node)
        workflow.add_node("handle_cist_answer", self._handle_cist_answer_node)
        workflow.add_node("check_completion", self._check_completion_node)
        workflow.add_node("finalize_response", self._finalize_response_node)
        
        # 시작점 설정
        workflow.set_entry_point("analyze_input")
        
        # 조건부 엣지 추가
        workflow.add_conditional_edges(
            "analyze_input",
            self._route_after_analysis,
            {
                "decide_cist": "decide_cist_insertion",
                "handle_cist_answer": "handle_cist_answer",
                "regular_conversation": "generate_light_response"
            }
        )
        
        workflow.add_conditional_edges(
            "decide_cist_insertion",
            self._route_after_cist_decision,
            {
                "check_cache": "check_cached_questions",
                "regular_conversation": "generate_light_response"
            }
        )
        
        workflow.add_conditional_edges(
            "check_cached_questions",
            self._route_after_cache_check,
            {
                "use_cached": "use_cached_question",
                "need_generation": "generate_light_response"
            }
        )
        
        workflow.add_edge("use_cached_question", "finalize_response")
        
        workflow.add_conditional_edges(
            "generate_light_response",
            self._route_after_light_response,
            {
                "trigger_async": "trigger_async_processing",
                "finalize": "finalize_response"
            }
        )
        
        workflow.add_edge("trigger_async_processing", "finalize_response")
        workflow.add_edge("handle_cist_answer", "check_completion")
        
        workflow.add_conditional_edges(
            "check_completion",
            self._route_after_completion_check,
            {
                "complete": "finalize_response",
                "continue": "generate_light_response"
            }
        )
        
        workflow.add_edge("finalize_response", END)
        
        return workflow
    
    async def process_conversation_turn(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        photo_context: Optional[str] = None,
        conversation_history: List[Dict[str, Any]] = None,
        cist_progress: Dict[str, bool] = None,
        cist_scores: Dict[str, float] = None,
        turn_count: int = 0,
        photo_ids: List[str] = None
    ) -> Dict[str, Any]:
        """대화 턴 처리"""
        
        try:
            # 초기 상태 구성
            initial_state = ConversationGraphState(
                messages=[HumanMessage(content=user_message)],
                session_id=session_id,
                user_id=user_id,
                turn_count=turn_count,
                current_state=ConversationState.PHOTO_BASED_CHAT,
                photo_ids=photo_ids or [],
                current_photo_context=photo_context,
                cist_progress=cist_progress or {},
                cist_scores=cist_scores or {},
                should_insert_cist=False,
                target_cist_category=None,
                cist_decision_reason="",
                cached_questions_available=False,
                selected_question=None,
                async_task_id=None,
                response_content="",
                response_type=ResponseType.PHOTO_CONVERSATION,
                response_metadata={},
                needs_async_processing=False,
                is_session_complete=False
            )
            
            # 그래프 실행
            final_state = await self.app.ainvoke(initial_state)
            
            return {
                "success": True,
                "response": {
                    "content": final_state["response_content"],
                    "response_type": final_state["response_type"],
                    "metadata": final_state["response_metadata"]
                },
                "session_info": {
                    "session_id": session_id,
                    "turn_count": final_state["turn_count"],
                    "current_state": final_state["current_state"],
                    "cist_progress": final_state["cist_progress"],
                    "cist_scores": final_state["cist_scores"],
                    "is_complete": final_state["is_session_complete"]
                },
                "async_info": {
                    "task_id": final_state["async_task_id"],
                    "needs_processing": final_state["needs_async_processing"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in conversation graph processing: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": {
                    "content": "죄송합니다. 일시적인 오류가 발생했습니다. 다시 말씀해 주시겠어요?",
                    "response_type": ResponseType.PHOTO_CONVERSATION,
                    "metadata": {"error": True}
                }
            }
    
    async def _analyze_input_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """입력 분석 노드"""
        
        logger.info(f"Analyzing input for session {state['session_id']}")
        
        # 메시지 타입 분석
        last_message = state["messages"][-1].content
        
        # CIST 답변인지 확인 (메타데이터 기반)
        is_cist_answer = state.get("response_metadata", {}).get("awaiting_cist_answer", False)
        
        if is_cist_answer:
            state["current_state"] = ConversationState.CIST_EVALUATION
        else:
            state["current_state"] = ConversationState.PHOTO_BASED_CHAT
        
        state["turn_count"] += 1
        return state
    
    async def _decide_cist_insertion_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """CIST 삽입 결정 노드"""
        
        logger.info(f"Deciding CIST insertion for session {state['session_id']}")
        
        # ConversationContext 구성
        context = self._build_conversation_context(state)
        
        # 대화 히스토리 구성
        conversation_history = self._build_conversation_history(state["messages"])
        
        # CIST 삽입 결정
        should_insert, cist_category, reason = self.conversation_manager.should_insert_cist_question(
            context,
            state["messages"][-1].content,
            conversation_history
        )
        
        state["should_insert_cist"] = should_insert
        state["target_cist_category"] = cist_category.value if cist_category else None
        state["cist_decision_reason"] = reason
        
        logger.info(
            f"CIST decision: insert={should_insert}, "
            f"category={cist_category}, reason={reason}"
        )
        
        return state
    
    async def _check_cached_questions_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """캐시된 질문 확인 노드"""
        
        logger.info(f"Checking cached questions for session {state['session_id']}")
        
        if not state["target_cist_category"]:
            state["cached_questions_available"] = False
            return state
        
        # 대화 컨텍스트 구성
        conversation_context = self._build_conversation_context_string(state["messages"])
        
        # 캐시된 질문 조회
        cached_questions = await self.async_processor.get_cached_questions(
            state["session_id"],
            CISTCategory(state["target_cist_category"]),
            conversation_context
        )
        
        if cached_questions:
            # 가장 적절한 질문 선택
            best_question = max(cached_questions, key=lambda q: q.overall_score)
            state["selected_question"] = {
                "id": best_question.id,
                "content": best_question.adapted_question,
                "category": best_question.category.value,
                "original": best_question.original_question,
                "score": best_question.overall_score
            }
            state["cached_questions_available"] = True
        else:
            state["cached_questions_available"] = False
        
        logger.info(
            f"Cache check result: available={state['cached_questions_available']}, "
            f"found={len(cached_questions)} questions"
        )
        
        return state
    
    async def _use_cached_question_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """캐시된 질문 사용 노드"""
        
        logger.info(f"Using cached question for session {state['session_id']}")
        
        if not state["selected_question"]:
            raise ValueError("No cached question selected")
        
        question = state["selected_question"]
        
        state["response_content"] = question["content"]
        state["response_type"] = ResponseType.CIST_QUESTION
        state["response_metadata"] = {
            "cist_category": question["category"],
            "question_source": "cache",
            "question_id": question["id"],
            "original_question": question["original"],
            "awaiting_cist_answer": True
        }
        state["current_state"] = ConversationState.CIST_EVALUATION
        
        return state
    
    async def _generate_light_response_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """가벼운 응답 생성 노드"""
        
        logger.info(f"Generating light response for session {state['session_id']}")
        
        user_message = state["messages"][-1].content
        conversation_context = self._build_conversation_context_string(state["messages"])
        
        # 가벼운 LLM으로 응답 생성
        response_content = await self.question_generator.generate_light_response(
            user_message,
            conversation_context,
            state["current_photo_context"]
        )
        
        state["response_content"] = response_content
        state["response_type"] = ResponseType.PHOTO_CONVERSATION
        state["response_metadata"] = {
            "response_source": "light_llm",
            "conversation_type": "photo_based"
        }
        
        # 비동기 처리 필요 여부 결정
        if (state["should_insert_cist"] and 
            state["target_cist_category"] and 
            not state["cached_questions_available"]):
            state["needs_async_processing"] = True
        
        return state
    
    async def _trigger_async_processing_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """비동기 처리 시작 노드"""
        
        logger.info(f"Triggering async processing for session {state['session_id']}")
        
        if not state["target_cist_category"]:
            return state
        
        # 대화 컨텍스트 구성
        conversation_context = self._build_conversation_context_string(state["messages"])
        conversation_history = self._build_conversation_history(state["messages"])
        
        # 비동기 질문 생성 시작
        task_id = await self.async_processor.trigger_async_question_generation(
            state["session_id"],
            CISTCategory(state["target_cist_category"]),
            conversation_context,
            state["current_photo_context"],
            conversation_history,
            state["response_content"]
        )
        
        state["async_task_id"] = task_id
        state["current_state"] = ConversationState.ASYNC_PROCESSING
        state["response_metadata"]["async_task_id"] = task_id
        state["response_metadata"]["pending_cist_category"] = state["target_cist_category"]
        
        return state
    
    async def _handle_cist_answer_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """CIST 답변 처리 노드"""
        
        logger.info(f"Handling CIST answer for session {state['session_id']}")
        
        # TODO: 실제 CIST 평가 로직 구현
        # 현재는 더미 처리
        import random
        
        cist_category = state.get("target_cist_category")
        if cist_category:
            category_enum = CISTCategory(cist_category)
            max_score = CIST_MAX_SCORES.get(category_enum, 1)
            score = random.uniform(0.6, 1.0) * max_score
            
            # 점수 저장
            state["cist_scores"][cist_category] = score
            state["cist_progress"][cist_category] = True
            
            state["response_metadata"]["cist_result"] = {
                "category": cist_category,
                "score": score,
                "max_score": max_score
            }
        
        return state
    
    async def _check_completion_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """완료 상태 확인 노드"""
        
        logger.info(f"Checking completion for session {state['session_id']}")
        
        # 모든 CIST 카테고리 완료 확인
        total_categories = len(CISTCategory)
        completed_categories = len([v for v in state["cist_progress"].values() if v])
        
        if completed_categories >= total_categories:
            state["is_session_complete"] = True
            state["current_state"] = ConversationState.COMPLETED
            
            # 완료 메시지 생성
            total_score = sum(state["cist_scores"].values())
            max_total_score = sum(CIST_MAX_SCORES.values())
            
            state["response_content"] = (
                f"정말 훌륭하게 대화해주셨네요! "
                f"오늘 나눈 이야기들이 정말 소중한 추억들이었습니다. "
                f"평가 결과: {total_score:.1f}/{max_total_score}점"
            )
            state["response_type"] = ResponseType.EVALUATION_COMPLETE
            
        else:
            state["is_session_complete"] = False
        
        return state
    
    async def _finalize_response_node(self, state: ConversationGraphState) -> ConversationGraphState:
        """응답 마무리 노드"""
        
        logger.info(f"Finalizing response for session {state['session_id']}")
        
        # AI 메시지 추가
        ai_message = AIMessage(content=state["response_content"])
        state["messages"].append(ai_message)
        
        # 메타데이터 최종 업데이트
        state["response_metadata"]["timestamp"] = datetime.now().isoformat()
        state["response_metadata"]["turn_count"] = state["turn_count"]
        
        return state
    
    # 라우팅 함수들
    def _route_after_analysis(self, state: ConversationGraphState) -> str:
        """분석 후 라우팅"""
        if state["current_state"] == ConversationState.CIST_EVALUATION:
            return "handle_cist_answer"
        else:
            return "decide_cist"
    
    def _route_after_cist_decision(self, state: ConversationGraphState) -> str:
        """CIST 결정 후 라우팅"""
        if state["should_insert_cist"]:
            return "check_cache"
        else:
            return "regular_conversation"
    
    def _route_after_cache_check(self, state: ConversationGraphState) -> str:
        """캐시 확인 후 라우팅"""
        if state["cached_questions_available"]:
            return "use_cached"
        else:
            return "need_generation"
    
    def _route_after_light_response(self, state: ConversationGraphState) -> str:
        """가벼운 응답 후 라우팅"""
        if state["needs_async_processing"]:
            return "trigger_async"
        else:
            return "finalize"
    
    def _route_after_completion_check(self, state: ConversationGraphState) -> str:
        """완료 확인 후 라우팅"""
        if state["is_session_complete"]:
            return "complete"
        else:
            return "continue"
    
    # 헬퍼 함수들
    def _build_conversation_context(self, state: ConversationGraphState) -> ConversationContext:
        """ConversationContext 객체 구성"""
        return ConversationContext(
            session_id=state["session_id"],
            user_id=state["user_id"],
            current_state=state["current_state"],
            turn_count=state["turn_count"],
            photo_ids=state["photo_ids"],
            conversation_history=self._build_conversation_history(state["messages"]),
            cist_progress={CISTCategory(k): v for k, v in state["cist_progress"].items()},
            cist_scores={CISTCategory(k): v for k, v in state["cist_scores"].items()},
            current_photo_focus=state["current_photo_context"]
        )
    
    def _build_conversation_history(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """메시지를 대화 히스토리로 변환"""
        history = []
        
        for msg in messages:
            if isinstance(msg, HumanMessage):
                msg_type = "user"
            elif isinstance(msg, AIMessage):
                msg_type = "assistant"
            else:
                msg_type = "system"
            
            history.append({
                "id": str(uuid.uuid4()),
                "message_type": msg_type,
                "content": msg.content,
                "timestamp": datetime.now().isoformat()
            })
        
        return history
    
    def _build_conversation_context_string(self, messages: List[BaseMessage]) -> str:
        """메시지를 문자열 맥락으로 변환"""
        context_parts = []
        
        # 최근 5개 메시지만 사용
        recent_messages = messages[-5:] if len(messages) > 5 else messages
        
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                speaker = "사용자"
            elif isinstance(msg, AIMessage):
                speaker = "AI"
            else:
                continue
            
            context_parts.append(f"{speaker}: {msg.content}")
        
        return "\n".join(context_parts)