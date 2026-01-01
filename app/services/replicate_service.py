"""
Replicate Service for Image Editing
Supports erase, inpaint, background removal, and other editing operations
"""

from __future__ import annotations

import os
import io
import asyncio
import logging
from typing import Optional, Tuple, Dict, Any

import httpx

logger = logging.getLogger(__name__)


class ReplicateService:
    """Replicate service for AI image editing operations"""

    def __init__(self):
        """Initialize Replicate service"""
        self.api_key = os.getenv("REPLICATE_API_TOKEN")
        if not self.api_key:
            raise ValueError("REPLICATE_API_TOKEN not set")

    async def erase_objects(
        self,
        image_data: bytes,
        mask_data: bytes,
        output_format: str = "png",
        **kwargs
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Erase objects from image using Replicate's inpainting model

        Args:
            image_data: Original image bytes
            mask_data: Mask bytes (white=keep, black=remove)
            output_format: Output format (png, jpg, webp)
            **kwargs: Additional parameters

        Returns:
            Tuple of (edited_image_data, metadata)
        """
        logger.info("🎨 Replicate: Erasing objects...")

        # Convert bytes to base64 for Replicate API
        import base64
        image_b64 = base64.b64encode(image_data).decode()
        mask_b64 = base64.b64encode(mask_data).decode()

        # Start prediction
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Create prediction with proper inpainting model
            # Using stabilityai/sdxl-inpaint model which is proven for inpainting
            prediction_response = await client.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "version": "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",  # SDXL Inpaint model
                    "input": {
                        "prompt": kwargs.get("prompt", ""),
                        "image": f"data:image/png;base64,{image_b64}",
                        "mask": f"data:image/png;base64,{mask_b64}",
                        "num_inference_steps": kwargs.get("num_inference_steps", 20),
                        "guidance_scale": kwargs.get("guidance_scale", 7.5),
                        "strength": kwargs.get("strength", 0.8),
                        "scheduler": "K_EULER",
                    }
                }
            )

            if prediction_response.status_code != 201:
                error_msg = f"Replicate API error: {prediction_response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

            prediction = prediction_response.json()
            logger.info(f"Replicate prediction started: {prediction['id']}")

            # Poll for completion
            while prediction["status"] not in ["succeeded", "failed", "canceled"]:
                await asyncio.sleep(2)
                result = await client.get(
                    f"https://api.replicate.com/v1/predictions/{prediction['id']}",
                    headers={"Authorization": f"Token {self.api_key}"}
                )
                prediction = result.json()
                logger.debug(f"Replicate status: {prediction['status']}")

            if prediction["status"] != "succeeded":
                error_msg = f"Replicate prediction failed: {prediction.get('error', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # Get result
            result_url = prediction["output"][0]

            # Download result
            image_response = await client.get(result_url)
            edited_data = image_response.content

            metadata = {
                "provider": "replicate",
                "model": "sdxl-inpaint",
                "operation": "erase",
                "prediction_id": prediction["id"],
                "status": prediction["status"],
                "completed_at": prediction.get("completed_at"),
                "metrics": prediction.get("metrics", {}),
            }

            logger.info("✅ Replicate: Object erasure completed")
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
        Inpaint (fill) regions of image using Replicate

        Args:
            image_data: Original image bytes
            mask_data: Mask bytes (white=masked area to fill)
            prompt: Text prompt for inpainting
            output_format: Output format
            **kwargs: Additional parameters

        Returns:
            Tuple of (edited_image_data, metadata)
        """
        logger.info("🎨 Replicate: Inpainting...")

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
        Remove background from image using Replicate

        Args:
            image_data: Image bytes
            output_format: Output format
            **kwargs: Additional parameters

        Returns:
            Tuple of (edited_image_data, metadata)
        """
        logger.info("🎨 Replicate: Removing background...")

        # Replicate background removal using rembg model
        import base64
        image_b64 = base64.b64encode(image_data).decode()

        async with httpx.AsyncClient(timeout=60.0) as client:
            prediction_response = await client.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "version": "bg removal:09f0abdb8b4e1f4a6e4f3f5e0d5f0b9c7f9a0b8c9d8e7f6a5b4c3d2e1f0a",  # rembg model version
                    "input": {
                        "image": f"data:image/png;base64,{image_b64}",
                    }
                }
            )

            if prediction_response.status_code != 201:
                error_msg = f"Replicate API error: {prediction_response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

            prediction = prediction_response.json()

            # Poll for completion
            while prediction["status"] not in ["succeeded", "failed", "canceled"]:
                await asyncio.sleep(2)
                result = await client.get(
                    f"https://api.replicate.com/v1/predictions/{prediction['id']}",
                    headers={"Authorization": f"Token {self.api_key}"}
                )
                prediction = result.json()

            if prediction["status"] != "succeeded":
                raise Exception(f"Background removal failed: {prediction.get('error')}")

            # Get result
            result_url = prediction["output"][0]
            image_response = await client.get(result_url)
            edited_data = image_response.content

            metadata = {
                "provider": "replicate",
                "model": "rembg",
                "operation": "background_removal",
                "prediction_id": prediction["id"],
                "status": prediction["status"],
                "completed_at": prediction.get("completed_at"),
                "metrics": prediction.get("metrics", {}),
            }

            logger.info("✅ Replicate: Background removal completed")
            return edited_data, metadata

    async def upscale(
        self,
        image_data: bytes,
        scale: int = 2,
        output_format: str = "png",
        **kwargs
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Upscale image using Replicate's Real-ESRGAN model

        Args:
            image_data: Image bytes
            scale: Upscale factor (2, 4, 8)
            output_format: Output format
            **kwargs: Additional parameters

        Returns:
            Tuple of (edited_image_data, metadata)
        """
        logger.info(f"🎨 Replicate: Upscaling image by {scale}x...")

        import base64
        image_b64 = base64.b64encode(image_data).decode()

        async with httpx.AsyncClient(timeout=60.0) as client:
            prediction_response = await client.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "version": "real-esrgan:1:0.0.1",
                    "input": {
                        "image": f"data:image/png;base64,{image_b64}",
                        "scale": scale,
                        "face_enhance": kwargs.get("face_enhance", True),
                    }
                }
            )

            if prediction_response.status_code != 201:
                error_msg = f"Replicate API error: {prediction_response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

            prediction = prediction_response.json()

            # Poll for completion
            while prediction["status"] not in ["succeeded", "failed", "canceled"]:
                await asyncio.sleep(2)
                result = await client.get(
                    f"https://api.replicate.com/v1/predictions/{prediction['id']}",
                    headers={"Authorization": f"Token {self.api_key}"}
                )
                prediction = result.json()

            if prediction["status"] != "succeeded":
                raise Exception(f"Upscaling failed: {prediction.get('error')}")

            # Get result
            result_url = prediction["output"][0]
            image_response = await client.get(result_url)
            edited_data = image_response.content

            metadata = {
                "provider": "replicate",
                "model": "real-esrgan",
                "operation": "upscale",
                "scale": scale,
                "prediction_id": prediction["id"],
                "status": prediction["status"],
                "completed_at": prediction.get("completed_at"),
                "metrics": prediction.get("metrics", {}),
            }

            logger.info("✅ Replicate: Upscaling completed")
            return edited_data, metadata
