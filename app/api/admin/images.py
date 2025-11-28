# app/api/admin/images.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
import logging

from app.db.database import get_db
from app.db.models import GeneratedImage, User
from app.core.security import get_current_user
from app.schemas import ImageTypeUpdateRequest

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/enhanced-images-wrong-type")
async def get_enhanced_images_wrong_type(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all enhanced images that might have incorrect image_type."""
    
    # Only allow admins
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access this endpoint"
        )
    
    # Get all enhanced images with image_type="hero"
    # These are likely to be misclassified
    result = await db.execute(
        select(GeneratedImage)
        .where(
            GeneratedImage.meta_data.op("->>")("is_enhanced") == "true"
        )
        .order_by(GeneratedImage.created_at.desc())
    )
    
    images = result.scalars().all()
    
    # Format the response
    formatted_images = []
    for img in images:
        formatted_images.append({
            "id": img.id,
            "image_type": img.image_type,
            "aspect_ratio": img.aspect_ratio,
            "provider": img.provider,
            "model": img.model,
            "prompt": img.prompt[:100] + "..." if len(img.prompt) > 100 else img.prompt,
            "created_at": img.created_at.isoformat(),
            "metadata": img.meta_data,
            "image_url": img.image_url,
            "thumbnail_url": img.thumbnail_url
        })
    
    return {
        "images": formatted_images,
        "total": len(formatted_images)
    }


@router.put("/image-type/{image_id}")
async def update_image_type(
    image_id: int,
    request: ImageTypeUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the image_type for a specific image."""
    
    # Only allow admins
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access this endpoint"
        )
    
    # Get the image
    result = await db.execute(
        select(GeneratedImage).where(GeneratedImage.id == image_id)
    )
    
    image = result.scalars().first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found"
        )
    
    # Update the image_type
    await db.execute(
        update(GeneratedImage)
        .where(GeneratedImage.id == image_id)
        .values(image_type=request.image_type)
    )
    
    await db.commit()
    
    logger.info(f"Admin {current_user.email} updated image {image_id} type to {request.image_type}")
    
    return {
        "success": True,
        "message": f"Image type updated to {request.image_type}",
        "image_id": image_id,
        "new_image_type": request.image_type
    }


@router.put("/batch-update-image-type")
async def batch_update_image_type(
    request: dict,  # {image_ids: List[int], image_type: str}
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Batch update image_type for multiple images."""
    
    # Only allow admins
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access this endpoint"
        )
    
    image_ids = request.get("image_ids", [])
    new_image_type = request.get("image_type")
    
    if not image_ids or not new_image_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="image_ids and image_type are required"
        )
    
    # Update all images
    await db.execute(
        update(GeneratedImage)
        .where(GeneratedImage.id.in_(image_ids))
        .values(image_type=new_image_type)
    )
    
    await db.commit()
    
    logger.info(f"Admin {current_user.email} batch updated {len(image_ids)} images to type {new_image_type}")
    
    return {
        "success": True,
        "message": f"Updated {len(image_ids)} images to type {new_image_type}",
        "updated_count": len(image_ids),
        "new_image_type": new_image_type
    }
