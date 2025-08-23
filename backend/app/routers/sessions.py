from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
import math
from ..models.session import (
    SessionCreate, SessionUpdate, SessionResponse, SessionListResponse,
    ConversationCreate, ConversationUpdate, ConversationResponse, SessionStatus
)
from ..core.database import supabase
from ..core.deps import get_current_user_id

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def create_session(
    session: SessionCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a new conversation session."""
    try:
        # Validate that all photos belong to the user
        if session.selected_photos:
            photo_result = supabase.table("photos").select("id").eq("user_id", current_user_id).in_("id", session.selected_photos).execute()
            
            if len(photo_result.data) != len(session.selected_photos):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Some selected photos do not exist or don't belong to the user"
                )
        
        session_data = {
            "user_id": current_user_id,
            "session_type": session.session_type,
            "selected_photos": session.selected_photos,
            "status": "active"
        }
        
        result = supabase.table("sessions").insert(session_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session"
            )
        
        session_obj = result.data[0]
        return SessionResponse(**session_obj)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("", response_model=SessionListResponse)
async def get_sessions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[SessionStatus] = Query(None, alias="status"),
    current_user_id: str = Depends(get_current_user_id)
):
    """Get user's sessions with pagination."""
    try:
        # Build query
        query = supabase.table("sessions").select("*", count="exact").eq("user_id", current_user_id)
        
        # Apply status filter
        if status_filter:
            query = query.eq("status", status_filter.value)
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Execute query with pagination
        result = query.order("started_at", desc=True).range(offset, offset + limit - 1).execute()
        
        sessions = [SessionResponse(**session) for session in result.data]
        total = result.count or 0
        total_pages = math.ceil(total / limit) if total > 0 else 1
        
        return SessionListResponse(
            sessions=sessions,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get a specific session by ID."""
    try:
        result = supabase.table("sessions").select("*").eq("id", session_id).eq("user_id", current_user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session = result.data[0]
        return SessionResponse(**session)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}"
        )


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    session_update: SessionUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update session status and notes."""
    try:
        # Prepare update data
        update_data = {}
        if session_update.status is not None:
            update_data["status"] = session_update.status.value
            if session_update.status == SessionStatus.completed:
                update_data["completed_at"] = "now()"
        if session_update.notes is not None:
            update_data["notes"] = session_update.notes
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        result = supabase.table("sessions").update(update_data).eq("id", session_id).eq("user_id", current_user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session = result.data[0]
        return SessionResponse(**session)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )


@router.post("/{session_id}/conversations", response_model=ConversationResponse)
async def create_conversation(
    session_id: str,
    conversation: ConversationCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Add a new conversation to a session."""
    try:
        # Verify session belongs to user
        session_result = supabase.table("sessions").select("id").eq("id", session_id).eq("user_id", current_user_id).execute()
        
        if not session_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Verify photo belongs to user (if specified)
        if conversation.photo_id:
            photo_result = supabase.table("photos").select("id").eq("id", conversation.photo_id).eq("user_id", current_user_id).execute()
            
            if not photo_result.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Photo not found or doesn't belong to user"
                )
        
        conversation_data = {
            "session_id": session_id,
            "user_id": current_user_id,
            "photo_id": conversation.photo_id,
            "question_text": conversation.question_text,
            "question_type": conversation.question_type.value,
            "cist_category": conversation.cist_category,
            "conversation_order": conversation.conversation_order,
            "is_cist_item": conversation.question_type.value.startswith("cist_")
        }
        
        result = supabase.table("conversations").insert(conversation_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create conversation"
            )
        
        conversation_obj = result.data[0]
        return ConversationResponse(**conversation_obj)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )


@router.put("/{session_id}/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    session_id: str,
    conversation_id: str,
    conversation_update: ConversationUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update conversation with user response."""
    try:
        # Prepare update data
        update_data = {}
        if conversation_update.user_response_text is not None:
            update_data["user_response_text"] = conversation_update.user_response_text
        if conversation_update.user_response_audio_url is not None:
            update_data["user_response_audio_url"] = conversation_update.user_response_audio_url
        if conversation_update.response_duration_seconds is not None:
            update_data["response_duration_seconds"] = conversation_update.response_duration_seconds
        if conversation_update.ai_analysis is not None:
            update_data["ai_analysis"] = conversation_update.ai_analysis
        if conversation_update.cist_score is not None:
            update_data["cist_score"] = conversation_update.cist_score
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Update conversation
        result = supabase.table("conversations").update(update_data).eq("id", conversation_id).eq("session_id", session_id).eq("user_id", current_user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        conversation = result.data[0]
        return ConversationResponse(**conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update conversation: {str(e)}"
        )


@router.get("/{session_id}/conversations", response_model=list[ConversationResponse])
async def get_session_conversations(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get all conversations for a session."""
    try:
        # Verify session belongs to user
        session_result = supabase.table("sessions").select("id").eq("id", session_id).eq("user_id", current_user_id).execute()
        
        if not session_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get conversations
        result = supabase.table("conversations").select("*").eq("session_id", session_id).eq("user_id", current_user_id).order("conversation_order").execute()
        
        conversations = [ConversationResponse(**conv) for conv in result.data]
        return conversations
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversations: {str(e)}"
        )