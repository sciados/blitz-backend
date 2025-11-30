"""API endpoints for affiliate directory.

Provides endpoints for browsing affiliates, managing profiles, and networking.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from app.db.session import get_db
from app.services.message_service import MessageService
from app.schemas import (
    AffiliateProfileCreate,
    AffiliateProfileUpdate,
    AffiliateProfileResponse,
    AffiliateSearchResponse
)
from app.auth import get_current_user

router = APIRouter(prefix="/api/affiliates", tags=["affiliates"])


@router.get("", response_model=List[AffiliateProfileResponse])
async def list_affiliates(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of affiliates."""
    service = MessageService(db)
    profiles, total = await service.get_affiliates(
        page=page,
        per_page=per_page,
        search=search
    )

    return [
        AffiliateProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            email=profile.user.email,
            full_name=profile.user.full_name,
            profile_image_url=profile.user.profile_image_url,
            bio=profile.bio,
            specialty=profile.specialty,
            years_experience=profile.years_experience,
            website_url=profile.website_url,
            social_links=profile.social_links,
            stats=profile.stats,
            reputation_score=profile.reputation_score,
            verified=profile.verified,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
        for profile in profiles
    ]


@router.get("/search", response_model=List[AffiliateSearchResponse])
async def search_affiliates(
    search: Optional[str] = Query(None, description="Search term"),
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    user_type: Optional[str] = Query(None, description="Filter by user type (Affiliate, Creator, Business)"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search affiliates with connection status."""
    service = MessageService(db)
    results = await service.search_affiliates(
        current_user_id=current_user.id,
        search_term=search,
        specialty=specialty,
        user_type=user_type
    )

    return [
        AffiliateSearchResponse(
            id=result["id"],
            user_id=result["user_id"],
            email=result["email"],
            full_name=result["full_name"],
            user_type=result["user_type"],
            profile_image_url=result["profile_image_url"],
            specialty=result["specialty"],
            years_experience=result["years_experience"],
            reputation_score=result["reputation_score"],
            verified=result["verified"],
            is_connected=result["is_connected"],
            mutual_products=result["mutual_products"]
        )
        for result in results
    ]


@router.get("/{user_id}", response_model=AffiliateProfileResponse)
async def get_affiliate_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get affiliate profile by user ID."""
    service = MessageService(db)
    profile = await service.get_affiliate_profile(user_id=user_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return AffiliateProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        email=profile.user.email,
        full_name=profile.user.full_name,
        profile_image_url=profile.user.profile_image_url,
        bio=profile.bio,
        specialty=profile.specialty,
        years_experience=profile.years_experience,
        website_url=profile.website_url,
        social_links=profile.social_links,
        stats=profile.stats,
        reputation_score=profile.reputation_score,
        verified=profile.verified,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )


@router.post("/profile", response_model=AffiliateProfileResponse)
async def create_affiliate_profile(
    profile_data: AffiliateProfileCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or update affiliate profile."""
    service = MessageService(db)

    # Only affiliates can create profiles
    if current_user.role != "affiliate":
        raise HTTPException(status_code=403, detail="Only affiliates can create profiles")

    profile = await service.create_or_update_affiliate_profile(
        user_id=current_user.id,
        profile_data=profile_data.dict()
    )

    return AffiliateProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        email=profile.user.email,
        full_name=profile.user.full_name,
        profile_image_url=profile.user.profile_image_url,
        bio=profile.bio,
        specialty=profile.specialty,
        years_experience=profile.years_experience,
        website_url=profile.website_url,
        social_links=profile.social_links,
        stats=profile.stats,
        reputation_score=profile.reputation_score,
        verified=profile.verified,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )


@router.put("/profile", response_model=AffiliateProfileResponse)
async def update_affiliate_profile(
    profile_data: AffiliateProfileUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update affiliate profile."""
    service = MessageService(db)

    # Only affiliates can update profiles
    if current_user.role != "affiliate":
        raise HTTPException(status_code=403, detail="Only affiliates can update profiles")

    profile = await service.create_or_update_affiliate_profile(
        user_id=current_user.id,
        profile_data=profile_data.dict(exclude_unset=True)
    )

    return AffiliateProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        email=profile.user.email,
        full_name=profile.user.full_name,
        profile_image_url=profile.user.profile_image_url,
        bio=profile.bio,
        specialty=profile.specialty,
        years_experience=profile.years_experience,
        website_url=profile.website_url,
        social_links=profile.social_links,
        stats=profile.stats,
        reputation_score=profile.reputation_score,
        verified=profile.verified,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )


@router.get("/my-network", response_model=List[Dict[str, Any]])
async def get_my_network(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's affiliate network/connections."""
    service = MessageService(db)
    connections = await service.get_my_connections(user_id=current_user.id)

    # Return simplified connection info
    return [
        {
            "connection_id": conn.id,
            "user1_id": conn.user1_id,
            "user2_id": conn.user2_id,
            "connection_type": conn.connection_type,
            "created_at": conn.created_at
        }
        for conn in connections
    ]
