"""
Admin User Management API
Manage users, roles, and permissions
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from passlib.context import CryptContext

from app.db.models import User, Campaign
from app.db.session import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============================================================================
# SCHEMAS
# ============================================================================

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: str
    user_type: Optional[str] = None
    created_at: datetime
    is_active: bool
    last_login: Optional[datetime] = None
    campaign_count: int = 0
    affiliate_tier: Optional[str] = None
    affiliate_tier_upgraded_at: Optional[datetime] = None

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    user_type: Optional[str] = None
    is_active: Optional[bool] = None

class UserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "user"
    user_type: Optional[str] = None

class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    new_users_this_month: int

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user statistics for admin dashboard"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Total users
    total_result = await db.execute(select(func.count(User.id)))
    total_users = total_result.scalar() or 0

    # Active users (assume active by default since we don't have is_active field yet)
    active_users = total_users

    # Admin users
    admin_result = await db.execute(
        select(func.count(User.id)).where(User.role == "admin")
    )
    admin_users = admin_result.scalar() or 0

    # New users this month
    from datetime import datetime, timedelta
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= first_day_of_month)
    )
    new_users_this_month = new_users_result.scalar() or 0

    return UserStatsResponse(
        total_users=total_users,
        active_users=active_users,
        admin_users=admin_users,
        new_users_this_month=new_users_this_month
    )

@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all users with optional filtering"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Build query
    query = select(User)

    # Apply filters
    if search:
        query = query.where(
            or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )

    if role:
        query = query.where(User.role == role)

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(User.created_at.desc())

    result = await db.execute(query)
    users = result.scalars().all()

    # Get campaign counts for each user
    user_responses = []
    for user in users:
        from app.db.models import Campaign
        campaign_count_result = await db.execute(
            select(func.count(Campaign.id)).where(Campaign.user_id == user.id)
        )
        campaign_count = campaign_count_result.scalar() or 0

        user_responses.append(UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name or "",
            role=user.role,
            user_type=user.user_type,
            created_at=user.created_at,
            is_active=True,  # Default to active
            last_login=None,  # Not tracking yet
            campaign_count=campaign_count,
            affiliate_tier=user.affiliate_tier,
            affiliate_tier_upgraded_at=user.affiliate_tier_upgraded_at
        ))

    return user_responses

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific user by ID"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get campaign count
    from app.db.models import Campaign
    campaign_count_result = await db.execute(
        select(func.count(Campaign.id)).where(Campaign.user_id == user.id)
    )
    campaign_count = campaign_count_result.scalar() or 0

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name or "",
        role=user.role,
        user_type=user.user_type,
        created_at=user.created_at,
        is_active=True,
        campaign_count=campaign_count,
        affiliate_tier=user.affiliate_tier,
        affiliate_tier_upgraded_at=user.affiliate_tier_upgraded_at
    )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user information"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Don't allow admins to modify themselves
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot modify your own account")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Log the update request for debugging
    logger.info(f"[Admin] Updating user {user_id}: role={user_update.role}, user_type={user_update.user_type}, full_name={user_update.full_name}")

    # Update fields
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.role is not None and user_update.role != "":
        if user_update.role not in ["user", "admin"]:
            logger.error(f"[Admin] Invalid role received: {user_update.role}")
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role = user_update.role
    if user_update.user_type is not None:
        # Validate user_type (allow empty string to be converted to None)
        if user_update.user_type not in ["", "affiliate", "creator", "business", "admin"]:
            logger.error(f"[Admin] Invalid user_type received: {user_update.user_type}")
            raise HTTPException(status_code=400, detail="Invalid user_type")
        user.user_type = user_update.user_type if user_update.user_type else None
    # is_active would be updated here when we add that field

    await db.commit()
    await db.refresh(user)

    # Get campaign count
    from app.db.models import Campaign
    campaign_count_result = await db.execute(
        select(func.count(Campaign.id)).where(Campaign.user_id == user.id)
    )
    campaign_count = campaign_count_result.scalar() or 0

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name or "",
        role=user.role,
        user_type=user.user_type,
        created_at=user.created_at,
        is_active=True,
        campaign_count=campaign_count,
        affiliate_tier=user.affiliate_tier,
        affiliate_tier_upgraded_at=user.affiliate_tier_upgraded_at
    )

@router.post("", response_model=UserResponse)
async def create_user(
    user_create: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new user"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_create.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate role
    if user_create.role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    # Validate user_type if provided
    if user_create.user_type is not None and user_create.user_type not in ["", "affiliate", "creator", "business", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid user_type")

    # Create user
    hashed_password = pwd_context.hash(user_create.password)
    new_user = User(
        email=user_create.email,
        full_name=user_create.full_name,
        hashed_password=hashed_password,
        role=user_create.role,
        user_type=user_create.user_type if user_create.user_type else None
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name or "",
        role=new_user.role,
        user_type=new_user.user_type,
        created_at=new_user.created_at,
        is_active=True,
        campaign_count=0
    )

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a user (soft delete in the future)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Don't allow admins to delete themselves
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # For now, actually delete (in future, implement soft delete with is_active=False)
    await db.delete(user)
    await db.commit()

    return {"message": "User deleted successfully"}

@router.post("/{user_id}/upgrade-affiliate-tier")
async def upgrade_affiliate_tier(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upgrade a user's affiliate tier to Pro.

    This endpoint allows admins to upgrade Marketers to Pro Marketers,
    enabling them to create campaigns from any product URL.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get the user to upgrade
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user is an affiliate
    if user.role != "affiliate":
        raise HTTPException(
            status_code=400,
            detail="Only affiliate users can have their tier upgraded"
        )

    # Check if already pro
    if user.affiliate_tier == "pro":
        return {
            "message": "User is already a Pro affiliate",
            "affiliate_tier": user.affiliate_tier,
            "upgraded_at": user.affiliate_tier_upgraded_at
        }

    # Upgrade to pro
    user.affiliate_tier = "pro"
    user.affiliate_tier_upgraded_at = datetime.utcnow()

    await db.commit()
    await db.refresh(user)

    return {
        "message": f"Successfully upgraded {user.email} to Pro affiliate",
        "user_id": user.id,
        "email": user.email,
        "affiliate_tier": user.affiliate_tier,
        "upgraded_at": user.affiliate_tier_upgraded_at
    }
