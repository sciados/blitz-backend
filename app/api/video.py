"""
Video Generation API
Generate videos using Luma AI via PiAPI
"""

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import httpx
import asyncio
import uuid
import json
import logging
import tempfile
import os
from datetime import datetime

from app.db.session import AsyncSessionLocal
from app.db.models import User, VideoGeneration
from app.auth import get_current_user
from app.core.config.settings import settings
from app.services.storage_r2 import r2_storage

logger = logging.getLogger(__name__)

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
    campaign_id: Union[str, int]
    generation_mode: str = Field(default="text_to_video", description="Generation mode: text_to_video, image_to_video, slide_video")
    script: Optional[str] = Field(None, description="Full video script with timestamps (required for text_to_video and slide_video)")
    style: str = Field(default="marketing", description="Video style: marketing, educational, social")
    duration: int = Field(default=10, ge=5, le=60, description="Video duration in seconds (5s or 10s supported, other values use closest match)")
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

class VideoSaveRequest(BaseModel):
    video_id: int
    campaign_id: Optional[str] = None

class VideoSaveResponse(BaseModel):
    video_id: int
    r2_key: str
    video_url: str
    thumbnail_url: Optional[str] = None
    saved_at: datetime

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
        Provider name: 'piapi_luma', 'piapi_hunyuan', 'piapi_wanx', or 'replicate_veo'
    """
    # Allow override for testing
    if forced_provider in ['piapi_luma', 'piapi_hunyuan_fast', 'piapi_hunyuan_standard', 'piapi_wanx_1.3b', 'piapi_wanx_14b', 'replicate_veo']:
        return forced_provider

    # Starter tier: max 60 seconds
    if user_tier == 'starter' and duration > 60:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "TIER_LIMIT_EXCEEDED",
                "message": f"Your Starter plan ($7/month) supports videos up to 60 seconds. Upgrade to Enterprise for longer videos.",
                "current_limit": 60,
                "required_tier": "enterprise"
            }
        )

    # Auto-select provider based on duration and tier
    # For 10s videos: Use Luma ray-v2 (txt2video) or extend 5s to 10s (img2video/slide)
    if duration == 10:
        return "piapi_luma"  # Luma for txt2video, extended to 10s for img2video/slide

    # 5s videos: Use Hunyuan (best value)
    elif duration == 5:
        return "piapi_hunyuan_fast"  # $0.03 - Best value for 5s videos

    # Starter tier: max 60 seconds
    # Use Hunyuan for 6-60s (will generate 5s, then extend to requested duration)
    elif duration > 5 and duration <= 60:
        return "piapi_hunyuan_fast"  # Will generate 5s, extend to requested duration

    # Enterprise tier >60s: Use WanX 14B (premium quality)
    elif duration > 60 and user_tier == 'enterprise':
        return "piapi_wanx_14b"  # $0.28 - Premium quality for long videos

    # Default fallback for edge cases
    else:
        return "piapi_hunyuan_fast"  # Use Hunyuan as fallback

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
            # PiAPI Luma supports:
            # - ray-v1: 5s duration (all modes)
            # - ray-v2: 10s duration (txt2video only, img2video uses ray-v1)
            if duration >= 10 and generation_mode == "text_to_video":
                model_name = "ray-v2"
                actual_duration = 10
            else:
                model_name = "ray-v1"
                actual_duration = 5

            input_params = {
                "model_name": model_name,
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
                logger.info(f"PiAPI Luma response: {result}")

                # Extract task ID from response (PiAPI returns it in nested data object)
                task_id = result.get("data", {}).get("task_id")

                # If not in data, check top level (PiAPI might have different response structure)
                if not task_id:
                    task_id = result.get("task_id")

                if not task_id:
                    logger.error(f"No task ID in PiAPI response. Full response: {result}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"No task ID returned from PiAPI video generation. Response: {result}"
                    )

                logger.info(f"PiAPI Luma video generation started: {task_id}")

                return {
                    "id": task_id,
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

        Script is already in flowing narrative format (from prompt builder)
        """
        # Script is already in flowing narrative format, no conversion needed
        narrative_prompt = self._convert_script_to_narrative(script)

        style_prompts = {
            "marketing": "Create a professional, engaging marketing video with smooth transitions and clear visuals that drive action.",
            "educational": "Create a clear, informative educational video with clean visuals and easy-to-read text overlays.",
            "social": "Create a dynamic, eye-catching social media video optimized for mobile viewing with bold visuals."
        }

        base_prompt = style_prompts.get(style, style_prompts["marketing"])
        duration_context = f"The video should be approximately {duration} seconds long with a clear beginning, middle, and end."

        return f"{base_prompt} {duration_context}\n\n{narrative_prompt}"

    def _convert_script_to_narrative(self, script: str) -> str:
        """
        Convert production script format to flowing narrative for AI video platforms

        Input:  [0s] [VISUAL: product shot] [VOICEOVER: text here]
                [2s] [TRANSITION: zoom] [VISUAL: close-up] [VOICEOVER: more text]

        Output: A professional marketing video opens with product shot, then transitions
                with zoom to close-up, showing text here and more text...
        """
        import re

        # Check if script contains production format markers
        if not re.search(r'\[(TIMESTAMP|VISUAL|VOICEOVER|TRANSITION):', script, re.IGNORECASE):
            # Not in production format, return as-is
            return script

        # Extract all segments
        segments = re.findall(r'\[([^\]]+)\]', script)

        visual_elements = []
        voiceover_elements = []
        transitions = []

        # Parse segments
        i = 0
        while i < len(segments):
            segment = segments[i].strip()
            if ':' in segment:
                key, value = segment.split(':', 1)
                key = key.strip().upper()
                value = value.strip()

                if key == 'VISUAL':
                    visual_elements.append(value)
                elif key == 'VOICEOVER':
                    voiceover_elements.append(value)
                elif key == 'TRANSITION':
                    transitions.append(value)
            i += 1

        # Build flowing narrative
        narrative_parts = []

        if visual_elements:
            # Start with the first visual
            narrative_parts.append(f"A professional marketing video opens with {visual_elements[0]}")

            # Add subsequent visuals with transitions
            for i, visual in enumerate(visual_elements[1:], 1):
                if i <= len(transitions):
                    transition = transitions[i-1] if i-1 < len(transitions) else "smooth transition"
                    narrative_parts.append(f"Scene transitions with {transition} to show {visual}")
                else:
                    narrative_parts.append(f"Visual shows {visual}")

        # Add voiceover as flowing text
        if voiceover_elements:
            voiceover_text = " ".join(voiceover_elements)
            narrative_parts.append(f"The narrative emphasizes {voiceover_text}")

        if not narrative_parts:
            return script

        return ". ".join(narrative_parts) + "."

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

                # Extract output data if available (before checking status)
                output = data.get("output", {})
                video_url = None
                thumbnail_url = None

                # Check different possible output structures
                if isinstance(output, dict):
                    # Try common video URL fields (check nested objects first)
                    video_data = output.get("video")
                    if isinstance(video_data, dict):
                        video_url = video_data.get("url")
                    else:
                        video_url = output.get("video_url") or output.get("video")

                    # Try thumbnail URL (check nested objects first)
                    thumbnail_data = output.get("thumbnail")
                    if isinstance(thumbnail_data, dict):
                        thumbnail_url = thumbnail_data.get("url")
                    else:
                        thumbnail_url = output.get("thumbnail_url") or output.get("thumbnail")

                # Map PiAPI status to our status format (match PiAPI's capitalization)
                status_mapping = {
                    "Pending": "processing",
                    "Processing": "processing",
                    "Completed": "completed",
                    "Success": "completed",  # PiAPI returns "Success"
                    "Failed": "failed",
                    "Staged": "processing"
                }
                mapped_status = status_mapping.get(status, "unknown")

                # Workaround: if video URL exists, video is complete
                if mapped_status in ["processing", "unknown"] and video_url:
                    logger.info(f"Luma video shows '{mapped_status}' but video URL exists. Marking as completed.")
                    mapped_status = "completed"

                    # Also check files array as fallback
                    if not video_url:
                        video_url = (output.get("files", [{}])[0].get("url") if output.get("files") else None)
                    if not thumbnail_url:
                        thumbnail_url = (output.get("images", [{}])[0].get("url") if output.get("images") else None)

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


