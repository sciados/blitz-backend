# app/api/campaigns.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
import hashlib
import logging

from app.db.session import get_db
from app.db.models import User, Campaign, GeneratedContent, ProductIntelligence, ShortenedLink
from app.schemas import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignAnalytics,
    MessageResponse
)
from app.auth import get_current_active_user
from app.services.url_shortener import URLShortenerService

logger = logging.getLogger(__name__)

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

    Marketers can only create campaigns from Product Library products.
    Pro Marketers can create campaigns from any external product URL.
    """

    # Check affiliate tier restrictions
    if current_user.user_type == "affiliate":
        # Standard tier affiliates can only use Product Library products
        if current_user.affiliate_tier == "standard":
            # If trying to use custom product URL (not from library), reject
            if campaign_data.product_url and not campaign_data.product_intelligence_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Upgrade Required",
                        "message": "Marketers can only create campaigns from the Product Library. Upgrade to Pro to create campaigns with any product URL.",
                        "code": "AFFILIATE_TIER_UPGRADE_REQUIRED",
                        "upgrade_required": True
                    }
                )

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
        affiliate_link=campaign_data.affiliate_link,
        keywords=campaign_data.keywords,
        product_description=campaign_data.product_description,
        product_type=campaign_data.product_type,
        target_audience=campaign_data.target_audience,
        marketing_angles=campaign_data.marketing_angles,
        product_intelligence_id=campaign_data.product_intelligence_id,
        status="draft"
    )

    db.add(new_campaign)
    await db.flush()  # Flush to get campaign.id before creating shortened link

    # Auto-shorten affiliate link if provided
    if campaign_data.affiliate_link:
        try:
            shortener = URLShortenerService(db)
            shortened_link = await shortener.shorten_url(
                original_url=campaign_data.affiliate_link,
                campaign_id=new_campaign.id,
                user_id=current_user.id,
                title=f"{new_campaign.name} - Affiliate Link"
            )
            new_campaign.affiliate_link_short_code = shortened_link.short_code
            logger.info(f"✅ Auto-shortened affiliate link for campaign {new_campaign.id}: {shortened_link.short_code}")
        except Exception as e:
            logger.error(f"❌ Failed to auto-shorten affiliate link: {str(e)}")
            # Don't fail campaign creation if shortening fails

    await db.commit()
    await db.refresh(new_campaign)

    # If campaign was created with a product from library, trigger compilation
    # This will reuse cached intelligence but ensure KnowledgeBase ingestion happens
    if new_campaign.product_intelligence_id:
        import asyncio

        async def background_compile():
            """Background task to compile intelligence for campaign"""
            try:
                from app.db.session import AsyncSessionLocal
                from app.services.intelligence_compiler_service import IntelligenceCompilerService

                async with AsyncSessionLocal() as bg_db:
                    compiler = IntelligenceCompilerService(bg_db)

                    logger.info(f"🚀 Starting background compilation for campaign {new_campaign.id}")

                    result = await compiler.compile_for_campaign(
                        campaign_id=new_campaign.id,
                        options={
                            'deep_scrape': False,
                            'scrape_images': True,
                            'max_images': 10,
                            'enable_rag': True,
                            'force_recompile': False  # Use cache
                        }
                    )

                    if result.get('success'):
                        logger.info(f"✅ Background compilation completed for campaign {new_campaign.id}")
                        if result.get('was_cached'):
                            logger.info(f"   📚 KnowledgeBase ingestion completed (intelligence was cached)")
                    else:
                        logger.error(f"❌ Background compilation failed for campaign {new_campaign.id}: {result.get('error')}")

            except Exception as e:
                logger.error(f"❌ Background compilation error for campaign {new_campaign.id}: {str(e)}")

        # Start background task (fire-and-forget)
        asyncio.create_task(background_compile())
        logger.info(f"📦 Campaign {new_campaign.id} created with product. Compilation started in background.")

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
        thumbnail_image_url = None
        if campaign.product_intelligence_id:
            intel_result = await db.execute(
                select(ProductIntelligence).where(
                    ProductIntelligence.id == campaign.product_intelligence_id
                )
            )
            intelligence = intel_result.scalar_one_or_none()
            if intelligence:
                if intelligence.intelligence_data:
                    intelligence_data = intelligence.intelligence_data
                if intelligence.thumbnail_image_url:
                    thumbnail_image_url = intelligence.thumbnail_image_url

        campaign_responses.append(CampaignResponse(
            id=campaign.id,
            user_id=campaign.user_id,
            name=campaign.name,
            product_url=campaign.product_url,
            affiliate_network=campaign.affiliate_network,
            affiliate_link=campaign.affiliate_link,
            affiliate_link_short_code=campaign.affiliate_link_short_code,
            keywords=campaign.keywords,
            product_description=campaign.product_description,
            product_type=campaign.product_type,
            target_audience=campaign.target_audience,
            marketing_angles=campaign.marketing_angles,
            status=campaign.status,
            product_intelligence_id=campaign.product_intelligence_id,
            intelligence_data=intelligence_data,
            thumbnail_image_url=thumbnail_image_url,
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

    # Admins can view all campaigns, regular users can only view their own
    if current_user.role == "admin":
        result = await db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
    else:
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
    thumbnail_image_url = None
    if campaign.product_intelligence_id:
        from app.db.models import ProductIntelligence
        intel_result = await db.execute(
            select(ProductIntelligence).where(
                ProductIntelligence.id == campaign.product_intelligence_id
            )
        )
        intelligence = intel_result.scalar_one_or_none()
        if intelligence:
            if intelligence.intelligence_data:
                intelligence_data = intelligence.intelligence_data
            if intelligence.thumbnail_image_url:
                thumbnail_image_url = intelligence.thumbnail_image_url

    # Build response with intelligence data
    return CampaignResponse(
        id=campaign.id,
        user_id=campaign.user_id,
        name=campaign.name,
        product_url=campaign.product_url,
        affiliate_network=campaign.affiliate_network,
        affiliate_link=campaign.affiliate_link,
        affiliate_link_short_code=campaign.affiliate_link_short_code,
        keywords=campaign.keywords,
        product_description=campaign.product_description,
        product_type=campaign.product_type,
        target_audience=campaign.target_audience,
        marketing_angles=campaign.marketing_angles,
        status=campaign.status,
        product_intelligence_id=campaign.product_intelligence_id,
        intelligence_data=intelligence_data,
        thumbnail_image_url=thumbnail_image_url,
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

    # Handle affiliate_link separately for auto-shortening or deletion
    affiliate_link_action = None  # 'add', 'remove', or None
    if 'affiliate_link' in update_data:
        affiliate_link = update_data.pop('affiliate_link')
        if affiliate_link:
            # User is adding/updating the affiliate link
            affiliate_link_action = 'add'
            campaign.affiliate_link = affiliate_link
        else:
            # User is clearing the affiliate link
            affiliate_link_action = 'remove'

    for field, value in update_data.items():
        setattr(campaign, field, value)

    await db.flush()

    # Handle affiliate link actions
    if affiliate_link_action == 'add':
        # Auto-shorten the new affiliate link
        try:
            # Delete old shortened link if it exists
            if campaign.affiliate_link_short_code:
                old_link_result = await db.execute(
                    select(ShortenedLink).where(
                        ShortenedLink.short_code == campaign.affiliate_link_short_code,
                        ShortenedLink.campaign_id == campaign.id
                    )
                )
                old_shortened_link = old_link_result.scalar_one_or_none()
                if old_shortened_link:
                    await db.delete(old_shortened_link)
                    logger.info(f"🗑️ Deleted old shortened link {campaign.affiliate_link_short_code}")

            # Create new shortened link
            shortener = URLShortenerService(db)
            shortened_link = await shortener.shorten_url(
                original_url=campaign.affiliate_link,
                campaign_id=campaign.id,
                user_id=current_user.id,
                title=f"{campaign.name} - Affiliate Link"
            )
            campaign.affiliate_link_short_code = shortened_link.short_code
            logger.info(f"✅ Auto-shortened affiliate link for campaign {campaign.id}: {shortened_link.short_code}")
        except Exception as e:
            logger.error(f"❌ Failed to auto-shorten affiliate link: {str(e)}")
            # Don't fail update if shortening fails

    elif affiliate_link_action == 'remove':
        # Delete the shortened link if it exists
        if campaign.affiliate_link_short_code:
            short_link_result = await db.execute(
                select(ShortenedLink).where(
                    ShortenedLink.short_code == campaign.affiliate_link_short_code,
                    ShortenedLink.campaign_id == campaign.id
                )
            )
            shortened_link = short_link_result.scalar_one_or_none()
            if shortened_link:
                await db.delete(shortened_link)
                logger.info(f"🗑️ Deleted shortened link {campaign.affiliate_link_short_code} for campaign {campaign.id}")

        # Clear affiliate link fields
        campaign.affiliate_link = None
        campaign.affiliate_link_short_code = None
        logger.info(f"✅ Removed affiliate link from campaign {campaign.id}")

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
    """Delete a campaign. Admins can delete any campaign, users can only delete their own."""

    # Admins can delete any campaign, regular users can only delete their own
    if current_user.role == "admin":
        result = await db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
    else:
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
# DELETE AFFILIATE LINK
# ============================================================================

@router.delete("/{campaign_id}/affiliate-link", response_model=CampaignResponse)
async def delete_affiliate_link(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete the affiliate link from a campaign.

    This will:
    - Remove the affiliate_link and affiliate_link_short_code from the campaign
    - Delete the associated shortened link record
    - Delete all click tracking data (cascade delete)
    """

    # Get campaign (user can only delete their own affiliate links)
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

    # Delete the shortened link if it exists
    if campaign.affiliate_link_short_code:
        # Find and delete the shortened link
        short_link_result = await db.execute(
            select(ShortenedLink).where(
                ShortenedLink.short_code == campaign.affiliate_link_short_code,
                ShortenedLink.campaign_id == campaign_id
            )
        )
        shortened_link = short_link_result.scalar_one_or_none()

        if shortened_link:
            await db.delete(shortened_link)
            logger.info(f"🗑️ Deleted shortened link {campaign.affiliate_link_short_code} for campaign {campaign_id}")

    # Clear affiliate link fields from campaign
    campaign.affiliate_link = None
    campaign.affiliate_link_short_code = None

    await db.commit()
    await db.refresh(campaign)

    logger.info(f"✅ Removed affiliate link from campaign {campaign_id}")

    return campaign

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
# ============================================================================
# ACTIVE CAMPAIGN LIMIT ENFORCEMENT
# ============================================================================

