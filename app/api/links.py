"""
Link Shortener API Endpoints

Handles:
- Creating shortened links
- Redirecting short links with click tracking
- Link analytics
- Link management
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl
import logging

from app.db.session import get_db
from app.db.models import User, Campaign, ShortenedLink
from app.auth import get_current_active_user
from app.services.url_shortener import URLShortenerService

logger = logging.getLogger(__name__)

# Main router for link management (authenticated endpoints)
router = APIRouter(prefix="/api/links", tags=["URL Shortener"])

# Separate router for public redirect (prefixed to avoid conflicts, no auth)
redirect_router = APIRouter(prefix="/r", tags=["URL Shortener"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateShortLinkRequest(BaseModel):
    """Request to create a shortened link"""
    original_url: HttpUrl
    campaign_id: int
    custom_slug: Optional[str] = None
    title: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class ShortLinkResponse(BaseModel):
    """Response with shortened link details"""
    id: int
    short_code: str
    short_url: str
    original_url: str
    title: Optional[str]
    campaign_id: int
    total_clicks: int
    unique_clicks: int
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class LinkAnalyticsResponse(BaseModel):
    """Response with link analytics data"""
    short_code: str
    total_clicks: int
    unique_clicks: int
    clicks_by_country: List[Dict[str, Any]]
    clicks_by_device: Dict[str, int]
    clicks_by_date: List[Dict[str, Any]]
    period_days: int


# ============================================================================
# REDIRECT ENDPOINT (Public - No Auth Required)
# ============================================================================

@redirect_router.get("/{short_code}", include_in_schema=False)
async def redirect_short_link(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Redirect a shortened link and track the click

    This is the public endpoint that users click on.
    No authentication required.

    Example: GET /abc123 → Redirects to affiliate link
    """
    shortener = URLShortenerService(db)

    # Get shortened link
    shortened_link = await shortener.get_link_by_code(short_code)

    if not shortened_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found or has expired"
        )

    # CRITICAL: Load data from shortened_link BEFORE any async operations
    # to avoid detached instance errors
    original_url = shortened_link.original_url
    utm_params = shortened_link.utm_params

    # Get real client IP (from X-Forwarded-For header if behind proxy)
    client_ip = request.headers.get('x-forwarded-for')
    if client_ip:
        # X-Forwarded-For can be a comma-separated list; get the first (original client)
        client_ip = client_ip.split(',')[0].strip()
    else:
        # Fallback to direct connection IP
        client_ip = request.client.host if request.client else None

    # Extract request data for analytics
    request_data = {
        'ip_address': client_ip,
        'user_agent': request.headers.get('user-agent'),
        'referer': request.headers.get('referer'),
        'additional_data': {
            'accept_language': request.headers.get('accept-language'),
            'accept_encoding': request.headers.get('accept-encoding'),
            'x_forwarded_for': request.headers.get('x-forwarded-for')  # Store for debugging
        }
    }

    # Track the click (async, don't wait)
    try:
        await shortener.track_click(shortened_link, request_data)
        await db.commit()
        logger.info(f"✅ Tracked click for {short_code} from {request_data.get('ip_address')}")
    except Exception as e:
        # Don't fail redirect if tracking fails
        logger.error(f"❌ Failed to track click for {short_code}: {str(e)}", exc_info=True)
        # Rollback the failed transaction
        await db.rollback()

    # Build redirect URL with UTM parameters
    redirect_url = shortener.build_redirect_url(
        original_url,
        utm_params
    )

    # Redirect to original URL
    return RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )


# ============================================================================
# DEBUG ENDPOINTS
# ============================================================================

