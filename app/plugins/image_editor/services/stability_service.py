# app/plugins/image_editor/services/stability_service.py

# Updated: 2025-12-22 - Fixed JSON/binary response handling
"""
Stability AI Service for Image Editing Operations
Handles all interactions with Stability AI API
"""
import os
import httpx
import base64
from typing import Optional, Tuple
from io import BytesIO


class StabilityAIService:
    """Service for interacting with Stability AI API"""
    
    def __init__(self):
        self.api_key = os.getenv("STABILITY_API_KEY")
        if not self.api_key:
            raise ValueError("STABILITY_API_KEY environment variable not set")
        
        self.base_url = "https://api.stability.ai/v2beta"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
    
    async def inpaint_image(
        self,
        image_data: bytes,
        mask_data: bytes,
        prompt: str,
        negative_prompt: Optional[str] = None,
        seed: int = 0,
        output_format: str = "png"
    ) -> Tuple[bytes, dict]:
        """
        Perform inpainting operation on an image
        
        Args:
            image_data: Original image bytes
            mask_data: Mask image bytes (white areas will be inpainted)
            prompt: Description of what to paint in masked area
            negative_prompt: What to avoid
            seed: Random seed for reproducibility
            output_format: Output format (png, jpeg, webp)
        
        Returns:
            Tuple of (edited_image_bytes, metadata_dict)
        """
        endpoint = f"{self.base_url}/stable-image/edit/inpaint"
        
        # Prepare multipart form data
        files = {
            "image": ("image.png", image_data, "image/png"),
            "mask": ("mask.png", mask_data, "image/png")
        }
        
        data = {
            "prompt": prompt,
            "output_format": output_format,
            "seed": seed
        }
        
        if negative_prompt:
            data["negative_prompt"] = negative_prompt
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                headers=self.headers,
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                error_detail = response.text if response.content else "Unknown error"
                raise Exception(f"Stability AI API error: {response.status_code} - {error_detail}")
            
            # Check response format
            content_type = response.headers.get("content-type", "")

            if "application/json" in content_type or response.content.startswith(b'{"'):
                # JSON response with base64 image
                result = response.json()
                if "image" in result:
                    image_bytes = base64.b64decode(result["image"])
                else:
                    raise Exception("No image data in Stability AI response")
                # Extract metadata from JSON
                metadata = {
                    "model": "stable-diffusion-xl-1024-v1-0",
                    "finish_reason": result.get("finish_reason", "SUCCESS"),
                    "seed": result.get("seed", seed)
                }
            else:
                # Direct binary image response
                image_bytes = response.content
                metadata = {
                    "model": "stable-diffusion-xl-1024-v1-0",
                    "finish_reason": "SUCCESS",
                    "seed": seed
                }
            
            return image_bytes, metadata
    
    async def remove_background(
        self,
        image_data: bytes,
        output_format: str = "png"
    ) -> Tuple[bytes, dict]:
        """
        Remove background from an image
        
        Args:
            image_data: Original image bytes
            output_format: Output format (png, webp)
        
        Returns:
            Tuple of (edited_image_bytes, metadata_dict)
        """
        endpoint = f"{self.base_url}/stable-image/edit/remove-background"
        
        files = {
            "image": ("image.png", image_data, "image/png")
        }
        
        data = {
            "output_format": output_format
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                headers=self.headers,
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                error_detail = response.text if response.content else "Unknown error"
                raise Exception(f"Stability AI API error: {response.status_code} - {error_detail}")
            
            result = response.json()
            
            if "image" in result:
                image_bytes = base64.b64decode(result["image"])
            else:
                raise Exception("No image data in Stability AI response")
            
            metadata = {
                "model": "stable-diffusion-xl-1024-v1-0",
                "finish_reason": result.get("finish_reason", "SUCCESS")
            }
            
            return image_bytes, metadata
    
    async def search_and_replace(
        self,
        image_data: bytes,
        search_prompt: str,
        prompt: str,
        negative_prompt: Optional[str] = None,
        seed: int = 0,
        output_format: str = "png"
    ) -> Tuple[bytes, dict]:
        """
        Search for an object and replace it with something else
        
        Args:
            image_data: Original image bytes
            search_prompt: What to search for and replace
            prompt: What to replace it with
            negative_prompt: What to avoid
            seed: Random seed
            output_format: Output format
        
        Returns:
            Tuple of (edited_image_bytes, metadata_dict)
        """
        endpoint = f"{self.base_url}/stable-image/edit/search-and-replace"
        
        files = {
            "image": ("image.png", image_data, "image/png")
        }
        
        data = {
            "search_prompt": search_prompt,
            "prompt": prompt,
            "output_format": output_format,
            "seed": seed
        }
        
        if negative_prompt:
            data["negative_prompt"] = negative_prompt
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                headers=self.headers,
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                error_detail = response.text if response.content else "Unknown error"
                raise Exception(f"Stability AI API error: {response.status_code} - {error_detail}")
            
            result = response.json()
            
            if "image" in result:
                image_bytes = base64.b64decode(result["image"])
            else:
                raise Exception("No image data in Stability AI response")
            
            metadata = {
                "model": "stable-diffusion-xl-1024-v1-0",
                "finish_reason": result.get("finish_reason", "SUCCESS"),
                "seed": result.get("seed", seed)
            }
            
            return image_bytes, metadata
    
    async def outpaint_image(
        self,
        image_data: bytes,
        prompt: str,
        left: int = 0,
        right: int = 0,
        up: int = 0,
        down: int = 0,
        creativity: float = 0.5,
        seed: int = 0,
        output_format: str = "png"
    ) -> Tuple[bytes, dict]:
        """
        Extend image borders with AI-generated content (outpainting)
        
        Args:
            image_data: Original image bytes
            prompt: Description of what to generate in extended areas
            left: Pixels to extend on left (0-2000)
            right: Pixels to extend on right (0-2000)
            up: Pixels to extend on top (0-2000)
            down: Pixels to extend on bottom (0-2000)
            creativity: How creative to be (0.0-1.0)
            seed: Random seed
            output_format: Output format
        
        Returns:
            Tuple of (edited_image_bytes, metadata_dict)
        """
        endpoint = f"{self.base_url}/stable-image/edit/outpaint"
        
        files = {
            "image": ("image.png", image_data, "image/png")
        }
        
        data = {
            "prompt": prompt,
            "left": left,
            "right": right,
            "up": up,
            "down": down,
            "creativity": creativity,
            "seed": seed,
            "output_format": output_format
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                headers=self.headers,
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                error_detail = response.text if response.content else "Unknown error"
                raise Exception(f"Stability AI API error: {response.status_code} - {error_detail}")
            
            result = response.json()
            
            if "image" in result:
                image_bytes = base64.b64decode(result["image"])
            else:
                raise Exception("No image data in Stability AI response")
            
            metadata = {
                "model": "stable-diffusion-xl-1024-v1-0",
                "finish_reason": result.get("finish_reason", "SUCCESS"),
                "seed": result.get("seed", seed)
            }
            
            return image_bytes, metadata
    
    async def erase_objects(
        self,
        image_data: bytes,
        mask_data: bytes,
        seed: int = 0,
        output_format: str = "png"
    ) -> Tuple[bytes, dict]:
        """
        Erase objects from image using mask (removes without replacement)
        
        Args:
            image_data: Original image bytes
            mask_data: Mask image bytes (white areas will be erased)
            seed: Random seed
            output_format: Output format
        
        Returns:
            Tuple of (edited_image_bytes, metadata_dict)
        """
        endpoint = f"{self.base_url}/stable-image/edit/erase"
        
        files = {
            "image": ("image.png", image_data, "image/png"),
            "mask": ("mask.png", mask_data, "image/png")
        }
        
        data = {
            "seed": seed,
            "output_format": output_format
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                headers=self.headers,
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                error_detail = response.text if response.content else "Unknown error"
                raise Exception(f"Stability AI API error: {response.status_code} - {error_detail}")
            
            result = response.json()
            
            if "image" in result:
                image_bytes = base64.b64decode(result["image"])
            else:
                raise Exception("No image data in Stability AI response")
            
            metadata = {
                "model": "stable-diffusion-xl-1024-v1-0",
                "finish_reason": result.get("finish_reason", "SUCCESS"),
                "seed": result.get("seed", seed)
            }
            
            return image_bytes, metadata
    
    async def upscale_image(
        self,
        image_data: bytes,
        prompt: str,
        negative_prompt: Optional[str] = None,
        creativity: float = 0.35,
        seed: int = 0,
        output_format: str = "png"
    ) -> Tuple[bytes, dict]:
        """
        Creative upscaling - enhance and upscale image with AI
        
        Args:
            image_data: Original image bytes
            prompt: Description to guide upscaling
            negative_prompt: What to avoid
            creativity: How much creative freedom (0.0-0.35 recommended)
            seed: Random seed
            output_format: Output format
        
        Returns:
            Tuple of (edited_image_bytes, metadata_dict)
        """
        endpoint = f"{self.base_url}/stable-image/upscale/creative"
        
        files = {
            "image": ("image.png", image_data, "image/png")
        }
        
        data = {
            "prompt": prompt,
            "creativity": creativity,
            "seed": seed,
            "output_format": output_format
        }
        
        if negative_prompt:
            data["negative_prompt"] = negative_prompt
        
        async with httpx.AsyncClient(timeout=90.0) as client:  # Longer timeout for upscaling
            response = await client.post(
                endpoint,
                headers=self.headers,
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                error_detail = response.text if response.content else "Unknown error"
                raise Exception(f"Stability AI API error: {response.status_code} - {error_detail}")
            
            result = response.json()
            
            if "image" in result:
                image_bytes = base64.b64decode(result["image"])
            else:
                raise Exception("No image data in Stability AI response")
            
            metadata = {
                "model": "sd3-large-turbo",
                "finish_reason": result.get("finish_reason", "SUCCESS"),
                "seed": result.get("seed", seed)
            }
            
            return image_bytes, metadata
    
    async def sketch_to_image(
        self,
        image_data: bytes,
        prompt: str,
        negative_prompt: Optional[str] = None,
        control_strength: float = 0.7,
        seed: int = 0,
        output_format: str = "png"
    ) -> Tuple[bytes, dict]:
        """
        Convert sketch/drawing to realistic image
        
        Args:
            image_data: Sketch/drawing image bytes
            prompt: Description of what the sketch represents
            negative_prompt: What to avoid
            control_strength: How closely to follow sketch (0.0-1.0)
            seed: Random seed
            output_format: Output format
        
        Returns:
            Tuple of (edited_image_bytes, metadata_dict)
        """
        endpoint = f"{self.base_url}/stable-image/control/sketch"
        
        files = {
            "image": ("image.png", image_data, "image/png")
        }
        
        data = {
            "prompt": prompt,
            "control_strength": control_strength,
            "seed": seed,
            "output_format": output_format
        }
        
        if negative_prompt:
            data["negative_prompt"] = negative_prompt
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                headers=self.headers,
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                error_detail = response.text if response.content else "Unknown error"
                raise Exception(f"Stability AI API error: {response.status_code} - {error_detail}")
            
            result = response.json()
            
            if "image" in result:
                image_bytes = base64.b64decode(result["image"])
            else:
                raise Exception("No image data in Stability AI response")
            
            metadata = {
                "model": "sd3-large-turbo",
                "finish_reason": result.get("finish_reason", "SUCCESS"),
                "seed": result.get("seed", seed)
            }
            
            return image_bytes, metadata
    
    def estimate_cost_credits(self, operation_type: str) -> float:
        """
        Estimate the cost in Stability AI credits for an operation
        
        Args:
            operation_type: Type of operation (inpainting, background_removal, etc.)
        
        Returns:
            Estimated cost in credits
        """
        # These are approximate costs - adjust based on actual Stability AI pricing
        cost_map = {
            "inpainting": 3.0,
            "background_removal": 2.0,
            "search_replace": 3.0,
            "outpainting": 3.0,
            "upscaling": 6.5,  # More expensive due to higher resolution
            "erase": 2.0,
            "sketch_to_image": 3.0
        }
        
        return cost_map.get(operation_type, 3.0)
