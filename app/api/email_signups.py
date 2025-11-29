# app/api/email_signups.py
from fastapi import APIRouter, HTTPException, Request, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from typing import Optional, List
import csv
import io
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.models import EmailSignup
from app.schemas import EmailSignupCreate, EmailSignupResponse, StatsResponse
from app.auth import get_current_user
from app.core.config.settings import settings

router = APIRouter(prefix="/api", tags=["email-signups"])

# Helper function to get client IP
def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    # Try various headers that might contain the real IP
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, get the first one
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"

# Endpoint: POST /api/signup
@router.post("/signup", response_model=EmailSignupResponse, status_code=status.HTTP_201_CREATED)
async def create_signup(
    signup: EmailSignupCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new email signup or update existing one.
    If email already exists, updates the record instead of creating duplicate.
    """
    # Get client metadata
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    # Check if email already exists
    result = await db.execute(
        select(EmailSignup).where(EmailSignup.email == signup.email)
    )
    existing_signup = result.scalar_one_or_none()

    if existing_signup:
        # Update existing signup - reactivate if inactive
        existing_signup.audience_type = signup.audience_type
        existing_signup.source = signup.source
        existing_signup.is_active = True
        if not existing_signup.ip_address:
            existing_signup.ip_address = ip_address
        if not existing_signup.user_agent:
            existing_signup.user_agent = user_agent
        existing_signup.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(existing_signup)
        return existing_signup

    # Create new signup
    new_signup = EmailSignup(
        email=signup.email,
        audience_type=signup.audience_type,
        source=signup.source,
        ip_address=ip_address,
        user_agent=user_agent,
        is_active=True,
        notified=False
    )

    db.add(new_signup)
    await db.commit()
    await db.refresh(new_signup)

    return new_signup

# Endpoint: GET /api/signups
@router.get("/signups", response_model=List[EmailSignupResponse])
async def get_signups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    audience_type: Optional[str] = Query(None),
    active_only: bool = Query(True),
    current_user: Optional = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all email signups with optional filtering.
    Requires authentication.
    """
    # Build query
    query = select(EmailSignup)

    if active_only:
        query = query.where(EmailSignup.is_active == True)

    if audience_type:
        query = query.where(EmailSignup.audience_type == audience_type)

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(EmailSignup.created_at.desc())

    result = await db.execute(query)
    signups = result.scalars().all()

    return signups

# Endpoint: GET /api/stats
@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    current_user: Optional = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get email signup statistics.
    Requires authentication.
    """
    # Get total count
    total_result = await db.execute(
        select(func.count(EmailSignup.id)).where(EmailSignup.is_active == True)
    )
    total_signups = total_result.scalar() or 0

    # Get count by audience type
    product_dev_result = await db.execute(
        select(func.count(EmailSignup.id)).where(
            and_(
                EmailSignup.audience_type == "product-dev",
                EmailSignup.is_active == True
            )
        )
    )
    product_dev = product_dev_result.scalar() or 0

    affiliate_result = await db.execute(
        select(func.count(EmailSignup.id)).where(
            and_(
                EmailSignup.audience_type == "affiliate",
                EmailSignup.is_active == True
            )
        )
    )
    affiliate = affiliate_result.scalar() or 0

    business_result = await db.execute(
        select(func.count(EmailSignup.id)).where(
            and_(
                EmailSignup.audience_type == "business",
                EmailSignup.is_active == True
            )
        )
    )
    business = business_result.scalar() or 0

    # Get count from last 24 hours
    last_24h_result = await db.execute(
        select(func.count(EmailSignup.id)).where(
            and_(
                EmailSignup.created_at >= datetime.utcnow() - timedelta(days=1),
                EmailSignup.is_active == True
            )
        )
    )
    last_24h = last_24h_result.scalar() or 0

    return StatsResponse(
        total_signups=total_signups,
        product_dev=product_dev,
        affiliate=affiliate,
        business=business,
        last_24h=last_24h
    )

# Endpoint: GET /api/export
@router.get("/export")
async def export_signups(
    audience_type: Optional[str] = Query(None),
    active_only: bool = Query(True),
    current_user: Optional = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export email signups as CSV.
    Requires authentication.
    """
    # Build query
    query = select(EmailSignup)

    if active_only:
        query = query.where(EmailSignup.is_active == True)

    if audience_type:
        query = query.where(EmailSignup.audience_type == audience_type)

    query = query.order_by(EmailSignup.created_at.desc())

    result = await db.execute(query)
    signups = result.scalars().all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "Email",
        "Audience Type",
        "Source",
        "IP Address",
        "User Agent",
        "Created At",
        "Updated At",
        "Is Active",
        "Notified"
    ])

    # Write data
    for signup in signups:
        writer.writerow([
            signup.email,
            signup.audience_type,
            signup.source,
            signup.ip_address or "",
            signup.user_agent or "",
            signup.created_at.isoformat(),
            signup.updated_at.isoformat(),
            "Yes" if signup.is_active else "No",
            "Yes" if signup.notified else "No"
        ])

    # Prepare response
    output.seek(0)

    # Create filename with current date
    filename = f"email_signups_{datetime.utcnow().strftime('%Y%m%d')}.csv"

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

# Endpoint: DELETE /api/signup/{email}
@router.delete("/signup/{email}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_signup(
    email: str,
    current_user: Optional = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete an email signup (marks as inactive).
    Requires authentication.
    """
    result = await db.execute(
        select(EmailSignup).where(EmailSignup.email == email)
    )
    signup = result.scalar_one_or_none()

    if not signup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email signup not found"
        )

    # Soft delete - mark as inactive instead of deleting
    signup.is_active = False
    signup.updated_at = datetime.utcnow()

    await db.commit()

    return None

# Endpoint: GET /health (public)
@router.get("/health")
async def email_health_check():
    """Health check endpoint for email service."""
    return {
        "status": "healthy",
        "service": "Email Signup Service",
        "timestamp": datetime.utcnow().isoformat()
    }
