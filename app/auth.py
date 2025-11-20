# app/auth.py

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Import your project modules
try:
    from app.db.session import get_db
except Exception:
    from db.session import get_db  # type: ignore

try:
    from app.db.models import User
except Exception:
    from models.user import User  # type: ignore

# Initialize logger early
logger = logging.getLogger("app.auth")

try:
    from app.core.config.settings import settings
    logger.info("✓ Using JWT_SECRET_KEY from environment variables (production settings)")
except Exception as e:
    # Minimal fallback - ONLY used if settings import fails (development/testing)
    logger.warning(f"⚠️ Settings import failed, using fallback JWT_SECRET_KEY: {e}")
    logger.warning("⚠️ THIS SHOULD NOT HAPPEN IN PRODUCTION!")

    class _Settings(BaseModel):
        JWT_SECRET_KEY: str = "CHANGE_ME_SUPER_SECRET"
        JWT_ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours (for active content creation sessions)

    settings = _Settings()  # type: ignore

# ----
# Password hashing
# ----

# Use bcrypt with proper configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    if not isinstance(password, str):
        raise TypeError("password must be a string")

    # Guard extremely long values (bcrypt limit)
    if len(password) > 72:
        raise ValueError("Password must be 72 characters or fewer.")
    
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing failed: {e}")
        raise ValueError("Failed to hash password")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    if not isinstance(plain_password, str):
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.exception("Password verification failed: %s", e)
        return False


# ----
# JWT Tokens
# ----

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class TokenPayload(BaseModel):
    sub: str  # user email or id as string
    exp: int


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(tz=timezone.utc) + expires_delta
    else:
        expire = datetime.now(tz=timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY,  # Use JWT_SECRET_KEY from settings
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,  # Use JWT_SECRET_KEY from settings
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},
        )
        return TokenPayload(**payload)
    except JWTError as e:
        logger.warning("JWT decode error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ----
# User helpers - ASYNC
# ----

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email - async version"""
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID - async version"""
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate user - async version"""
    user = await get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ----
# FastAPI dependencies for authentication/authorization
# ----

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get current user from JWT token"""
    payload = decode_access_token(token)
    user_email = payload.sub
    
    # Get user by email (since we store email in the token)
    user = await get_user_by_email(db, user_email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current active user"""
    # If you have a field like is_active
    is_active = getattr(current_user, "is_active", True)
    if not is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# ----
# Optional schemas commonly used by auth routes
# ----

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str