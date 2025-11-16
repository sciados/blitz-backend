# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import User
from app.schemas import UserCreate, UserLogin, UserResponse, Token
from app.auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_user_by_email
)
from app.core.config.settings import settings

# Profile update schema
class ProfileUpdate(BaseModel):
    full_name: str
    profile_image_url: str | None = None

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# ====
# REGISTER
# ====

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    pwd = user_data.password
    
    # Validate password type
    if not isinstance(pwd, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Password must be a string."
        )

    # Validate password length (bcrypt has 72 byte limit)
    if len(pwd) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Password must be at least 8 characters."
        )
    
    if len(pwd) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Password must be 72 characters or fewer."
        )
    
    # Hash password
    try:
        hashed_password = get_password_hash(pwd)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

# ====
# LOGIN
# ====

@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login and receive access token."""
    
    user = await authenticate_user(db, user_credentials.email, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with role
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# ====
# GET CURRENT USER
# ====

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return current_user

# ====
# UPDATE PROFILE
# ====

@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile information."""
    # Update full name
    current_user.full_name = profile_data.full_name

    # Update profile image URL if provided
    if profile_data.profile_image_url is not None:
        current_user.profile_image_url = profile_data.profile_image_url

    await db.commit()
    await db.refresh(current_user)

    return current_user

# ====
# REFRESH TOKEN
# ====

@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_active_user)
):
    """Refresh access token for authenticated user (extends session)."""

    # Create new access token with same data but fresh expiration
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.email, "role": current_user.role},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}