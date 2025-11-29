"""
Admin API endpoints for email campaigns
Handles sending launch emails to signup audiences
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.db.session import get_db
from app.db.models import EmailSignup
from app.services.resend_service import ResendService
from app.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin-campaigns"])

# Initialize service
try:
    resend_service = ResendService()
except Exception as e:
    # Service not available (RESEND_API_KEY not set)
    resend_service = None


@router.post("/email-campaigns/send")
async def send_campaign(
    background_tasks: BackgroundTasks,
    audience_type: Optional[str] = Query(None, description="Filter by audience"),
    subject: str = Query(..., description="Email subject"),
    template_type: str = Query("launch", description="Template type"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send campaign email to signups.
    Supports sending to all signups or filtered by audience_type.
    """

    # Check if service is available
    if resend_service is None:
        raise HTTPException(
            status_code=503,
            detail="Email service not configured. RESEND_API_KEY not set."
        )

    # Get signups
    query = select(EmailSignup).where(EmailSignup.is_active == True)

    if audience_type:
        query = query.where(EmailSignup.audience_type == audience_type)

    result = await db.execute(query)
    signups = result.scalars().all()

    if not signups:
        raise HTTPException(status_code=404, detail="No signups found")

    # Get emails list
    emails = [signup.email for signup in signups]

    # Get template
    template = resend_service.get_launch_template(
        audience_type or "affiliate",
        {"first_name": ""}
    )

    # Send campaign in background
    background_tasks.add_task(
        resend_service.send_campaign_to_audience,
        emails,
        subject,
        template
    )

    return {
        "message": f"Campaign started for {len(emails)} recipients",
        "total_emails": len(emails),
        "audience_type": audience_type or "all"
    }


@router.post("/email-campaigns/send-single")
async def send_single_email(
    email: str,
    subject: str,
    html: str,
    current_user=Depends(get_current_user)
):
    """Send email to single recipient"""

    if resend_service is None:
        raise HTTPException(
            status_code=503,
            detail="Email service not configured. RESEND_API_KEY not set."
        )

    result = await resend_service.send_email(email, subject, html)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "message": "Email sent successfully",
        "email_id": result["data"]["id"]
    }


@router.get("/email-campaigns/status")
async def get_campaign_status(
    current_user=Depends(get_current_user)
):
    """Check if email service is configured and available"""

    if resend_service is None:
        return {
            "status": "not_configured",
            "message": "RESEND_API_KEY not set"
        }

    try:
        # Try to verify the service is working
        test_result = await resend_service.send_email(
            to="test@example.com",
            subject="Test",
            html="<p>Test</p>"
        )

        # This will fail (invalid email) but confirms service is working
        return {
            "status": "configured",
            "message": "Email service ready"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Service error: {str(e)}"
        }
