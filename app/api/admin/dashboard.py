"""
Admin Dashboard Stats API
Provide statistics for admin dashboard
"""

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models import User, Campaign, GeneratedContent
from app.db.models import Campaign
from app.db.session import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/admin/dashboard", tags=["admin-dashboard"])

# ============================================================================
# SCHEMAS
# ============================================================================

class DashboardStats(BaseModel):
    total_users: int
    active_campaigns: int
    total_campaigns: int
    api_calls_today: int
    system_health: str

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for admin dashboard"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Total users
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    # Active campaigns
    active_campaigns_result = await db.execute(
        select(func.count(Campaign.id)).where(Campaign.status == "active")
    )
    active_campaigns = active_campaigns_result.scalar() or 0

    # Total campaigns
    total_campaigns_result = await db.execute(select(func.count(Campaign.id)))
    total_campaigns = total_campaigns_result.scalar() or 0

    # API calls today (placeholder for now - would need analytics tracking)
    api_calls_today = 0

    # System health (simple check - always healthy for now)
    system_health = "Healthy"

    return DashboardStats(
        total_users=total_users,
        active_campaigns=active_campaigns,
        total_campaigns=total_campaigns,
        api_calls_today=api_calls_today,
        system_health=system_health
    )