class HunyuanVideoService:
    """Service for generating videos using Hunyuan Video via PiAPI"""

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
        motion_intensity: str = "medium",
        model_variant: str = "standard"
    ) -> Dict[str, Any]:
        """
        Generate video using Hunyuan Video via PiAPI

        Args:
            generation_mode: text_to_video, image_to_video, or slide_video
            script: Video script with timestamps (required for text_to_video and slide_video)
            style: marketing, educational, or social
            duration: Video duration in seconds
            aspect_ratio: 16:9, 9:16, or 1:1
            image_url: URL of source image (required for image_to_video)
            slides: List of slides with text/images (for slide_video)
            motion_intensity: low, medium, or high
            model_variant: 'standard' (only variant available)

        Returns:
            Dict with generation details
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Prepare the input parameters
            # Hunyuan uses standard /api/v1/task endpoint
            input_params = {
                "prompt": self._prepare_prompt(script, style, duration),
                "aspect_ratio": aspect_ratio,
                "duration": duration  # Add duration parameter
            }

            # Determine task type
            task_type = "txt2video"
            if generation_mode == "image_to_video" and image_url:
                task_type = "img2video-concat"
                input_params["image"] = image_url

            request_data = {
                "model": "Qubico/hunyuan",
                "task_type": task_type,
                "input": input_params
            }

            logger.info(f"Generating video with Hunyuan: {input_params['prompt'][:100]}...")

            response = await client.post(
                f"{self.base_url}/api/v1/task",
                headers=self.headers,
                json=request_data
            )

            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("message", error_detail)
                except:
                    pass
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Hunyuan video generation failed: {error_detail}"
                )

            result = response.json()
            task_id = result.get("data", {}).get("task_id")

            if not task_id:
                logger.error(f"No task ID in Hunyuan response. Full response: {result}")
                raise HTTPException(
                    status_code=500,
                    detail="No task ID returned from Hunyuan video generation"
                )

            logger.info(f"Hunyuan video generation started: {task_id}")

            return {
                "id": task_id,
                "status": "processing",
                "actual_duration": 5  # Hunyuan generates 5-second videos
            }

    def _prepare_prompt(self, script: Optional[str], style: str, duration: int) -> str:
        """Prepare prompt for Hunyuan video generation"""
        if not script:
            script = f"Create a {style} video"

        style_prompts = {
            "marketing": "Professional, engaging marketing video with smooth transitions",
            "educational": "Clear, informative educational video with clean visuals",
            "social": "Dynamic, eye-catching social media video optimized for mobile"
        }

        base_prompt = style_prompts.get(style, style_prompts["marketing"])
        return f"{base_prompt}. Duration: {duration}s. Script: {script}"

    async def get_generation_status(self, generation_id: str) -> Dict[str, Any]:
        """
        Check the status of a Hunyuan video generation
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
                        detail=f"Failed to get Hunyuan status: {response.text}"
                    )

                result = response.json()
                data = result.get("data", {})
                status = data.get("status", "unknown")

                # Extract video URLs first (before checking status)
                output = data.get("output", {})
                video_url = None
                thumbnail_url = None

                if isinstance(output, dict):
                    # Try nested object structure first (output["video"]["url"])
                    video_data = output.get("video")
                    if isinstance(video_data, dict):
                        video_url = video_data.get("url")
                    else:
                        video_url = output.get("video_url")

                    # Try thumbnail
                    thumbnail_data = output.get("thumbnail")
                    if isinstance(thumbnail_data, dict):
                        thumbnail_url = thumbnail_data.get("url")
                    else:
                        thumbnail_url = output.get("thumbnail_url")

                # Map Hunyuan status to our format (match API's capitalization)
                status_mapping = {
                    "Pending": "processing",
                    "Processing": "processing",
                    "Completed": "completed",
                    "Success": "completed",
                    "Failed": "failed"
                }
                mapped_status = status_mapping.get(status, "unknown")

                # Workaround for Hunyuan API bug: if video URL exists, video is complete
                if mapped_status == "processing" and video_url:
                    logger.info(f"Hunyuan API shows 'processing' but video URL exists. Marking as completed.")
                    mapped_status = "completed"

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
                    detail=f"Failed to connect to PiAPI Hunyuan: {str(e)}"
                )


