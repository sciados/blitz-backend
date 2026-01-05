# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
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
from app.utils.r2_storage import R2Storage
from app.services.usage_limits import start_trial, check_trial_status, get_effective_tier, UsageLimitsService

# Profile update schema
class ProfileUpdate(BaseModel):
    full_name: str
    profile_image_url: str | None = None
    signature: str | None = None

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

    # Start 7-day free trial for new user
    await start_trial(db, new_user.id, trial_days=7)
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
    
    # Create access token with role and subscription tier
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.email,
            "role": user.role,
            "subscription_tier": user.subscription_tier or "trial",
            "user_type": user.user_type
        },
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


@router.get("/subscription")
async def get_subscription_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's subscription/trial status.
    Returns tier, trial info, and days remaining.
    """
    status = await check_trial_status(db, current_user.id)

    return {
        "user_id": current_user.id,
        "email": current_user.email,
        **status,
        "pricing": {
            "standard": {"price": 7, "name": "Standard"},
            "pro": {"price": 47, "name": "Pro"},
            "business": {"price": 97, "name": "Business"}
        }
    }


@router.get("/usage")
async def get_usage_and_limits(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's usage and tier limits.
    Returns current usage counts and maximum limits for dashboard display.
    """
    # Get effective tier (considers trial, subscription, etc.)
    effective_tier = await get_effective_tier(db, current_user.id)

    # Get usage and limits using the service
    service = UsageLimitsService(db)
    usage = await service.get_user_usage(current_user.id)
    limits = await service.get_tier_limits(effective_tier)

    # Default limits if none found
    if not limits:
        limits = {
            "monthly_campaigns": 3,
            "monthly_ai_text_generations": 10,
            "monthly_ai_image_generations": 10,
            "monthly_ai_video_scripts": 5,
        }

    return {
        "tier": effective_tier,
        "usage": {
            "campaigns": usage.get("campaigns_created", 0),
            "text_content": usage.get("ai_text_generations_used", 0),
            "images": usage.get("ai_image_generations_used", 0),
            "videos": usage.get("ai_video_scripts_used", 0),
        },
        "limits": {
            "campaigns": limits.get("monthly_campaigns"),
            "text_content": limits.get("monthly_ai_text_generations"),
            "images": limits.get("monthly_ai_image_generations"),
            "videos": limits.get("monthly_ai_video_scripts"),
        }
    }

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

    # Update signature if provided
    if profile_data.signature is not None:
        current_user.signature = profile_data.signature

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

# ====
# UPLOAD PROFILE IMAGE
# ====

@router.post("/upload-profile-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload profile image to Cloudflare R2 and update user profile.
    Accepts: JPG, PNG, GIF, WebP (max 5MB)
    """

    # Check if R2 is configured
    if not R2Storage.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File upload service is not configured"
        )

    # Validate file size (5MB max)
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 5MB limit"
        )

    # Validate content type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )

    try:
        # Delete old profile image if exists
        if current_user.profile_image_url:
            R2Storage.delete_file(current_user.profile_image_url)

        # Upload to R2
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        image_url = R2Storage.upload_file(
            file=file,
            folder="profile-images",
            allowed_extensions=allowed_extensions
        )

        # Update user profile
        current_user.profile_image_url = image_url
        await db.commit()
        await db.refresh(current_user)

        return {
            "message": "Profile image uploaded successfully",
            "profile_image_url": image_url
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )