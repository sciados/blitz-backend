"""Simple PIL-based text overlay - replacing Tkinter version"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import List, Optional
import logging
import random
import time
import base64
import httpx
from io import BytesIO
import hashlib
import os
import glob

from app.db.session import get_db
from app.db.models import User, Campaign, GeneratedImage, ProductIntelligence
from app.auth import get_current_user
from app.schemas import (
    ImageGenerateRequest,
    ImageBatchRequest,
    ImageVariationRequest,
    ImageResponse,
    ImageListResponse,
    ImageDeleteResponse,
    ImageUpgradeRequest,
    ImageSaveDraftRequest,
    ImageTextOverlayRequest,
    ImageTextOverlayResponse
)
from app.services.image_generator import ImageGenerator, ImageGenerationResult
from app.services.image_prompt_builder import ImagePromptBuilder
from app.services.storage_r2 import r2_storage
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

def _hex_to_rgb(hex_color: str):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def _find_font_file(font_family: str):
    """Find TTF font file for given font family."""
    font_name = font_family.lower().strip()
    font_dirs = ["/app/app/fonts", "/tmp/fonts"]

    # Search in directories
    for font_dir in font_dirs:
        if os.path.exists(font_dir):
            # Find all .ttf files recursively
            for ttf_file in glob.glob(os.path.join(font_dir, "**/*.ttf"), recursive=True):
                font_basename = os.path.basename(ttf_file).lower()
                font_name_only = os.path.splitext(font_basename)[0]

                # Normalize for comparison
                font_name_normalized = font_name.replace(" ", "").replace("-", "").replace("_", "")
                font_name_only_normalized = font_name_only.replace("-", "").replace("_", "")

                # Check if normalized font name matches
                if font_name_normalized in font_name_only_normalized or font_name_only_normalized in font_name_normalized:
                    logger.info(f"✅ Font matched: '{font_family}' -> '{ttf_file}'")
                    return ttf_file

    logger.warning(f"❌ Font not found: '{font_family}', using default")
    return None

async def add_text_overlay_pil(
    request: ImageTextOverlayRequest,
    current_user: User,
    db: AsyncSession
):
    """Add text overlay to an image using PIL - SIMPLE VERSION."""
    # Verify campaign ownership if campaign_id is provided
    campaign = None
    if request.campaign_id:
        result = await db.execute(
            select(Campaign).where(
                Campaign.id == request.campaign_id,
                Campaign.user_id == current_user.id
            )
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

    try:
        # Download image from URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            image_response = await client.get(request.image_url)
            image_response.raise_for_status()
            image_data = image_response.content

        # Open image from bytes
        image = Image.open(BytesIO(image_data)).convert("RGBA")

        logger.info(f"🎨 Processing {len(request.text_layers)} text layer(s) using PIL")
        logger.info(f"🖼️ Original image size: {image.width}x{image.height}")

        # Create draw object
        draw = ImageDraw.Draw(image)

        # Process each text layer
        for text_layer_config in request.text_layers:
            # Use ABSOLUTE pixel coordinates
            x = int(text_layer_config.x)
            y = int(text_layer_config.y)
            font_size = int(text_layer_config.font_size)

            logger.info(f"🎨 Drawing text: '{text_layer_config.text}' at ({x}, {y}), size={font_size}, font={text_layer_config.font_family}")

            # Find and load font
            font_path = _find_font_file(text_layer_config.font_family)
            if font_path:
                font = ImageFont.truetype(font_path, font_size)
            else:
                font = ImageFont.load_default()

            # Convert colors
            color_rgb = _hex_to_rgb(text_layer_config.color)

            # Draw stroke if specified
            if text_layer_config.stroke_width > 0 and text_layer_config.stroke_color:
                stroke_rgb = _hex_to_rgb(text_layer_config.stroke_color)
                stroke_width = int(text_layer_config.stroke_width)
                # Draw stroke by drawing text multiple times with offset
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx*dx + dy*dy <= stroke_width * stroke_width:
                            draw.text(
                                (x + dx, y + dy),
                                text_layer_config.text,
                                font=font,
                                fill=stroke_rgb
                            )

            # Draw main text
            draw.text(
                (x, y),
                text_layer_config.text,
                font=font,
                fill=color_rgb
            )

        logger.info(f"✅ Text overlay complete")

        # Convert back to RGB
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            final_image = background
        else:
            final_image = image

        # Save to bytes buffer
        buffer = BytesIO()
        final_image.save(buffer, format="PNG", quality=95)
        composed_image_data = buffer.getvalue()

        # Upload to R2
        r2_key, image_url = await r2_storage.upload_file(
            file_bytes=composed_image_data,
            key=f"campaigns/{request.campaign_id or 0}/generated_images/text_overlay_{int(time.time())}_{hashlib.md5(request.image_url.encode()).hexdigest()[:8]}.png",
            content_type="image/png"
        )

        # Generate thumbnail
        async def generate_thumbnail(image_url: str, campaign_id: int, size: tuple = (256, 256)):
            """Generate thumbnail for image."""
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url)
                    img = Image.open(BytesIO(response.content))
                    img.thumbnail(size, Image.Resampling.LANCZOS)

                    buffer = BytesIO()
                    img.save(buffer, format="JPEG", quality=80)
                    thumbnail_data = buffer.getvalue()

                    _, thumbnail_url = await r2_storage.upload_file(
                        file_bytes=thumbnail_data,
                        key=f"campaigns/{campaign_id}/generated_images/thumbnails/{int(time.time())}_{hashlib.md5(image_url.encode()).hexdigest()[:8]}.jpg",
                        content_type="image/jpeg"
                    )

                    return thumbnail_url
            except Exception as e:
                logger.error(f"Failed to generate thumbnail: {e}")
                return None

        thumbnail_url = await generate_thumbnail(image_url, request.campaign_id or 0)

        # Save to database
        image_record = GeneratedImage(
            campaign_id=request.campaign_id,
            image_type=request.image_type,
            image_url=image_url,
            thumbnail_url=thumbnail_url,
            provider=request.provider,
            model=request.model,
            prompt=request.prompt,
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            meta_data={
                "text_overlay": True,
                "original_image_url": request.image_url,
                "text_layers": [layer.dict() for layer in request.text_layers]
            },
            ai_generation_cost=0.0,
            content_id=None
        )

        db.add(image_record)
        await db.commit()
        await db.refresh(image_record)

        return ImageTextOverlayResponse(
            id=image_record.id,
            campaign_id=image_record.campaign_id,
            image_type=image_record.image_type,
            image_url=image_record.image_url,
            thumbnail_url=image_record.thumbnail_url,
            provider=image_record.provider,
            model=image_record.model,
            prompt=image_record.prompt,
            style=image_record.style,
            aspect_ratio=image_record.aspect_ratio,
            metadata=image_record.meta_data or {},
            ai_generation_cost=0.0,
            created_at=image_record.created_at
        )

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download image: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Text overlay failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text overlay failed: {str(e)}"
        )
