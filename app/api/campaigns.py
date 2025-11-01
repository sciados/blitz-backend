# app/api/campaigns.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
import hashlib

from app.db.session import get_db
from app.db.models import User, Campaign, GeneratedContent, ProductIntelligence
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
    """
    Create a new campaign.

    Campaign can be created without a product URL initially.
    User can add URL later via check-url endpoint or browse product library.
    """

    # Normalize product URL if provided: add trailing slash to avoid 301 redirects during scraping
    product_url = None
    if campaign_data.product_url:
        product_url = str(campaign_data.product_url)
        if not product_url.endswith('/'):
            product_url = product_url + '/'

    new_campaign = Campaign(
        user_id=current_user.id,
        name=campaign_data.name,
        product_url=product_url,
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
    """List all campaigns for the current user with intelligence data."""

    result = await db.execute(
        select(Campaign)
        .where(Campaign.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(Campaign.created_at.desc())
    )

    campaigns = result.scalars().all()

    # Fetch intelligence data for campaigns that have it
    from app.db.models import ProductIntelligence
    campaign_responses = []
    for campaign in campaigns:
        intelligence_data = None
        if campaign.product_intelligence_id:
            intel_result = await db.execute(
                select(ProductIntelligence).where(
                    ProductIntelligence.id == campaign.product_intelligence_id
                )
            )
            intelligence = intel_result.scalar_one_or_none()
            if intelligence and intelligence.intelligence_data:
                intelligence_data = intelligence.intelligence_data

        campaign_responses.append(CampaignResponse(
            id=campaign.id,
            user_id=campaign.user_id,
            name=campaign.name,
            product_url=campaign.product_url,
            affiliate_network=campaign.affiliate_network,
            keywords=campaign.keywords,
            product_description=campaign.product_description,
            product_type=campaign.product_type,
            target_audience=campaign.target_audience,
            marketing_angles=campaign.marketing_angles,
            status=campaign.status,
            intelligence_data=intelligence_data,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at
        ))

    return campaign_responses

# ============================================================================
# GET CAMPAIGN
# ============================================================================

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific campaign with intelligence data."""

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

    # Fetch intelligence data if available
    intelligence_data = None
    if campaign.product_intelligence_id:
        from app.db.models import ProductIntelligence
        intel_result = await db.execute(
            select(ProductIntelligence).where(
                ProductIntelligence.id == campaign.product_intelligence_id
            )
        )
        intelligence = intel_result.scalar_one_or_none()
        if intelligence and intelligence.intelligence_data:
            intelligence_data = intelligence.intelligence_data

    # Build response with intelligence data
    return CampaignResponse(
        id=campaign.id,
        user_id=campaign.user_id,
        name=campaign.name,
        product_url=campaign.product_url,
        affiliate_network=campaign.affiliate_network,
        keywords=campaign.keywords,
        product_description=campaign.product_description,
        product_type=campaign.product_type,
        target_audience=campaign.target_audience,
        marketing_angles=campaign.marketing_angles,
        status=campaign.status,
        intelligence_data=intelligence_data,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at
    )

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

    # Normalize product_url if it's being updated
    if 'product_url' in update_data and update_data['product_url']:
        url = str(update_data['product_url'])
        if not url.endswith('/'):
            update_data['product_url'] = url + '/'

    for field, value in update_data.items():
        setattr(campaign, field, value)
    
    await db.commit()
    await db.refresh(campaign)

    return campaign

# ============================================================================
# CHECK URL IN PRODUCT LIBRARY
# ============================================================================

@router.post("/{campaign_id}/check-url")
async def check_product_url(
    campaign_id: int,
    product_url: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check if a product URL exists in the public library.

    If found, automatically links the campaign to existing intelligence.
    If not found, returns exists=False so user can compile new intelligence.

    Request body: {"product_url": "https://example.com/product"}

    Response:
    - exists: true/false
    - product_intelligence_id: ID if found
    - product_name: Name if found
    - message: Status message
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

    # Normalize URL
    normalized_url = product_url.strip()
    if not normalized_url.endswith('/'):
        normalized_url = normalized_url + '/'

    # Generate URL hash for lookup
    url_hash = hashlib.sha256(normalized_url.encode()).hexdigest()

    # Check if product exists in library
    intel_result = await db.execute(
        select(ProductIntelligence).where(
            ProductIntelligence.url_hash == url_hash
        )
    )

    intelligence = intel_result.scalar_one_or_none()

    if intelligence:
        # Product exists - link campaign to existing intelligence
        campaign.product_url = normalized_url
        campaign.product_intelligence_id = intelligence.id

        # Increment usage counter
        intelligence.times_used += 1
        intelligence.last_accessed_at = func.now()

        await db.commit()

        return {
            "exists": True,
            "product_intelligence_id": intelligence.id,
            "product_name": intelligence.product_name,
            "product_category": intelligence.product_category,
            "message": "Product found in library! Intelligence linked to campaign.",
            "intelligence_compiled": True  # Frontend can mark step as complete
        }
    else:
        # Product doesn't exist - user needs to compile intelligence
        campaign.product_url = normalized_url
        await db.commit()

        return {
            "exists": False,
            "product_intelligence_id": None,
            "message": "Product not found in library. Please compile intelligence.",
            "intelligence_compiled": False  # Frontend shows compile button
        }

# ============================================================================
# LINK CAMPAIGN TO EXISTING PRODUCT
# ============================================================================

@router.patch("/{campaign_id}/link-product")
async def link_campaign_to_product(
    campaign_id: int,
    product_intelligence_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Link a campaign to an existing product from the public library.

    Used when user browses the product library and selects an existing product
    instead of entering a new URL.

    Request body: {"product_intelligence_id": 123}
    """

    # Verify campaign ownership
    campaign_result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id
        )
    )

    campaign = campaign_result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Verify product exists in library
    intel_result = await db.execute(
        select(ProductIntelligence).where(
            ProductIntelligence.id == product_intelligence_id
        )
    )

    intelligence = intel_result.scalar_one_or_none()

    if not intelligence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in library"
        )

    # Link campaign to product
    campaign.product_intelligence_id = product_intelligence_id
    campaign.product_url = intelligence.product_url
    campaign.affiliate_network = intelligence.affiliate_network

    # Increment usage counter
    intelligence.times_used += 1
    intelligence.last_accessed_at = func.now()

    await db.commit()

    return {
        "success": True,
        "message": "Campaign linked to product successfully",
        "product_name": intelligence.product_name,
        "product_category": intelligence.product_category,
        "intelligence_compiled": True
    }

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