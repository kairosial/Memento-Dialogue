from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class SessionType(str, Enum):
    reminiscence = "reminiscence"
    assessment = "assessment"
    mixed = "mixed"


class SessionStatus(str, Enum):
    active = "active"
    completed = "completed"
    paused = "paused"
    cancelled = "cancelled"


class ConversationType(str, Enum):
    open_ended = "open_ended"
    cist_orientation = "cist_orientation"
    cist_memory = "cist_memory"
    cist_attention = "cist_attention"
    cist_executive = "cist_executive"
    cist_language = "cist_language"


class SessionBase(BaseModel):
    session_type: SessionType = SessionType.reminiscence
    selected_photos: List[str] = Field(..., min_items=1)


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    notes: Optional[str] = None


class SessionResponse(SessionBase):
    id: str
    user_id: str
    status: SessionStatus
    total_duration_seconds: int
    cist_score: Optional[int]
    cist_completed_items: int
    started_at: datetime
    completed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    photo_id: Optional[str] = None
    question_text: str
    question_type: ConversationType
    cist_category: Optional[str] = None
    conversation_order: int


class ConversationCreate(ConversationBase):
    session_id: str


class ConversationUpdate(BaseModel):
    user_response_text: Optional[str] = None
    user_response_audio_url: Optional[str] = None
    response_duration_seconds: Optional[int] = None
    ai_analysis: Optional[dict] = None
    cist_score: Optional[int] = None


class ConversationResponse(ConversationBase):
    id: str
    session_id: str
    user_id: str
    user_response_text: Optional[str]
    user_response_audio_url: Optional[str]
    response_duration_seconds: Optional[int]
    ai_analysis: Optional[dict]
    cist_score: Optional[int]
    is_cist_item: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool