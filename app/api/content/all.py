"""
Unified Content Library API
Get all content (text and images) for a campaign in one endpoint
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Union
from datetime import datetime

from app.db.session import get_db
from app.db.models import User, Campaign, GeneratedContent, GeneratedImage
from app.auth import get_current_user

router = APIRouter(prefix="/api/content", tags=["content"])


@router.get("/campaign/{campaign_id}/all")
async def get_all_campaign_content(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    content_type: str = None  # Filter by content_type (text, video_script, etc.)
):
    """
    Get all content (both text and images) for a campaign.

    Returns unified list with type discriminator:
    - { type: "text", data: GeneratedContent }
    - { type: "image", data: GeneratedImage }
    """
    # Verify campaign ownership
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    unified_contents = []

    # Fetch text-based content (GeneratedContent)
    text_query = select(GeneratedContent).where(
        GeneratedContent.campaign_id == campaign_id
    )

    if content_type:
        text_query = text_query.where(GeneratedContent.content_type == content_type)

    text_query = text_query.offset(skip).limit(limit).order_by(GeneratedContent.created_at.desc())

    text_result = await db.execute(text_query)
    text_contents = text_result.scalars().all()

    # Convert to unified format
    for content in text_contents:
        unified_contents.append({
            "type": "text",
            "data": {
                "id": content.id,
                "campaign_id": content.campaign_id,
                "content_type": content.content_type,
                "marketing_angle": content.marketing_angle,
                "content_data": content.content_data,
                "compliance_status": content.compliance_status,
                "compliance_score": content.compliance_score,
                "compliance_notes": content.compliance_notes,
                "version": content.version,
                "parent_content_id": content.parent_content_id,
                "created_at": content.created_at
            }
        })

    # Fetch image content (GeneratedImage) - only if not filtering by text content type
    if not content_type or content_type == "image":
        image_query = select(GeneratedImage).where(
            GeneratedImage.campaign_id == campaign_id
        )

        image_query = image_query.offset(skip).limit(limit).order_by(GeneratedImage.created_at.desc())

        image_result = await db.execute(image_query)
        image_contents = image_result.scalars().all()

        # Convert to unified format
        for image in image_contents:
            unified_contents.append({
                "type": "image",
                "data": {
                    "id": image.id,
                    "campaign_id": image.campaign_id,
                    "image_type": image.image_type,
                    "image_url": image.image_url,
                    "thumbnail_url": image.thumbnail_url,
                    "provider": image.provider,
                    "style": image.style,
                    "prompt": image.prompt,
                    "aspect_ratio": image.aspect_ratio,
                    "resolution": image.resolution,
                    "compliance_status": image.compliance_status,
                    "compliance_score": image.compliance_score,
                    "compliance_notes": image.compliance_notes,
                    "version": image.version,
                    "parent_image_id": image.parent_image_id,
                    "created_at": image.created_at
                }
            })

    # Sort combined results by created_at (newest first)
    unified_contents.sort(key=lambda x: x["data"]["created_at"], reverse=True)

    # Apply limit to combined results
    total = len(unified_contents)
    unified_contents = unified_contents[skip:skip + limit]

    return {
        "contents": unified_contents,
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "per_page": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    }
