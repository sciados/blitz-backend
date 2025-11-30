"""
Developer Analytics API
Provides product and performance analytics for a specific developer
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, distinct

from app.db.models import User, ProductIntelligence, Campaign, ShortenedLink, LinkClick
from app.db.session import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/developer/{user_id}")
async def get_developer_analytics(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = get_db
):
    """
    Get analytics for a specific developer's products.
    Returns product performance metrics, affiliate counts, and campaign data.
    """
    # Verify the developer exists
    developer_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    developer = developer_result.scalar_one_or_none()

    if not developer:
        raise HTTPException(status_code=404, detail="Developer not found")

    # Get all products created by this developer
    products_result = await db.execute(
        select(ProductIntelligence).where(
            ProductIntelligence.created_by_user_id == user_id
        )
    )
    products = products_result.scalars().all()

    if not products:
        return {
            "products": [],
            "total_affiliates": 0,
            "active_campaigns": 0,
            "total_clicks": 0,
            "unique_visitors": 0,
            "product_performance": []
        }

    product_ids = [p.id for p in products]

    # Get all campaigns using these products
    campaigns_result = await db.execute(
        select(Campaign).where(
            Campaign.product_intelligence_id.in_(product_ids)
        )
    )
    campaigns = campaigns_result.scalars().all()

    # Get all shortened links for these campaigns
    campaign_ids = [c.id for c in campaigns]

    if not campaign_ids:
        return {
            "products": products,
            "total_affiliates": 0,
            "active_campaigns": 0,
            "total_clicks": 0,
            "unique_visitors": 0,
            "product_performance": []
        }

    links_result = await db.execute(
        select(ShortenedLink).where(
            ShortenedLink.campaign_id.in_(campaign_ids)
        )
    )
    links = links_result.scalars().all()

    if not links:
        return {
            "products": products,
            "total_affiliates": len(set(c.user_id for c in campaigns)),
            "active_campaigns": len(campaigns),
            "total_clicks": 0,
            "unique_visitors": 0,
            "product_performance": [
                {
                    "product_id": p.id,
                    "product_name": p.product_name,
                    "campaigns": len([c for c in campaigns if c.product_intelligence_id == p.id]),
                    "affiliates": len(set(c.user_id for c in campaigns if c.product_intelligence_id == p.id)),
                    "total_clicks": 0,
                    "unique_clicks": 0
                }
                for p in products
            ]
        }

    link_ids = [l.id for l in links]

    # Get all clicks for these links
    clicks_result = await db.execute(
        select(LinkClick).where(
            LinkClick.shortened_link_id.in_(link_ids)
        )
    )
    clicks = clicks_result.scalars().all()

    # Calculate unique visitors (by IP address)
    unique_visitors = len(set(click.ip_address for click in clicks if click.ip_address))
    total_clicks = len(clicks)

    # Get unique affiliates
    unique_affiliates = len(set(c.user_id for c in campaigns))

    # Calculate product performance
    product_performance = []
    for product in products:
        product_campaigns = [c for c in campaigns if c.product_intelligence_id == product.id]
        product_link_ids = [l.id for l in links if l.campaign_id in [c.id for c in product_campaigns]]

        product_clicks = [click for click in clicks if click.shortened_link_id in product_link_ids]
        product_total_clicks = len(product_clicks)
        product_unique_clicks = len(set(click.ip_address for click in product_clicks if click.ip_address))
        product_affiliates = len(set(c.user_id for c in product_campaigns))

        product_performance.append({
            "product_id": product.id,
            "product_name": product.product_name,
            "campaigns": len(product_campaigns),
            "affiliates": product_affiliates,
            "total_clicks": product_total_clicks,
            "unique_clicks": product_unique_clicks
        })

    return {
        "products": [
            {
                "id": p.id,
                "product_name": p.product_name,
                "product_url": p.product_url,
                "is_public": p.is_public,
                "created_by_user_id": p.created_by_user_id
            }
            for p in products
        ],
        "total_affiliates": unique_affiliates,
        "active_campaigns": len(campaigns),
        "total_clicks": total_clicks,
        "unique_visitors": unique_visitors,
        "product_performance": product_performance
    }
