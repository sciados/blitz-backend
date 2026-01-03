# app/plugins/image_editor/services/replicate_service.py
"""
Replicate AI Service for Image Editing Operations
Handles all interactions with Replicate API
Uses LaMa, BiRefNet, Real-ESRGAN, and other open-source models

UPDATED: Now uses jinaai/lama (newer, better maintained version)
"""

import asyncio
import os
import httpx
import base64
import time
from typing import Optional, Tuple
from io import BytesIO


class ReplicateService:
    """Service for interacting with Replicate API"""
    
    # Best models for each operation (UPDATED - Latest versions)
    MODELS = {
        "inpaint": "jinaai/lama:e440909d3512c31646ee2e0c7d6f6f4923224863a6a10c494606e79fb5844497",
        "erase": "jinaai/lama:e440909d3512c31646ee2e0c7d6f6f4923224863a6a10c494606e79fb5844497",
        "background_remove": "cjwbw/rembg:fb8af171cfa1616ddcf1242c093f9c46bcada5ad4cf6f2fbe8b81b330ec5c003",
        "upscale": "nightmareai/real-esrgan:42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b",
        "outpaint": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
    }
    
    def __init__(self):
        self.api_token = os.getenv("REPLICATE_API_TOKEN")
        if not self.api_token:
            raise ValueError("REPLICATE_API_TOKEN environment variable not set")
        
        self.base_url = "https://api.replicate.com/v1"
        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }
    
    async def _create_prediction(self, version: str, input_params: dict) -> dict:
        """
        Create a prediction on Replicate
        
        Args:
            version: Model version hash
            input_params: Input parameters for the model
        
        Returns:
            Prediction response
        """
        endpoint = f"{self.base_url}/predictions"
        
        payload = {
            "version": version,
            "input": input_params
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                endpoint,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code != 201:
                error_detail = response.text if response.content else "Unknown error"
                raise Exception(f"Replicate API error: {response.status_code} - {error_detail}")
            
            return response.json()
    
    async def _wait_for_prediction(self, prediction_id: str, max_wait: int = 120) -> dict:
        """
        Poll prediction until complete or timeout
        
        Args:
            prediction_id: Prediction ID to poll
            max_wait: Maximum seconds to wait
        
        Returns:
            Completed prediction response
        """
        endpoint = f"{self.base_url}/predictions/{prediction_id}"
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            while True:
                if time.time() - start_time > max_wait:
                    raise Exception(f"Prediction timeout after {max_wait} seconds")
                
                response = await client.get(endpoint, headers=self.headers)
                
                if response.status_code != 200:
                    error_detail = response.text if response.content else "Unknown error"
                    raise Exception(f"Replicate API error: {response.status_code} - {error_detail}")
                
                result = response.json()
                status = result.get("status")
                
                if status == "succeeded":
                    return result
                elif status == "failed":
                    error = result.get("error", "Unknown error")
                    raise Exception(f"Prediction failed: {error}")
                elif status == "canceled":
                    raise Exception("Prediction was canceled")
                
                # Wait before polling again
                await asyncio.sleep(1)
    
    def _get_output_url(self, result: dict) -> str:
        """
        Extract output URL from Replicate result
        Handles both list and string outputs
        
        Args:
            result: Replicate prediction result
            
        Returns:
            Output image URL
        """
        output = result.get("output")
        if not output:
            raise Exception("No output in Replicate response")
        
        # Replicate can return a list or a single URL
        if isinstance(output, list):
            if len(output) == 0:
                raise Exception("Empty output list from Replicate")
            return output[0]  # Return first URL
        
        return output  # Return single URL
    
    async def inpaint_image(
        self,
        image_data: bytes,
        mask_data: bytes,
        prompt: str = "remove the masked area",
        output_format: str = "png"
    ) -> Tuple[bytes, dict]:
        """
        Perform inpainting using jinaai/lama model (newer version)
        
        Args:
            image_data: Original image bytes
            mask_data: Mask image bytes (white areas will be inpainted)
            prompt: Prompt for inpainting (required by jinaai/lama)
            output_format: Output format (png, jpeg, webp)
        
        Returns:
            Tuple of (edited_image_bytes, metadata_dict)
        """
        # Convert bytes to base64 data URLs
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        mask_b64 = base64.b64encode(mask_data).decode('utf-8')
        
        image_url = f"data:image/png;base64,{image_b64}"
        mask_url = f"data:image/png;base64,{mask_b64}"
        
        # jinaai/lama model parameters (requires prompt)
        input_params = {
            "image": image_url,
            "mask": mask_url,
            "prompt": prompt,  # Required by jinaai/lama
        }
        
        try:
            # Create prediction
            prediction = await self._create_prediction(
                self.MODELS["inpaint"],
                input_params
            )
            
            # Wait for completion
            result = await self._wait_for_prediction(prediction["id"])
            
            # Get output image URL (handles list or string)
            output_url = self._get_output_url(result)
            
            # Download result image
            async with httpx.AsyncClient(timeout=30.0) as client:
                img_response = await client.get(output_url)
                if img_response.status_code != 200:
                    raise Exception(f"Failed to download result image: {img_response.status_code}")
                
                image_bytes = img_response.content
            
            metadata = {
                "model": "jinaai/lama",
                "platform": "replicate",
                "prediction_id": prediction["id"],
            }
            
            return image_bytes, metadata
            
        except Exception as e:
            # Log error for debugging
            print(f"Replicate inpaint error: {str(e)}")
            raise
    
    async def erase_objects(
        self,
        image_data: bytes,
        mask_data: bytes,
        output_format: str = "png"
    ) -> Tuple[bytes, dict]:
        """
        Erase objects using jinaai/lama model (same as inpaint)
        
        Args:
            image_data: Original image bytes
            mask_data: Mask image bytes
            output_format: Output format
        
        Returns:
            Tuple of (edited_image_bytes, metadata_dict)
        """
        # Use inpaint with a generic prompt for erasing
        return await self.inpaint_image(
            image_data, 
            mask_data, 
            prompt="remove the masked area",
            output_format=output_format
        )
    
    async def remove_background(
        self,
        image_data: bytes,
        output_format: str = "png"
    ) -> Tuple[bytes, dict]:
        """
        Remove background using RMBG model
        
        Args:
            image_data: Original image bytes
            output_format: Output format
        
        Returns:
            Tuple of (edited_image_bytes, metadata_dict)
        """
        # Convert bytes to base64 data URL
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        image_url = f"data:image/png;base64,{image_b64}"
        
        input_params = {
            "image": image_url
        }
        
        try:
            # Create prediction
            prediction = await self._create_prediction(
                self.MODELS["background_remove"],
                input_params
            )
            
            # Wait for completion
            result = await self._wait_for_prediction(prediction["id"])
            
            # Get output image URL (handles list or string)
            output_url = self._get_output_url(result)
            
            # Download result image
            async with httpx.AsyncClient(timeout=30.0) as client:
                img_response = await client.get(output_url)
                if img_response.status_code != 200:
                    raise Exception(f"Failed to download result image: {img_response.status_code}")
                
                image_bytes = img_response.content
            
            metadata = {
                "model": "rembg",
                "platform": "replicate",
                "prediction_id": prediction["id"],
            }
            
            return image_bytes, metadata
            
        except Exception as e:
            print(f"Replicate background removal error: {str(e)}")
            raise
    
    async def upscale_image(
        self,
        image_data: bytes,
        scale: int = 2,
        output_format: str = "png"
    ) -> Tuple[bytes, dict]:
        """
        Upscale image using Real-ESRGAN
        
        Args:
            image_data: Original image bytes
            scale: Upscaling factor (2 or 4)
            output_format: Output format
        
        Returns:
            Tuple of (edited_image_bytes, metadata_dict)
        """
        # Convert bytes to base64 data URL
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        image_url = f"data:image/png;base64,{image_b64}"
        
        input_params = {
            "image": image_url,
            "scale": scale,
            "face_enhance": False,
        }
        
        try:
            # Create prediction
            prediction = await self._create_prediction(
                self.MODELS["upscale"],
                input_params
            )
            
            # Wait for completion (longer timeout for upscaling)
            result = await self._wait_for_prediction(prediction["id"], max_wait=180)
            
            # Get output image URL (handles list or string)
            output_url = self._get_output_url(result)
            
            # Download result image
            async with httpx.AsyncClient(timeout=60.0) as client:
                img_response = await client.get(output_url)
                if img_response.status_code != 200:
                    raise Exception(f"Failed to download result image: {img_response.status_code}")
                
                image_bytes = img_response.content
            
            metadata = {
                "model": "real-esrgan",
                "platform": "replicate",
                "prediction_id": prediction["id"],
                "scale": scale,
            }
            
            return image_bytes, metadata
            
        except Exception as e:
            print(f"Replicate upscale error: {str(e)}")
            raise
    
    def estimate_cost_usd(self, operation_type: str) -> float:
        """
        Estimate the cost in USD for an operation
        
        Args:
            operation_type: Type of operation
        
        Returns:
            Estimated cost in USD
        """
        cost_map = {
            "inpaint": 0.008,
            "erase": 0.008,
            "background_remove": 0.005,
            "upscale": 0.01,
            "outpaint": 0.01,
        }
        
        return cost_map.get(operation_type, 0.008)