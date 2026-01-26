"""File upload endpoints"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from app.core.dependencies import get_current_user
from app.schemas.file import FileUploadResponse
from app.services.s3_service import s3_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])

# Allowed file types and max size
ALLOWED_EXTENSIONS = {
    'image': ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'],
    'document': ['pdf', 'doc', 'docx', 'txt'],
    'video': ['mp4', 'mov', 'avi', 'mkv'],
    'audio': ['mp3', 'wav', 'ogg']
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 10MB


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename"""
    return filename.split('.')[-1].lower() if '.' in filename else ''


def is_allowed_file(filename: str) -> bool:
    """Check if file type is allowed"""
    ext = get_file_extension(filename)
    all_allowed = [ext for exts in ALLOWED_EXTENSIONS.values() for ext in exts]
    return ext in all_allowed


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a file to S3 and return the public URL
    
    - **file**: File to upload (max 10MB)
    
    Supported file types:
    - Images: jpg, jpeg, png, gif, webp, svg
    - Documents: pdf, doc, docx, txt
    - Videos: mp4, mov, avi, mkv
    - Audio: mp3, wav, ogg
    
    Requires authentication.
    """
    try:
        # Validate file presence
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Validate filename
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        # Check file type
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join([ext for exts in ALLOWED_EXTENSIONS.values() for ext in exts])}"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Determine folder based on file type
        ext = get_file_extension(file.filename)
        folder = 'other'
        for file_type, extensions in ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                folder = file_type
                break
        
        # Upload to S3
        file_url = await s3_service.upload_file(
            file_content=file_content,
            file_name=file.filename,
            content_type=file.content_type or 'application/octet-stream',
            folder=f"uploads/{folder}",
            user_id=current_user.get('id')
        )
        
        if not file_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to S3"
            )
        
        logger.info(f"File uploaded successfully by user {current_user['id']}: {file.filename} -> {file_url}")
        
        return FileUploadResponse(
            success=True,
            message="File uploaded successfully",
            file_url=file_url,
            file_name=file.filename,
            file_size=file_size,
            content_type=file.content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )
