# app/api/images/ai_erase.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import base64
import requests
import io
from PIL import Image
import os
from typing import Optional
import asyncio

router = APIRouter()


class AIEraseRequest(BaseModel):
    image_base64: str
    mask_base64: str


class AIEraseResponse(BaseModel):
    inpainted_image_url: Optional[str] = None
    success: bool = False
    message: Optional[str] = None


@router.post("/api/images/ai-erase", response_model=AIEraseResponse)
async def ai_erase_image(request: AIEraseRequest):
    """
    Remove text/objects from images using AI inpainting (Stability AI)

    Args:
        request: Contains base64-encoded image and mask

    Returns:
        Inpainted image URL
    """
    try:
        # Decode base64 image
        if request.image_base64.startswith('data:image'):
            # Remove data URL prefix if present
            request.image_base64 = request.image_base64.split(',')[1]

        image_data = base64.b64decode(request.image_base64)
        image = Image.open(io.BytesIO(image_data))

        # Decode base64 mask
        if request.mask_base64.startswith('data:image'):
            # Remove data URL prefix if present
            request.mask_base64 = request.mask_base64.split(',')[1]

        mask_data = base64.b64decode(request.mask_base64)
        mask = Image.open(io.BytesIO(mask_data))

        # Ensure mask is grayscale
        if mask.mode != 'L':
            mask = mask.convert('L')

        # Prepare image for Stability AI
        # Convert PIL Image to bytes
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes = image_bytes.getvalue()

        mask_bytes = io.BytesIO()
        mask.save(mask_bytes, format='PNG')
        mask_bytes = mask_bytes.getvalue()

        # Call Stability AI Inpainting API
        api_key = os.getenv('STABILITY_API_KEY')
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="Stability AI API key not configured"
            )

        # Stability AI Inpainting endpoint (v2beta API)
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/edit/inpaint",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            },
            files={
                "image": ("image.png", base64.b64decode(request.image_base64), "image/png"),
                "mask": ("mask.png", base64.b64decode(request.mask_base64), "image/png"),
            },
            data={
                "output_format": "png",
                "prompt": "plain background, seamless fill, no text",  # Describe what should be in the masked area
            }
        )
        print(f"API Response Status: {response.status_code}")
        print(f"API Response: {response.text[:500]}")

        if response.status_code != 200:
            print(f"Stability AI API Error - Status: {response.status_code}")
            print(f"Response: {response.text}")
            try:
                error_json = response.json()
                print(f"Error JSON: {error_json}")
            except:
                pass
            raise HTTPException(
                status_code=500,
                detail=f"Stability AI API error (status {response.status_code}): {response.text}"
            )

        # The v2beta API returns JSON with base64 image
        result = response.json()

        # Extract base64 image from response
        if "image" in result:
            inpainted_base64 = result["image"]
            if not inpainted_base64:
                raise HTTPException(
                    status_code=500,
                    detail="No inpainted image in response"
                )

            # Save to R2 storage
            from app.services.storage_r2 import r2_storage
            import time
            import uuid

            # Generate unique key for R2
            timestamp = int(time.time())
            key = f"ai-erased/erased_{uuid.uuid4().hex[:8]}_{timestamp}.png"

            # Convert base64 to bytes
            inpainted_bytes = base64.b64decode(inpainted_base64)

            # Upload to R2
            _, inpainted_image_url = await r2_storage.upload_file(
                file_bytes=inpainted_bytes,
                key=key,
                content_type="image/png"
            )

            return AIEraseResponse(
                inpainted_image_url=inpainted_image_url,
                success=True,
                message="Successfully erased text/objects"
            )
        else:
            print(f"Response structure: {result}")
            raise HTTPException(
                status_code=500,
                detail="No image field in response"
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in AI erase: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to erase image: {str(e)}"
        )
