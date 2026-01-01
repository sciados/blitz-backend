"""File upload API endpoint."""
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import time
import hashlib
import mimetypes
from typing import Optional

from app.db.session import get_db
from app.db.models import User, Campaign
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


@router.post("/campaign-media")
async def upload_campaign_media(
    file: UploadFile = File(...),
    campaign_id: int = Form(...),
    media_type: str = Form(default="image", description="Type: image or video"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload images or videos to a campaign."""

    # Verify campaign ownership
    result = await db.execute(
        select(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found or access denied"
        )

    # Validate media type and file type
    if media_type == "image":
        valid_mime_types = [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
        ]
        folder = "uploads"
    elif media_type == "video":
        valid_mime_types = [
            "video/mp4",
            "video/webm",
            "video/ogg",
        ]
        folder = "videos"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid media_type. Must be 'image' or 'video'"
        )

    if file.content_type not in valid_mime_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Must be a {media_type}"
        )

    # Generate unique filename
    timestamp = int(time.time())
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    file_hash = hashlib.md5(f"{file.filename}_{timestamp}".encode()).hexdigest()[:8]
    filename = f"upload_{timestamp}_{file_hash}.{file_extension}"

    # Read file content
    file_content = await file.read()

    # Check file size (50MB limit)
    max_size = 50 * 1024 * 1024
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 50MB"
        )

    # Upload to R2 in campaign folder
    try:
        file_key, file_url = await r2_storage.upload_file(
            file_bytes=file_content,
            key=f"campaigns/{campaign_id}/{folder}/{filename}",
            content_type=file.content_type
        )

        logger.info(f"Uploaded {media_type} file: {filename} for campaign {campaign_id}")

        return {
            "url": file_url,
            "filename": filename,
            "content_type": file.content_type,
            "size": len(file_content),
            "media_type": media_type,
            "campaign_id": campaign_id
        }
    except Exception as e:
        logger.error(f"Failed to upload file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
