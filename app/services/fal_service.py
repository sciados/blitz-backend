"""
FAL Service for Image Editing
Supports erase, inpaint, background removal, and other editing operations
"""

from __future__ import annotations

import os
import logging
from typing import Tuple, Dict, Any
import base64

import httpx

logger = logging.getLogger(__name__)


class FALService:
    """FAL service for AI image editing operations"""

    def __init__(self):
        """Initialize FAL service"""
        self.api_key = os.getenv("FAL_API_KEY")
        if not self.api_key:
            raise ValueError("FAL_API_KEY not set")

    async def erase_objects(
        self,
        image_data: bytes,
        mask_data: bytes,
        output_format: str = "png",
        **kwargs
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Erase objects from image using FAL's inpainting model

        Args:
            image_data: Original image bytes
            mask_data: Mask bytes (white=erase for Stability convention, will be inverted internally)
            output_format: Output format (png, jpg, webp)
            **kwargs: Additional parameters

        Returns:
            Tuple of (edited_image_data, metadata)
        """
        logger.info("🎨 FAL: Erasing objects...")

        # IMPORTANT: FAL inpainting models use INVERTED mask convention
        # Stability AI: white = erase
        # FAL: black = erase (need to invert)
        # Invert mask: white becomes black, black becomes white
        from PIL import Image
        import io

        # Convert mask to PIL Image
        mask_img = Image.open(io.BytesIO(mask_data)).convert("RGB")
        # Invert colors: white (255) -> black (0), black (0) -> white (255)
        inverted_mask = Image.eval(mask_img, lambda x: 255 - x)
        # Convert back to bytes
        inverted_buffer = io.BytesIO()
        inverted_mask.save(inverted_buffer, format="PNG")
        inverted_mask_data = inverted_buffer.getvalue()

        # Convert bytes to base64 for FAL API
        image_b64 = base64.b64encode(image_data).decode()
        mask_b64 = base64.b64encode(inverted_mask_data).decode()

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Use FAL's LaMa inpainting model
            # LaMa is a very reliable and popular inpainting model
            response = await client.post(
                "https://fal.run/fal-ai/lama",
                headers={"Authorization": f"Key {self.api_key}"},
                json={
                    "image_url": f"data:image/png;base64,{image_b64}",
                    "mask_image_url": f"data:image/png;base64,{mask_b64}",
                    "prompt": kwargs.get("prompt", ""),
                    "num_inference_steps": kwargs.get("num_inference_steps", 20),
                    "guidance_scale": kwargs.get("guidance_scale", 7.5),
                    "strength": kwargs.get("strength", 0.8),
                    "seed": kwargs.get("seed", 42),
                }
            )

            if response.status_code != 200:
                error_msg = f"FAL API error: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

            result = response.json()

            # FAL returns the result URL
            if "image" in result:
                result_url = result["image"]["url"]
            elif "images" in result and len(result["images"]) > 0:
                result_url = result["images"][0]["url"]
            else:
                raise Exception(f"Unexpected FAL response format: {result}")

            # Download result
            image_response = await client.get(result_url)
            edited_data = image_response.content

            metadata = {
                "provider": "fal",
                "model": "lama",
                "operation": "erase",
                "fal_request_id": result.get("request_id"),
                "metrics": result.get("metrics", {}),
            }

            logger.info("✅ FAL: Object erasure completed")
            return edited_data, metadata

    async def inpaint(
        self,
        image_data: bytes,
        mask_data: bytes,
        prompt: str,
        output_format: str = "png",
        **kwargs
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Inpaint (fill) regions of image using FAL

        Args:
            image_data: Original image bytes
            mask_data: Mask bytes (white=masked area to fill)
            prompt: Text prompt for inpainting
            output_format: Output format
            **kwargs: Additional parameters

        Returns:
            Tuple of (edited_image_data, metadata)
        """
        logger.info("🎨 FAL: Inpainting...")

        # Use the same erase_objects method with a prompt
        return await self.erase_objects(
            image_data=image_data,
            mask_data=mask_data,
            output_format=output_format,
            prompt=prompt,
            **kwargs
        )

    async def remove_background(
        self,
        image_data: bytes,
        output_format: str = "png",
        **kwargs
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Remove background from image using FAL

        Args:
            image_data: Image bytes
            output_format: Output format
            **kwargs: Additional parameters

        Returns:
            Tuple of (edited_image_data, metadata)
        """
        logger.info("🎨 FAL: Removing background...")

        image_b64 = base64.b64encode(image_data).decode()

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://fal.run/fal-ai/birefnet",
                headers={"Authorization": f"Key {self.api_key}"},
                json={
                    "image_url": f"data:image/png;base64,{image_b64}",
                }
            )

            if response.status_code != 200:
                error_msg = f"FAL API error: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

            result = response.json()

            # Get result URL
            if "image" in result:
                result_url = result["image"]["url"]
            elif "images" in result and len(result["images"]) > 0:
                result_url = result["images"][0]["url"]
            else:
                raise Exception(f"Unexpected FAL response format: {result}")

            # Download result
            image_response = await client.get(result_url)
            edited_data = image_response.content

            metadata = {
                "provider": "fal",
                "model": "birefnet",
                "operation": "background_removal",
                "fal_request_id": result.get("request_id"),
                "metrics": result.get("metrics", {}),
            }

            logger.info("✅ FAL: Background removal completed")
            return edited_data, metadata

    async def upscale(
        self,
        image_data: bytes,
        scale: int = 2,
        output_format: str = "png",
        **kwargs
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Upscale image using FAL's Real-ESRGAN model

        Args:
            image_data: Image bytes
            scale: Upscale factor (2, 4, 8)
            output_format: Output format
            **kwargs: Additional parameters

        Returns:
            Tuple of (edited_image_data, metadata)
        """
        logger.info(f"🎨 FAL: Upscaling image by {scale}x...")

        # For FAL, we can use the Real-ESRGAN endpoint directly with image bytes
        # but FAL prefers image URLs, so we need to upload first or use base64

        # Option 1: Use image-to-image with upscaling
        image_b64 = base64.b64encode(image_data).decode()

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://fal.run/fal-ai/real-esrgan",
                headers={"Authorization": f"Key {self.api_key}"},
                json={
                    "image_url": f"data:image/png;base64,{image_b64}",
                    "scale": scale,
                    "face_enhance": kwargs.get("face_enhance", True),
                }
            )

            if response.status_code != 200:
                error_msg = f"FAL API error: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

            result = response.json()

            # Get result URL
            if "image" in result:
                result_url = result["image"]["url"]
            elif "images" in result and len(result["images"]) > 0:
                result_url = result["images"][0]["url"]
            else:
                raise Exception(f"Unexpected FAL response format: {result}")

            # Download result
            image_response = await client.get(result_url)
            edited_data = image_response.content

            metadata = {
                "provider": "fal",
                "model": "real-esrgan",
                "operation": "upscale",
                "scale": scale,
                "fal_request_id": result.get("request_id"),
                "metrics": result.get("metrics", {}),
            }

            logger.info("✅ FAL: Upscaling completed")
            return edited_data, metadata
