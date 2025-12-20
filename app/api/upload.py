"""File upload API endpoint."""
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time
import hashlib
import mimetypes
from typing import Optional

from app.db.session import get_db
from app.db.models import User
from app.auth import get_current_user
from app.services.storage_r2 import r2_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("/hero-media")
async def upload_hero_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload hero media (image or video) for product details."""
    # Validate file type
    valid_mime_types = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "video/mp4",
        "video/webm",
        "video/ogg",
    ]

    if file.content_type not in valid_mime_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Must be an image or video."
        )

    # Validate file size (max 50MB)
    # Note: FastAPI doesn't provide file size directly, but we can check during upload
    # For now, we'll trust the frontend validation

    # Generate unique filename
    timestamp = int(time.time())
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    file_hash = hashlib.md5(file.filename.encode()).hexdigest()[:8]
    filename = f"hero_media_{timestamp}_{file_hash}.{file_extension}"

    # Read file content
    file_content = await file.read()

    # Check file size (50MB limit)
    max_size = 50 * 1024 * 1024
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 50MB"
        )

    # Upload to R2
    try:
        file_key, file_url = await r2_storage.upload_file(
            file_bytes=file_content,
            key=f"users/{current_user.id}/hero_media/{filename}",
            content_type=file.content_type
        )

        logger.info(f"Uploaded hero media file: {filename} for user {current_user.id}")

        return {
            "url": file_url,
            "filename": filename,
            "content_type": file.content_type,
            "size": len(file_content)
        }
    except Exception as e:
        logger.error(f"Failed to upload file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
