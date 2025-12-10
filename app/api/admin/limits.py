"""
Admin Limits Management API
Manage tier-based usage limits and monitor platform consumption
Now backed by database tables: tier_limits and user_usage
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime, timedelta, date

from app.db.session import get_db
from app.db.models import User
from app.auth import get_current_user

router = APIRouter(prefix="/api/admin/limits", tags=["admin-limits"])


def require_admin(current_user: User):
    """Raise 403 if user is not admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class TierLimit(BaseModel):
    id: int
    tier_name: str
    monthly_ai_video_scripts: Optional[int] = None  # NULL = unlimited
    monthly_ai_text_generations: Optional[int] = None
    monthly_ai_image_generations: Optional[int] = None
    monthly_campaigns: Optional[int] = None
    max_tokens_per_request: int = 4000
    can_use_premium_ai: bool = False
    can_use_templates: bool = True
    description: Optional[str] = None

class TierLimitUpdate(BaseModel):
    monthly_ai_video_scripts: Optional[int] = None
    monthly_ai_text_generations: Optional[int] = None
    monthly_ai_image_generations: Optional[int] = None
    monthly_campaigns: Optional[int] = None
    max_tokens_per_request: Optional[int] = None
    can_use_premium_ai: Optional[bool] = None
    can_use_templates: Optional[bool] = None
    description: Optional[str] = None

class UserUsageResponse(BaseModel):
    user_id: int
    email: str
    tier: str
    usage_month: str
    ai_video_scripts_used: int
    ai_text_generations_used: int
    ai_image_generations_used: int
    campaigns_created: int
    estimated_cost_usd: float

class UsageSummaryResponse(BaseModel):
    total_users: int
    total_cost_this_month: float
    usage_by_tier: dict


# ============================================================================
# API ENDPOINTS - Database-backed
# ============================================================================

@router.get("/tiers", response_model=List[TierLimit])
async def get_tier_limits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all tier limit configurations from database"""
    require_admin(current_user)

    query = text("""
        SELECT id, tier_name, monthly_ai_video_scripts, monthly_ai_text_generations,
               monthly_ai_image_generations, monthly_campaigns, max_tokens_per_request,
               can_use_premium_ai, can_use_templates, description
        FROM tier_limits
        ORDER BY id
    """)
    result = await db.execute(query)
    rows = result.fetchall()

    return [
        TierLimit(
            id=row[0],
            tier_name=row[1],
            monthly_ai_video_scripts=row[2],
            monthly_ai_text_generations=row[3],
            monthly_ai_image_generations=row[4],
            monthly_campaigns=row[5],
            max_tokens_per_request=row[6],
            can_use_premium_ai=row[7],
            can_use_templates=row[8],
            description=row[9]
        )
        for row in rows
    ]


@router.put("/tiers/{tier_name}", response_model=TierLimit)
async def update_tier_limit(
    tier_name: str,
    updates: TierLimitUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update limits for a specific tier"""
    require_admin(current_user)

    # Build dynamic update query
    update_fields = []
    params = {"tier_name": tier_name}

    if updates.monthly_ai_video_scripts is not None:
        update_fields.append("monthly_ai_video_scripts = :video_scripts")
        params["video_scripts"] = updates.monthly_ai_video_scripts if updates.monthly_ai_video_scripts != -1 else None

    if updates.monthly_ai_text_generations is not None:
        update_fields.append("monthly_ai_text_generations = :text_gens")
        params["text_gens"] = updates.monthly_ai_text_generations if updates.monthly_ai_text_generations != -1 else None

    if updates.monthly_ai_image_generations is not None:
        update_fields.append("monthly_ai_image_generations = :image_gens")
        params["image_gens"] = updates.monthly_ai_image_generations if updates.monthly_ai_image_generations != -1 else None

    if updates.monthly_campaigns is not None:
        update_fields.append("monthly_campaigns = :campaigns")
        params["campaigns"] = updates.monthly_campaigns if updates.monthly_campaigns != -1 else None

    if updates.max_tokens_per_request is not None:
        update_fields.append("max_tokens_per_request = :max_tokens")
        params["max_tokens"] = updates.max_tokens_per_request

    if updates.can_use_premium_ai is not None:
        update_fields.append("can_use_premium_ai = :premium_ai")
        params["premium_ai"] = updates.can_use_premium_ai

    if updates.can_use_templates is not None:
        update_fields.append("can_use_templates = :templates")
        params["templates"] = updates.can_use_templates

    if updates.description is not None:
        update_fields.append("description = :description")
        params["description"] = updates.description

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    update_fields.append("updated_at = CURRENT_TIMESTAMP")

    query = text(f"""
        UPDATE tier_limits
        SET {', '.join(update_fields)}
        WHERE tier_name = :tier_name
        RETURNING id, tier_name, monthly_ai_video_scripts, monthly_ai_text_generations,
                  monthly_ai_image_generations, monthly_campaigns, max_tokens_per_request,
                  can_use_premium_ai, can_use_templates, description
    """)

    result = await db.execute(query, params)
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tier '{tier_name}' not found"
        )

    await db.commit()

    return TierLimit(
        id=row[0],
        tier_name=row[1],
        monthly_ai_video_scripts=row[2],
        monthly_ai_text_generations=row[3],
        monthly_ai_image_generations=row[4],
        monthly_campaigns=row[5],
        max_tokens_per_request=row[6],
        can_use_premium_ai=row[7],
        can_use_templates=row[8],
        description=row[9]
    )


