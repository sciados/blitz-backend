"""
Image Generation Service
Handles rotating AI platform image generation with Cloudflare R2 storage.
"""

from __future__ import annotations

import os
import io
import time
import hashlib
import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

import httpx
from PIL import Image

from app.core.config.settings import settings
from app.services.storage_r2 import R2Storage

logger = logging.getLogger(__name__)


@dataclass
class ImageGenerationResult:
    """Result from image generation."""
    image_url: str
    thumbnail_url: Optional[str]
    provider: str
    model: str
    prompt: str
    style: str
    aspect_ratio: str
    metadata: Dict[str, Any]
    cost: float = 0.0


@dataclass
class ProviderSpec:
    """AI provider specification."""
    name: str
    model: str
    cost_per_image: float
    max_resolution: str
    supports_aspect_ratio: bool
    estimated_time: float  # seconds


class ImageGenerator:
    """Handles rotating AI platform image generation."""

    # Provider configurations
    PROVIDERS = {
        # Free Tier Providers (Use first for cost optimization)
        "pollinations": ProviderSpec(
            name="pollinations",
            model="flux",
            cost_per_image=0.00000,  # Completely free
            max_resolution="1024x1024",
            supports_aspect_ratio=True,
            estimated_time=4.0
        ),
        "fal": ProviderSpec(
            name="fal",
            model="sdxl-turbo",
            cost_per_image=0.00001,  # Free tier
            max_resolution="1024x1024",
            supports_aspect_ratio=True,
            estimated_time=3.0
        ),
        "huggingface": ProviderSpec(
            name="huggingface",
            model="stable-diffusion-xl",
            cost_per_image=0.00000,  # Free inference
            max_resolution="1024x1024",
            supports_aspect_ratio=True,
            estimated_time=6.0
        ),
        # Low-Cost Providers
        "stability": ProviderSpec(
            name="stability",
            model="sd-3.5-medium",
            cost_per_image=0.001,
            max_resolution="1024x1024",
            supports_aspect_ratio=True,
            estimated_time=5.0
        ),
        "leonardo": ProviderSpec(
            name="leonardo",
            model="Leonardo Diffusion XL",
            cost_per_image=0.001,
            max_resolution="1024x1024",
            supports_aspect_ratio=True,
            estimated_time=7.0
        ),
        # Premium Quality
        "replicate": ProviderSpec(
            name="replicate",
            model="flux",
            cost_per_image=0.002,
            max_resolution="1024x1024",
            supports_aspect_ratio=True,
            estimated_time=8.0
        ),
        "ideogram": ProviderSpec(
            name="ideogram",
            model="ideogram-v2",
            cost_per_image=0.00050,  # Very affordable
            max_resolution="1024x1024",
            supports_aspect_ratio=True,
            estimated_time=5.0
        )
    }

    def __init__(self):
        """Initialize image generator."""
        self.r2_storage = R2Storage()
        self.provider_rotation = ["fal", "replicate", "stability"]
        self.current_provider_index = 0

    def select_provider(
        self,
        image_type: str,
        style: str,
        campaign_intelligence: Optional[Dict[str, Any]] = None
    ) -> ProviderSpec:
        """
        Select optimal provider based on requirements.

        Args:
            image_type: Type of image (hero, social, ad, etc.)
            style: Image style preference
            campaign_intelligence: Campaign intelligence data for context

        Returns:
            ProviderSpec: Selected provider specification
        """
        # Cost optimization: prefer fal (free) for most cases
        if settings.AI_COST_OPTIMIZATION:
            # Use fal for standard quality, replicate for high-end
            if style in ["photorealistic", "artistic"] and image_type in ["hero", "ad"]:
                # High-end images use better provider
                provider_name = "stability"
            else:
                # Standard images use fal
                provider_name = "fal"
        else:
            # Rotate through providers
            provider_name = self.provider_rotation[self.current_provider_index]
            self.current_provider_index = (self.current_provider_index + 1) % len(self.provider_rotation)

        return self.PROVIDERS[provider_name]

    def _parse_aspect_ratio(self, aspect_ratio: str) -> Dict[str, int]:
        """Parse aspect ratio string to dimensions."""
        ratio_map = {
            "1:1": (1024, 1024),
            "16:9": (1024, 576),
            "9:16": (576, 1024),
            "4:3": (1024, 768),
            "21:9": (1024, 438)
        }

        return ratio_map.get(aspect_ratio, (1024, 1024))

    async def generate_image(
        self,
        prompt: str,
        image_type: str,
        style: str = "photorealistic",
        aspect_ratio: str = "1:1",
        campaign_intelligence: Optional[Dict[str, Any]] = None,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> ImageGenerationResult:
        """
        Generate image using rotating AI providers.

        Args:
            prompt: Image generation prompt
            image_type: Type of image (hero, social, ad, etc.)
            style: Image style (photorealistic, artistic, etc.)
            aspect_ratio: Image aspect ratio (1:1, 16:9, etc.)
            campaign_intelligence: Campaign intelligence data
            custom_params: Additional generation parameters

        Returns:
            ImageGenerationResult: Generated image data
        """
        start_time = time.time()

        # Select provider
        provider = self.select_provider(image_type, style, campaign_intelligence)
        logger.info(f"🎨 Selected provider: {provider.name} ({provider.model})")

        # Parse dimensions
        width, height = self._parse_aspect_ratio(aspect_ratio)

        # Generate image using selected provider
        if provider.name == "fal":
            result = await self._generate_with_fal(
                prompt, width, height, style, custom_params or {}
            )
        elif provider.name == "replicate":
            result = await self._generate_with_replicate(
                prompt, width, height, style, custom_params or {}
            )
        elif provider.name == "stability":
            result = await self._generate_with_stability(
                prompt, width, height, style, custom_params or {}
            )
        else:
            raise ValueError(f"Unsupported provider: {provider.name}")

        generation_time = time.time() - start_time
        logger.info(f"✅ Image generated in {generation_time:.2f}s using {provider.name}")

        # Upload to Cloudflare R2
        image_url = await self.r2_storage.upload_image(
            image_data=result["image_data"],
            filename=f"{int(time.time())}_{hashlib.md5(prompt.encode()).hexdigest()[:8]}.png",
            content_type="image/png"
        )

        # Generate thumbnail
        thumbnail_url = await self._generate_thumbnail(image_url)

        # Build result
        return ImageGenerationResult(
            image_url=image_url,
            thumbnail_url=thumbnail_url,
            provider=provider.name,
            model=provider.model,
            prompt=prompt,
            style=style,
            aspect_ratio=aspect_ratio,
            metadata={
                "width": width,
                "height": height,
                "generation_time": generation_time,
                "campaign_intelligence_version": campaign_intelligence.get("version") if campaign_intelligence else None,
                "custom_params": custom_params or {}
            },
            cost=provider.cost_per_image
        )

    async def _generate_with_fal(
        self,
        prompt: str,
        width: int,
        height: int,
        style: str,
        custom_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate image using FAL AI."""
        api_key = os.getenv("FAL_API_KEY")
        if not api_key:
            raise ValueError("FAL_API_KEY not set")

        # Prepare prompt with style
        enhanced_prompt = f"{prompt}, {style} style"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://fal.run/fal-ai/sdxl-turbo",
                headers={"Authorization": f"Key {api_key}"},
                json={
                    "prompt": enhanced_prompt,
                    "image_size": f"{width}x{height}",
                    "num_inference_steps": 4,
                    "guidance_scale": 3.5,
                    "num_images": 1
                }
            )

            if response.status_code != 200:
                logger.error(f"FAL API error: {response.text}")
                raise Exception(f"Image generation failed: {response.text}")

            data = response.json()

            # Download generated image
            image_url = data["images"][0]["url"]
            image_response = await client.get(image_url)
            image_data = image_response.content

            return {"image_data": image_data, "metadata": data}

    async def _generate_with_replicate(
        self,
        prompt: str,
        width: int,
        height: int,
        style: str,
        custom_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate image using Replicate."""
        api_key = os.getenv("REPLICATE_API_TOKEN")
        if not api_key:
            raise ValueError("REPLICATE_API_TOKEN not set")

        # Prepare prompt with style
        enhanced_prompt = f"{prompt}, {style} style"

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Start generation
            prediction_response = await client.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "version": "MODEL_VERSION_HASH",  # Need actual version hash
                    "input": {
                        "prompt": enhanced_prompt,
                        "width": width,
                        "height": height,
                        "num_outputs": 1
                    }
                }
            )

            if prediction_response.status_code != 201:
                logger.error(f"Replicate API error: {prediction_response.text}")
                raise Exception(f"Image generation failed: {prediction_response.text}")

            prediction = prediction_response.json()

            # Poll for completion
            while prediction["status"] not in ["succeeded", "failed"]:
                await asyncio.sleep(2)
                result = await client.get(
                    f"https://api.replicate.com/v1/predictions/{prediction['id']}",
                    headers={"Authorization": f"Token {api_key}"}
                )
                prediction = result.json()

            if prediction["status"] != "succeeded":
                raise Exception(f"Image generation failed: {prediction.get('error')}")

            # Download generated image
            image_url = prediction["output"][0]
            image_response = await client.get(image_url)
            image_data = image_response.content

            return {"image_data": image_data, "metadata": prediction}

    async def _generate_with_stability(
        self,
        prompt: str,
        width: int,
        height: int,
        style: str,
        custom_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate image using Stability AI."""
        api_key = os.getenv("STABILITY_API_KEY")
        if not api_key:
            raise ValueError("STABILITY_API_KEY not set")

        # Prepare prompt with style
        enhanced_prompt = f"{prompt}, {style} style"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                json={
                    "text_prompts": [{"text": enhanced_prompt}],
                    "cfg_scale": 7,
                    "height": height,
                    "width": width,
                    "samples": 1,
                    "steps": 30
                }
            )

            if response.status_code != 200:
                logger.error(f"Stability API error: {response.text}")
                raise Exception(f"Image generation failed: {response.text}")

            data = response.json()

            # Extract image from base64
            import base64
            image_base64 = data["artifacts"][0]["base64"]
            image_data = base64.b64decode(image_base64)

            return {"image_data": image_data, "metadata": data}

    async def _generate_thumbnail(self, image_url: str, size: tuple = (256, 256)) -> Optional[str]:
        """Generate thumbnail for image."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                image = Image.open(io.BytesIO(response.content))

                # Resize image
                image.thumbnail(size, Image.Resampling.LANCZOS)

                # Save to bytes
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=80)
                thumbnail_data = buffer.getvalue()

                # Upload to R2
                thumbnail_url = await self.r2_storage.upload_image(
                    image_data=thumbnail_data,
                    filename=f"thumbnails/{int(time.time())}_{hashlib.md5(image_url.encode()).hexdigest()[:8]}.jpg",
                    content_type="image/jpeg"
                )

                return thumbnail_url
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            return None

    async def batch_generate(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[ImageGenerationResult]:
        """
        Generate multiple images in parallel.

        Args:
            requests: List of generation request dicts

        Returns:
            List[ImageGenerationResult]: Generated images
        """
        logger.info(f"🎨 Starting batch generation of {len(requests)} images")

        tasks = []
        for req in requests:
            task = self.generate_image(
                prompt=req["prompt"],
                image_type=req["image_type"],
                style=req.get("style", "photorealistic"),
                aspect_ratio=req.get("aspect_ratio", "1:1"),
                campaign_intelligence=req.get("campaign_intelligence"),
                custom_params=req.get("custom_params")
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, ImageGenerationResult)]

        logger.info(f"✅ Batch generation complete: {len(valid_results)}/{len(requests)} successful")
        return valid_results

    async def create_variations(
        self,
        base_image_url: str,
        base_prompt: str,
        num_variations: int = 3,
        variation_strength: float = 0.7
    ) -> List[ImageGenerationResult]:
        """
        Create variations of an existing image.

        Args:
            base_image_url: URL of base image
            base_prompt: Original prompt used
            num_variations: Number of variations to create
            variation_strength: How much to vary (0.0-1.0)

        Returns:
            List[ImageGenerationResult]: Generated variations
        """
        logger.info(f"🎨 Creating {num_variations} variations of image")

        # For now, use the base prompt with slight modifications
        # In production, use image-to-image models for better variations
        variation_prompts = []
        for i in range(num_variations):
            variation_prompt = f"{base_prompt}, variation {i+1}, {variation_strength*100}% similarity"
            variation_prompts.append(variation_prompt)

        tasks = [
            self.generate_image(
                prompt=prompt,
                image_type="variation",
                style="photorealistic",
                aspect_ratio="1:1"
            )
            for prompt in variation_prompts
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid_results = [r for r in results if isinstance(r, ImageGenerationResult)]

        logger.info(f"✅ Created {len(valid_results)} variations")
        return valid_results
