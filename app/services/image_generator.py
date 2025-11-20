"""
Image Generation Service
Handles rotating AI platform image generation with Cloudflare R2 storage.
"""

from __future__ import annotations

import os
import io
import time
import hashlib
import base64
import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

import httpx
from PIL import Image

from app.core.config.settings import settings
from app.services.storage_r2 import r2_storage
from app.services.image_provider_config import provider_config

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
        # FREE Providers (Zero cost - try these first!)
        "pollinations": ProviderSpec(
            name="pollinations",
            model="flux",
            cost_per_image=0.00000,  # Completely free
            max_resolution="1024x1024",
            supports_aspect_ratio=True,
            estimated_time=4.0
        ),
        "huggingface": ProviderSpec(
            name="huggingface",
            model="stable-diffusion-xl",
            cost_per_image=0.00000,  # Free inference
            max_resolution="1024x1024",
            supports_aspect_ratio=True,
            estimated_time=6.0
        ),
        "replicate_free": ProviderSpec(
            name="replicate",
            model="free-sdxl",  # Using free model
            cost_per_image=0.00000,  # Free tier
            max_resolution="1024x1024",
            supports_aspect_ratio=True,
            estimated_time=10.0
        ),
        # ULTRA-CHEAP Providers (Less than $0.001) - With API Keys
        "fal": ProviderSpec(
            name="fal",
            model="sdxl-turbo",
            cost_per_image=0.00001,  # $0.00001 per image (free tier)
            max_resolution="1024x1024",
            supports_aspect_ratio=True,
            estimated_time=3.0
        ),
        # Low-Cost Providers ($0.001-$0.01) - With API Keys
        "stability": ProviderSpec(
            name="stability",
            model="ultra",
            cost_per_image=0.001,  # $0.001 per image
            max_resolution="1024x1024",
            supports_aspect_ratio=True,
            estimated_time=5.0
        ),
        # Premium Quality ($0.002+) - With API Keys
        "replicate": ProviderSpec(
            name="replicate",
            model="flux",
            cost_per_image=0.002,  # $0.002 per image
            max_resolution="1024x1024",
            supports_aspect_ratio=True,
            estimated_time=8.0
        )
    }

    def __init__(self):
        """Initialize image generator."""
        # Using r2_storage instance from storage_r2 module
        self.r2_storage = r2_storage
        # Speed-optimized rotation for PREVIEW mode (fastest first)
        # Removed slow/pollinating providers and failing ones
        self.provider_rotation = [
            "replicate",       # FAST: ~6s (actual)
            "stability",       # MEDIUM: ~12s (actual)
            "pollinations"     # SLOW: ~28s (only as last resort)
        ]
        self.current_provider_index = 0

        # Run provider discovery on startup
        self._update_provider_configs()

    def _update_provider_configs(self):
        """Update provider configurations with latest engines."""
        try:
            logger.info("🔄 Initializing provider engines...")
            # Run discovery in the background without blocking
            asyncio.create_task(self._async_update_engines())
        except Exception as e:
            logger.error(f"Failed to update provider configs: {str(e)}")

    async def _async_update_engines(self):
        """Async method to update engine configurations."""
        try:
            updates = await provider_config.update_all_providers()

            # Update Stability AI engine if discovered
            if "stability" in updates:
                old_engine = self.providers["stability"].model
                self.providers["stability"].model = updates["stability"]
                logger.info(f"✅ Updated Stability AI engine: {old_engine} → {updates['stability']}")

            # Update FAL engine if discovered
            if "fal" in updates:
                old_engine = self.providers["fal"].model
                self.providers["fal"].model = updates["fal"]
                logger.info(f"✅ Updated FAL engine: {old_engine} → {updates['fal']}")

            logger.info("✅ Provider engine discovery complete!")

        except Exception as e:
            logger.error(f"Error during engine discovery: {str(e)}")

    async def refresh_provider_engines(self):
        """Manually trigger provider engine refresh (can be called via API)."""
        logger.info("🔄 Manually refreshing provider engines...")
        await self._async_update_engines()
        return {"status": "success", "message": "Provider engines refreshed"}

    def select_provider(
        self,
        image_type: str,
        style: str,
        campaign_intelligence: Optional[Dict[str, Any]] = None,
        quality_boost: bool = False
    ) -> ProviderSpec:
        """
        Select optimal provider based on requirements.

        Args:
            image_type: Type of image (hero, social, ad, etc.)
            style: Image style preference
            campaign_intelligence: Campaign intelligence data for context
            quality_boost: If True, prioritize higher-quality providers

        Returns:
            ProviderSpec: Selected provider specification
        """
        # 🔄 Always rotate through providers for images
        # This ensures we don't get stuck on a failing provider
        provider_name = self.provider_rotation[self.current_provider_index]

        # If quality boost is enabled, use premium providers
        if quality_boost:
            # Skip free providers and use higher-quality paid providers
            # Only include providers with API keys: fal, stability, replicate
            premium_providers = ["fal", "stability", "replicate"]
            if provider_name in ["pollinations", "huggingface", "replicate_free"]:
                # Jump to next premium provider
                current_idx = self.provider_rotation.index(provider_name)
                for i in range(1, len(self.provider_rotation)):
                    next_idx = (current_idx + i) % len(self.provider_rotation)
                    if self.provider_rotation[next_idx] in premium_providers:
                        provider_name = self.provider_rotation[next_idx]
                        self.current_provider_index = next_idx
                        break

        self.current_provider_index = (self.current_provider_index + 1) % len(self.provider_rotation)

        return self.PROVIDERS[provider_name]

    def _parse_aspect_ratio(self, aspect_ratio: str) -> Dict[str, int]:
        """Parse aspect ratio string to dimensions."""
        # Use dimensions compatible with ALL providers (Replicate requires multiples of 64)
        ratio_map = {
            "1:1": (1024, 1024),     # Square
            "16:9": (1024, 576),     # Landscape (16:9 ratio, multiples of 64)
            "9:16": (576, 1024),     # Portrait (9:16 ratio, multiples of 64)
            "4:3": (1024, 768),      # Standard (4:3 ratio, multiples of 64)
            "21:9": (1536, 448)      # Ultrawide (21:9 ratio, multiples of 64)
        }

        return ratio_map.get(aspect_ratio, (1024, 1024))

    async def generate_image(
        self,
        prompt: str,
        image_type: str,
        style: str = "photorealistic",
        aspect_ratio: str = "1:1",
        campaign_intelligence: Optional[Dict[str, Any]] = None,
        custom_params: Optional[Dict[str, Any]] = None,
        quality_boost: bool = False,
        campaign_id: Optional[int] = None,  # Campaign UUID for R2 path organization
        save_to_r2: bool = True  # Skip R2 upload for preview images
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
            quality_boost: Enable premium provider selection
            campaign_id: Campaign ID for R2 path organization
            save_to_r2: Save to R2 storage (False for preview)

        Returns:
            ImageGenerationResult: Generated image data
        """
        start_time = time.time()

        # Select provider
        provider = self.select_provider(image_type, style, campaign_intelligence, quality_boost)
        logger.info(f"🎨 Selected provider: {provider.name} ({provider.model})")

        # Parse dimensions
        width, height = self._parse_aspect_ratio(aspect_ratio)

        # Generate image using selected provider
        # Generate image using selected provider with fallback
        try:
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
            elif provider.name == "pollinations":
                result = await self._generate_with_pollinations(
                    prompt, width, height, style, custom_params or {}
                )
            elif provider.name == "huggingface":
                result = await self._generate_with_huggingface(
                    prompt, width, height, style, custom_params or {}
                )
            elif provider.name == "leonardo":
                result = await self._generate_with_leonardo(
                    prompt, width, height, style, custom_params or {}
                )
            elif provider.name == "ideogram":
                result = await self._generate_with_ideogram(
                    prompt, width, height, style, custom_params or {}
                )
            else:
                raise ValueError(f"Unsupported provider: {provider.name}")
        except Exception as e:
            logger.error(f"Provider {provider.name} failed: {e}")
            # Try next provider in rotation
            logger.info(f"Trying next provider...")
            self.current_provider_index = (self.current_provider_index + 1) % len(self.provider_rotation)
            return await self.generate_image(
                prompt, image_type, style, aspect_ratio,
                campaign_intelligence, custom_params,
                quality_boost=quality_boost,
                campaign_id=campaign_id,
                save_to_r2=save_to_r2
            )

        generation_time = time.time() - start_time
        logger.info(f"✅ Image generated in {generation_time:.2f}s using {provider.name}")
        # Upload to Cloudflare R2 only if save_to_r2 is True
        if save_to_r2:
            r2_key, image_url = await self.r2_storage.upload_file(
                file_bytes=result["image_data"],
                key=f"campaigns/{campaign_id}/generated_images/{int(time.time())}_{hashlib.md5(prompt.encode()).hexdigest()[:8]}.png",
                content_type="image/png"
            )
            # Generate thumbnail for saved images
            thumbnail_url = await self._generate_thumbnail(image_url, campaign_id)
        else:
            # For preview - use provider URL directly without uploading to R2
            image_url = result["image_url"]
            thumbnail_url = None  # No thumbnail for preview images
            logger.info(f"🔍 Preview mode - using provider URL directly (not saved to R2)")

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

    async def enhance_image(
        self,
        base_image_url: str,
        prompt: str,
        image_type: str,
        style: str,
        aspect_ratio: str,
        quality_boost: bool = True,
        campaign_id: int = 0,
        save_to_r2: bool = True
    ) -> ImageGenerationResult:
        """
        Enhance an existing image using image-to-image generation.

        Args:
            base_image_url: URL of the base image to enhance
            prompt: Enhancement prompt
            image_type: Type of image
            style: Image style
            aspect_ratio: Image aspect ratio
            quality_boost: Whether to use quality boost
            campaign_id: Campaign ID for saving
            save_to_r2: Whether to save to R2

        Returns:
            ImageGenerationResult: Enhanced image
        """
        logger.info(f"✨ Enhancing image from: {base_image_url}")

        # Parse aspect ratio to get dimensions
        width, height = self._parse_aspect_ratio(aspect_ratio)

        # Select provider (use premium providers for enhancement)
        provider = self.select_provider(
            image_type=image_type,
            style=style,
            quality_boost=True
        )
        logger.info(f"🎨 Selected provider for enhancement: {provider.name}")

        start_time = time.time()

        try:
            # Generate enhanced image
            result = await self._generate_with_provider(
                provider=provider,
                prompt=prompt,
                width=width,
                height=height,
                style=style,
                custom_params={"base_image_url": base_image_url},
                is_enhancement=True
            )
        except Exception as e:
            logger.error(f"Provider {provider.name} failed: {e}")
            # For now, just re-raise - could add fallback logic here
            raise Exception(f"Image enhancement failed: {str(e)}")

        generation_time = time.time() - start_time
        logger.info(f"✅ Image enhanced in {generation_time:.2f}s using {provider.name}")

        # Upload to R2 if requested
        if save_to_r2:
            r2_key, image_url = await self.r2_storage.upload_file(
                file_bytes=result["image_data"],
                key=f"campaigns/{campaign_id}/generated_images/enhanced_{int(time.time())}_{hashlib.md5(prompt.encode()).hexdigest()[:8]}.png",
                content_type="image/png"
            )
            # Generate thumbnail for saved images
            thumbnail_url = await self._generate_thumbnail(image_url, campaign_id)
        else:
            # Use provider URL directly
            image_url = result["image_url"]
            thumbnail_url = None
            logger.info(f"🔍 Enhancement preview mode - using provider URL directly")

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
                "is_enhanced": True,
                "base_image_url": base_image_url,
                "custom_params": {"base_image_url": base_image_url}
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

        async with httpx.AsyncClient(timeout=20.0) as client:
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
            logger.info(f"FAL response keys: {list(data.keys())}")
            logger.info(f"FAL response structure: {data}")

            # FAL returns different response format - handle both old and new formats
            if "images" in data and len(data["images"]) > 0:
                image_url = data["images"][0]["url"]
            elif "image" in data:
                image_url = data["image"]["url"]
            elif "url" in data:
                image_url = data["url"]
            else:
                logger.error(f"Unexpected FAL response format: {data}")
                raise Exception(f"Unexpected FAL response format")
            image_response = await client.get(image_url)
            image_data = image_response.content

            return {"image_data": image_data, "image_url": image_url, "metadata": data}

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

        async with httpx.AsyncClient(timeout=15.0) as client:
            # Start generation
            prediction_response = await client.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "version": "ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",  # Flux model
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

            return {"image_data": image_data, "image_url": image_url, "metadata": prediction}

    async def _generate_with_stability(
        self,
        prompt: str,
        width: int,
        height: int,
        style: str,
        custom_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate image using Stability AI v2beta API."""
        api_key = os.getenv("STABILITY_API_KEY")
        if not api_key:
            raise ValueError("STABILITY_API_KEY not set")

        # Prepare prompt with style
        enhanced_prompt = f"{prompt}, {style} style"

        # Convert dimensions to aspect ratio string (Stability AI uses aspect_ratio param)
        ratio = f"{width}:{height}"

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.stability.ai/v2beta/stable-image/generate/ultra",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "image/*"
                },
                files={"none": b""},
                data={
                    "prompt": enhanced_prompt,
                    "output_format": "webp",
                    "aspect_ratio": ratio,
                }
            )

            if response.status_code != 200:
                logger.error(f"Stability API error: {response.text}")
                raise Exception(f"Image generation failed: {response.text}")

            # Response is binary image data
            image_data = response.content

            # For preview mode (no R2), create a temporary data URL
            # In production mode, this gets replaced with R2 URL
            import base64
            data_url = f"data:image/webp;base64,{base64.b64encode(image_data).decode('utf-8')}"

            return {
                "image_data": image_data,
                "image_url": data_url,
                "metadata": {"model": "ultra", "format": "webp"}
            }

    async def _generate_with_pollinations(
        self,
        prompt: str,
        width: int,
        height: int,
        style: str,
        custom_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate image using Pollinations AI (completely free)."""
        # Pollinations doesn't require an API key - completely free
        # Prepare prompt with style
        enhanced_prompt = f"{prompt}, {style} style"

        # URL encode the prompt
        from urllib.parse import quote
        encoded_prompt = quote(enhanced_prompt)

        # Pollinations free API
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={custom_params.get('seed', 1)}&nologo=true"

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(image_url)

            if response.status_code != 200:
                logger.error(f"Pollinations API error: {response.text}")
                raise Exception(f"Image generation failed: {response.text}")

            # Response is binary image data
            image_data = response.content

            return {"image_data": image_data, "image_url": image_url, "metadata": {"model": "flux", "provider": "pollinations"}}

    async def _generate_with_huggingface(
        self,
        prompt: str,
        width: int,
        height: int,
        style: str,
        custom_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate image using Hugging Face Inference API."""
        api_key = os.getenv("HUGGINGFACE_API_TOKEN")
        if not api_key:
            raise ValueError("HUGGINGFACE_API_TOKEN not set")

        # Prepare prompt with style
        enhanced_prompt = f"{prompt}, {style} style"

        # HuggingFace Inference API - free tier available
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "inputs": enhanced_prompt,
                    "parameters": {
                        "width": width,
                        "height": height,
                        "num_inference_steps": custom_params.get("num_inference_steps", 30)
                    }
                }
            )

            if response.status_code != 200:
                logger.error(f"HuggingFace API error: {response.text}")
                raise Exception(f"Image generation failed: {response.text}")

            # Response is binary image data
            image_data = response.content

            # For HuggingFace, we don't have the original URL, so we'll use a placeholder
            # This is fine since HuggingFace isn't used for preview (free providers are)
            return {"image_data": image_data, "image_url": "huggingface://generated", "metadata": {"model": "stable-diffusion-xl-base-1.0", "provider": "huggingface"}}

    async def _generate_with_ideogram(
        self,
        prompt: str,
        width: int,
        height: int,
        style: str,
        custom_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate image using Ideogram API."""
        api_key = os.getenv("IDEOGRAM_API_KEY")
        if not api_key:
            raise ValueError("IDEOGRAM_API_KEY not set")

        # Prepare prompt with style
        enhanced_prompt = f"{prompt}, {style} style"

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.ideogram.ai/v1/images/generations",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "prompt": enhanced_prompt,
                    "aspect_ratio": f"{width}:{height}",
                    "num_images": 1,
                    "model": "ideogram-v2"
                }
            )

            if response.status_code != 200:
                logger.error(f"Ideogram API error: {response.text}")
                raise Exception(f"Image generation failed: {response.text}")

            data = response.json()
            # Get the image URL from response
            if "data" in data and len(data["data"]) > 0:
                image_url = data["data"][0]["url"]
            else:
                raise Exception(f"Unexpected Ideogram response format: {data}")

            # Download the image
            image_response = await client.get(image_url)
            image_data = image_response.content

            return {"image_data": image_data, "image_url": image_url, "metadata": data}

    async def _generate_with_leonardo(
        self,
        prompt: str,
        width: int,
        height: int,
        style: str,
        custom_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate image using Leonardo AI."""
        api_key = os.getenv("LEONARDO_API_KEY")
        if not api_key:
            raise ValueError("LEONARDO_API_KEY not set")

        # Prepare prompt with style
        enhanced_prompt = f"{prompt}, {style} style"

        async with httpx.AsyncClient(timeout=20.0) as client:
            # Start generation
            generation_response = await client.post(
                "https://cloud.leonardo.ai/api/rest/v1/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": enhanced_prompt,
                    "modelId": "Leonardo_Diffusion_XL",
                    "width": width,
                    "height": height,
                    "num_images": 1
                }
            )

            if generation_response.status_code != 201:
                logger.error(f"Leonardo API error: {generation_response.text}")
                raise Exception(f"Image generation failed: {generation_response.text}")

            generation_data = generation_response.json()
            generation_id = generation_data["generation"]["id"]

            # Poll for completion
            import time
            max_attempts = 30
            for _ in range(max_attempts):
                await asyncio.sleep(2)
                result_response = await client.get(
                    f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                result_data = result_response.json()

                if result_data["generations"]["by_pk"]["status"] == "COMPLETED":
                    # Get image URL
                    images = result_data["generations"]["by_pk"]["images"]
                    if images and len(images) > 0:
                        image_url = images[0]["url"]

                        # Download the image
                        image_response = await client.get(image_url)
                        image_data = image_response.content

                        return {"image_data": image_data, "image_url": image_url, "metadata": result_data}
                elif result_data["generations"]["by_pk"]["status"] == "FAILED":
                    raise Exception(f"Image generation failed: {result_data}")

            raise Exception("Image generation timed out")

    async def _generate_thumbnail(self, image_url: str, campaign_id: int, size: tuple = (256, 256)) -> Optional[str]:
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
                _, thumbnail_url = await self.r2_storage.upload_file(
                    file_bytes=thumbnail_data,
                    key=f"campaigns/{campaign_id}/generated_images/thumbnails/{int(time.time())}_{hashlib.md5(image_url.encode()).hexdigest()[:8]}.jpg",
                    content_type="image/jpeg"
                )

                return thumbnail_url
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            return None

    async def batch_generate(
        self,
        requests: List[Dict[str, Any]],
        save_to_r2: bool = True,
        campaign_id: Optional[int] = None
    ) -> List[ImageGenerationResult]:
        """
        Generate multiple images in parallel.

        Args:
            requests: List of generation request dicts
            save_to_r2: Whether to save images to R2 (False for preview drafts)
            campaign_id: Campaign ID for R2 path organization

        Returns:
            List[ImageGenerationResult]: Generated images
        """
        logger.info(f"🎨 Starting batch generation of {len(requests)} images (save_to_r2={save_to_r2})")

        tasks = []
        for req in requests:
            task = self.generate_image(
                prompt=req["prompt"],
                image_type=req["image_type"],
                style=req.get("style", "photorealistic"),
                aspect_ratio=req.get("aspect_ratio", "1:1"),
                campaign_intelligence=req.get("campaign_intelligence"),
                custom_params=req.get("custom_params"),
                save_to_r2=save_to_r2,
                campaign_id=campaign_id
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

    async def save_draft_image(
        self,
        image_url: str,
        campaign_id: int,
        image_type: str,
        style: str,
        aspect_ratio: str,
        provider: str,
        model: str,
        prompt: str,
        custom_prompt: Optional[str] = None
    ) -> ImageGenerationResult:
        """
        Save a draft image by downloading it from the provider URL and uploading to R2.
        Note: Draft saves do NOT include thumbnail generation (unlike premium saves).

        Args:
            image_url: URL of the draft image to save
            campaign_id: Campaign ID
            image_type: Type of image
            style: Image style
            aspect_ratio: Image aspect ratio
            provider: Provider name
            model: Model name
            prompt: Original prompt
            custom_prompt: Custom prompt if any

        Returns:
            ImageGenerationResult: Saved image information (no thumbnail)
        """
        logger.info(f"💾 Saving draft image from {provider}")

        try:
            # Shorten extremely long URLs (e.g., Pollinations URLs with encoded prompts)
            # HTTP clients have limits on URL length, so we extract just the essential parts
            shortened_url = image_url
            if "image.pollinations.ai" in image_url and len(image_url) > 200:
                # Extract seed from long Pollinations URL and create shorter version
                import re
                seed_match = re.search(r'seed=(\d+)', image_url)
                width_match = re.search(r'width=(\d+)', image_url)
                height_match = re.search(r'height=(\d+)', image_url)

                if seed_match and width_match and height_match:
                    seed = seed_match.group(1)
                    width = width_match.group(1)
                    height = height_match.group(1)
                    # Create minimal URL with just seed and dimensions
                    shortened_url = f"https://image.pollinations.ai/prompt/IMG?width={width}&height={height}&seed={seed}&nologo=true"
                    logger.info(f"Shortened Pollinations URL from {len(image_url)} to {len(shortened_url)} chars")
            elif len(image_url) > 2000:
                # Generic fallback for any other extremely long URLs
                # This shouldn't happen in normal operation, but prevents crashes
                logger.warning(f"Extremely long URL detected ({len(image_url)} chars), may fail to download")
                # Try anyway - some HTTP clients support longer URLs

            # Download image from provider URL
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(shortened_url)
                image_data = response.content

            # Generate filename
            filename = f"draft_{int(time.time())}_{hashlib.md5(image_url.encode()).hexdigest()[:8]}.png"

            # Upload to R2 (main image only, no thumbnail for drafts)
            r2_key, saved_image_url = await self.r2_storage.upload_file(
                file_bytes=image_data,
                key=f"campaigns/{campaign_id}/generated_images/{filename}",
                content_type="image/png"
            )

            # No thumbnail for draft saves (only premium saves get thumbnails)
            thumbnail_url = None

            # Return result
            return ImageGenerationResult(
                image_url=saved_image_url,
                thumbnail_url=thumbnail_url,
                provider=provider,
                model=model,
                prompt=prompt,
                style=style,
                aspect_ratio=aspect_ratio,
                metadata={
                    "saved_from_draft": True,
                    "custom_prompt": custom_prompt,
                    "original_url": image_url
                },
                cost=0.0  # Draft images are free
            )
        except Exception as e:
            logger.error(f"Failed to save draft image: {e}")
            raise