@router.get("/usage", response_model=List[UserUsageResponse])
async def get_all_user_usage(
    month: Optional[str] = None,  # Format: YYYY-MM
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get usage for all users for a specific month (default: current month)"""
    require_admin(current_user)

    # Default to current month
    if month:
        year, mon = month.split("-")
        usage_month = date(int(year), int(mon), 1)
    else:
        today = date.today()
        usage_month = date(today.year, today.month, 1)

    query = text("""
        SELECT u.id, u.email, COALESCE(u.affiliate_tier, 'standard') as tier,
               COALESCE(uu.ai_video_scripts_used, 0),
               COALESCE(uu.ai_text_generations_used, 0),
               COALESCE(uu.ai_image_generations_used, 0),
               COALESCE(uu.campaigns_created, 0),
               COALESCE(uu.estimated_cost_usd, 0)
        FROM users u
        LEFT JOIN user_usage uu ON u.id = uu.user_id AND uu.usage_month = :month
        WHERE u.role != 'admin'
        ORDER BY COALESCE(uu.estimated_cost_usd, 0) DESC
    """)

    result = await db.execute(query, {"month": usage_month})
    rows = result.fetchall()

    return [
        UserUsageResponse(
            user_id=row[0],
            email=row[1],
            tier=row[2],
            usage_month=usage_month.strftime("%Y-%m"),
            ai_video_scripts_used=row[3],
            ai_text_generations_used=row[4],
            ai_image_generations_used=row[5],
            campaigns_created=row[6],
            estimated_cost_usd=float(row[7])
        )
        for row in rows
    ]


@router.get("/usage/summary", response_model=UsageSummaryResponse)
async def get_usage_summary(
    month: Optional[str] = None,  # Format: YYYY-MM
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated usage summary by tier"""
    require_admin(current_user)

    # Default to current month
    if month:
        year, mon = month.split("-")
        usage_month = date(int(year), int(mon), 1)
    else:
        today = date.today()
        usage_month = date(today.year, today.month, 1)

    # Get total users and cost
    total_query = text("""
        SELECT COUNT(DISTINCT u.id), COALESCE(SUM(uu.estimated_cost_usd), 0)
        FROM users u
        LEFT JOIN user_usage uu ON u.id = uu.user_id AND uu.usage_month = :month
        WHERE u.role != 'admin'
    """)
    total_result = await db.execute(total_query, {"month": usage_month})
    total_row = total_result.fetchone()

    # Get usage by tier
    tier_query = text("""
        SELECT COALESCE(u.affiliate_tier, 'standard') as tier,
               COUNT(DISTINCT u.id) as user_count,
               COALESCE(SUM(uu.ai_video_scripts_used), 0) as video_scripts,
               COALESCE(SUM(uu.ai_text_generations_used), 0) as text_gens,
               COALESCE(SUM(uu.ai_image_generations_used), 0) as image_gens,
               COALESCE(SUM(uu.estimated_cost_usd), 0) as total_cost
        FROM users u
        LEFT JOIN user_usage uu ON u.id = uu.user_id AND uu.usage_month = :month
        WHERE u.role != 'admin'
        GROUP BY COALESCE(u.affiliate_tier, 'standard')
    """)
    tier_result = await db.execute(tier_query, {"month": usage_month})
    tier_rows = tier_result.fetchall()

    usage_by_tier = {}
    for row in tier_rows:
        usage_by_tier[row[0]] = {
            "user_count": row[1],
            "ai_video_scripts": row[2],
            "ai_text_generations": row[3],
            "ai_image_generations": row[4],
            "total_cost": float(row[5])
        }

    return UsageSummaryResponse(
        total_users=total_row[0],
        total_cost_this_month=float(total_row[1]),
        usage_by_tier=usage_by_tier
    )


@router.delete("/usage/{user_id}")
async def reset_user_usage(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reset a user's usage for the current month (admin only)"""
    require_admin(current_user)

    today = date.today()
    usage_month = date(today.year, today.month, 1)

    query = text("""
        DELETE FROM user_usage
        WHERE user_id = :user_id AND usage_month = :month
    """)
    await db.execute(query, {"user_id": user_id, "month": usage_month})
    await db.commit()

    return {"message": f"Usage reset for user {user_id}"}
