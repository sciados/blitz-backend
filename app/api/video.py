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
    duration: int = Field(default=10, ge=5, le=20, description="Video duration in seconds (5-20s for short-form)")
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio: 16:9, 9:16, 1:1")
    # For image_to_video mode
    image_url: Optional[str] = Field(None, description="URL of the source image (required for image_to_video)")
    # For slide_video mode
    slides: Optional[List[Dict[str, Any]]] = Field(None, description="List of slides with text and optionally images (for slide_video)")
    motion_intensity: str = Field(default="medium", description="Motion intensity: low, medium, high")
    # Optional: Force a specific provider (for testing or user preference)
    provider: Optional[str] = Field(None, description="Optional: force 'piapi_luma' or 'replicate_veo'")

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
# PROVIDER SELECTION & TIER CHECKING
# ============================================================================

def select_video_provider(duration: int, user_tier: str = "starter", forced_provider: Optional[str] = None) -> str:
    """
    Auto-select video provider based on duration and user tier

    Args:
        duration: Requested video duration in seconds
        user_tier: User's subscription tier (starter, pro, enterprise)
        forced_provider: Optional override (for testing)

    Returns:
        Provider name: 'piapi_luma' or 'replicate_veo'
    """
    # Allow override for testing
    if forced_provider in ['piapi_luma', 'replicate_veo']:
        return forced_provider

    # Starter tier: max 10 seconds
    if user_tier == 'starter' and duration > 10:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "TIER_LIMIT_EXCEEDED",
                "message": f"Your Starter plan ($7/month) supports videos up to 10 seconds. Upgrade to Pro or Enterprise for 15-20 second videos.",
                "current_limit": 10,
                "required_tier": "pro"
            }
        )

    # Auto-select provider based on duration
    if duration <= 10:
        return "piapi_luma"  # Fast, reliable, cost-effective
    else:
        return "replicate_veo"  # Supports long videos (15-20s)

# ============================================================================
# VIDEO GENERATION SERVICES
# ============================================================================