class WanxVideoService:
    """Service for generating videos using WanX via PiAPI"""

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
        motion_intensity: str = "medium",
        model_variant: str = "1.3b"
    ) -> Dict[str, Any]:
        """
        Generate video using WanX via PiAPI

        Args:
            generation_mode: text_to_video, image_to_video, or slide_video
            script: Video script with timestamps (required for text_to_video and slide_video)
            style: marketing, educational, or social
            duration: Video duration in seconds (5 or 60)
            aspect_ratio: 16:9 or 9:16 (WanX limitation)
            image_url: URL of source image (required for image_to_video)
            slides: List of slides with text/images (for slide_video)
            motion_intensity: low, medium, or high
            model_variant: '1.3b' or '14b'

        Returns:
            Dict with generation details
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Validate aspect ratio (WanX only supports 16:9 and 9:16)
            if aspect_ratio not in ["16:9", "9:16"]:
                # Default to 16:9 if invalid
                aspect_ratio = "16:9"

            # Select task type based on variant
            task_type = f"txt2video-{model_variant}"

            # Determine actual duration
            # WanX generates fixed duration: 5s for all models
            actual_duration = 5

            # Prepare the input parameters
            input_params = {
                "prompt": self._prepare_prompt(script, style, actual_duration),
                "aspect_ratio": aspect_ratio
            }

            # Add mode-specific parameters
            if generation_mode == "image_to_video" and image_url:
                # WanX only supports img2video with 14b models
                if model_variant == "1.3b":
                    # No img2video support for 1.3b, fallback to 14b
                    task_type = "img2video-14b"
                else:
                    task_type = f"img2video-{model_variant}"
                input_params["image"] = image_url

            request_data = {
                "model": "Qubico/wanx",
                "task_type": task_type,
                "input": input_params
            }

            logger.info(f"Generating video with WanX ({model_variant}): {input_params['prompt'][:100]}...")

            response = await client.post(
                f"{self.base_url}/api/v1/task",
                headers=self.headers,
                json=request_data
            )

            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("message", error_detail)
                except:
                    pass
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"WanX video generation failed: {error_detail}"
                )

            result = response.json()
            task_id = result.get("data", {}).get("task_id")

            if not task_id:
                raise HTTPException(
                    status_code=500,
                    detail="No task ID returned from WanX video generation"
                )

            logger.info(f"WanX video generation started: {task_id}")

            return {
                "id": task_id,
                "status": "processing",
                "actual_duration": actual_duration
            }

    def _prepare_prompt(self, script: Optional[str], style: str, duration: int) -> str:
        """Prepare prompt for WanX video generation"""
        if not script:
            script = f"Create a {style} video"

        style_prompts = {
            "marketing": "Professional, engaging marketing video with smooth transitions and high production value",
            "educational": "Clear, informative educational video with clean visuals and easy-to-read text",
            "social": "Dynamic, eye-catching social media video optimized for mobile with bold visuals"
        }

        base_prompt = style_prompts.get(style, style_prompts["marketing"])
        duration_note = "5-second clip" if duration == 5 else "1-minute video"
        return f"{base_prompt}. {duration_note}. Script: {script}"

    async def get_generation_status(self, generation_id: str) -> Dict[str, Any]:
        """
        Check the status of a WanX video generation
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
                        detail=f"Failed to get WanX status: {response.text}"
                    )

                result = response.json()
                data = result.get("data", {})
                status = data.get("status", "unknown")

                # Map WanX status to our format
                status_mapping = {
                    "pending": "processing",
                    "processing": "processing",
                    "completed": "completed",
                    "failed": "failed"
                }
                mapped_status = status_mapping.get(status.lower(), "unknown")

                # Extract video URLs
                output = data.get("output", {})
                video_url = None
                thumbnail_url = None

                if isinstance(output, dict):
                    if "video_url" in output:
                        video_url = output.get("video_url")
                    # WanX may not provide thumbnail separately

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
                    detail=f"Failed to connect to PiAPI WanX: {str(e)}"
                )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(
    request: VideoGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    user_id = current_user.id
    user_tier = "starter"  # TODO: Get from user profile

    # Validate request parameters
    if request.generation_mode == "text_to_video" and not request.script:
        raise HTTPException(
            status_code=422,
            detail="Script is required for text_to_video mode"
        )

    if request.generation_mode == "image_to_video" and not request.image_url:
        raise HTTPException(
            status_code=422,
            detail="Image URL is required for image_to_video mode"
        )

    # TODO: Check if user has reached video generation limit
    # If user has reached limit, return 429

    # Validate API key
    video_service = LumaVideoService()
    hunyuan_service = HunyuanVideoService()
    wanx_service = WanxVideoService()

    if not video_service.api_key:
        raise HTTPException(
            status_code=503,
            detail="Video generation service not configured"
        )

    try:
        # Convert campaign_id to int, handling both string and int inputs
        campaign_id_int = None
        if request.campaign_id:
            try:
                campaign_id_int = int(request.campaign_id)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid campaign_id: {request.campaign_id}. Must be a number."
                )

        # Check tier and select provider based on duration
        selected_provider = select_video_provider(
            duration=request.duration,
            user_tier=user_tier,
            forced_provider=request.provider
        )
        logger.info(f"Selected provider for duration {request.duration}s: {selected_provider}")

        # Route to appropriate service
        if selected_provider == "piapi_luma":
            # Use PiAPI with Luma AI (5s)
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

            # Use actual_duration from the result (5s for ray-v1)
            actual_duration = generation_result.get("actual_duration", 5)

            # Save to database
            video_gen = await save_video_generation_to_db(
                user_id=user_id,
                campaign_id=campaign_id_int,
                task_id=generation_result["id"],
                provider=selected_provider,
                model_name="ray-v1",
                request=request,
                actual_duration=actual_duration,
                db=db
            )

            # Start background task to poll PiAPI for status
            logger.info(f"Adding background task for video {video_gen.id}")
            background_tasks.add_task(
                update_video_status,
                video_id=video_gen.id,
                db=db,
                video_service=video_service
            )
            logger.info(f"Background task added for video {video_gen.id}")

        elif selected_provider == "piapi_hunyuan_fast":
            # Use Hunyuan Fast (cheapest, 5s)
            generation_result = await hunyuan_service.generate_video(
                generation_mode=request.generation_mode,
                script=request.script,
                style=request.style,
                duration=request.duration,
                aspect_ratio=request.aspect_ratio,
                image_url=request.image_url,
                slides=request.slides,
                motion_intensity=request.motion_intensity,
                model_variant="fast"
            )

            actual_duration = generation_result.get("actual_duration", 5)

            # Save to database
            video_gen = await save_video_generation_to_db(
                user_id=user_id,
                campaign_id=campaign_id_int,
                task_id=generation_result["id"],
                provider=selected_provider,
                model_name="hunyuan-fast",
                request=request,
                actual_duration=actual_duration,
                db=db
            )

            # Start background task to poll for status
            logger.info(f"Adding Hunyuan background task for video {video_gen.id}")
            background_tasks.add_task(
                update_video_status_hunyuan,
                video_id=video_gen.id,
                db=db,
                video_service=hunyuan_service
            )
            logger.info(f"Hunyuan background task added for video {video_gen.id}")

        elif selected_provider == "piapi_hunyuan_standard":
            # Use Hunyuan Standard (higher quality, 5s)
            generation_result = await hunyuan_service.generate_video(
                generation_mode=request.generation_mode,
                script=request.script,
                style=request.style,
                duration=request.duration,
                aspect_ratio=request.aspect_ratio,
                image_url=request.image_url,
                slides=request.slides,
                motion_intensity=request.motion_intensity,
                model_variant="standard"
            )

            actual_duration = generation_result.get("actual_duration", 5)

            # Save to database
            video_gen = await save_video_generation_to_db(
                user_id=user_id,
                campaign_id=campaign_id_int,
                task_id=generation_result["id"],
                provider=selected_provider,
                model_name="hunyuan-standard",
                request=request,
                actual_duration=actual_duration,
                db=db
            )

            # Start background task to poll for status
            logger.info(f"Adding Hunyuan background task for video {video_gen.id}")
            background_tasks.add_task(
                update_video_status_hunyuan,
                video_id=video_gen.id,
                db=db,
                video_service=hunyuan_service
            )
            logger.info(f"Hunyuan background task added for video {video_gen.id}")

        elif selected_provider == "piapi_wanx_1.3b":
            # Use WanX 1.3B (5s or 60s)
            generation_result = await wanx_service.generate_video(
                generation_mode=request.generation_mode,
                script=request.script,
                style=request.style,
                duration=request.duration,
                aspect_ratio=request.aspect_ratio,
                image_url=request.image_url,
                slides=request.slides,
                motion_intensity=request.motion_intensity,
                model_variant="1.3b"
            )

            actual_duration = generation_result.get("actual_duration", 5)

            # Save to database
            video_gen = await save_video_generation_to_db(
                user_id=user_id,
                campaign_id=campaign_id_int,
                task_id=generation_result["id"],
                provider=selected_provider,
                model_name="wanx-1.3b",
                request=request,
                actual_duration=actual_duration,
                db=db
            )

            # Start background task to poll for status
            background_tasks.add_task(
                update_video_status_wanx,
                video_id=video_gen.id,
                db=db,
                video_service=wanx_service
            )

        elif selected_provider == "piapi_wanx_14b":
            # Use WanX 14B (premium quality, 5s or 60s)
            generation_result = await wanx_service.generate_video(
                generation_mode=request.generation_mode,
                script=request.script,
                style=request.style,
                duration=request.duration,
                aspect_ratio=request.aspect_ratio,
                image_url=request.image_url,
                slides=request.slides,
                motion_intensity=request.motion_intensity,
                model_variant="14b"
            )

            actual_duration = generation_result.get("actual_duration", 5)

            # Save to database
            video_gen = await save_video_generation_to_db(
                user_id=user_id,
                campaign_id=campaign_id_int,
                task_id=generation_result["id"],
                provider=selected_provider,
                model_name="wanx-14b",
                request=request,
                actual_duration=actual_duration,
                db=db
            )

            # Start background task to poll for status
            background_tasks.add_task(
                update_video_status_wanx,
                video_id=video_gen.id,
                db=db,
                video_service=wanx_service
            )

        elif selected_provider == "replicate_veo":
            # TODO: Implement Replicate Veo integration
            # For now, return error
            raise HTTPException(
                status_code=501,
                detail={
                    "error": "PROVIDER_NOT_IMPLEMENTED",
                    "message": f"{selected_provider} provider not yet implemented. Available providers: Hunyuan (Fast/Standard), WanX (1.3B/14B), PiAPI Luma",
                    "available_providers": ["piapi_hunyuan_fast", "piapi_hunyuan_standard", "piapi_wanx_1.3b", "piapi_wanx_14b", "piapi_luma"]
                }
            )

        # Create response
        response = VideoGenerateResponse(
            video_id=generation_result.get("id", str(uuid.uuid4())),
            status="processing",
            duration=actual_duration,
            cost=round(actual_duration * 0.05, 2),
            created_at=datetime.utcnow()
        )

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

