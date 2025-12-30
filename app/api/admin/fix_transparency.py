# app/api/admin/fix_transparency.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import Dict, Any

from app.db.session import get_db
from app.db.models import User, GeneratedImage
from app.auth import get_current_user
from app.services.image_generator import check_image_has_transparency

router = APIRouter()


@router.post("/fix-transparency/{campaign_id}", status_code=status.HTTP_200_OK)
async def fix_transparency(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Fix has_transparency field for all images in a campaign.
    This endpoint checks each image and updates the has_transparency field based on actual image content.
    Only available to admin users.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can fix transparency"
        )

    # Fetch all images for this campaign
    query = select(GeneratedImage).where(GeneratedImage.campaign_id == campaign_id)
    result = await db.execute(query)
    images = result.scalars().all()

    updated_count = 0
    for img in images:
        # Check if image has transparency
        has_transp = await check_image_has_transparency(img.image_url)

        if has_transp != img.has_transparency:
            img.has_transparency = has_transp
            updated_count += 1

    await db.commit()

    return {
        "campaign_id": campaign_id,
        "total_images": len(images),
        "updated": updated_count,
        "message": f"Updated {updated_count} images for campaign {campaign_id}"
    }