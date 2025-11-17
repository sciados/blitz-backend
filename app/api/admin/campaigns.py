# app/api/admin/campaigns.py
"""
Admin endpoints for campaign management and intelligence viewing
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
import logging

from app.db.session import get_db
from app.db.models import User, Campaign
from app.auth import get_current_user

router = APIRouter(prefix="/api/admin/campaigns", tags=["Admin - Campaigns"])
logger = logging.getLogger(__name__)


@router.get("/list")
async def list_all_campaigns(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all campaigns across all users (admin only).

    Used for admin monitoring, testing, and intelligence review.
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get all campaigns with user information
    result = await db.execute(
        select(Campaign).order_by(Campaign.created_at.desc())
    )
    campaigns = result.scalars().all()

    # Get user info for each campaign
    campaign_list = []
    for campaign in campaigns:
        # Get user
        user_result = await db.execute(
            select(User).where(User.id == campaign.user_id)
        )
        user = user_result.scalar_one_or_none()

        campaign_list.append({
            "id": campaign.id,
            "name": campaign.name,
            "product_url": campaign.product_url,
            "affiliate_network": campaign.affiliate_network,
            "commission_rate": campaign.commission_rate,
            "status": campaign.status,
            "product_intelligence_id": campaign.product_intelligence_id,
            "has_intelligence": campaign.intelligence_data is not None and len(campaign.intelligence_data) > 0,
            "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
            "user": {
                "id": user.id if user else None,
                "email": user.email if user else "Unknown",
                "role": user.role if user else "unknown"
            }
        })

    return {
        "campaigns": campaign_list,
        "total": len(campaign_list)
    }


@router.get("/{campaign_id}/intelligence")
async def get_full_intelligence(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the complete intelligence_data JSON for a campaign (admin only).

    Returns the full, unfiltered intelligence data for review and testing.
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get campaign
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get user info
    user_result = await db.execute(
        select(User).where(User.id == campaign.user_id)
    )
    user = user_result.scalar_one_or_none()

    return {
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "product_url": campaign.product_url,
        "user": {
            "id": user.id if user else None,
            "email": user.email if user else "Unknown"
        },
        "intelligence_data": campaign.intelligence_data,
        "product_intelligence_id": campaign.product_intelligence_id,
        "compiled_at": campaign.created_at.isoformat() if campaign.created_at else None
    }
