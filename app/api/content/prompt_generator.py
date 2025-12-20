"""Prompt Generator API - Unified prompt generation endpoint"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import User, Campaign
from app.auth import get_current_user
from app.services.prompt_generator_service import PromptGeneratorService

router = APIRouter(prefix="/api/prompt", tags=["prompt-generator"])


# Request/Response Models
class GeneratePromptRequest(BaseModel):
    campaign_id: int
    content_type: str
    user_prompt: Optional[str] = None
    # Content-type specific parameters
    image_type: Optional[str] = None
    style: Optional[str] = None
    aspect_ratio: Optional[str] = None
    video_type: Optional[str] = None
    duration: Optional[int] = None
    article_type: Optional[str] = None


class GeneratePromptResponse(BaseModel):
    prompt: str
    content_type: str
    metadata: Dict[str, Any]
    # Content-type specific fields
    image_type: Optional[str] = None
    style: Optional[str] = None
    aspect_ratio: Optional[str] = None
    video_type: Optional[str] = None
    duration: Optional[int] = None
    keywords: Optional[List[str]] = None


class GetKeywordsRequest(BaseModel):
    campaign_id: int


class GetKeywordsResponse(BaseModel):
    ingredients: List[str]
    features: List[str]
    benefits: List[str]
    pain_points: List[str]


# Dependency to get PromptGeneratorService
def get_prompt_generator(db: AsyncSession = Depends(get_db)) -> PromptGeneratorService:
    """Get PromptGeneratorService instance with database session."""
    return PromptGeneratorService(db)


@router.post("/generate", response_model=GeneratePromptResponse)
async def generate_prompt(
    request: GeneratePromptRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    prompt_service: PromptGeneratorService = Depends(get_prompt_generator)
):
    """
    Generate an optimized prompt for any content type using campaign intelligence

    This endpoint:
    1. Fetches campaign intelligence for the specified campaign
    2. Extracts relevant data based on content type
    3. Generates a tailored prompt that incorporates intelligence data
    4. Returns the prompt along with metadata

    Supported content types:
    - image, hero_image, social_image, ad_image, product_shot
    - video, video_script, slide_video
    - article, review_article, tutorial, comparison
    - email, email_sequence
    - social_post, social_media
    - landing_page
    """
    # Verify campaign ownership
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == request.campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Generate prompt using the service
    try:
        result = await prompt_service.generate_prompt(
            campaign_id=request.campaign_id,
            content_type=request.content_type,
            user_prompt=request.user_prompt,
            # Pass through content-type specific parameters
            image_type=request.image_type,
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            video_type=request.video_type,
            duration=request.duration,
            article_type=request.article_type
        )

        return GeneratePromptResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate prompt: {str(e)}"
        )


@router.post("/keywords", response_model=GetKeywordsResponse)
async def get_available_keywords(
    request: GetKeywordsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    prompt_service: PromptGeneratorService = Depends(get_prompt_generator)
):
    """
    Get available keywords from campaign intelligence for user selection

    Returns categorized keywords (ingredients, features, benefits, pain_points)
    that users can select from when generating content.
    """
    # Verify campaign ownership
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == request.campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Get available keywords
    try:
        keywords = await prompt_service.get_available_keywords(request.campaign_id)
        return GetKeywordsResponse(**keywords)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get keywords: {str(e)}"
        )
