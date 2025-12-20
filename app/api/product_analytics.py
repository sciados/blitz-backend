"""
Product Analytics API
Provide product performance metrics and affiliate leaderboards
"""

from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, distinct
from sqlalchemy.orm import selectinload

from app.db.models import User, ProductIntelligence, Campaign, GeneratedContent, ShortenedLink, LinkClick
from app.db.session import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/product-analytics", tags=["product-analytics"])


class AffiliateLeaderboardEntry(BaseModel):
    """Single affiliate entry in leaderboard"""
    rank: int
    user_id: int
    user_email: str
    full_name: Optional[str]

    # Metrics
    total_clicks: int
    unique_clicks: int
    content_pieces: int
    campaigns_count: int

    # Scoring
    score: float
    medal: Optional[str] = None  # "gold", "silver", "bronze"

    # Activity
    last_activity: Optional[datetime]


class ProductLeaderboard(BaseModel):
    """Product leaderboard with top affiliates"""
    product_id: int
    product_name: str
    total_affiliates: int
    date_range_days: int
    leaderboard: List[AffiliateLeaderboardEntry]


def calculate_affiliate_score(clicks: int, unique_clicks: int, content: int, campaigns: int) -> float:
    """
    Calculate composite score for affiliate ranking

    Weights:
    - Link Clicks: 50% (total clicks weighted more than unique)
    - Content Pieces: 30%
    - Campaigns: 20%
    """
    # Normalize click score (70% total clicks, 30% unique clicks)
    click_score = (clicks * 0.7) + (unique_clicks * 0.3)

    # Composite score
    score = (
        (click_score * 0.5) +      # 50% from clicks
        (content * 0.3) +          # 30% from content
        (campaigns * 20 * 0.2)     # 20% from campaigns (weighted up since typically fewer)
    )

    return round(score, 2)


