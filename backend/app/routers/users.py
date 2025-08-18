from fastapi import APIRouter, HTTPException, status, Depends
from ..models.user import UserResponse, UserUpdate, UserOnboarding
from ..core.database import supabase
from ..core.deps import get_current_user_id

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user_id: str = Depends(get_current_user_id)):
    """Get current user's profile."""
    try:
        result = supabase.table("users").select("*").eq("id", current_user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        user_data = result.data[0]
        return UserResponse(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user profile: {str(e)}"
        )


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update current user's profile."""
    try:
        # Prepare update data (only include non-None fields)
        update_data = {}
        if user_update.full_name is not None:
            update_data["full_name"] = user_update.full_name
        if user_update.birth_date is not None:
            update_data["birth_date"] = user_update.birth_date.isoformat()
        if user_update.gender is not None:
            update_data["gender"] = user_update.gender
        if user_update.phone is not None:
            update_data["phone"] = user_update.phone
        if user_update.profile_image_url is not None:
            update_data["profile_image_url"] = user_update.profile_image_url
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Update user in database
        result = supabase.table("users").update(update_data).eq("id", current_user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        updated_user = result.data[0]
        return UserResponse(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}"
        )


@router.post("/onboarding")
async def complete_onboarding(
    onboarding_data: UserOnboarding,
    current_user_id: str = Depends(get_current_user_id)
):
    """Complete user onboarding process."""
    try:
        update_data = {
            "privacy_consent": onboarding_data.privacy_consent,
            "terms_accepted": onboarding_data.terms_accepted,
            "notification_enabled": onboarding_data.notification_enabled,
            "onboarding_completed": True
        }
        
        result = supabase.table("users").update(update_data).eq("id", current_user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "success": True,
            "message": "Onboarding completed successfully",
            "data": {
                "onboarding_completed": True,
                "privacy_consent": onboarding_data.privacy_consent,
                "terms_accepted": onboarding_data.terms_accepted,
                "notification_enabled": onboarding_data.notification_enabled
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete onboarding: {str(e)}"
        )