@router.post("/save-to-library", response_model=VideoSaveResponse, status_code=201)
async def save_video_to_library(
    request: VideoSaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Save a generated video to R2 storage by downloading from provider URL
    """
    user_id = current_user.id

    try:
        # Get video from database
        result = await db.execute(
            text("SELECT id, task_id, provider, model_name, video_url, video_raw_url, thumbnail_url, campaign_id, saved_to_r2, r2_key FROM video_generations WHERE id = :id AND user_id = :user_id"),
            {"id": request.video_id, "user_id": user_id}
        )
        video_record = result.fetchone()

        if not video_record:
            raise HTTPException(
                status_code=404,
                detail="Video not found"
            )

        video_id, task_id, provider, model_name, video_url, video_raw_url, thumbnail_url, campaign_id, saved_to_r2, r2_key = video_record

        # Check if already saved
        if saved_to_r2 and r2_key:
            logger.info(f"Video {video_id} already saved to R2 with key: {r2_key}")
            return VideoSaveResponse(
                video_id=video_id,
                r2_key=r2_key,
                video_url=video_url,
                thumbnail_url=thumbnail_url,
                saved_at=datetime.utcnow()
            )

        # If video_url is missing from database, re-check status with provider
        if not video_url:
            logger.info(f"Video URL not in database, re-checking status for task {task_id}...")

            # Determine which service to use based on provider
            if provider == "piapi_hunyuan_fast" or provider == "piapi_hunyuan":
                video_service = HunyuanVideoService()
            elif provider == "piapi_wanx":
                video_service = WanxVideoService()
            else:
                # Default to Hunyuan for backward compatibility
                video_service = HunyuanVideoService()

            # Get fresh status from provider
            status_result = await video_service.get_generation_status(task_id)

            # Update database with fresh status and URLs
            update_data = {
                "status": status_result.get("status"),
                "progress": status_result.get("progress", 0),
                "video_url": status_result.get("video_url"),
                "thumbnail_url": status_result.get("thumbnail_url")
            }

            if status_result.get("status") == "completed":
                update_data["completed_at"] = datetime.utcnow()

            # Update database
            await db.execute(
                text("""
                    UPDATE video_generations
                    SET status = :status, progress = :progress, video_url = :video_url,
                        thumbnail_url = :thumbnail_url,
                        completed_at = COALESCE(completed_at, :completed_at)
                    WHERE id = :id
                """),
                {
                    "id": video_id,
                    "status": update_data["status"],
                    "progress": update_data["progress"],
                    "video_url": update_data["video_url"],
                    "thumbnail_url": update_data["thumbnail_url"],
                    "completed_at": update_data.get("completed_at")
                }
            )
            await db.commit()

            # Refresh video_url from updated database
            video_url = update_data["video_url"]
            thumbnail_url = update_data["thumbnail_url"]

            logger.info(f"Updated video {video_id} with URL from provider")

        # Validate video URL exists after update
        if not video_url:
            raise HTTPException(
                status_code=400,
                detail="Video URL not available. Video may still be processing."
            )

        # Download video from provider URL
        logger.info(f"Downloading video {video_id} from {video_url[:100]}...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(video_url)
            response.raise_for_status()
            video_data = response.content
            logger.info(f"Downloaded {len(video_data)} bytes")

        # Generate R2 key
        campaign_id_str = campaign_id or "0"
        unique_id = str(uuid.uuid4())
        r2_key = f"campaigns/{campaign_id_str}/videos/{unique_id}.mp4"

        # Upload to R2
        logger.info(f"Uploading to R2 with key: {r2_key}")
        r2_key_result, r2_url = await r2_storage.upload_file(
            file_bytes=video_data,
            key=r2_key,
            content_type="video/mp4"
        )

        # Update database
        await db.execute(
            text("UPDATE video_generations SET video_url = :video_url, video_raw_url = :video_raw_url, saved_to_r2 = TRUE, r2_key = :r2_key WHERE id = :id"),
            {
                "id": video_id,
                "video_url": r2_url,
                "video_raw_url": r2_url,
                "r2_key": r2_key
            }
        )
        await db.commit()

        logger.info(f"✅ Video {video_id} saved to R2: {r2_url}")

        return VideoSaveResponse(
            video_id=video_id,
            r2_key=r2_key,
            video_url=r2_url,
            thumbnail_url=thumbnail_url,
            saved_at=datetime.utcnow()
        )

    except httpx.HTTPError as e:
        logger.error(f"HTTP error downloading video: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download video from provider: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error saving video to library: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save video to library: {str(e)}"
        )


@router.delete("/{video_id}", status_code=204)
async def delete_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a video from R2 storage and database
    """
    user_id = current_user.id

    try:
        # Get video from database
        result = await db.execute(
            text("SELECT id, r2_key, saved_to_r2 FROM video_generations WHERE id = :id AND user_id = :user_id"),
            {"id": video_id, "user_id": user_id}
        )
        video_record = result.fetchone()

        if not video_record:
            raise HTTPException(
                status_code=404,
                detail="Video not found"
            )

        video_id_db, r2_key, saved_to_r2 = video_record

        # Delete from R2 if saved there
        if saved_to_r2 and r2_key:
            logger.info(f"Deleting video from R2: {r2_key}")
            try:
                from app.utils.r2_storage import r2_storage
                await r2_storage.delete_file(r2_key)
                logger.info(f"✅ Deleted video from R2: {r2_key}")
            except Exception as e:
                logger.error(f"Failed to delete from R2: {e}")
                # Continue with database deletion even if R2 deletion fails

        # Delete from database
        await db.execute(
            text("DELETE FROM video_generations WHERE id = :id AND user_id = :user_id"),
            {"id": video_id, "user_id": user_id}
        )
        await db.commit()

        logger.info(f"✅ Deleted video {video_id} from database")

        return

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting video: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete video: {str(e)}"
        )


