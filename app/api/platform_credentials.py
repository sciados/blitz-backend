# app/api/platform_credentials.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.db.session import get_db
from app.db.models import UserPlatformCredential, User
from app.auth import get_current_active_user
from app.utils.encryption import credential_encryption

router = APIRouter(prefix="/api/platform-credentials", tags=["Platform Credentials"])

# ============================================================================
# SCHEMAS
# ============================================================================

class PlatformCredentialCreate(BaseModel):
    platform_name: str
    account_nickname: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    additional_settings: Optional[dict] = None

class PlatformCredentialUpdate(BaseModel):
    account_nickname: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    additional_settings: Optional[dict] = None
    is_active: Optional[bool] = None

class PlatformCredentialResponse(BaseModel):
    id: int
    platform_name: str
    account_nickname: Optional[str]
    has_api_key: bool
    has_api_secret: bool
    additional_settings: Optional[dict]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# SUPPORTED PLATFORMS
# ============================================================================

SUPPORTED_PLATFORMS = {
    "clickbank": {
        "name": "ClickBank",
        "description": "Digital marketplace for affiliate products",
        "fields": ["api_key", "account_nickname"],
        "icon": "🏦",
        "docs_url": "https://support.clickbank.com/hc/en-us/articles/220369987-API-Keys"
    },
    "jvzoo": {
        "name": "JVZoo",
        "description": "Affiliate marketplace for digital products",
        "fields": ["api_key", "api_secret"],
        "icon": "💼",
        "docs_url": "https://www.jvzoo.com/affiliates/api"
    },
    "warriorplus": {
        "name": "Warrior Plus",
        "description": "Digital product affiliate network",
        "fields": ["api_key"],
        "icon": "⚔️",
        "docs_url": "https://warriorplus.com/api"
    },
    "digistore24": {
        "name": "Digistore24",
        "description": "European affiliate marketplace",
        "fields": ["api_key", "api_secret"],
        "icon": "🇪🇺",
        "docs_url": "https://www.digistore24.com/api"
    },
    "paykickstart": {
        "name": "PayKickstart",
        "description": "Shopping cart and affiliate management",
        "fields": ["api_key", "api_secret"],
        "icon": "🚀",
        "docs_url": "https://paykickstart.com/docs/api"
    },
    "thrivecart": {
        "name": "ThriveCart",
        "description": "Shopping cart platform",
        "fields": ["api_key"],
        "icon": "🛒",
        "docs_url": "https://thrivecart.com/api"
    },
}

@router.get("/platforms")
async def get_supported_platforms():
    """Get list of supported platforms"""
    return {"platforms": SUPPORTED_PLATFORMS}

# ============================================================================
# CRUD ENDPOINTS
# ============================================================================

@router.get("", response_model=List[PlatformCredentialResponse])
async def get_user_credentials(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all platform credentials for current user"""
    result = await db.execute(
        select(UserPlatformCredential)
        .where(UserPlatformCredential.user_id == current_user.id)
        .order_by(UserPlatformCredential.platform_name)
    )
    credentials = result.scalars().all()

    # Return without decrypted keys (just indicate if they exist)
    return [
        PlatformCredentialResponse(
            id=cred.id,
            platform_name=cred.platform_name,
            account_nickname=cred.account_nickname,
            has_api_key=bool(cred.api_key_encrypted),
            has_api_secret=bool(cred.api_secret_encrypted),
            additional_settings=cred.additional_settings,
            is_active=cred.is_active,
            created_at=cred.created_at,
            updated_at=cred.updated_at,
        )
        for cred in credentials
    ]

@router.post("", response_model=PlatformCredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    data: PlatformCredentialCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new platform credential"""

    # Validate platform
    if data.platform_name not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported platform: {data.platform_name}"
        )

    # Check if credential already exists for this platform
    result = await db.execute(
        select(UserPlatformCredential)
        .where(
            and_(
                UserPlatformCredential.user_id == current_user.id,
                UserPlatformCredential.platform_name == data.platform_name
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Credentials for {data.platform_name} already exist. Use update endpoint."
        )

    # Encrypt API credentials
    api_key_encrypted = credential_encryption.encrypt(data.api_key) if data.api_key else None
    api_secret_encrypted = credential_encryption.encrypt(data.api_secret) if data.api_secret else None

    # Create credential
    credential = UserPlatformCredential(
        user_id=current_user.id,
        platform_name=data.platform_name,
        account_nickname=data.account_nickname,
        api_key_encrypted=api_key_encrypted,
        api_secret_encrypted=api_secret_encrypted,
        additional_settings=data.additional_settings,
        is_active=True
    )

    db.add(credential)
    await db.commit()
    await db.refresh(credential)

    return PlatformCredentialResponse(
        id=credential.id,
        platform_name=credential.platform_name,
        account_nickname=credential.account_nickname,
        has_api_key=bool(credential.api_key_encrypted),
        has_api_secret=bool(credential.api_secret_encrypted),
        additional_settings=credential.additional_settings,
        is_active=credential.is_active,
        created_at=credential.created_at,
        updated_at=credential.updated_at,
    )

@router.patch("/{credential_id}", response_model=PlatformCredentialResponse)
async def update_credential(
    credential_id: int,
    data: PlatformCredentialUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update platform credential"""

    # Get credential
    result = await db.execute(
        select(UserPlatformCredential)
        .where(
            and_(
                UserPlatformCredential.id == credential_id,
                UserPlatformCredential.user_id == current_user.id
            )
        )
    )
    credential = result.scalar_one_or_none()

    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )

    # Update fields
    if data.account_nickname is not None:
        credential.account_nickname = data.account_nickname

    if data.api_key is not None:
        credential.api_key_encrypted = credential_encryption.encrypt(data.api_key)

    if data.api_secret is not None:
        credential.api_secret_encrypted = credential_encryption.encrypt(data.api_secret)

    if data.additional_settings is not None:
        credential.additional_settings = data.additional_settings

    if data.is_active is not None:
        credential.is_active = data.is_active

    await db.commit()
    await db.refresh(credential)

    return PlatformCredentialResponse(
        id=credential.id,
        platform_name=credential.platform_name,
        account_nickname=credential.account_nickname,
        has_api_key=bool(credential.api_key_encrypted),
        has_api_secret=bool(credential.api_secret_encrypted),
        additional_settings=credential.additional_settings,
        is_active=credential.is_active,
        created_at=credential.created_at,
        updated_at=credential.updated_at,
    )

@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete platform credential"""

    # Get credential
    result = await db.execute(
        select(UserPlatformCredential)
        .where(
            and_(
                UserPlatformCredential.id == credential_id,
                UserPlatformCredential.user_id == current_user.id
            )
        )
    )
    credential = result.scalar_one_or_none()

    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )

    await db.delete(credential)
    await db.commit()

    return None
