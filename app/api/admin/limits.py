"""
Admin Limits Management API
Manage tier-based usage limits and monitor platform consumption
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime, timedelta

from app.db.session import AsyncSessionLocal

router = APIRouter(prefix="/api/admin/limits", tags=["admin-limits"])

# Dependency to get DB session
async def get_db() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class TierLimit(BaseModel):
    tier_name: str
    display_name: str
    videos_per_month: int = -1
    images_per_month: int = -1
    video_scripts_per_month: int = -1
    articles_per_month: int = -1
    emails_per_month: int = -1
    social_posts_per_month: int = -1
    campaigns_per_month: int = -1
    is_active: bool = True

class TierLimitUpdate(BaseModel):
    videos_per_month: Optional[int] = None
    images_per_month: Optional[int] = None
    video_scripts_per_month: Optional[int] = None
    articles_per_month: Optional[int] = None
    emails_per_month: Optional[int] = None
    social_posts_per_month: Optional[int] = None
    campaigns_per_month: Optional[int] = None
    is_active: Optional[bool] = None

class UsageMetric(BaseModel):
    tier_name: str
    total_users: int
    videos_generated: int
    images_generated: int
    video_scripts_generated: int
    articles_generated: int
    revenue: float
    avg_usage_percentage: float

class BulkUpdateRequest(BaseModel):
    tier_name: str
    field: str
    value: int
    reason: Optional[str] = None

class BulkUpdateResponse(BaseModel):
    count: int
    updates: List[BulkUpdateRequest]

# ============================================================================
# DEFAULT TIER LIMITS DATA
# ============================================================================

DEFAULT_TIER_LIMITS = {
    "trial": TierLimit(
        tier_name="trial",
        display_name="Trial",
        videos_per_month=4,
        images_per_month=5,
        video_scripts_per_month=10,
        articles_per_month=10,
        emails_per_month=3,
        social_posts_per_month=20,
        campaigns_per_month=3,
        is_active=True
    ),
    "starter": TierLimit(
        tier_name="starter",
        display_name="Starter",
        videos_per_month=8,
        images_per_month=30,
        video_scripts_per_month=50,
        articles_per_month=25,
        emails_per_month=10,
        social_posts_per_month=100,
        campaigns_per_month=10,
        is_active=True
    ),
    "pro": TierLimit(
        tier_name="pro",
        display_name="Pro",
        videos_per_month=40,
        images_per_month=100,
        video_scripts_per_month=200,
        articles_per_month=-1,  # Unlimited
        emails_per_month=50,
        social_posts_per_month=-1,  # Unlimited
        campaigns_per_month=-1,  # Unlimited
        is_active=True
    ),
    "business": TierLimit(
        tier_name="business",
        display_name="Business",
        videos_per_month=40,
        images_per_month=300,
        video_scripts_per_month=500,
        articles_per_month=-1,  # Unlimited
        emails_per_month=-1,  # Unlimited
        social_posts_per_month=-1,  # Unlimited
        campaigns_per_month=-1,  # Unlimited
        is_active=True
    ),
    "enterprise": TierLimit(
        tier_name="enterprise",
        display_name="Enterprise",
        videos_per_month=160,
        images_per_month=1000,
        video_scripts_per_month=1500,
        articles_per_month=-1,  # Unlimited
        emails_per_month=-1,  # Unlimited
        social_posts_per_month=-1,  # Unlimited
        campaigns_per_month=-1,  # Unlimited
        is_active=True
    ),
}

# Mock usage metrics (replace with actual database queries)
MOCK_USAGE_METRICS = {
    "free": UsageMetric(
        tier_name="free",
        total_users=1250,
        videos_generated=124,
        images_generated=1245,
        video_scripts_generated=2341,
        articles_generated=8934,
        revenue=0,
        avg_usage_percentage=45.2
    ),
    "starter": UsageMetric(
        tier_name="starter",
        total_users=580,
        videos_generated=156,
        images_generated=3891,
        video_scripts_generated=4821,
        articles_generated=15234,
        revenue=16820,
        avg_usage_percentage=67.3
    ),
    "pro": UsageMetric(
        tier_name="pro",
        total_users=235,
        videos_generated=987,
        images_generated=8923,
        video_scripts_generated=12456,
        articles_generated=45678,
        revenue=23265,
        avg_usage_percentage=78.9
    ),
    "business": UsageMetric(
        tier_name="business",
        total_users=89,
        videos_generated=456,
        images_generated=6789,
        video_scripts_generated=8923,
        articles_generated=23456,
        revenue=17711,
        avg_usage_percentage=82.4
    ),
    "enterprise": UsageMetric(
        tier_name="enterprise",
        total_users=23,
        videos_generated=523,
        images_generated=3456,
        video_scripts_generated=4567,
        articles_generated=12345,
        revenue=11477,
        avg_usage_percentage=91.2
    ),
}

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/tiers", response_model=Dict[str, List[TierLimit]])
async def get_tier_limits():
    """
    Get all tier limits configuration
    """
    return {"tiers": list(DEFAULT_TIER_LIMITS.values())}

@router.put("/tiers/{tier_name}", response_model=TierLimit)
async def update_tier_limit(
    tier_name: str,
    updates: TierLimitUpdate
):
    """
    Update limits for a specific tier
    """
    if tier_name not in DEFAULT_TIER_LIMITS:
        raise HTTPException(
            status_code=404,
            detail=f"Tier '{tier_name}' not found"
        )

    # Get current tier data
    current_tier = DEFAULT_TIER_LIMITS[tier_name]
    tier_dict = current_tier.model_dump()

    # Apply updates
    for field, value in updates.model_dump(exclude_unset=True).items():
        tier_dict[field] = value

    # Create updated tier
    updated_tier = TierLimit(**tier_dict)
    DEFAULT_TIER_LIMITS[tier_name] = updated_tier

    return updated_tier

@router.get("/usage", response_model=Dict[str, List[UsageMetric]])
async def get_usage_analytics():
    """
    Get usage analytics for all tiers
    """
    return {"metrics": list(MOCK_USAGE_METRICS.values())}

@router.post("/bulk-update", response_model=BulkUpdateResponse)
async def bulk_update_limits(
    updates: List[BulkUpdateRequest]
):
    """
    Bulk update multiple tier limits
    """
    updated_count = 0

    for update in updates:
        if update.tier_name not in DEFAULT_TIER_LIMITS:
            raise HTTPException(
                status_code=404,
                detail=f"Tier '{update.tier_name}' not found"
            )

        # Get current tier
        current_tier = DEFAULT_TIER_LIMITS[update.tier_name]
        tier_dict = current_tier.model_dump()

        # Update the specified field
        if hasattr(current_tier, update.field):
            setattr(current_tier, update.field, update.value)
            updated_count += 1
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field '{update.field}' for tier '{update.tier_name}'"
            )

    return BulkUpdateResponse(
        count=updated_count,
        updates=updates
    )
