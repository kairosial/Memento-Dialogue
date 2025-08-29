from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
import uuid
from datetime import datetime
import tempfile
import os

from core.auth import get_supabase_user
from core.config import supabase_admin, settings
from services.image_analyzer import ImageAnalyzer

router = APIRouter()

class PhotoAnalysisResponse(BaseModel):
    photo_id: str
    analysis_result: dict
    analyzed_at: datetime
    success: bool
    message: str

@router.post("/photos/{photo_id}/analyze", response_model=PhotoAnalysisResponse)
async def analyze_photo(
    photo_id: str,
    user_info: dict = Depends(get_supabase_user)
):
    """
    사진을 OpenAI GPT-4o로 분석하고 결과를 DB에 저장
    """
    try:
        user_id = user_info["id"]
        
        # 1. 사용자가 해당 사진의 소유자인지 확인
        photo_response = supabase_admin.table("photos").select("*").eq("id", photo_id).eq("user_id", user_id).execute()
        
        if not photo_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사진을 찾을 수 없거나 접근 권한이 없습니다."
            )
        
        photo_data = photo_response.data[0]
        file_path = photo_data["file_path"]
        
        # 2. Supabase Storage에서 이미지 파일 다운로드
        try:
            file_response = supabase_admin.storage.from_("photos").download(file_path)
            image_bytes = file_response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"이미지 파일을 다운로드할 수 없습니다: {str(e)}"
            )
        
        # 3. 임시 파일로 저장 (ImageAnalyzer가 파일 경로를 필요로 함)
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(image_bytes)
            temp_file.close()
            
            # 4. ImageAnalyzer로 분석 수행
            analyzer = ImageAnalyzer()
            analysis_result = analyzer.analyze_image(temp_file.name)
            
            if analysis_result is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="이미지 분석에 실패했습니다."
                )
            
        finally:
            # 임시 파일 정리
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
        
        # 5. 분석 결과를 DB에 저장
        analyzed_at = datetime.now()
        
        update_response = supabase_admin.table("photos").update({
            "photo_analyze_result": analysis_result,
            "analyzed_at": analyzed_at.isoformat()
        }).eq("id", photo_id).eq("user_id", user_id).execute()
        
        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="분석 결과 저장에 실패했습니다."
            )
        
        return PhotoAnalysisResponse(
            photo_id=photo_id,
            analysis_result=analysis_result,
            analyzed_at=analyzed_at,
            success=True,
            message="사진 분석이 완료되었습니다."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Photo analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사진 분석 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/photos/{photo_id}/analysis")
async def get_photo_analysis(
    photo_id: str,
    user_info: dict = Depends(get_supabase_user)
):
    """
    특정 사진의 분석 결과 조회
    """
    try:
        user_id = user_info["id"]
        
        photo_response = supabase_admin.table("photos").select(
            "id, photo_analyze_result, analyzed_at"
        ).eq("id", photo_id).eq("user_id", user_id).execute()
        
        if not photo_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사진을 찾을 수 없거나 접근 권한이 없습니다."
            )
        
        photo_data = photo_response.data[0]
        
        return {
            "photo_id": photo_id,
            "analysis_result": photo_data.get("photo_analyze_result"),
            "analyzed_at": photo_data.get("analyzed_at"),
            "has_analysis": photo_data.get("photo_analyze_result") is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get photo analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"분석 결과 조회 중 오류가 발생했습니다: {str(e)}"
        )