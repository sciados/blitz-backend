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

from app.models.user import User
from app.db.session import get_db
from app.core.auth import get_current_user

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
    created_at: datetime
    is_active: bool
    last_login: Optional[datetime] = None
    campaign_count: int = 0

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "user"

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
        from app.models.campaign import Campaign
        campaign_count_result = await db.execute(
            select(func.count(Campaign.id)).where(Campaign.user_id == user.id)
        )
        campaign_count = campaign_count_result.scalar() or 0

        user_responses.append(UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name or "",
            role=user.role,
            created_at=user.created_at,
            is_active=True,  # Default to active
            last_login=None,  # Not tracking yet
            campaign_count=campaign_count
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
    from app.models.campaign import Campaign
    campaign_count_result = await db.execute(
        select(func.count(Campaign.id)).where(Campaign.user_id == user.id)
    )
    campaign_count = campaign_count_result.scalar() or 0

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name or "",
        role=user.role,
        created_at=user.created_at,
        is_active=True,
        campaign_count=campaign_count
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

    # Update fields
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.role is not None:
        if user_update.role not in ["user", "admin"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role = user_update.role
    # is_active would be updated here when we add that field

    await db.commit()
    await db.refresh(user)

    # Get campaign count
    from app.models.campaign import Campaign
    campaign_count_result = await db.execute(
        select(func.count(Campaign.id)).where(Campaign.user_id == user.id)
    )
    campaign_count = campaign_count_result.scalar() or 0

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name or "",
        role=user.role,
        created_at=user.created_at,
        is_active=True,
        campaign_count=campaign_count
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

    # Create user
    hashed_password = pwd_context.hash(user_create.password)
    new_user = User(
        email=user_create.email,
        full_name=user_create.full_name,
        hashed_password=hashed_password,
        role=user_create.role
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name or "",
        role=new_user.role,
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