class LumaVideoService:
    """Service for generating videos using Luma AI via PiAPI"""

    def __init__(self):
        self.api_key = settings.X_API_KEY
        self.base_url = "https://api.piapi.ai"
        self.headers = {
            "x-api-key": self.api_key,
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
            # Prepare the input parameters
            # PiAPI Luma supports ray-v1 (5s) and ray-v2 (5s, 10s)
            # However, ray-v2 may not be available yet, so we use ray-v1
            actual_duration = 5  # Only 5s is supported by ray-v1

            input_params = {
                "model_name": "ray-v1",  # Using ray-v1 which is confirmed to work
                "duration": actual_duration,
                "aspect_ratio": aspect_ratio
            }

            # Add mode-specific parameters
            if generation_mode == "text_to_video":
                if not script:
                    raise HTTPException(
                        status_code=400,
                        detail="Script is required for text_to_video mode"
                    )
                input_params["prompt"] = self._prepare_prompt(script, style, duration)

            elif generation_mode == "image_to_video":
                if not image_url:
                    raise HTTPException(
                        status_code=400,
                        detail="Image URL is required for image_to_video mode"
                    )
                # Prompt is required even for image_to_video
                input_params["prompt"] = script or f"Create a video with this image showing {style} content"
                input_params["key_frames"] = {
                    "frame0": {
                        "type": "image",
                        "url": image_url
                    }
                }

            elif generation_mode == "slide_video":
                if not slides or len(slides) == 0:
                    raise HTTPException(
                        status_code=400,
                        detail="Slides are required for slide_video mode"
                    )
                # PiAPI supports up to 2 keyframes: frame0 (start) and frame1 (end)
                # Use first two selected images
                key_frames = {}
                if len(slides) > 0 and slides[0].get("image_url"):
                    key_frames["frame0"] = {
                        "type": "image",
                        "url": slides[0]["image_url"]
                    }
                    # Use first slide's text as prompt if available, otherwise generate one
                    if slides[0].get("text"):
                        input_params["prompt"] = slides[0]["text"]
                    else:
                        input_params["prompt"] = f"Create a {style} video transition"

                if len(slides) > 1 and slides[1].get("image_url"):
                    key_frames["frame1"] = {
                        "type": "image",
                        "url": slides[1]["image_url"]
                    }

                if key_frames:
                    input_params["key_frames"] = key_frames

            # Ensure prompt is always set (required by PiAPI)
            if "prompt" not in input_params:
                input_params["prompt"] = f"Create a {style} video"

            # Build the payload in PiAPI format
            payload = {
                "model": "luma",
                "task_type": "video_generation",
                "input": input_params
            }

            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/task",
                    headers=self.headers,
                    json=payload
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"PiAPI error: {response.text}"
                    )

                result = response.json()

                # Extract task ID from response
                return {
                    "id": result.get("task_id", str(uuid.uuid4())),
                    "status": "processing",
                    "video_url": None,  # Will be available when status is checked
                    "thumbnail_url": None,
                    "actual_duration": actual_duration,  # Return actual duration used
                }

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
        Check the status of a video generation using PiAPI

        Args:
            generation_id: The task ID returned by generate_video

        Returns:
            Dict with status details
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/task/{generation_id}",
                    headers=self.headers
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Failed to get status: {response.text}"
                    )

                result = response.json()

                # Extract data from response
                data = result.get("data", {})
                status = data.get("status", "unknown")

                # Map PiAPI status to our status format
                status_mapping = {
                    "Pending": "processing",
                    "Processing": "processing",
                    "Completed": "completed",
                    "Failed": "failed",
                    "Staged": "processing"
                }
                mapped_status = status_mapping.get(status, "unknown")

                # Extract output data if available
                output = data.get("output", {})
                video_url = None
                thumbnail_url = None

                # Check different possible output structures
                if isinstance(output, dict):
                    # Try common video URL fields
                    video_url = (
                        output.get("video_url")
                        or output.get("video")
                        or (output.get("files", [{}])[0].get("url") if output.get("files") else None)
                    )
                    thumbnail_url = (
                        output.get("thumbnail_url")
                        or output.get("thumbnail")
                        or (output.get("images", [{}])[0].get("url") if output.get("images") else None)
                    )

                return {
                    "status": mapped_status,
                    "video_url": video_url,
                    "thumbnail_url": thumbnail_url,
                    "progress": 100 if mapped_status == "completed" else 0,
                    "error": data.get("error", {}).get("message") if data.get("error") else None
                }

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
    Generate a video from a script

    This endpoint:
    1. Checks user's tier limits based on requested duration
    2. Auto-selects the best provider (PiAPI for 5-10s, Replicate for 15-20s)
    3. Initiates video generation
    4. Returns generation details
    5. Tracks usage in background
    """
    # TODO: Get current user from auth token
    # For now, using a mock user and tier
    user_id = "mock-user-id"
    user_tier = "starter"  # TODO: Get from user profile

    # TODO: Check if user has reached video generation limit
    # If user has reached limit, return 429

    # Validate API key
    video_service = LumaVideoService()
    if not video_service.api_key:
        raise HTTPException(
            status_code=503,
            detail="Video generation service not configured"
        )

    try:
        # Check tier and select provider based on duration
        selected_provider = select_video_provider(
            duration=request.duration,
            user_tier=user_tier,
            forced_provider=request.provider
        )

        # Route to appropriate service
        if selected_provider == "piapi_luma":
            # Use PiAPI with Luma AI (5s, 10s)
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
            # Cost: ~$0.05/second for Luma AI
            # Use actual_duration from the result (5s for ray-v1)
            actual_duration = generation_result.get("actual_duration", 5)
            cost = round(actual_duration * 0.05, 2)

        elif selected_provider == "replicate_veo":
            # TODO: Implement Replicate Veo integration
            # For now, return error
            raise HTTPException(
                status_code=501,
                detail={
                    "error": "PROVIDER_NOT_IMPLEMENTED",
                    "message": f"{selected_provider} provider not yet implemented. Currently only PiAPI (5s) is available.",
                    "available_providers": ["piapi_luma"]
                }
            )

        # Create response
        response = VideoGenerateResponse(
            video_id=generation_result.get("id", str(uuid.uuid4())),
            status="processing",
            duration=actual_duration,
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
