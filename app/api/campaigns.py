# app/api/campaigns.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.db.session import get_db
from app.db.models import User, Campaign, GeneratedContent
from app.schemas import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignAnalytics,
    MessageResponse
)
from app.auth import get_current_active_user

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])

# ============================================================================
# CREATE CAMPAIGN
# ============================================================================

@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new campaign."""
    
    new_campaign = Campaign(
        user_id=current_user.id,
        name=campaign_data.name,
        product_url=str(campaign_data.product_url),
        affiliate_network=campaign_data.affiliate_network,
        keywords=campaign_data.keywords,
        product_description=campaign_data.product_description,
        product_type=campaign_data.product_type,
        target_audience=campaign_data.target_audience,
        marketing_angles=campaign_data.marketing_angles,
        status="draft"
    )
    
    db.add(new_campaign)
    await db.commit()
    await db.refresh(new_campaign)
    
    return new_campaign

# ============================================================================
# LIST CAMPAIGNS
# ============================================================================

@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all campaigns for the current user."""
    
    result = await db.execute(
        select(Campaign)
        .where(Campaign.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(Campaign.created_at.desc())
    )
    
    campaigns = result.scalars().all()
    return campaigns

# ============================================================================
# GET CAMPAIGN
# ============================================================================

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific campaign."""
    
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
    
    return campaign

# ============================================================================
# UPDATE CAMPAIGN
# ============================================================================

@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    campaign_update: CampaignUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a campaign."""
    
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
    
    # Update fields
    update_data = campaign_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(campaign, field, value)
    
    await db.commit()
    await db.refresh(campaign)
    
    return campaign

# ============================================================================
# DELETE CAMPAIGN
# ============================================================================

@router.delete("/{campaign_id}", response_model=MessageResponse)
async def delete_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a campaign."""
    
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
    
    await db.delete(campaign)
    await db.commit()
    
    return MessageResponse(message="Campaign deleted successfully")

# ============================================================================
# GET CAMPAIGN ANALYTICS
# ============================================================================

@router.get("/{campaign_id}/analytics", response_model=CampaignAnalytics)
async def get_campaign_analytics(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics for a campaign."""
    
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
    
    # Get content statistics
    content_result = await db.execute(
        select(
            func.count(GeneratedContent.id).label("total"),
            GeneratedContent.content_type,
        )
        .where(GeneratedContent.campaign_id == campaign_id)
        .group_by(GeneratedContent.content_type)
    )
    
    content_stats = content_result.all()
    
    total_content = sum(stat.total for stat in content_stats)
    content_by_type = {stat.content_type: stat.total for stat in content_stats}
    
    # Get compliance score (average)
    compliance_result = await db.execute(
        select(func.avg(GeneratedContent.compliance_score))
        .where(GeneratedContent.campaign_id == campaign_id)
    )
    
    avg_compliance = compliance_result.scalar() or 0.0
    
    # Get last generated content
    last_content_result = await db.execute(
        select(GeneratedContent.created_at)
        .where(GeneratedContent.campaign_id == campaign_id)
        .order_by(GeneratedContent.created_at.desc())
        .limit(1)
    )
    
    last_generated = last_content_result.scalar_one_or_none()
    
    return CampaignAnalytics(
        campaign_id=campaign_id,
        total_content=total_content,
        content_by_type=content_by_type,
        compliance_score=float(avg_compliance),
        last_generated=last_generated
    )