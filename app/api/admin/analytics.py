"""
Admin Analytics API
Provide usage and performance metrics
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.db.models import User
from app.db.models import Campaign
from app.db.models import GeneratedContent as Content
from app.db.session import get_db
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/admin/analytics", tags=["admin-analytics"])

# ============================================================================
# SCHEMAS
# ============================================================================

class ContentTypeStats(BaseModel):
    content_type: str
    count: int
    total_words: int

class UserUsageStats(BaseModel):
    user_email: str
    campaign_count: int
    content_count: int
    total_words: int

class TimeSeriesPoint(BaseModel):
    date: str
    count: int

class AnalyticsSummary(BaseModel):
    total_content_pieces: int
    total_words_generated: int
    avg_content_length: int
    most_popular_type: str
    content_by_type: List[ContentTypeStats]
    top_users: List[UserUsageStats]
    content_over_time: List[TimeSeriesPoint]

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics summary for the last N days"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Total content pieces
    total_content_result = await db.execute(
        select(func.count(Content.id)).where(Content.created_at >= start_date)
    )
    total_content = total_content_result.scalar() or 0

    # Total words generated (using character count / 5 as rough estimate)
    total_chars_result = await db.execute(
        select(func.sum(func.length(Content.content))).where(Content.created_at >= start_date)
    )
    total_chars = total_chars_result.scalar() or 0
    total_words = total_chars // 5

    # Average content length
    avg_content_length = total_words // total_content if total_content > 0 else 0

    # Content by type
    content_by_type_result = await db.execute(
        select(
            Content.content_type,
            func.count(Content.id).label('count'),
            func.sum(func.length(Content.content)).label('total_chars')
        )
        .where(Content.created_at >= start_date)
        .group_by(Content.content_type)
        .order_by(func.count(Content.id).desc())
    )
    content_by_type_rows = content_by_type_result.all()

    content_by_type = [
        ContentTypeStats(
            content_type=row.content_type,
            count=row.count,
            total_words=(row.total_chars or 0) // 5
        )
        for row in content_by_type_rows
    ]

    # Most popular type
    most_popular_type = content_by_type[0].content_type if content_by_type else "N/A"

    # Top users by usage
    top_users_result = await db.execute(
        select(
            User.email,
            func.count(func.distinct(Campaign.id)).label('campaign_count'),
            func.count(Content.id).label('content_count'),
            func.sum(func.length(Content.content)).label('total_chars')
        )
        .join(Campaign, Campaign.user_id == User.id)
        .join(Content, Content.campaign_id == Campaign.id)
        .where(Content.created_at >= start_date)
        .group_by(User.id, User.email)
        .order_by(func.count(Content.id).desc())
        .limit(10)
    )
    top_users_rows = top_users_result.all()

    top_users = [
        UserUsageStats(
            user_email=row.email,
            campaign_count=row.campaign_count,
            content_count=row.content_count,
            total_words=(row.total_chars or 0) // 5
        )
        for row in top_users_rows
    ]

    # Content over time (daily for last 30 days, weekly for longer periods)
    content_over_time = []
    if days <= 30:
        # Daily data
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            count_result = await db.execute(
                select(func.count(Content.id))
                .where(and_(Content.created_at >= day_start, Content.created_at < day_end))
            )
            count = count_result.scalar() or 0

            content_over_time.append(TimeSeriesPoint(
                date=day_start.strftime("%Y-%m-%d"),
                count=count
            ))
    else:
        # Weekly data
        weeks = days // 7
        for i in range(weeks):
            week_start = start_date + timedelta(weeks=i)
            week_end = week_start + timedelta(weeks=1)

            count_result = await db.execute(
                select(func.count(Content.id))
                .where(and_(Content.created_at >= week_start, Content.created_at < week_end))
            )
            count = count_result.scalar() or 0

            content_over_time.append(TimeSeriesPoint(
                date=week_start.strftime("%Y-%m-%d"),
                count=count
            ))

    return AnalyticsSummary(
        total_content_pieces=total_content,
        total_words_generated=total_words,
        avg_content_length=avg_content_length,
        most_popular_type=most_popular_type,
        content_by_type=content_by_type,
        top_users=top_users,
        content_over_time=content_over_time
    )

@router.get("/campaigns")
async def get_campaign_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get campaign-level analytics"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Campaigns by status
    campaigns_by_status_result = await db.execute(
        select(
            Campaign.status,
            func.count(Campaign.id).label('count')
        )
        .group_by(Campaign.status)
    )
    campaigns_by_status = [
        {"status": row.status, "count": row.count}
        for row in campaigns_by_status_result.all()
    ]

    # Campaigns by affiliate network
    campaigns_by_network_result = await db.execute(
        select(
            Campaign.affiliate_network,
            func.count(Campaign.id).label('count')
        )
        .group_by(Campaign.affiliate_network)
        .order_by(func.count(Campaign.id).desc())
        .limit(10)
    )
    campaigns_by_network = [
        {"network": row.affiliate_network, "count": row.count}
        for row in campaigns_by_network_result.all()
    ]

    return {
        "campaigns_by_status": campaigns_by_status,
        "campaigns_by_network": campaigns_by_network
    }