@router.get("/active-limit")
async def get_active_campaign_limit(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's current active campaign count and their tier's limit.
    
    Returns:
    {
        "current_active": 2,
        "limit": 4,
        "remaining": 2,
        "can_activate_more": true
    }
    """
    from app.models.admin_settings import TierConfig
    
    # Get user's subscription tier
    tier_name = current_user.subscription_tier or "trial"
    
    # Get tier configuration
    tier_result = await db.execute(
        select(TierConfig).where(TierConfig.tier_name == tier_name)
    )
    tier_config = tier_result.scalar_one_or_none()
    
    # Default limits if tier not found
    if not tier_config:
        limit = 4  # Default for trial/free
    else:
        limit = tier_config.active_campaigns_limit or 4
    
    # Count currently active campaigns
    active_count_result = await db.execute(
        select(func.count(Campaign.id))
        .where(
            Campaign.user_id == current_user.id,
            Campaign.status == "active"
        )
    )
    current_active = active_count_result.scalar() or 0
    
    remaining = max(0, limit - current_active)
    can_activate_more = current_active < limit
    
    return {
        "current_active": current_active,
        "limit": limit,
        "remaining": remaining,
        "can_activate_more": can_activate_more,
        "tier": tier_name
    }

@router.patch("/{campaign_id}/status")
async def toggle_campaign_status(
    campaign_id: int,
    new_status: str,  # "active" or "paused" or "draft"
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle campaign status with active campaign limit validation.
    
    If activating a campaign, checks that user won't exceed their tier's limit.
    """
    from app.models.admin_settings import TierConfig
    
    # Get campaign
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
    
    # Validate status
    valid_statuses = ["draft", "active", "paused", "completed"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # If activating a campaign, check active limit
    if new_status == "active" and campaign.status != "active":
        # Get user's tier configuration
        tier_name = current_user.subscription_tier or "trial"
        tier_result = await db.execute(
            select(TierConfig).where(TierConfig.tier_name == tier_name)
        )
        tier_config = tier_result.scalar_one_or_none()
        
        # Get active campaigns limit
        if tier_config:
            limit = tier_config.active_campaigns_limit or 4
        else:
            limit = 4  # Default
        
        # Count currently active campaigns (excluding this one if it's already active)
        active_count_result = await db.execute(
            select(func.count(Campaign.id))
            .where(
                Campaign.user_id == current_user.id,
                Campaign.status == "active",
                Campaign.id != campaign_id
            )
        )
        current_active = active_count_result.scalar() or 0
        
        # Check if activating would exceed limit
        if current_active >= limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Active Campaign Limit Reached",
                    "message": f"You've reached the maximum of {limit} active campaigns for your {tier_name} tier. Pause some campaigns before activating new ones.",
                    "current_active": current_active,
                    "limit": limit,
                    "code": "ACTIVE_CAMPAIGN_LIMIT_EXCEEDED"
                }
            )
    
    # Update campaign status
    campaign.status = new_status
    await db.commit()
    await db.refresh(campaign)
    
    # Return updated campaign with active count
    active_count_result = await db.execute(
        select(func.count(Campaign.id))
        .where(
            Campaign.user_id == current_user.id,
            Campaign.status == "active"
        )
    )
    current_active = active_count_result.scalar() or 0
    
    return {
        "campaign": campaign,
        "active_campaigns_count": current_active,
        "message": f"Campaign status updated to {new_status}"
    }
