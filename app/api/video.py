"""
Video Generation API
Generate videos using Luma AI via PiAPI
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import asyncio
import uuid
import json
from datetime import datetime

from app.db.session import AsyncSessionLocal
from app.db.models import User
from app.core.config.settings import settings

router = APIRouter(prefix="/api/video", tags=["video"])

# Dependency to get DB session
async def get_db() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class VideoGenerateRequest(BaseModel):
    campaign_id: str
    generation_mode: str = Field(default="text_to_video", description="Generation mode: text_to_video, image_to_video, slide_video")
    script: Optional[str] = Field(None, description="Full video script with timestamps (required for text_to_video and slide_video)")
    style: str = Field(default="marketing", description="Video style: marketing, educational, social")
    duration: int = Field(default=20, ge=5, le=20, description="Video duration in seconds (5-20s for short-form)")
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio: 16:9, 9:16, 1:1")
    # For image_to_video mode
    image_url: Optional[str] = Field(None, description="URL of the source image (required for image_to_video)")
    # For slide_video mode
    slides: Optional[List[Dict[str, Any]]] = Field(None, description="List of slides with text and optionally images (for slide_video)")
    motion_intensity: str = Field(default="medium", description="Motion intensity: low, medium, high")

class VideoGenerateResponse(BaseModel):
    video_id: str
    status: str  # processing, completed, failed
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: int
    cost: float
    created_at: datetime

class VideoStatusResponse(BaseModel):
    video_id: str
    status: str
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    progress: Optional[int] = None  # 0-100
    error_message: Optional[str] = None

# ============================================================================
# VIDEO GENERATION SERVICE
# ============================================================================

class LumaVideoService:
    """Service for generating videos using Luma AI via PiAPI"""

    def __init__(self):
        self.api_key = settings.X_API_KEY
        self.base_url = "https://api.piapi.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def generate_video(
        self,
        generation_mode: str,
        script: Optional[str],
        style: str,
        duration: int,
        aspect_ratio: str,
        image_url: Optional[str] = None,
        slides: Optional[List[Dict[str, Any]]] = None,
        motion_intensity: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate video using Luma AI via PiAPI

        Args:
            generation_mode: text_to_video, image_to_video, or slide_video
            script: Video script with timestamps (required for text_to_video and slide_video)
            style: marketing, educational, or social
            duration: Video duration in seconds (5-20 for short-form)
            aspect_ratio: 16:9, 9:16, or 1:1
            image_url: URL of source image (required for image_to_video)
            slides: List of slides with text/images (for slide_video)
            motion_intensity: low, medium, or high

        Returns:
            Dict with generation details
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Prepare the request payload for Luma AI
            payload = {
                "model": "luma-dream-machine-v1",
                "generation_mode": generation_mode,
                "aspect_ratio": aspect_ratio,
                "duration": duration,
                "style": style,
                "motion_intensity": motion_intensity
            }

            # Add mode-specific parameters
            if generation_mode == "text_to_video":
                if not script:
                    raise HTTPException(
                        status_code=400,
                        detail="Script is required for text_to_video mode"
                    )
                payload["prompt"] = self._prepare_prompt(script, style, duration)

            elif generation_mode == "image_to_video":
                if not image_url:
                    raise HTTPException(
                        status_code=400,
                        detail="Image URL is required for image_to_video mode"
                    )
                payload["image_url"] = image_url
                # For image-to-video, use the script as additional guidance if provided
                if script:
                    payload["prompt"] = script

            elif generation_mode == "slide_video":
                if not slides:
                    raise HTTPException(
                        status_code=400,
                        detail="Slides are required for slide_video mode"
                    )
                payload["slides"] = slides
                # Combine slide text for context if script not provided
                if not script and slides:
                    combined_text = " ".join([slide.get("text", "") for slide in slides])
                    payload["prompt"] = self._prepare_prompt(combined_text, style, duration)
                elif script:
                    payload["prompt"] = self._prepare_prompt(script, style, duration)

            try:
                response = await client.post(
                    f"{self.base_url}/video/generate",
                    headers=self.headers,
                    json=payload
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"PiAPI error: {response.text}"
                    )

                return response.json()

            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to connect to PiAPI: {str(e)}"
                )

    def _prepare_prompt(self, script: str, style: str, duration: int) -> str:
        """
        Prepare the video generation prompt for Luma AI

        Combines the script with style-specific guidance
        """
        style_prompts = {
            "marketing": "Create a professional, engaging marketing video with smooth transitions and clear visuals that drive action.",
            "educational": "Create a clear, informative educational video with clean visuals and easy-to-read text overlays.",
            "social": "Create a dynamic, eye-catching social media video optimized for mobile viewing with bold visuals."
        }

        base_prompt = style_prompts.get(style, style_prompts["marketing"])
        duration_context = f"The video should be approximately {duration} seconds long with a clear beginning, middle, and end."

        return f"{base_prompt} {duration_context}\n\nScript:\n{script}"

    async def get_generation_status(self, generation_id: str) -> Dict[str, Any]:
        """
        Check the status of a video generation

        Args:
            generation_id: The generation ID returned by generate_video

        Returns:
            Dict with status details
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/video/status/{generation_id}",
                    headers=self.headers
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Failed to get status: {response.text}"
                    )

                return response.json()

            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to connect to PiAPI: {str(e)}"
                )

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(
    request: VideoGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a video from a script using Luma AI

    This endpoint:
    1. Validates the user's tier limits
    2. Initiates video generation with Luma AI
    3. Returns generation details
    4. Tracks usage in background
    """
    # TODO: Get current user from auth token
    # For now, using a mock user
    user_id = "mock-user-id"

    # TODO: Check user's tier limits
    # If user has reached video limit, return 429

    # Initialize video service
    video_service = LumaVideoService()

    # Validate API key
    if not video_service.api_key:
        raise HTTPException(
            status_code=503,
            detail="Video generation service not configured"
        )

    try:
        # Generate video using Luma AI
        generation_result = await video_service.generate_video(
            generation_mode=request.generation_mode,
            script=request.script,
            style=request.style,
            duration=request.duration,
            aspect_ratio=request.aspect_ratio,
            image_url=request.image_url,
            slides=request.slides,
            motion_intensity=request.motion_intensity
        )

        # Calculate cost based on Luma AI official pricing (Ray Flash 2, 720p)
        # $0.24 for 5 seconds = $0.048 per second
        # Short-form videos (5-20s): ~$0.05 per second
        cost = round(request.duration * 0.05, 2)

        # Create response
        response = VideoGenerateResponse(
            video_id=generation_result.get("id", str(uuid.uuid4())),
            status="processing",
            duration=request.duration,
            cost=cost,
            created_at=datetime.utcnow()
        )

        # TODO: Save to database in background
        # background_tasks.add_task(save_video_generation, user_id, request, response)

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate video: {str(e)}"
        )

@router.get("/status/{video_id}", response_model=VideoStatusResponse)
async def get_video_status(
    video_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the status of a video generation

    Returns:
        Current status, progress, and URLs if completed
    """
    # TODO: Get current user from auth token
    user_id = "mock-user-id"

    # TODO: Check if video belongs to user

    # Initialize video service
    video_service = LumaVideoService()

    try:
        # Get status from PiAPI
        status_result = await video_service.get_generation_status(video_id)

        # Map PiAPI status to our response
        status_mapping = {
            "pending": "processing",
            "processing": "processing",
            "completed": "completed",
            "failed": "failed"
        }

        response = VideoStatusResponse(
            video_id=video_id,
            status=status_mapping.get(status_result.get("status", "unknown"), "unknown"),
            video_url=status_result.get("video_url"),
            thumbnail_url=status_result.get("thumbnail_url"),
            progress=status_result.get("progress", 0),
            error_message=status_result.get("error")
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get video status: {str(e)}"
        )

@router.get("/library", response_model=Dict[str, Any])
async def get_video_library(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's generated videos

    Returns:
        Paginated list of generated videos
    """
    # TODO: Get current user from auth token
    user_id = "mock-user-id"

    # TODO: Query database for user's videos
    # For now, return mock data

    videos = []
    total = 0

    return {
        "videos": videos,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def save_video_generation(
    user_id: str,
    request: VideoGenerateRequest,
    response: VideoGenerateResponse,
    db: AsyncSession
):
    """
    Save video generation record to database

    TODO: Implement database save
    """
    # This will be implemented when we add the database models
    pass