@redirect_router.get("/{short_code}/debug", response_model=Dict[str, Any])
async def debug_link_public(
    short_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Public debug endpoint to check link and click data (NO AUTH REQUIRED)
    Useful for troubleshooting tracking issues
    """
    from app.db.models import LinkClick

    shortener = URLShortenerService(db)

    # Get link
    shortened_link = await shortener.get_link_by_code(short_code)

    if not shortened_link:
        raise HTTPException(status_code=404, detail="Link not found")

    # Get all clicks for this link
    clicks_result = await db.execute(
        select(LinkClick)
        .where(LinkClick.shortened_link_id == shortened_link.id)
        .order_by(LinkClick.clicked_at.desc())
    )
    clicks = clicks_result.scalars().all()

    return {
        "short_code": short_code,
        "link_id": shortened_link.id,
        "original_url": shortened_link.original_url,
        "total_clicks": shortened_link.total_clicks,
        "unique_clicks": shortened_link.unique_clicks,
        "is_active": shortened_link.is_active,
        "clicks_in_db": len(clicks),
        "recent_clicks": [
            {
                "ip": str(click.ip_address),
                "clicked_at": click.clicked_at.isoformat(),
                "device": click.device_type,
                "is_unique": click.is_unique
            }
            for click in clicks[:10]
        ]
    }


# ============================================================================
# LINK MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("", response_model=ShortLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_short_link(
    link_data: CreateShortLinkRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a shortened link for an affiliate URL

    Automatically generates a short code or uses custom slug.
    """
    # Verify campaign ownership
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == link_data.campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Build UTM parameters if provided
    utm_params = None
    if link_data.utm_source or link_data.utm_medium or link_data.utm_campaign:
        utm_params = {
            'utm_source': link_data.utm_source or 'blitz',
            'utm_medium': link_data.utm_medium or 'affiliate',
            'utm_campaign': link_data.utm_campaign or campaign.name.lower().replace(' ', '-')
        }

    # Create shortened link
    shortener = URLShortenerService(db)

    try:
        shortened_link = await shortener.shorten_url(
            original_url=str(link_data.original_url),
            campaign_id=campaign.id,
            user_id=current_user.id,
            custom_slug=link_data.custom_slug,
            title=link_data.title,
            utm_params=utm_params
        )

        await db.commit()
        await db.refresh(shortened_link)

        # Build short URL with domain rotation
        from app.services.domain_rotator import domain_rotator
        short_url = domain_rotator.build_short_url(shortened_link.short_code)

        return ShortLinkResponse(
            id=shortened_link.id,
            short_code=shortened_link.short_code,
            short_url=short_url,
            original_url=shortened_link.original_url,
            title=shortened_link.title,
            campaign_id=shortened_link.campaign_id,
            total_clicks=shortened_link.total_clicks,
            unique_clicks=shortened_link.unique_clicks,
            is_active=shortened_link.is_active,
            created_at=shortened_link.created_at.isoformat()
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[ShortLinkResponse])
async def list_short_links(
    campaign_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all shortened links for the current user

    Optionally filter by campaign_id
    """
    query = select(ShortenedLink).where(ShortenedLink.user_id == current_user.id)

    if campaign_id:
        # Verify campaign ownership
        campaign_result = await db.execute(
            select(Campaign).where(
                Campaign.id == campaign_id,
                Campaign.user_id == current_user.id
            )
        )
        if not campaign_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        query = query.where(ShortenedLink.campaign_id == campaign_id)

    query = query.order_by(ShortenedLink.created_at.desc())

    result = await db.execute(query)
    links = result.scalars().all()

    # Build response with domain rotation
    from app.services.domain_rotator import domain_rotator
    short_links = []
    for link in links:
        short_url = domain_rotator.build_short_url(link.short_code)
        short_links.append(ShortLinkResponse(
            id=link.id,
            short_code=link.short_code,
            short_url=short_url,
            original_url=link.original_url,
            title=link.title,
            campaign_id=link.campaign_id,
            total_clicks=link.total_clicks,
            unique_clicks=link.unique_clicks,
            is_active=link.is_active,
            created_at=link.created_at.isoformat()
        ))

    return short_links


@router.get("/{short_code}/analytics", response_model=LinkAnalyticsResponse)
async def get_link_analytics(
    short_code: str,
    days: int = 30,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed analytics for a shortened link

    Returns clicks by country, device, date, etc.
    """
    # Get shortened link and verify ownership
    result = await db.execute(
        select(ShortenedLink).where(
            ShortenedLink.short_code == short_code,
            ShortenedLink.user_id == current_user.id
        )
    )
    shortened_link = result.scalar_one_or_none()

    if not shortened_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )

    # Get analytics
    shortener = URLShortenerService(db)
    analytics = await shortener.get_link_analytics(shortened_link.id, days)

    return LinkAnalyticsResponse(
        short_code=short_code,
        total_clicks=analytics['total_clicks'],
        unique_clicks=shortened_link.unique_clicks,
        clicks_by_country=analytics['clicks_by_country'],
        clicks_by_device=analytics['clicks_by_device'],
        clicks_by_date=analytics['clicks_by_date'],
        period_days=analytics['period_days']
    )


@router.patch("/{short_code}/toggle")
async def toggle_link_status(
    short_code: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle a link between active and inactive

    Inactive links will return 404 when accessed
    """
    # Get shortened link and verify ownership
    result = await db.execute(
        select(ShortenedLink).where(
            ShortenedLink.short_code == short_code,
            ShortenedLink.user_id == current_user.id
        )
    )
    shortened_link = result.scalar_one_or_none()

    if not shortened_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )

    # Toggle status
    shortened_link.is_active = not shortened_link.is_active
    await db.commit()
    await db.refresh(shortened_link)

    return {
        "short_code": short_code,
        "is_active": shortened_link.is_active,
        "message": f"Link {'activated' if shortened_link.is_active else 'deactivated'} successfully"
    }


@router.delete("/{short_code}")
async def delete_short_link(
    short_code: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a shortened link

    This will also delete all associated click analytics
    """
    # Get shortened link and verify ownership
    result = await db.execute(
        select(ShortenedLink).where(
            ShortenedLink.short_code == short_code,
            ShortenedLink.user_id == current_user.id
        )
    )
    shortened_link = result.scalar_one_or_none()

    if not shortened_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )

    # Delete link (CASCADE will delete all clicks)
    await db.delete(shortened_link)
    await db.commit()

    return {
        "message": "Link deleted successfully",
        "short_code": short_code
    }