@router.get("/my-campaigns")
async def get_my_product_campaigns(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all campaigns that use the current user's products.
    Used by Product Developers to view analytics on their products.
    Non-admin endpoint - only returns campaigns for products created by the current user.
    """
    # Get all products created by current user
    products_result = await db.execute(
        select(ProductIntelligence.id, ProductIntelligence.product_name).where(
            ProductIntelligence.created_by_user_id == current_user.id
        )
    )
    products = products_result.all()

    if not products:
        return {
            "campaigns": [],
            "total": 0
        }

    product_ids = [p[0] for p in products]

    # Get all campaigns using these products
    result = await db.execute(
        select(Campaign).where(
            Campaign.product_intelligence_id.in_(product_ids)
        ).order_by(Campaign.created_at.desc())
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


@router.get("/leaderboard/{product_id}", response_model=ProductLeaderboard)
async def get_product_leaderboard(
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(20, ge=5, le=100, description="Number of top affiliates to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get affiliate leaderboard for a specific product

    Returns top affiliates ranked by composite score:
    - Link clicks (50%)
    - Content pieces generated (30%)
    - Campaigns created (20%)

    Top 3 receive medals (gold, silver, bronze)
    """
    # Get product info
    product_result = await db.execute(
        select(ProductIntelligence).where(ProductIntelligence.id == product_id)
    )
    product = product_result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check authorization: Admin, product owner, or any authenticated user viewing public data
    is_admin = current_user.role == "admin"
    is_owner = product.created_by_user_id == current_user.id

    if not (is_admin or is_owner):
        # Non-owners can view leaderboard but with limited info (no emails)
        pass

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get all campaigns for this product
    campaigns_result = await db.execute(
        select(Campaign)
        .where(Campaign.product_intelligence_id == product_id)
        .options(selectinload(Campaign.user))
    )
    campaigns = campaigns_result.scalars().all()

    if not campaigns:
        return ProductLeaderboard(
            product_id=product_id,
            product_name=product.product_name or "Unknown Product",
            total_affiliates=0,
            date_range_days=days,
            leaderboard=[]
        )

    # Group campaigns by user and calculate metrics
    affiliate_metrics = {}

    for campaign in campaigns:
        user_id = campaign.user_id

        if user_id not in affiliate_metrics:
            affiliate_metrics[user_id] = {
                "user": campaign.user,
                "campaigns_count": 0,
                "content_pieces": 0,
                "total_clicks": 0,
                "unique_clicks": 0,
                "last_activity": None,
                "campaign_ids": []
            }

        # Count campaigns
        affiliate_metrics[user_id]["campaigns_count"] += 1
        affiliate_metrics[user_id]["campaign_ids"].append(campaign.id)

        # Track latest activity
        if campaign.updated_at:
            if not affiliate_metrics[user_id]["last_activity"] or campaign.updated_at > affiliate_metrics[user_id]["last_activity"]:
                affiliate_metrics[user_id]["last_activity"] = campaign.updated_at

    # Get content counts per campaign
    for user_id, metrics in affiliate_metrics.items():
        campaign_ids = metrics["campaign_ids"]

        # Count content pieces in date range
        content_result = await db.execute(
            select(func.count(GeneratedContent.id))
            .where(
                and_(
                    GeneratedContent.campaign_id.in_(campaign_ids),
                    GeneratedContent.created_at >= start_date
                )
            )
        )
        metrics["content_pieces"] = content_result.scalar() or 0

        # Get latest content activity
        latest_content_result = await db.execute(
            select(func.max(GeneratedContent.created_at))
            .where(GeneratedContent.campaign_id.in_(campaign_ids))
        )
        latest_content = latest_content_result.scalar()
        if latest_content and (not metrics["last_activity"] or latest_content > metrics["last_activity"]):
            metrics["last_activity"] = latest_content

        # Count clicks from shortened links
        links_result = await db.execute(
            select(ShortenedLink.id)
            .where(ShortenedLink.campaign_id.in_(campaign_ids))
        )
        link_ids = [row[0] for row in links_result.all()]

        if link_ids:
            # Total clicks in date range
            total_clicks_result = await db.execute(
                select(func.count(LinkClick.id))
                .where(
                    and_(
                        LinkClick.shortened_link_id.in_(link_ids),
                        LinkClick.clicked_at >= start_date
                    )
                )
            )
            metrics["total_clicks"] = total_clicks_result.scalar() or 0

            # Unique clicks (by IP address) in date range
            unique_clicks_result = await db.execute(
                select(func.count(distinct(LinkClick.ip_address)))
                .where(
                    and_(
                        LinkClick.shortened_link_id.in_(link_ids),
                        LinkClick.clicked_at >= start_date,
                        LinkClick.ip_address.isnot(None)
                    )
                )
            )
            metrics["unique_clicks"] = unique_clicks_result.scalar() or 0

            # Get latest click activity
            latest_click_result = await db.execute(
                select(func.max(LinkClick.clicked_at))
                .where(LinkClick.shortened_link_id.in_(link_ids))
            )
            latest_click = latest_click_result.scalar()
            if latest_click and (not metrics["last_activity"] or latest_click > metrics["last_activity"]):
                metrics["last_activity"] = latest_click

    # Calculate scores and rank affiliates
    ranked_affiliates = []

    for user_id, metrics in affiliate_metrics.items():
        score = calculate_affiliate_score(
            clicks=metrics["total_clicks"],
            unique_clicks=metrics["unique_clicks"],
            content=metrics["content_pieces"],
            campaigns=metrics["campaigns_count"]
        )

        # Only include affiliates with activity
        if score > 0:
            user = metrics["user"]

            # Hide email for non-owners/non-admins
            email = user.email if (is_admin or is_owner) else f"user_{user.id}@hidden.com"

            ranked_affiliates.append({
                "user_id": user_id,
                "user": user,
                "score": score,
                "total_clicks": metrics["total_clicks"],
                "unique_clicks": metrics["unique_clicks"],
                "content_pieces": metrics["content_pieces"],
                "campaigns_count": metrics["campaigns_count"],
                "last_activity": metrics["last_activity"]
            })

    # Sort by score descending
    ranked_affiliates.sort(key=lambda x: x["score"], reverse=True)

    # Build leaderboard with medals
    leaderboard = []
    medals = ["gold", "silver", "bronze"]

    for rank, affiliate in enumerate(ranked_affiliates[:limit], start=1):
        user = affiliate["user"]

        # Assign medal to top 3
        medal = medals[rank - 1] if rank <= 3 else None

        leaderboard.append(AffiliateLeaderboardEntry(
            rank=rank,
            user_id=affiliate["user_id"],
            user_email=user.email if (is_admin or is_owner) else f"Affiliate {affiliate['user_id']}",
            full_name=user.full_name if (is_admin or is_owner) else None,
            total_clicks=affiliate["total_clicks"],
            unique_clicks=affiliate["unique_clicks"],
            content_pieces=affiliate["content_pieces"],
            campaigns_count=affiliate["campaigns_count"],
            score=affiliate["score"],
            medal=medal,
            last_activity=affiliate["last_activity"]
        ))

    return ProductLeaderboard(
        product_id=product_id,
        product_name=product.product_name or "Unknown Product",
        total_affiliates=len(ranked_affiliates),
        date_range_days=days,
        leaderboard=leaderboard
    )