@router.get("/library", response_model=Dict[str, Any])
async def get_video_library(
    page: int = 1,
    per_page: int = 20,
    campaign_id: Optional[int] = None,
    video_type: Optional[str] = Query(None, description="Filter by type: 'generated' or 'overlays'"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's generated videos, optionally filtered by campaign and type

    Args:
        page: Page number (default: 1)
        per_page: Videos per page (default: 20)
        campaign_id: Optional campaign ID to filter videos
        video_type: Optional filter - 'generated' (AI videos) or 'overlays' (edited videos)

    Returns:
        Paginated list of generated videos
    """
    user_id = current_user.id
    logger.info(f"get_video_library - current_user.id: {current_user.id}, current_user.email: {current_user.email}")

    # Calculate offset for pagination
    offset = (page - 1) * per_page

    # Build query conditions
    where_conditions = ["user_id = :user_id"]
    query_params = {
        "user_id": user_id,
        "limit": per_page,
        "offset": offset
    }

    # Add campaign filter if provided
    if campaign_id:
        where_conditions.append("campaign_id = :campaign_id")
        query_params["campaign_id"] = campaign_id

    # Add video type filter
    if video_type:
        if video_type == "generated":
            # Show AI-generated videos (not overlays)
            where_conditions.append("generation_mode != 'text_overlay'")
        elif video_type == "overlays":
            # Show only overlay videos
            where_conditions.append("generation_mode = 'text_overlay'")

    # Query database for user's videos
    result = await db.execute(
        text(f"""
            SELECT id, task_id, provider, model_name, generation_mode, prompt, script,
                   style, aspect_ratio, requested_duration, actual_duration, video_url,
                   video_raw_url, thumbnail_url, last_frame_url, video_width, video_height,
                   status, progress, cost, created_at, started_at, completed_at, error_message,
                   saved_to_r2, r2_key, campaign_id
            FROM video_generations
            WHERE {" AND ".join(where_conditions)}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        query_params
    )
    videos = result.fetchall()

    # Log what we found
    logger.info(f"Found {len(videos)} videos for user_id {user_id}")
    for v in videos[:5]:  # Log first 5 videos
        logger.info(f"  Video ID {v[0]}: generation_mode={v[4]}, status={v[17]}, campaign_id={v[25]}")

    # Get total count
    count_query = "SELECT COUNT(*) FROM video_generations WHERE " + " AND ".join(where_conditions)
    count_result = await db.execute(text(count_query), query_params)
    total = count_result.fetchone()[0]

    # Start background tasks for any stuck videos (processing/unknown) that need polling
    stuck_videos_query = "SELECT id, task_id, provider FROM video_generations WHERE " + " AND ".join(where_conditions) + " AND status IN ('processing', 'unknown')"
    stuck_result = await db.execute(text(stuck_videos_query), query_params)
    stuck_videos = stuck_result.fetchall()

    # Start background polling for stuck videos (don't wait for completion)
    for stuck_video in stuck_videos:
        video_id = stuck_video[0]
        task_id = stuck_video[1]
        provider = stuck_video[2]

        logger.info(f"Starting polling for stuck video {video_id} (status will be updated in background)")

        # Start appropriate polling task based on provider
        # Each task gets its own database session
        async def start_polling_with_new_session():
            async with AsyncSessionLocal() as task_db:
                try:
                    if provider == "piapi_luma":
                        luma_service = LumaVideoService()
                        await update_video_status(video_id=video_id, db=task_db, video_service=luma_service)
                    elif "hunyuan" in provider:
                        hunyuan_service = HunyuanVideoService()
                        await update_video_status_hunyuan(video_id=video_id, db=task_db, video_service=hunyuan_service)
                    elif "wanx" in provider:
                        wanx_service = WanxVideoService()
                        await update_video_status_wanx(video_id=video_id, db=task_db, video_service=wanx_service)
                finally:
                    await task_db.close()

        # Run polling task in background
        asyncio.create_task(start_polling_with_new_session())

    # Format videos for response
    formatted_videos = []
    for video in videos:
        formatted_videos.append({
            "id": video[0],
            "task_id": video[1],
            "provider": video[2],
            "model_name": video[3],
            "generation_mode": video[4],
            "prompt": video[5],
            "script": video[6],
            "style": video[7],
            "aspect_ratio": video[8],
            "requested_duration": video[9],
            "actual_duration": video[10],
            "video_url": video[11],
            "video_raw_url": video[12],
            "thumbnail_url": video[13],
            "last_frame_url": video[14],
            "video_width": video[15],
            "video_height": video[16],
            "status": video[17],
            "progress": video[18],
            "cost": video[19],
            "created_at": video[20].isoformat() if video[20] else None,
            "started_at": video[21].isoformat() if video[21] else None,
            "completed_at": video[22].isoformat() if video[22] else None,
            "error_message": video[23],
            "saved_to_r2": video[24],
            "r2_key": video[25],
            "campaign_id": video[26]
        })

    return {
        "videos": formatted_videos,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def save_video_generation_to_db(
    user_id: int,
    campaign_id: int | None,
    task_id: str,
    provider: str,
    model_name: str,
    request: VideoGenerateRequest,
    actual_duration: int,
    db: AsyncSession
) -> VideoGeneration:
    """
    Save video generation record to database
    """
    logger.info(f"Saving video generation - task_id: {task_id}, user_id: {user_id}, provider: {provider}")

    video_gen = VideoGeneration(
        user_id=user_id,
        campaign_id=campaign_id,
        task_id=task_id,
        provider=provider,
        model_name=model_name,
        generation_mode=request.generation_mode,
        prompt=request.script,  # Use script as prompt
        script=request.script,
        style=request.style,
        aspect_ratio=request.aspect_ratio,
        requested_duration=request.duration,
        actual_duration=actual_duration,
        status="processing",
        progress=0,
        cost=round(actual_duration * 0.05, 2),
        created_at=datetime.utcnow()
    )

    db.add(video_gen)
    await db.commit()
    await db.refresh(video_gen)

    logger.info(f"Video generation saved - ID: {video_gen.id}, task_id: {task_id}")

    return video_gen


async def update_video_status(
    video_id: int,
    db: AsyncSession,
    video_service: LumaVideoService
):
    """
    Background task to poll PiAPI for video status and update database
    Polls every 5 seconds until video is complete or failed
    """
    import asyncio

    try:
        # Get video from database
        result = await db.execute(
            text("SELECT task_id FROM video_generations WHERE id = :id"),
            {"id": video_id}
        )
        video_record = result.fetchone()

        if not video_record:
            logger.error(f"Video record not found: {video_id}")
            return

        task_id = video_record[0]
        logger.info(f"Starting status polling for video {video_id}, task {task_id}")
        logger.info(f"Background task started - video_id: {video_id}, task_id: {task_id}")

        # Poll PiAPI for status (with retry logic)
        max_attempts = 60  # Poll for up to 5 minutes
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            logger.info(f"Polling attempt {attempt}/{max_attempts} for video {video_id}")

            status_result = await video_service.get_generation_status(task_id)

            # Map status to our format (match PiAPI's capitalization)
            status_mapping = {
                "Pending": "processing",
                "Processing": "processing",
                "Completed": "completed",
                "Success": "completed",  # PiAPI returns "Success"
                "Failed": "failed"
            }
            mapped_status = status_mapping.get(status_result.get("status", "unknown"), "unknown")

            # Workaround: if video URL exists, video is complete
            if mapped_status in ["processing", "unknown"] and status_result.get("video_url"):
                logger.info(f"Luma video {video_id} shows '{mapped_status}' but video URL exists. Marking as completed.")
                mapped_status = "completed"

            logger.info(f"Video {video_id} status: {mapped_status}")

            # Update database with current status
            update_data = {
                "status": mapped_status,
                "progress": status_result.get("progress", 0),
            }

            # If completed, add video URLs and metadata
            if mapped_status == "completed":
                update_data.update({
                    "video_url": status_result.get("video_url"),
                    "video_raw_url": status_result.get("video_raw_url"),
                    "thumbnail_url": status_result.get("thumbnail_url"),
                    "completed_at": datetime.utcnow()
                })

            # If failed, add error info
            if mapped_status == "failed":
                update_data.update({
                    "error_message": status_result.get("error"),
                    "error_code": "GENERATION_FAILED"
                })

            # Build dynamic UPDATE query based on available fields
            set_clauses = []
            params = {"id": video_id}

            for field, value in update_data.items():
                set_clauses.append(f"{field} = :{field}")
                params[field] = value

            # Always include id in params
            set_clauses.append("id = :id")

            # Execute update with only the fields that have values
            update_sql = f"UPDATE video_generations SET {', '.join(set_clauses)} WHERE id = :id"
            await db.execute(text(update_sql), params)
            await db.commit()

            logger.info(f"Updated video {video_id} status to {mapped_status}")

            # If video is complete or failed, stop polling
            if mapped_status in ["completed", "failed"]:
                logger.info(f"Video {video_id} polling complete: {mapped_status}. Final video_url: {update_data.get('video_url', 'NONE')}")
                break

            # Wait 5 seconds before next poll
            await asyncio.sleep(5)

        if attempt >= max_attempts:
            logger.warning(f"Video {video_id} polling timeout after {max_attempts} attempts")

    except Exception as e:
        logger.error(f"Error updating video status: {str(e)}")
        await db.rollback()


async def update_video_status_hunyuan(
    video_id: int,
    db: AsyncSession,
    video_service: HunyuanVideoService
):
    """
    Background task to poll Hunyuan for video status and update database
    Polls every 5 seconds until video is complete or failed
    """
    import asyncio

    try:
        # Get video from database
        result = await db.execute(
            text("SELECT task_id, prompt, cost FROM video_generations WHERE id = :id"),
            {"id": video_id}
        )
        video_record = result.fetchone()

        if not video_record:
            logger.error(f"Video record not found: {video_id}")
            return

        task_id = video_record[0]
        logger.info(f"Starting Hunyuan status polling for video {video_id}, task {task_id}")

        # Poll Hunyuan for status (with retry logic)
        max_attempts = 60  # Poll for up to 5 minutes
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            logger.info(f"Hunyuan polling attempt {attempt}/{max_attempts} for video {video_id}")

            status_result = await video_service.get_generation_status(task_id)

            # Map status to our format (match API's capitalization)
            status_mapping = {
                "Pending": "processing",
                "Processing": "processing",
                "Completed": "completed",
                "Success": "completed",
                "Failed": "failed"
            }
            mapped_status = status_mapping.get(status_result.get("status", "unknown"), "unknown")

            # Workaround for Hunyuan API bug: if video URL exists, video is complete
            if mapped_status == "processing" and status_result.get("video_url"):
                logger.info(f"Hunyuan video {video_id} shows 'processing' but video URL exists. Marking as completed.")
                mapped_status = "completed"

            logger.info(f"Hunyuan video {video_id} status: {mapped_status}")

            # Update database
            update_data = {
                "status": mapped_status,
                "progress": status_result.get("progress", 0),
            }

            # If completed, add video URLs and metadata
            if mapped_status == "completed":
                video_url = status_result.get("video_url")
                thumbnail_url = status_result.get("thumbnail_url")

                # Extend video if needed (Hunyuan always generates 5s)
                # We need to check the requested duration from the prompt
                try:
                    # Extract duration from prompt metadata
                    import json
                    prompt_data = json.loads(video_record[1]) if video_record[1] else {}
                    requested_duration = prompt_data.get("duration", 5)
                    actual_duration = 5  # Hunyuan always generates 5s

                    # Extend video if actual < requested
                    if requested_duration > actual_duration and video_url:
                        logger.info(f"Extending video {video_id} from {actual_duration}s to {requested_duration}s")
                        extended_url = await video_extension_service.extend_video_duration(
                            video_url=video_url,
                            requested_duration=requested_duration,
                            actual_duration=actual_duration,
                            campaign_id=1  # Get from database if needed
                        )
                        if extended_url:
                            video_url = extended_url
                            logger.info(f"Successfully extended video {video_id}")
                except Exception as e:
                    logger.warning(f"Could not extend video {video_id}: {str(e)}")
                    # Continue with original URL

                update_data.update({
                    "video_url": video_url,
                    "thumbnail_url": thumbnail_url,
                    "completed_at": datetime.utcnow()
                })

            # If failed, add error info
            if mapped_status == "failed":
                update_data.update({
                    "error_message": status_result.get("error"),
                    "error_code": "GENERATION_FAILED"
                })

            # Build dynamic UPDATE query based on available fields
            set_clauses = []
            params = {"id": video_id}

            for field, value in update_data.items():
                set_clauses.append(f"{field} = :{field}")
                params[field] = value

            # Execute update with only the fields that have values
            update_sql = f"UPDATE video_generations SET {', '.join(set_clauses)} WHERE id = :id"
            await db.execute(text(update_sql), params)
            await db.commit()

            logger.info(f"Updated Hunyuan video {video_id} status to {mapped_status}")

            # If video is complete or failed, stop polling
            if mapped_status in ["completed", "failed"]:
                logger.info(f"Hunyuan video {video_id} polling complete: {mapped_status}")
                break

            # Wait 5 seconds before next poll
            await asyncio.sleep(5)

        if attempt >= max_attempts:
            logger.warning(f"Hunyuan video {video_id} polling timeout after {max_attempts} attempts")

    except Exception as e:
        logger.error(f"Error updating Hunyuan video status: {str(e)}")
        await db.rollback()


async def update_video_status_wanx(
    video_id: int,
    db: AsyncSession,
    video_service: WanxVideoService
):
    """
    Background task to poll WanX for video status and update database
    Polls every 5 seconds until video is complete or failed
    """
    import asyncio

    try:
        # Get video from database
        result = await db.execute(
            text("SELECT task_id FROM video_generations WHERE id = :id"),
            {"id": video_id}
        )
        video_record = result.fetchone()

        if not video_record:
            logger.error(f"Video record not found: {video_id}")
            return

        task_id = video_record[0]
        logger.info(f"Starting WanX status polling for video {video_id}, task {task_id}")

        # Poll WanX for status (with retry logic)
        max_attempts = 60  # Poll for up to 5 minutes
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            logger.info(f"WanX polling attempt {attempt}/{max_attempts} for video {video_id}")

            status_result = await video_service.get_generation_status(task_id)

            # Map status to our format
            status_mapping = {
                "pending": "processing",
                "processing": "processing",
                "completed": "completed",
                "failed": "failed"
            }
            mapped_status = status_mapping.get(status_result.get("status", "unknown"), "unknown")

            logger.info(f"WanX video {video_id} status: {mapped_status}")

            # Update database
            update_data = {
                "status": mapped_status,
                "progress": status_result.get("progress", 0),
            }

            # If completed, add video URLs and metadata
            if mapped_status == "completed":
                update_data.update({
                    "video_url": status_result.get("video_url"),
                    "thumbnail_url": status_result.get("thumbnail_url"),
                    "completed_at": datetime.utcnow()
                })

            # If failed, add error info
            if mapped_status == "failed":
                update_data.update({
                    "error_message": status_result.get("error"),
                    "error_code": "GENERATION_FAILED"
                })

            # Build dynamic UPDATE query based on available fields
            set_clauses = []
            params = {"id": video_id}

            for field, value in update_data.items():
                set_clauses.append(f"{field} = :{field}")
                params[field] = value

            # Execute update with only the fields that have values
            update_sql = f"UPDATE video_generations SET {', '.join(set_clauses)} WHERE id = :id"
            await db.execute(text(update_sql), params)
            await db.commit()

            logger.info(f"Updated WanX video {video_id} status to {mapped_status}")

            # If video is complete or failed, stop polling
            if mapped_status in ["completed", "failed"]:
                logger.info(f"WanX video {video_id} polling complete: {mapped_status}")
                break

            # Wait 5 seconds before next poll
            await asyncio.sleep(5)

        if attempt >= max_attempts:
            logger.warning(f"WanX video {video_id} polling timeout after {max_attempts} attempts")

    except Exception as e:
        logger.error(f"Error updating WanX video status: {str(e)}")
        await db.rollback()


# ============================================================================
# VIDEO EXTENSION SERVICE
# ============================================================================

class VideoExtensionService:
    """Service for extending videos to requested duration using ffmpeg"""

    def __init__(self):
        self.temp_dir = tempfile.gettempdir()

    async def extend_video_duration(
        self,
        video_url: str,
        requested_duration: int,
        actual_duration: int,
        campaign_id: int
    ) -> Optional[str]:
        """
        Extend video to requested duration using ffmpeg

        Args:
            video_url: URL of the source video
            requested_duration: Duration user requested
            actual_duration: Actual duration of generated video
            campaign_id: Campaign ID for storage path

        Returns:
            URL of extended video, or None if extension not needed/possible
        """
        # Only extend if actual < requested
        if actual_duration >= requested_duration:
            return None

        try:
            # Download video
            video_path = await self._download_video(video_url)

            # Create extended video
            output_path = await self._extend_video_ffmpeg(
                video_path,
                actual_duration,
                requested_duration
            )

            # Upload to R2
            final_url = await self._upload_to_r2(
                output_path,
                campaign_id,
                requested_duration
            )

            # Cleanup
            self._cleanup_temp_files([video_path, output_path])

            logger.info(f"Extended video from {actual_duration}s to {requested_duration}s")
            return final_url

        except Exception as e:
            logger.error(f"Failed to extend video: {str(e)}")
            # Don't raise - just return original URL
            return None

    async def _download_video(self, video_url: str) -> str:
        """Download video from URL to temp file"""
        import aiohttp
        import aiofiles

        filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
        filepath = os.path.join(self.temp_dir, filename)

        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as response:
                response.raise_for_status()

                async with aiofiles.open(filepath, "wb") as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)

        return filepath

    async def _extend_video_ffmpeg(
        self,
        input_path: str,
        actual_duration: int,
        requested_duration: int
    ) -> str:
        """Extend video using ffmpeg loop filter"""
        import subprocess
        import asyncio

        output_filename = f"extended_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(self.temp_dir, output_filename)

        # Calculate loop count to reach requested duration
        # Loop the video enough times to cover requested duration
        loop_count = int(requested_duration / actual_duration) + 1

        # Use ffmpeg to loop the video
        cmd = [
            "ffmpeg",
            "-stream_loop", str(loop_count),
            "-i", input_path,
            "-t", str(requested_duration),  # Trim to exact duration
            "-c", "copy",  # Copy streams without re-encoding
            "-y",
            output_path
        ]

        # Run ffmpeg
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown ffmpeg error"
            raise Exception(f"ffmpeg failed: {error_msg}")

        return output_path

    async def _upload_to_r2(
        self,
        video_path: str,
        campaign_id: int,
        duration: int
    ) -> str:
        """Upload extended video to R2 storage"""
        import time
        import hashlib

        # Generate R2 key
        timestamp = int(time.time())
        url_hash = hashlib.md5(str(campaign_id).encode()).hexdigest()[:8]
        key = f"campaigns/{campaign_id}/videos/extended/extended_{duration}s_{timestamp}_{url_hash}.mp4"

        # Read file bytes
        with open(video_path, "rb") as f:
            file_bytes = f.read()

        # Upload to R2
        _, public_url = await r2_storage.upload_file(
            file_bytes=file_bytes,
            key=key,
            content_type="video/mp4"
        )

        return public_url

    def _cleanup_temp_files(self, filepaths: list[str]) -> None:
        """Clean up temporary files"""
        for filepath in filepaths:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {filepath}: {e}")


# Create global instance
video_extension_service = VideoExtensionService()
