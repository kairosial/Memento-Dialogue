from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form, Query
from typing import List, Optional
import uuid
import os
import aiofiles
from PIL import Image
import io
from ..models.photo import (
    PhotoResponse, PhotoListResponse, PhotoUpdate, 
    AlbumCreate, AlbumResponse, AlbumUpdate
)
from ..core.database import supabase
from ..core.deps import get_current_user_id
import math

router = APIRouter(prefix="/photos", tags=["photos"])

# Allowed image types
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def get_image_dimensions(image_data: bytes) -> tuple:
    """Get image dimensions from image data."""
    try:
        image = Image.open(io.BytesIO(image_data))
        return image.size  # (width, height)
    except Exception:
        return (None, None)


@router.get("", response_model=PhotoListResponse)
async def get_photos(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    tags: Optional[str] = Query(None),
    favorite: Optional[bool] = Query(None),
    album_id: Optional[str] = Query(None),
    current_user_id: str = Depends(get_current_user_id)
):
    """Get user's photos with pagination and filters."""
    try:
        # Build query
        query = supabase.table("photos").select("*", count="exact").eq("user_id", current_user_id).eq("is_deleted", False)
        
        # Apply filters
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            for tag in tag_list:
                query = query.contains("tags", [tag])
        
        if favorite is not None:
            query = query.eq("is_favorite", favorite)
        
        if album_id:
            query = query.eq("album_id", album_id)
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Execute query with pagination
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        photos = [PhotoResponse(**photo) for photo in result.data]
        total = result.count or 0
        total_pages = math.ceil(total / limit) if total > 0 else 1
        
        return PhotoListResponse(
            photos=photos,
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
            detail=f"Failed to retrieve photos: {str(e)}"
        )


@router.post("/upload", response_model=PhotoResponse)
async def upload_photo(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    taken_at: Optional[str] = Form(None),
    location_name: Optional[str] = Form(None),
    album_id: Optional[str] = Form(None),
    current_user_id: str = Depends(get_current_user_id)
):
    """Upload a new photo."""
    try:
        # Validate file type
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = f"{current_user_id}/{unique_filename}"
        
        # Get image dimensions
        width, height = get_image_dimensions(file_content)
        
        # Upload to Supabase Storage
        storage_response = supabase.storage.from_("photos").upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        
        if hasattr(storage_response, 'error') and storage_response.error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {storage_response.error.message}"
            )
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Create photo record in database
        photo_data = {
            "user_id": current_user_id,
            "file_name": file.filename,  # Legacy field
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_path": file_path,
            "file_size": len(file_content),
            "mime_type": file.content_type,
            "width": width,
            "height": height,
            "description": description,
            "tags": tag_list,
            "taken_at": taken_at,
            "location_name": location_name,
            "album_id": album_id
        }
        
        db_result = supabase.table("photos").insert(photo_data).execute()
        
        if not db_result.data:
            # Clean up uploaded file if database insert fails
            supabase.storage.from_("photos").remove([file_path])
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save photo metadata"
            )
        
        photo = db_result.data[0]
        return PhotoResponse(**photo)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Photo upload failed: {str(e)}"
        )


@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo(
    photo_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get a specific photo by ID."""
    try:
        result = supabase.table("photos").select("*").eq("id", photo_id).eq("user_id", current_user_id).eq("is_deleted", False).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found"
            )
        
        photo = result.data[0]
        return PhotoResponse(**photo)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve photo: {str(e)}"
        )


@router.put("/{photo_id}", response_model=PhotoResponse)
async def update_photo(
    photo_id: str,
    photo_update: PhotoUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update photo metadata."""
    try:
        # Prepare update data
        update_data = {}
        if photo_update.description is not None:
            update_data["description"] = photo_update.description
        if photo_update.tags is not None:
            update_data["tags"] = photo_update.tags
        if photo_update.is_favorite is not None:
            update_data["is_favorite"] = photo_update.is_favorite
        if photo_update.album_id is not None:
            update_data["album_id"] = photo_update.album_id
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Update photo
        result = supabase.table("photos").update(update_data).eq("id", photo_id).eq("user_id", current_user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found"
            )
        
        photo = result.data[0]
        return PhotoResponse(**photo)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update photo: {str(e)}"
        )


@router.delete("/{photo_id}")
async def delete_photo(
    photo_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Soft delete a photo."""
    try:
        # Soft delete (mark as deleted)
        result = supabase.table("photos").update({"is_deleted": True}).eq("id", photo_id).eq("user_id", current_user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found"
            )
        
        return {
            "success": True,
            "message": "Photo deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete photo: {str(e)}"
        )


# Album management endpoints
@router.post("/albums", response_model=AlbumResponse)
async def create_album(
    album: AlbumCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a new album."""
    try:
        album_data = {
            "user_id": current_user_id,
            "name": album.name,
            "description": album.description
        }
        
        result = supabase.table("albums").insert(album_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create album"
            )
        
        album_obj = result.data[0]
        return AlbumResponse(**album_obj)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create album: {str(e)}"
        )


@router.get("/albums", response_model=List[AlbumResponse])
async def get_albums(current_user_id: str = Depends(get_current_user_id)):
    """Get user's albums."""
    try:
        result = supabase.table("albums").select("*").eq("user_id", current_user_id).order("created_at", desc=True).execute()
        
        albums = [AlbumResponse(**album) for album in result.data]
        return albums
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve albums: {str(e)}"
        )