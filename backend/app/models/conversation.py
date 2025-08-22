from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from pydantic import BaseModel


class ConversationState(str, Enum):
    """대화 상태 정의"""
    INIT = "init"                           # 초기 상태
    PHOTO_BASED_CHAT = "photo_based_chat"   # 일반 사진 기반 대화
    CIST_EVALUATION = "cist_evaluation"     # CIST 인지기능 평가 중
    ASYNC_PROCESSING = "async_processing"   # 비동기 처리 중 (후보 질문 생성/평가)
    WAITING_CACHE = "waiting_cache"         # 캐시 조회 대기
    COMPLETED = "completed"                 # 대화 세션 완료


class CISTCategory(str, Enum):
    """CIST 검사 카테고리"""
    ORIENTATION_TIME = "orientation_time"       # 시간 지남력 (4점)
    ORIENTATION_PLACE = "orientation_place"     # 장소 지남력 (1점)
    MEMORY_REGISTRATION = "memory_registration" # 기억등록
    MEMORY_RECALL = "memory_recall"             # 기억회상
    MEMORY_RECOGNITION = "memory_recognition"   # 기억재인
    ATTENTION = "attention"                     # 주의력 (1점)
    EXECUTIVE_FUNCTION = "executive_function"   # 집행기능 (2점)
    LANGUAGE_NAMING = "language_naming"         # 언어기능 - 이름대기 (3점)


class ResponseType(str, Enum):
    """응답 타입"""
    PHOTO_CONVERSATION = "photo_conversation"   # 일반 사진 대화
    CIST_QUESTION = "cist_question"            # CIST 질문
    FOLLOWUP_QUESTION = "followup_question"    # 후속 질문
    EVALUATION_COMPLETE = "evaluation_complete" # 평가 완료


@dataclass
class ConversationContext:
    """대화 맥락 정보"""
    session_id: str
    user_id: str
    current_state: ConversationState
    turn_count: int = 0
    photo_ids: List[str] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    cist_progress: Dict[CISTCategory, bool] = field(default_factory=dict)
    cist_scores: Dict[CISTCategory, float] = field(default_factory=dict)
    cached_questions: List[Dict[str, Any]] = field(default_factory=list)
    current_photo_focus: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class ConversationMessage(BaseModel):
    """대화 메시지 모델"""
    id: str
    session_id: str
    user_id: str
    message_type: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Dict[str, Any] = {}
    timestamp: datetime
    photo_id: Optional[str] = None
    cist_category: Optional[CISTCategory] = None
    response_type: Optional[ResponseType] = None


class CISTQuestionCandidate(BaseModel):
    """CIST 질문 후보"""
    id: str
    session_id: str
    category: CISTCategory
    original_question: str
    adapted_question: str
    context_relevance_score: float
    naturalness_score: float
    difficulty_score: float
    overall_score: float
    photo_context: Optional[str] = None
    conversation_context: str
    created_at: datetime
    is_used: bool = False


class ConversationSession(BaseModel):
    """대화 세션 모델"""
    id: str
    user_id: str
    state: ConversationState
    photo_ids: List[str]
    context: Dict[str, Any]
    cist_progress: Dict[str, bool]
    cist_scores: Dict[str, float]
    total_turns: int
    start_time: datetime
    end_time: Optional[datetime] = None
    is_active: bool = True


class PathPrediction(BaseModel):
    """대화 경로 예측"""
    id: str
    session_id: str
    current_turn: int
    predicted_paths: List[Dict[str, Any]]
    confidence_scores: List[float]
    photo_context: Optional[str] = None
    conversation_context: str
    created_at: datetime


class AsyncTask(BaseModel):
    """비동기 작업 정보"""
    id: str
    task_type: str  # 'question_generation', 'question_evaluation', 'path_prediction'
    session_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    input_data: Dict[str, Any]
    result_data: Dict[str, Any] = {}
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# 상태 전환 규칙
STATE_TRANSITIONS = {
    ConversationState.INIT: [
        ConversationState.PHOTO_BASED_CHAT,
        ConversationState.CIST_EVALUATION
    ],
    ConversationState.PHOTO_BASED_CHAT: [
        ConversationState.CIST_EVALUATION,
        ConversationState.ASYNC_PROCESSING,
        ConversationState.COMPLETED
    ],
    ConversationState.CIST_EVALUATION: [
        ConversationState.PHOTO_BASED_CHAT,
        ConversationState.ASYNC_PROCESSING,
        ConversationState.COMPLETED
    ],
    ConversationState.ASYNC_PROCESSING: [
        ConversationState.WAITING_CACHE,
        ConversationState.PHOTO_BASED_CHAT,
        ConversationState.CIST_EVALUATION
    ],
    ConversationState.WAITING_CACHE: [
        ConversationState.CIST_EVALUATION,
        ConversationState.PHOTO_BASED_CHAT
    ],
    ConversationState.COMPLETED: []
}

# CIST 카테고리별 최대 점수
CIST_MAX_SCORES = {
    CISTCategory.ORIENTATION_TIME: 4,
    CISTCategory.ORIENTATION_PLACE: 1,
    CISTCategory.MEMORY_REGISTRATION: 3,
    CISTCategory.MEMORY_RECALL: 3,
    CISTCategory.MEMORY_RECOGNITION: 4,
    CISTCategory.ATTENTION: 1,
    CISTCategory.EXECUTIVE_FUNCTION: 2,
    CISTCategory.LANGUAGE_NAMING: 3
}