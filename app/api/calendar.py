"""Calendar API endpoints for calendar-driven content generation."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from app.db.session import get_db
from app.db.models import User, Campaign
from app.auth import get_current_active_user
from app.services.generator_manager import GeneratorManager

router = APIRouter(prefix="/api/calendar", tags=["calendar"])
logger = logging.getLogger(__name__)


# Pydantic models for requests/responses
class CalendarGenerateRequest(BaseModel):
    """Request model for calendar-driven content generation"""
    campaign_id: int
    day_number: int
    content_type: str
    marketing_angle: str
    primary_goal: str
    context: Optional[str] = None
    keywords: Optional[List[str]] = None
    length: Optional[str] = None
    # Image-specific parameters
    style: Optional[str] = "photorealistic"
    aspect_ratio: Optional[str] = "1:1"


class BatchCalendarGenerateRequest(BaseModel):
    """Request model for batch generation from calendar"""
    campaign_id: int
    items: List[CalendarGenerateRequest]


class CalendarContentResponse(BaseModel):
    """Response model for calendar-generated content"""
    success: bool
    content: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/generate", response_model=CalendarContentResponse)
async def generate_content_from_calendar(
    request: CalendarGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate content using calendar-driven approach

    This endpoint takes calendar parameters (day, content type, marketing angle, etc.)
    and generates context-aware content using campaign intelligence.

    Args:
        request: Calendar generation request with all parameters
        current_user: Authenticated user
        db: Database session

    Returns:
        Generated content with metadata
    """
    try:
        # Verify campaign belongs to user
        campaign = await _verify_campaign_ownership(db, request.campaign_id, current_user.id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found or access denied"
            )

        # Get user's signature for email content
        user_signature = current_user.signature

        # Initialize generator manager
        generator_manager = GeneratorManager(db)

        # Build calendar parameters
        calendar_params = {
            "day_number": request.day_number,
            "content_type": request.content_type,
            "marketing_angle": request.marketing_angle,
            "primary_goal": request.primary_goal,
            "context": request.context,
            "keywords": request.keywords or [],
            "length": request.length,
            "style": request.style,
            "aspect_ratio": request.aspect_ratio
        }

        # Generate content from calendar
        result = await generator_manager.generate_from_calendar(
            campaign_id=request.campaign_id,
            calendar_params=calendar_params,
            user_signature=user_signature
        )

        if result.get("success"):
            logger.info(
                f"✅ Calendar-driven generation successful: Campaign {request.campaign_id}, "
                f"Day {request.day_number}, Type: {request.content_type}"
            )
            return CalendarContentResponse(
                success=True,
                content=result.get("content"),
                metadata=result.get("metadata")
            )
        else:
            error_msg = result.get("error", "Unknown error during generation")
            logger.error(f"❌ Calendar-driven generation failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in calendar generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/generate/batch", response_model=Dict[str, Any])
async def batch_generate_content_from_calendar(
    request: BatchCalendarGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate multiple content items from calendar in batch

    This endpoint generates multiple pieces of content based on a list of
    calendar items, useful for generating all content for a campaign day
    or week at once.

    Args:
        request: Batch generation request with campaign_id and list of items
        current_user: Authenticated user
        db: Database session

    Returns:
        Batch generation results with success/failure counts
    """
    try:
        # Verify campaign belongs to user
        campaign = await _verify_campaign_ownership(db, request.campaign_id, current_user.id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found or access denied"
            )

        # Get user's signature for email content
        user_signature = current_user.signature

        # Initialize generator manager
        generator_manager = GeneratorManager(db)

        # Convert request items to calendar parameters
        calendar_items = []
        for item in request.items:
            calendar_items.append({
                "day_number": item.day_number,
                "content_type": item.content_type,
                "marketing_angle": item.marketing_angle,
                "primary_goal": item.primary_goal,
                "context": item.context,
                "keywords": item.keywords or [],
                "length": item.length,
                "style": item.style,
                "aspect_ratio": item.aspect_ratio
            })

        # Generate content in batch
        result = await generator_manager.batch_generate_from_calendar(
            campaign_id=request.campaign_id,
            calendar_items=calendar_items,
            user_signature=user_signature
        )

        logger.info(
            f"📦 Batch generation completed: {result.get('successful')} successful, "
            f"{result.get('failed')} failed"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in batch calendar generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/plan/{campaign_id}")
async def get_calendar_plan(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the 21-day marketing plan for a campaign

    This endpoint returns the strategic marketing plan for the campaign,
    including day-by-day content recommendations.

    Args:
        campaign_id: Campaign ID
        current_user: Authenticated user
        db: Database session

    Returns:
        21-day marketing plan data
    """
    try:
        # Verify campaign belongs to user
        campaign = await _verify_campaign_ownership(db, campaign_id, current_user.id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found or access denied"
            )

        # Import the marketing plan data
        from app.config.marketing_plan_data import marketing_plan_data

        # Return the plan (this is a static 21-day plan)
        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "plan": marketing_plan_data,
            "total_days": 21,
            "note": "This is a strategic 21-day marketing plan. Content should be generated according to the daily recommendations."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving calendar plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/recommendations/{campaign_id}/{day_number}")
async def get_day_recommendations(
    campaign_id: int,
    day_number: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get content recommendations for a specific day

    This endpoint returns the recommended content types, marketing angles,
    and goals for a specific day in the campaign.

    Args:
        campaign_id: Campaign ID
        day_number: Day number (1-21)
        current_user: Authenticated user
        db: Database session

    Returns:
        Day-specific recommendations
    """
    try:
        # Verify campaign belongs to user
        campaign = await _verify_campaign_ownership(db, campaign_id, current_user.id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found or access denied"
            )

        # Import the marketing plan data
        from app.config.marketing_plan_data import marketing_plan_data

        # Validate day number
        if day_number < 1 or day_number > 21:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Day number must be between 1 and 21"
            )

        # Get recommendations for the day
        day_data = marketing_plan_data.get(str(day_number), {})
        if not day_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No recommendations found for day {day_number}"
            )

        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "day": day_number,
            "date_offset": day_data.get("date_offset", day_number - 1),
            "theme": day_data.get("theme", ""),
            "primary_goal": day_data.get("primary_goal", ""),
            "content_recommendations": day_data.get("content_recommendations", []),
            "key_points": day_data.get("key_points", []),
            "marketing_angles": day_data.get("marketing_angles", [])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving day recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


async def _verify_campaign_ownership(db: AsyncSession, campaign_id: int, user_id: int):
    """
    Helper function to verify campaign belongs to user

    Args:
        db: Database session
        campaign_id: Campaign ID
        user_id: User ID

    Returns:
        Campaign object if verified, None otherwise
    """
    stmt = select(Campaign).where(
        Campaign.id == campaign_id,
        Campaign.user_id == user_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
