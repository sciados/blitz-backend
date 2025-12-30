# app/api/content/images.py

"""Image generation API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
import random
import time
import base64
import httpx
import io

from app.db.session import get_db
from app.db.models import User, Campaign, GeneratedImage, ImageEdit, ProductIntelligence
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
    ImageTextOverlayResponse,
    ImageImageOverlayRequest,
    ImageImageOverlayResponse,
    ImageTrimRequest,
    ImageTrimResponse,
    ImageCompositeRequest,
    ImageCompositeResponse
)
from app.services.image_generator import ImageGenerator, ImageGenerationResult, check_image_has_transparency
from app.services.image_prompt_builder import ImagePromptBuilder
from app.services.storage_r2 import r2_storage
from app.services.text_renderer import TkinterTextRenderer
from app.services.r2_storage import r2_storage
from app.services.usage_limits import get_effective_tier, check_usage_limit, increment_usage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/images", tags=["images"])


@router.put("/{image_id}/url", response_model=ImageResponse)
async def update_image_url(
    image_id: int,
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an image's URL (for operations like AI erase)"""

    # Get the image record with campaign join to verify ownership
    result = await db.execute(
        select(GeneratedImage, Campaign).join(
            Campaign, GeneratedImage.campaign_id == Campaign.id
        ).where(
            GeneratedImage.id == image_id,
            Campaign.user_id == current_user.id
        )
    )
    result_tuple = result.first()

    if not result_tuple:
        raise HTTPException(
            status_code=404,
            detail="Image not found"
        )

    image = result_tuple[0]

    # Update the image URL
    image.image_url = request["image_url"]

    # Update thumbnail if provided
    if "thumbnail_url" in request:
        image.thumbnail_url = request["thumbnail_url"]

    await db.commit()
    await db.refresh(image)

    return ImageResponse(
        id=image.id,
        campaign_id=image.campaign_id,
        image_type=image.image_type,
        image_url=image.image_url,
        thumbnail_url=image.thumbnail_url,
        provider=image.provider,
        model=image.model,
        prompt=image.prompt,
        style=image.style,
        aspect_ratio=image.aspect_ratio,
        meta_data=image.meta_data,
        created_at=image.created_at
    )


@router.post("/create-from-existing", response_model=ImageResponse)
async def create_image_from_existing(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new image record from an existing one (for edited versions like AI erase)"""

    original_image_id = request["original_image_id"]
    new_image_url = request["new_image_url"]
    campaign_id = request["campaign_id"]

    # Get the original image record with campaign join to verify ownership
    result = await db.execute(
        select(GeneratedImage, Campaign).join(
            Campaign, GeneratedImage.campaign_id == Campaign.id
        ).where(
            GeneratedImage.id == original_image_id,
            Campaign.user_id == current_user.id
        )
    )
    result_tuple = result.first()

    if not result_tuple:
        raise HTTPException(
            status_code=404,
            detail="Original image not found"
        )

    original_image = result_tuple[0]

    # Create a NEW image record with the same metadata but new URL
    # Check if the new image has transparency (background removal creates transparency)
    has_transp = await check_image_has_transparency(new_image_url)

    new_image = GeneratedImage(
        campaign_id=original_image.campaign_id,
        image_type=original_image.image_type,
        image_url=new_image_url,
        # Don't copy thumbnail - will be generated if needed
        thumbnail_url=original_image.thumbnail_url,  # Keep same thumbnail for now
        provider=original_image.provider,
        model=original_image.model,
        prompt=f"[EDITED] {original_image.prompt}",  # Mark as edited
        style=original_image.style,
        aspect_ratio=original_image.aspect_ratio,
        # Track parent-child relationship
        parent_image_id=original_image_id,
        # Background removal creates transparency
        has_transparency=has_transp,
        meta_data={
            **original_image.meta_data,
            "edited_from_image_id": original_image_id,
            "edit_type": "ai_erase",
            "original_created_at": original_image.created_at.isoformat() if original_image.created_at else None,
        },
        ai_generation_cost=0.0,  # No additional cost for editing
    )

    db.add(new_image)
    await db.commit()
    await db.refresh(new_image)

    return ImageResponse(
        id=new_image.id,
        campaign_id=new_image.campaign_id,
        image_type=new_image.image_type,
        image_url=new_image.image_url,
        thumbnail_url=new_image.thumbnail_url,
        provider=new_image.provider,
        model=new_image.model,
        prompt=new_image.prompt,
        style=new_image.style,
        aspect_ratio=new_image.aspect_ratio,
        meta_data=new_image.meta_data,
        created_at=new_image.created_at
    )


@router.post("/campaign", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def add_shared_image_to_campaign(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a shared/stock image to a campaign"""

    campaign_id = request["campaign_id"]
    image_url = request["image_url"]
    prompt = request.get("prompt", "Shared image")
    metadata = request.get("metadata", {})

    # Verify campaign ownership
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Create new image record for the shared image
    new_image = GeneratedImage(
        campaign_id=campaign_id,
        image_type="variation",  # Shared images are variations
        image_url=image_url,
        provider="shared",  # Mark as shared
        model="shared",
        prompt=prompt,
        style="photorealistic",  # Use valid enum value
        aspect_ratio="1:1",  # Default, can be updated later
        has_transparency=False,  # Assume no transparency unless specified
        meta_data={  # Note: Python attribute is meta_data, DB column is metadata
            "source": "shared",
            **metadata
        },
        ai_generation_cost=0.0,  # No cost for shared images
    )

    db.add(new_image)
    await db.commit()
    await db.refresh(new_image)

    return ImageResponse(
        id=new_image.id,
        campaign_id=new_image.campaign_id,
        image_type=new_image.image_type,
        image_url=new_image.image_url,
        thumbnail_url=new_image.thumbnail_url,
        provider=new_image.provider,
        model=new_image.model,
        prompt=new_image.prompt,
        style=new_image.style,
        aspect_ratio=new_image.aspect_ratio,
        metadata=new_image.meta_data,  # Note: Python attribute is meta_data
        created_at=new_image.created_at
    )


# Text Overlay - Simple direct positioning using bbox[1] offset


# Dependency to get ImageGenerator instance
def get_image_generator() -> ImageGenerator:
    """Get ImageGenerator instance."""
    return ImageGenerator()


# Dependency to get ImagePromptBuilder instance
def get_image_prompt_builder() -> ImagePromptBuilder:
    """Get ImagePromptBuilder instance."""
    return ImagePromptBuilder()


@router.post("/generate", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def generate_image(
    request: ImageGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    image_generator: ImageGenerator = Depends(get_image_generator),
    prompt_builder: ImagePromptBuilder = Depends(get_image_prompt_builder)
):
    """Generate image for campaign using saved intelligence or highlight features."""
    # Verify campaign ownership
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

    # OPTIMIZATION: Use highlight_features if provided, skip intelligence query
    intelligence_data = None
    logger.info(f"Campaign ID: {campaign.id}, product_intelligence_id: {campaign.product_intelligence_id}")

    # Extract keywords from highlight_features if provided (Dict with categories)
    extracted_keywords = None
    if request.highlight_features:
        # Extract all keywords from all categories
        all_keywords = []
        if isinstance(request.highlight_features, dict):
            for category, keywords in request.highlight_features.items():
                if keywords and isinstance(keywords, list):
                    all_keywords.extend(keywords)
        extracted_keywords = all_keywords if all_keywords else None
        logger.info(f"Using highlight_features - extracted keywords: {extracted_keywords}")

    # Only fetch intelligence if highlight_features are NOT provided
    if not extracted_keywords and campaign.product_intelligence_id:
        logger.info("No highlight_features provided, fetching intelligence data...")
        result = await db.execute(
            select(ProductIntelligence).where(
                ProductIntelligence.id == campaign.product_intelligence_id
            )
        )
        product_intelligence = result.scalar_one_or_none()
        logger.info(f"ProductIntelligence found: {product_intelligence is not None}")

        if product_intelligence:
            intelligence_data = product_intelligence.intelligence_data
            logger.info(f"Intelligence data keys: {list(intelligence_data.keys()) if intelligence_data else 'None'}")
    elif extracted_keywords:
        logger.info(f"Using highlight_features directly: {extracted_keywords}")
    else:
        logger.info("No intelligence data available and no highlight_features provided")

    # Build prompt using intelligence data or highlight_features
    prompt = prompt_builder.build_prompt(
        campaign_intelligence=intelligence_data,
        image_type=request.image_type,
        user_prompt=request.custom_prompt,
        style=request.style,
        aspect_ratio=request.aspect_ratio,
        quality_boost=request.quality_boost or False,
        highlight_features=extracted_keywords  # Pass extracted list of keywords
    )

    logger.info(f"Generated prompt: {prompt}")
    logger.info(f"Highlight features: {request.highlight_features}")

    # Add testimonial if requested
    if request.use_testimonial:
        prompt = prompt_builder.enhance_with_testimonial(
            base_prompt=prompt,
            testimonial_text=request.use_testimonial,
            author_name="Customer"
        )

    # Add text overlay if requested
    if request.include_text_overlay:
        prompt = prompt_builder.enhance_with_text_overlay(
            base_prompt=prompt,
            text_content=request.include_text_overlay,
            position=request.overlay_position or "center"
        )

    # Add platform-specific enhancements
    if request.platform:
        prompt = prompt_builder.build_social_media_variant(
            base_prompt=prompt,
            platform=request.platform,
            content_type=request.image_type
        )

    # Generate image
    try:
        result = await image_generator.generate_image(
            prompt=prompt,
            image_type=request.image_type,
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            campaign_intelligence=intelligence_data,
            quality_boost=request.quality_boost or False,
            campaign_id=request.campaign_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image generation failed: {str(e)}"
        )

    # Check if the generated image has transparency
    has_transp = await check_image_has_transparency(result.image_url)

    # Save to database
    image_record = GeneratedImage(
        campaign_id=request.campaign_id,
        image_type=request.image_type,
        image_url=result.image_url,
        thumbnail_url=result.thumbnail_url,
        provider=result.provider,
        model=result.model,
        prompt=result.prompt,
        style=request.style,
        aspect_ratio=request.aspect_ratio,
        # New generation - no parent, check transparency
        parent_image_id=None,
        has_transparency=has_transp,
        meta_data=result.metadata,
        ai_generation_cost=result.cost
    )

    db.add(image_record)
    await db.commit()
    await db.refresh(image_record)

    # ========================================================================
    # INCREMENT USAGE AFTER SUCCESSFUL IMAGE GENERATION
    # ========================================================================
    # Check trial/subscription status
    effective_tier = await get_effective_tier(db, current_user.id)

    if effective_tier == "expired":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Your trial has expired. Please upgrade to continue generating images."
        )

    # Check usage limits for image generation
    allowed, message, current_usage, limit = await check_usage_limit(
        db, current_user.id, effective_tier, "ai_image_generations"
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly limit reached for image generation: {message}. Upgrade your plan for higher limits."
        )

    # Increment usage (use the actual cost from generation result)
    await increment_usage(
        db,
        current_user.id,
        "ai_image_generations",
        estimated_cost=result.cost
    )
    logger.info(f"[USAGE] Incremented ai_image_generations for user {current_user.id}, cost: ${result.cost:.4f}")

    return ImageResponse(
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
        ai_generation_cost=image_record.ai_generation_cost,
        content_id=image_record.content_id,
        created_at=image_record.created_at
    )


@router.post("/previews", response_model=List[ImageResponse], status_code=status.HTTP_201_CREATED)
async def preview_images(
    request: ImageGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    image_generator: ImageGenerator = Depends(get_image_generator),
    prompt_builder: ImagePromptBuilder = Depends(get_image_prompt_builder)
):
    """Generate 4 preview/draft images in a batch (free, temporary)."""
    # Verify campaign ownership
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

    # OPTIMIZATION: Use highlight_features if provided, skip intelligence query
    intelligence_data = None

    # Extract keywords from highlight_features if provided (Dict with categories)
    extracted_keywords = None
    if request.highlight_features:
        all_keywords = []
        if isinstance(request.highlight_features, dict):
            for category, keywords in request.highlight_features.items():
                if keywords and isinstance(keywords, list):
                    all_keywords.extend(keywords)
        extracted_keywords = all_keywords if all_keywords else None

    if not extracted_keywords and campaign.product_intelligence_id:
        result = await db.execute(
            select(ProductIntelligence).where(
                ProductIntelligence.id == campaign.product_intelligence_id
            )
        )
        product_intelligence = result.scalar_one_or_none()
        if product_intelligence:
            intelligence_data = product_intelligence.intelligence_data

    # Build prompt - use concise version for preview (free providers)
    prompt = prompt_builder.build_prompt(
        campaign_intelligence=intelligence_data,
        image_type=request.image_type,
        user_prompt=request.custom_prompt,
        style=request.style,
        aspect_ratio=request.aspect_ratio,
        quality_boost=False,  # Preview always uses free/low-cost providers
        concise=True,  # Use shorter prompts for free providers
        highlight_features=extracted_keywords
    )

    # Generate 4 unique drafts with different seeds
    generation_requests = []
    for i in range(4):
        # Generate unique seed for each draft
        random_seed = int(time.time() * 1000000) + random.randint(1, 1000000) + i

        generation_requests.append({
            "prompt": prompt,
            "image_type": request.image_type,
            "style": request.style,
            "aspect_ratio": request.aspect_ratio,
            "campaign_intelligence": intelligence_data,
            "custom_params": {"seed": random_seed}
        })

    # Generate images in batch (NOT saved to database, NOT saved to R2)
    try:
        results = await image_generator.batch_generate(
            requests=generation_requests,
            save_to_r2=False,  # Don't save preview drafts to R2
            campaign_id=request.campaign_id  # Pass campaign_id for proper organization
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image generation failed: {str(e)}"
        )

    # Return image data WITHOUT saving to database
    return [
        ImageResponse(
            id=0,  # No ID since not saved
            campaign_id=request.campaign_id,
            image_type=request.image_type,
            image_url=result.image_url,
            thumbnail_url=result.thumbnail_url,
            provider=result.provider,
            model=result.model,
            prompt=result.prompt,
            style=result.style,
            aspect_ratio=result.aspect_ratio,
            ai_generation_cost=result.cost,
            content_id=None
            # metadata and created_at not provided for drafts - not saved to DB
        )
        for result in results
    ]


@router.post("/preview", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def preview_image(
    request: ImageGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    image_generator: ImageGenerator = Depends(get_image_generator),
    prompt_builder: ImagePromptBuilder = Depends(get_image_prompt_builder)
):
    """Generate preview/draft image without saving to database (free, temporary)."""
    # Verify campaign ownership
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

    # OPTIMIZATION: Use highlight_features if provided, skip intelligence query
    intelligence_data = None

    # Extract keywords from highlight_features if provided (Dict with categories)
    extracted_keywords = None
    if request.highlight_features:
        all_keywords = []
        if isinstance(request.highlight_features, dict):
            for category, keywords in request.highlight_features.items():
                if keywords and isinstance(keywords, list):
                    all_keywords.extend(keywords)
        extracted_keywords = all_keywords if all_keywords else None

    if not extracted_keywords and campaign.product_intelligence_id:
        result = await db.execute(
            select(ProductIntelligence).where(
                ProductIntelligence.id == campaign.product_intelligence_id
            )
        )
        product_intelligence = result.scalar_one_or_none()
        if product_intelligence:
            intelligence_data = product_intelligence.intelligence_data

    # Build prompt - use concise version for preview (free providers)
    prompt = prompt_builder.build_prompt(
        campaign_intelligence=intelligence_data,
        image_type=request.image_type,
        user_prompt=request.custom_prompt,
        style=request.style,
        aspect_ratio=request.aspect_ratio,
        quality_boost=False,  # Preview always uses free/low-cost providers
        concise=True,  # Use shorter prompts for free providers
        highlight_features=extracted_keywords
    )

    # Generate a random seed for unique draft images
    # Using time + random ensures uniqueness across simultaneous requests
    random_seed = int(time.time() * 1000000) + random.randint(1, 1000000)

    # Generate image (NOT saved to database)
    try:
        result = await image_generator.generate_image(
            prompt=prompt,
            save_to_r2=False,  # Preview mode - do not upload to R2
            image_type=request.image_type,
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            campaign_intelligence=intelligence_data,
            quality_boost=False,  # Preview mode - no quality boost
            campaign_id=request.campaign_id,
            custom_params={"seed": random_seed}  # Ensure unique draft each time
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image generation failed: {str(e)}"
        )

    # Return image data WITHOUT saving to database
    return ImageResponse(
        id=0,  # No ID since not saved
        campaign_id=request.campaign_id,
        image_type=request.image_type,
        image_url=result.image_url,
        thumbnail_url=result.thumbnail_url,
        provider=result.provider,
        model=result.model,
        prompt=result.prompt,
        style=result.style,
        aspect_ratio=result.aspect_ratio,
        ai_generation_cost=result.cost,
        content_id=None
        # metadata and created_at not provided for drafts - not saved to DB
    )


@router.post("/save-draft", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def save_draft_image(
    request: ImageSaveDraftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    image_generator: ImageGenerator = Depends(get_image_generator)
):
    """Save a draft image to the library by downloading and storing it."""
    logger.info(f"💾 /save-draft endpoint called")
    logger.info(f"📥 Request data: campaign_id={request.campaign_id}, image_type={request.image_type}, provider={request.provider}")
    logger.info(f"🔍 Image URL type: {'data URL' if request.image_url.startswith('data:') else 'HTTP URL'}, length={len(request.image_url)}")

    # Verify campaign ownership
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == request.campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        logger.error(f"❌ Campaign not found: {request.campaign_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    logger.info(f"✅ Campaign verified: {campaign.name}")

    try:
        # Download the image from the provider URL and save to R2
        logger.info(f"⬇️ Calling image_generator.save_draft_image()...")
        result = await image_generator.save_draft_image(
            image_url=request.image_url,
            campaign_id=request.campaign_id,
            image_type=request.image_type,
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            provider=request.provider,
            model=request.model,
            prompt=request.prompt,
            custom_prompt=request.custom_prompt
        )
        logger.info(f"✅ save_draft_image returned: image_url={result.image_url}, thumbnail_url={result.thumbnail_url}")
    except Exception as e:
        logger.error(f"❌ save_draft_image failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save draft image: {str(e)}"
        )

    # Save to database
    # Merge metadata from request (e.g., is_edited flag) with result metadata
    merged_metadata = {**(result.metadata or {}), **(request.metadata or {})}

    # Check if the draft image has transparency
    has_transp = await check_image_has_transparency(result.image_url)

    logger.info(f"💾 Creating GeneratedImage record...")
    image_record = GeneratedImage(
        campaign_id=request.campaign_id,
        image_type=request.image_type,
        image_url=result.image_url,
        thumbnail_url=result.thumbnail_url,
        provider=result.provider,
        model=result.model,
        prompt=result.prompt,
        style=request.style,
        aspect_ratio=request.aspect_ratio,
        # New generation - no parent, check transparency
        parent_image_id=None,
        has_transparency=has_transp,
        meta_data=merged_metadata,
        ai_generation_cost=0.0,  # Draft images are free
        content_id=None
    )

    db.add(image_record)
    await db.commit()
    await db.refresh(image_record)
    logger.info(f"✅ GeneratedImage saved with id={image_record.id}")

    logger.info(f"📤 Returning ImageResponse: id={image_record.id}, image_url={image_record.image_url}")
    return ImageResponse(
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
        ai_generation_cost=image_record.ai_generation_cost,
        content_id=image_record.content_id,
        created_at=image_record.created_at
    )


@router.get("/proxy")
async def proxy_image(
    url: str,
    current_user: User = Depends(get_current_user)
):
    """
    Proxy image requests to avoid CORS issues with R2.
    Downloads image from R2 and streams it back to the client.
    Accepts either:
    - Full R2 URL: https://pub-xxx.r2.dev/campaigns/28/image.png
    - Just the path: /campaigns/28/image.png
    """
    logger.info(f"📸 Proxying image request: {url[:100]}...")
    logger.info(f"👤 User: {current_user.email}")

    try:
        # If it's just a path, construct the full R2 URL
        full_url = url
        if url.startswith("/"):
            # Remove leading slash and prepend R2 public URL
            r2_public_url = r2_storage.public_url_base
            full_url = f"{r2_public_url}{url}"
            logger.info(f"🔗 Constructed full URL: {full_url}")

        # Download the image from R2 using the centralized utility
        logger.info(f"⬇️ Downloading from R2...")
        image_bytes = await r2_storage.download_from_url(full_url)
        logger.info(f"✅ Downloaded {len(image_bytes)} bytes")

        # Determine content type from URL
        if url.lower().endswith('.png'):
            content_type = "image/png"
        elif url.lower().endswith('.jpg') or url.lower().endswith('.jpeg'):
            content_type = "image/jpeg"
        elif url.lower().endswith('.webp'):
            content_type = "image/webp"
        else:
            content_type = "image/png"  # Default

        # Return the image with proper headers
        from fastapi.responses import StreamingResponse
        logger.info(f"📤 Streaming image back to client...")
        return StreamingResponse(
            iter([image_bytes]),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        logger.error(f"❌ Failed to proxy image: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to proxy image: {str(e)}"
        )


@router.post("/upgrade", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def upgrade_image(
    request: ImageUpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    image_generator: ImageGenerator = Depends(get_image_generator)
):
    """Enhance a draft image to premium quality."""
    # Verify campaign ownership
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

    # Get intelligence data
    intelligence_data = None
    if campaign.product_intelligence_id:
        result = await db.execute(
            select(ProductIntelligence).where(
                ProductIntelligence.id == campaign.product_intelligence_id
            )
        )
        product_intelligence = result.scalar_one_or_none()
        if product_intelligence:
            intelligence_data = product_intelligence.intelligence_data

    # Build enhancement prompt
    prompt = request.custom_prompt or "Enhance and improve this image quality, higher resolution, detailed, sharp, premium"

    # File Organization for Enhancement:
    # 1. Download draft and save to: campaignforge-storage/campaigns/{id}/generated_files/temp/  (intermediate)
    # 2. Enhance image and save to: campaignforge-storage/campaigns/{id}/generated_files/         (final result)
    # This keeps the main folder clean with only final enhanced images
    logger.info(f"💾 Preparing draft for enhancement...")
    try:
        import httpx
        import hashlib
        import time
        import re

        # Handle different URL types for draft images
        draft_url = request.draft_image_url
        logger.info(f"📏 Original draft URL length: {len(request.draft_image_url)} chars")

        # Check if this is a data URL (base64-encoded image)
        if request.draft_image_url.startswith("data:image/"):
            # Data URL - extract base64 data directly (no HTTP download needed)
            logger.info(f"🔍 Detected data URL (base64-encoded image)")
            try:
                # Extract base64 data from data URL format: data:image/webp;base64,<data>
                if ";base64," in request.draft_image_url:
                    base64_data = request.draft_image_url.split(";base64,")[1]
                    image_data = base64.b64decode(base64_data)
                    logger.info(f"✅ Decoded {len(image_data)} bytes from base64 data URL")
                else:
                    raise Exception("Data URL does not contain base64 data")
            except Exception as e:
                logger.error(f"❌ Failed to decode data URL: {e}")
                raise Exception(f"Failed to decode data URL: {str(e)}")
        else:
            # Regular HTTP URL - download via HTTP client
            if "image.pollinations.ai" in request.draft_image_url and len(request.draft_image_url) > 200:
                seed_match = re.search(r'seed=(\d+)', request.draft_image_url)
                width_match = re.search(r'width=(\d+)', request.draft_image_url)
                height_match = re.search(r'height=(\d+)', request.draft_image_url)

                if seed_match and width_match and height_match:
                    seed = seed_match.group(1)
                    width = width_match.group(1)
                    height = height_match.group(1)
                    # Create minimal URL with just seed and dimensions
                    draft_url = f"https://image.pollinations.ai/prompt/IMG?width={width}&height={height}&seed={seed}&nologo=true"
                    logger.info(f"✂️ Shortened Pollinations URL: {len(request.draft_image_url)} → {len(draft_url)} chars")
                else:
                    # Regex didn't match - log warning but try original URL
                    logger.warning(f"⚠️ Could not extract parameters from Pollinations URL (seed={bool(seed_match)}, width={bool(width_match)}, height={bool(height_match)})")
                    logger.warning(f"⚠️ Will attempt with original URL, may fail if too long")
            elif len(request.draft_image_url) > 500:
                # Generic long URL warning for non-Pollinations URLs
                logger.warning(f"⚠️ Very long URL detected ({len(request.draft_image_url)} chars) from provider: {request.draft_image_url[:50]}...")

            # Download with extended timeout for potentially slow providers
            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.info(f"⬇️ Downloading draft image from: {draft_url[:100]}...")
                try:
                    img_response = await client.get(draft_url)
                    img_response.raise_for_status()
                    image_data = img_response.content
                    logger.info(f"✅ Downloaded {len(image_data)} bytes")
                except httpx.HTTPError as e:
                    logger.error(f"❌ HTTP error downloading draft: {e}")
                    raise Exception(f"Failed to download draft image: {str(e)}")

        # Upload to temp folder using centralized utility
        draft_filename = f"draft_for_enhancement_{int(time.time())}_{hashlib.md5(request.draft_image_url.encode()).hexdigest()[:8]}.png"
        _, draft_url = await r2_storage.upload_image(
            campaign_id=request.campaign_id,
            folder="temp",
            filename=draft_filename,
            image_bytes=image_data,
            content_type="image/png"
        )
        logger.info(f"✅ Draft saved to temp folder")
    except Exception as e:
        logger.error(f"Failed to save draft to temp: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save draft: {str(e)}"
        )

    # Now enhance the image using the draft URL
    try:
        result = await image_generator.enhance_image(
            base_image_url=draft_url,
            prompt=prompt,
            image_type=request.image_type,  # Preserve the original image type
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            quality_boost=True,  # Enhancement always uses premium providers
            campaign_id=request.campaign_id,
            save_to_r2=True  # Saves enhanced result to generated_images folder
        )
    except Exception as e:
        logger.error(f"Image enhancement failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image enhancement failed: {str(e)}"
        )

    # Check if the enhanced image has transparency
    has_transp = await check_image_has_transparency(result.image_url)

    # Save enhanced image to database
    image_record = GeneratedImage(
        campaign_id=request.campaign_id,
        image_type=request.image_type,  # Preserve the original image type
        image_url=result.image_url,
        thumbnail_url=result.thumbnail_url,
        provider=result.provider,
        model=result.model,
        prompt=result.prompt,
        style=request.style,
        aspect_ratio=request.aspect_ratio,
        # Enhancement - track parent relationship
        parent_image_id=None,  # Could be enhanced to track original if available
        has_transparency=has_transp,
        meta_data=result.metadata,
        ai_generation_cost=result.cost,
        content_id=None
    )

    db.add(image_record)
    await db.commit()
    await db.refresh(image_record)

    # ========================================================================
    # INCREMENT USAGE AFTER SUCCESSFUL IMAGE UPGRADE/ENHANCEMENT
    # ========================================================================
    # Increment usage for the enhanced image
    await increment_usage(
        db,
        current_user.id,
        "ai_image_generations",
        estimated_cost=result.cost
    )
    logger.info(f"[USAGE] Incremented ai_image_generations for user {current_user.id} (upgrade), cost: ${result.cost:.4f}")

    return ImageResponse(
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
        ai_generation_cost=image_record.ai_generation_cost,
        content_id=image_record.content_id,
        created_at=image_record.created_at
    )


@router.post("/batch-generate", response_model=List[ImageResponse], status_code=status.HTTP_201_CREATED)
async def batch_generate_images(
    request: ImageBatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    image_generator: ImageGenerator = Depends(get_image_generator),
    prompt_builder: ImagePromptBuilder = Depends(get_image_prompt_builder)
):
    """Generate multiple images in parallel for a campaign."""
    # Verify campaign ownership
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

    # OPTIMIZATION: Use highlight_features if provided, skip intelligence query
    intelligence_data = None

    # Extract keywords from highlight_features if provided (Dict with categories)
    extracted_keywords = None
    if request.highlight_features:
        all_keywords = []
        if isinstance(request.highlight_features, dict):
            for category, keywords in request.highlight_features.items():
                if keywords and isinstance(keywords, list):
                    all_keywords.extend(keywords)
        extracted_keywords = all_keywords if all_keywords else None

    if not extracted_keywords and campaign.product_intelligence_id:
        result = await db.execute(
            select(ProductIntelligence).where(
                ProductIntelligence.id == campaign.product_intelligence_id
            )
        )
        product_intelligence = result.scalar_one_or_none()
        if product_intelligence:
            intelligence_data = product_intelligence.intelligence_data

    # Build generation requests
    generation_requests = []
    for img_request in request.images:
        # Build prompt
        prompt = prompt_builder.build_prompt(
            campaign_intelligence=intelligence_data,
            image_type=img_request["image_type"],
            user_prompt=img_request.get("custom_prompt"),
            style=img_request.get("style", "photorealistic"),
            aspect_ratio=img_request.get("aspect_ratio", "1:1"),
            highlight_features=extracted_keywords
        )

        generation_requests.append({
            "prompt": prompt,
            "image_type": img_request["image_type"],
            "style": img_request.get("style", "photorealistic"),
            "aspect_ratio": img_request.get("aspect_ratio", "1:1"),
            "campaign_intelligence": intelligence_data,
            "custom_params": img_request.get("custom_params", {})
        })

    # Generate images in batch
    try:
        results = await image_generator.batch_generate(
            requests=generation_requests,
            save_to_r2=True,  # Save batch-generated images to R2
            campaign_id=request.campaign_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch image generation failed: {str(e)}"
        )

    # Save to database
    image_records = []
    for i, result in enumerate(results):
        # Check if the generated image has transparency
        has_transp = await check_image_has_transparency(result.image_url)

        image_record = GeneratedImage(
            campaign_id=request.campaign_id,
            image_type=generation_requests[i]["image_type"],
            image_url=result.image_url,
            thumbnail_url=result.thumbnail_url,
            provider=result.provider,
            model=result.model,
            prompt=result.prompt,
            style=result.style,
            aspect_ratio=result.aspect_ratio,
            # New generation - no parent, check transparency
            parent_image_id=None,
            has_transparency=has_transp,
            meta_data=result.metadata,
            ai_generation_cost=result.cost
        )

        db.add(image_record)
        image_records.append(image_record)

    await db.commit()

    # Refresh all records
    for record in image_records:
        await db.refresh(record)

    # ========================================================================
    # INCREMENT USAGE AFTER SUCCESSFUL BATCH IMAGE GENERATION
    # ========================================================================
    # Check trial/subscription status
    effective_tier = await get_effective_tier(db, current_user.id)

    if effective_tier == "expired":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Your trial has expired. Please upgrade to continue generating images."
        )

    # Calculate total cost for all images
    total_cost = sum(result.cost for result in results)

    # Increment usage by number of images generated
    # (each image counts as one generation)
    await increment_usage(
        db,
        current_user.id,
        "ai_image_generations",
        estimated_cost=total_cost
    )
    logger.info(f"[USAGE] Incremented ai_image_generations for user {current_user.id} ({len(results)} images), cost: ${total_cost:.4f}")

    return [
        ImageResponse(
            id=record.id,
            campaign_id=record.campaign_id,
            image_type=record.image_type,
            image_url=record.image_url,
            thumbnail_url=record.thumbnail_url,
            provider=record.provider,
            model=record.model,
            prompt=record.prompt,
            style=record.style,
            aspect_ratio=record.aspect_ratio,
            metadata=record.meta_data or {},
            ai_generation_cost=record.ai_generation_cost,
            content_id=record.content_id,
            created_at=record.created_at
        )
        for record in image_records
    ]


@router.get("/", response_model=List[ImageResponse])
async def list_all_user_images(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all generated images for the current user across all campaigns."""
    # Get all images for user's campaigns
    result = await db.execute(
        select(GeneratedImage)
        .join(Campaign)
        .where(Campaign.user_id == current_user.id)
        .order_by(GeneratedImage.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    images = result.scalars().all()

    return [
        ImageResponse(
            id=image.id,
            campaign_id=image.campaign_id,
            image_type=image.image_type,
            image_url=image.image_url,
            thumbnail_url=image.thumbnail_url,
            provider=image.provider,
            model=image.model,
            prompt=image.prompt,
            style=image.style,
            aspect_ratio=image.aspect_ratio,
            metadata=image.meta_data or {},
            ai_generation_cost=image.ai_generation_cost,
            content_id=image.content_id,
            created_at=image.created_at
        )
        for image in images
    ]


@router.get("/campaign/{campaign_id}", response_model=ImageListResponse)
async def list_campaign_images(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    image_type: Optional[str] = Query(None, description="Filter by image type"),
    has_transparency: Optional[bool] = Query(None, description="Filter by transparency (true=transparent only, false=opaque only)"),
    parent_image_id: Optional[int] = Query(None, description="Filter by parent image ID"),
    skip: int = 0,
    limit: int = 50
):
    """List all images for a campaign from both generated_images and image_edits tables."""
    # Verify campaign ownership
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Query generated_images table
    gen_query = select(GeneratedImage).where(GeneratedImage.campaign_id == campaign_id)
    if image_type:
        gen_query = gen_query.where(GeneratedImage.image_type == image_type)
    if has_transparency is not None:
        gen_query = gen_query.where(GeneratedImage.has_transparency == has_transparency)
    if parent_image_id is not None:
        gen_query = gen_query.where(GeneratedImage.parent_image_id == parent_image_id)

    # Get results from generated_images
    gen_result = await db.execute(gen_query.order_by(GeneratedImage.created_at.desc()))
    gen_images = gen_result.scalars().all()

    # Query image_edits table using raw SQL (no SQLAlchemy model exists)
    from sqlalchemy import text

    edit_sql = text("""
        SELECT id, user_id, campaign_id, original_image_path, edited_image_path,
               operation_type, operation_params, stability_model, api_cost_credits,
               processing_time_ms, success, error_message, parent_image_id,
               has_transparency, created_at, updated_at
        FROM image_edits
        WHERE campaign_id = :campaign_id
    """)
    params = {"campaign_id": campaign_id}

    if has_transparency is not None:
        edit_sql = text("""
            SELECT id, user_id, campaign_id, original_image_path, edited_image_path,
                   operation_type, operation_params, stability_model, api_cost_credits,
                   processing_time_ms, success, error_message, parent_image_id,
                   has_transparency, created_at, updated_at
            FROM image_edits
            WHERE campaign_id = :campaign_id AND has_transparency = :has_transparency
        """)
        params["has_transparency"] = has_transparency

    edit_result = await db.execute(edit_sql, params)
    edit_records = edit_result.fetchall()

    # Combine and convert results
    all_images = []

    # Add generated images
    for image in gen_images:
        all_images.append(
            ImageResponse(
                id=image.id,
                campaign_id=image.campaign_id,
                image_type=image.image_type,
                image_url=image.image_url,
                thumbnail_url=image.thumbnail_url,
                provider=image.provider,
                model=image.model,
                prompt=image.prompt,
                style=image.style,
                aspect_ratio=image.aspect_ratio,
                parent_image_id=image.parent_image_id,
                has_transparency=image.has_transparency,
                metadata=image.meta_data or {},
                ai_generation_cost=image.ai_generation_cost,
                content_id=image.content_id,
                created_at=image.created_at
            )
        )

    # Add image edits (convert to ImageResponse format)
    for edit in edit_records:
        # Map operation_type to a valid image_type
        # Edited images are variations of the original, so we use "variation"
        image_type = "variation"

        all_images.append(
            ImageResponse(
                id=edit.id,
                campaign_id=edit.campaign_id,
                image_type=image_type,
                image_url=edit.edited_image_path,
                thumbnail_url=None,  # image_edits doesn't have thumbnail_url
                provider=edit.stability_model or "stability",
                model=edit.stability_model or "unknown",
                prompt=f"Edited: {edit.operation_type}",
                style=None,
                aspect_ratio=None,
                parent_image_id=edit.parent_image_id,
                has_transparency=edit.has_transparency,
                metadata=edit.operation_params or {},
                ai_generation_cost=float(edit.api_cost_credits) if edit.api_cost_credits else 0.0,
                content_id=None,
                created_at=edit.created_at
            )
        )

    # Sort all images by created_at descending
    all_images.sort(key=lambda x: x.created_at, reverse=True)

    # Apply pagination
    total = len(all_images)
    paginated_images = all_images[skip:skip + limit]

    return ImageListResponse(
        images=paginated_images,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )


@router.get("/fonts", response_model=List[dict])
async def list_available_fonts():
    """List all available TTF fonts in the fonts directory."""
    import os
    import glob
    from pathlib import Path

    # Search in multiple possible locations
    font_dirs = ["/app/app/fonts"]
    fonts = []
    
    for font_dir in font_dirs:
        if os.path.exists(font_dir):
            logger.info(f"📂 Found fonts directory: {font_dir}")
            
            # Find all .ttf files recursively
            for ttf_file in glob.glob(os.path.join(font_dir, "**/*.ttf"), recursive=True):
                # Get relative path from fonts directory
                rel_path = os.path.relpath(ttf_file, font_dir)
                # Get just the filename without extension
                filename = os.path.basename(ttf_file)
                name_without_ext = os.path.splitext(filename)[0]

                # Create a friendly display name
                # Replace underscores and dashes with spaces, title case
                display_name = name_without_ext.replace("_", " ").replace("-", " ").title()

                fonts.append({
                    "value": display_name,  # Used in frontend
                    "label": display_name,  # Display label
                    "filename": filename,   # Actual filename
                    "path": rel_path,       # Relative path
                    "full_path": ttf_file   # Full filesystem path
                })
            # Found fonts, stop searching
            break
        else:
            logger.info(f"⚠️ Fonts directory not found: {font_dir}")
    
    # Sort alphabetically by label
    fonts.sort(key=lambda x: x["label"])

    logger.info(f"📝 Found {len(fonts)} fonts: {[f['label'] for f in fonts]}")

    return fonts


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a single generated image by ID."""
    # Get image and verify ownership
    result = await db.execute(
        select(GeneratedImage)
        .join(Campaign)
        .where(
            GeneratedImage.id == image_id,
            Campaign.user_id == current_user.id
        )
    )
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    return ImageResponse(
        id=image.id,
        campaign_id=image.campaign_id,
        image_type=image.image_type,
        image_url=image.image_url,
        thumbnail_url=image.thumbnail_url,
        provider=image.provider,
        model=image.model,
        style=image.style,
        aspect_ratio=image.aspect_ratio,
        prompt=image.prompt,
        metadata=image.meta_data or {},
        ai_generation_cost=image.ai_generation_cost,
        content_id=image.content_id,
        created_at=image.created_at
    )


@router.delete("/{image_id}", response_model=ImageDeleteResponse)
async def delete_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete generated image."""
    # Get image and verify ownership
    result = await db.execute(
        select(GeneratedImage)
        .join(Campaign)
        .where(
            GeneratedImage.id == image_id,
            Campaign.user_id == current_user.id
        )
    )
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    await db.delete(image)
    await db.commit()

    return ImageDeleteResponse(
        message="Image deleted successfully",
        deleted_id=image_id
    )


@router.post("/{image_id}/variations", response_model=List[ImageResponse])
async def create_variations(
    image_id: int,
    request: ImageVariationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    image_generator: ImageGenerator = Depends(get_image_generator)
):
    """Create variations of an existing image."""
    # Get base image and verify ownership
    result = await db.execute(
        select(GeneratedImage)
        .join(Campaign)
        .where(
            GeneratedImage.id == image_id,
            Campaign.user_id == current_user.id
        )
    )
    base_image = result.scalar_one_or_none()

    if not base_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Base image not found"
        )

    # Create variations
    try:
        results = await image_generator.create_variations(
            base_image_url=base_image.image_url,
            base_prompt=base_image.prompt,
            num_variations=request.num_variations,
            variation_strength=request.variation_strength
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image variation failed: {str(e)}"
        )

    # Save variations to database
    variation_records = []
    for result in results:
        image_record = GeneratedImage(
            campaign_id=base_image.campaign_id,
            image_type="variation",
            image_url=result.image_url,
            thumbnail_url=result.thumbnail_url,
            provider=result.provider,
            model=result.model,
            prompt=result.prompt,
            style=result.style,
            aspect_ratio=result.aspect_ratio,
            # Variation - track parent relationship
            parent_image_id=image_id,
            has_transparency=base_image.has_transparency,
            meta_data={**result.metadata, "base_image_id": image_id},
            ai_generation_cost=result.cost,
            content_id=base_image.content_id
        )

        db.add(image_record)
        variation_records.append(image_record)

    await db.commit()

    # Refresh all records
    for record in variation_records:
        await db.refresh(record)

    # ========================================================================
    # INCREMENT USAGE AFTER SUCCESSFUL IMAGE VARIATIONS
    # ========================================================================
    # Calculate total cost for all variations
    total_cost = sum(result.cost for result in results)

    # Increment usage by number of variations created
    await increment_usage(
        db,
        current_user.id,
        "ai_image_generations",
        estimated_cost=total_cost
    )
    logger.info(f"[USAGE] Incremented ai_image_generations for user {current_user.id} ({len(results)} variations), cost: ${total_cost:.4f}")

    return [
        ImageResponse(
            id=record.id,
            campaign_id=record.campaign_id,
            image_type=record.image_type,
            image_url=record.image_url,
            thumbnail_url=record.thumbnail_url,
            provider=record.provider,
            model=record.model,
            prompt=record.prompt,
            style=record.style,
            aspect_ratio=record.aspect_ratio,
            metadata=record.meta_data or {},
            ai_generation_cost=record.ai_generation_cost,
            content_id=record.content_id,
            created_at=record.created_at
        )
        for record in variation_records
    ]



@router.post("/text-overlay", response_model=ImageTextOverlayResponse, status_code=status.HTTP_201_CREATED)
async def add_text_overlay(
    request: ImageTextOverlayRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add text overlay to an image using PIL - SIMPLE VERSION."""
    from PIL import Image, ImageDraw, ImageFont
    import httpx
    from io import BytesIO
    import hashlib
    import time
    import os
    import glob

    # Cache for font files to avoid repeated searches
    _FONT_CACHE = {}

    # Pre-build font cache on first use
    def _build_font_cache():
        """Build a cache of all available font files."""
        if _FONT_CACHE:
            return  # Already built

        font_dirs = ["/app/app/fonts", "/tmp/fonts"]
        logger.info("🔍 Building font cache...")

        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                # Find all .ttf files recursively
                for ttf_file in glob.glob(os.path.join(font_dir, "**/*.ttf"), recursive=True):
                    font_basename = os.path.basename(ttf_file).lower()
                    font_name_only = os.path.splitext(font_basename)[0]

                    # Normalize for comparison
                    font_name_normalized = font_name_only.replace("-", "").replace("_", "")

                    # Store in cache (lowercase for case-insensitive matching)
                    _FONT_CACHE[font_name_normalized] = ttf_file

        logger.info(f"✅ Font cache built: {len(_FONT_CACHE)} fonts cached")

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

    def _hex_to_rgb(hex_color: str):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _find_font_file(font_family: str):
        """Find TTF font file for given font family using cache."""
        # Build cache on first use
        _build_font_cache()

        font_name = font_family.lower().strip()
        font_name_normalized = font_name.replace(" ", "").replace("-", "").replace("_", "")

        # Try exact match first
        if font_name_normalized in _FONT_CACHE:
            font_path = _FONT_CACHE[font_name_normalized]
            logger.info(f"✅ Font matched (exact): '{font_family}' -> '{font_path}'")
            return font_path

        # Try partial match
        for cached_font_name, cached_path in _FONT_CACHE.items():
            if font_name_normalized in cached_font_name or cached_font_name in font_name_normalized:
                logger.info(f"✅ Font matched (partial): '{font_family}' -> '{cached_path}'")
                return cached_path

        logger.warning(f"❌ Font not found: '{font_family}', using default")
        return None

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
        logger.info(f"🔍 Source URL: {request.image_url[:100]}...")
        logger.info(f"📐 Image mode: {image.mode}")

        # Create draw object
        draw = ImageDraw.Draw(image)

        # Process each text layer
        for text_layer_config in request.text_layers:
            # Use ABSOLUTE pixel coordinates
            x = int(text_layer_config.x)
            y = int(text_layer_config.y)
            font_size = int(text_layer_config.font_size)

            logger.info(f"📥 RECEIVED FROM FRONTEND: x={x}, y={y}, font_size={font_size}")
            logger.info(f"📥 Text content: '{text_layer_config.text}'")
            logger.info(f"📥 Image size: {image.width}x{image.height}")

            logger.info(f"🎨 Drawing text: '{text_layer_config.text}' at ({x}, {y}), size={font_size}, font={text_layer_config.font_family}")

            # Find and load font
            font_path = _find_font_file(text_layer_config.font_family)
            if font_path:
                font = ImageFont.truetype(font_path, font_size)
                logger.info(f"✅ Using font file: {font_path}")
            else:
                font = ImageFont.load_default()
                logger.warning(f"⚠️ Font not found, using default: {text_layer_config.font_family}")

            # Get bounding box for diagnostics
            text_bbox = font.getbbox(text_layer_config.text)
            logger.info(f"📐 Text bbox from PIL: {text_bbox}")
            logger.info(f"📏 bbox[0]={text_bbox[0]} (left offset), bbox[1]={text_bbox[1]} (top offset)")

            # For coordinates from ImageEditorModal (overlay positioning):
            # x, y represents the top-left position where text should appear
            # We need to adjust for the ascender so letters draw correctly
            # No constant offset needed - use the position directly
            x_adjusted = x
            y_adjusted = y + text_bbox[1]  # Add ascender so letters appear below textbox top

            logger.info(f"📏 Using overlay position directly: x={x_adjusted}, y={y_adjusted} (adjusted for ascender +{text_bbox[1]}px)")
            logger.info(f"📏 Textbox top at ({x_adjusted}, {y_adjusted})")

            logger.info(f"🎨 Drawing text at PIL coords: ({x}, {y}) - font_size={font_size}, font_path={font_path}")
            logger.info(f"📐 PIL image size: {image.width}x{image.height}, mode={image.mode}")
            logger.info(f"📏 Using simple draw.text((x, y), text) approach - no anchors or offsets")

            # Convert colors
            color_rgb = _hex_to_rgb(text_layer_config.color)
            stroke_rgb = None
            stroke_width = 0

            # Draw stroke if specified
            if text_layer_config.stroke_width > 0 and text_layer_config.stroke_color:
                stroke_rgb = _hex_to_rgb(text_layer_config.stroke_color)
                stroke_width = int(text_layer_config.stroke_width)

            logger.info(f"🎨 Drawing text at PIL coords: ({x_adjusted}, {y_adjusted}) - font_size={font_size}, font_path={font_path}")
            logger.info(f"📐 PIL image size: {image.width}x{image.height}, mode={image.mode}")
            logger.info(f"🔍 Text bbox from PIL: {font.getbbox(text_layer_config.text)}")
            logger.info(f"📏 Using adjusted draw.text((x_adjusted, y_adjusted), text) approach")

            # Draw text with styles using helper function
            _draw_text_with_styles(
                target_image=image,
                text=text_layer_config.text,
                position=(x_adjusted, y_adjusted),
                font=font,
                fill=color_rgb,
                stroke_fill=stroke_rgb,
                stroke_width=stroke_width,
                bold=text_layer_config.bold,
                italic=text_layer_config.italic,
                strikethrough=text_layer_config.strikethrough
            )

            logger.info(f"✅ Text drawn successfully at ({x_adjusted}, {y_adjusted})")
            logger.info(f"📍 Textbox top at y={y_adjusted}, letters at y={y_adjusted + text_bbox[1]}")

        logger.info(f"✅ Text overlay complete")

        # Convert back to RGB
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            final_image = background
        else:
            final_image = image

        logger.info(f"💾 Final image size: {final_image.width}x{final_image.height} (mode={final_image.mode})")

        # Save to bytes buffer
        buffer = BytesIO()
        final_image.save(buffer, format="PNG", quality=95)
        composed_image_data = buffer.getvalue()

        logger.info(f"💾 Saved composed image: {len(composed_image_data)} bytes, format={final_image.format if hasattr(final_image, 'format') else 'N/A'}, mode={final_image.mode}, size={final_image.size}")
        logger.info(f"🔍 First 100 bytes (hex): {composed_image_data[:100].hex()}")

        # Upload to R2 using centralized utility
        from app.services.r2_storage import R2Storage
        filename = R2Storage.generate_filename("text_overlay", "png", request.campaign_id, timestamp=time.time())
        r2_key, image_url = await r2_storage.upload_image(
            campaign_id=request.campaign_id or 0,
            folder="edited",
            filename=filename,
            image_bytes=composed_image_data,
            content_type="image/png"
        )

        # Generate thumbnail
        thumbnail_url = await generate_thumbnail(image_url, request.campaign_id or 0)

        # Save to database
        # Check if the composed image has transparency
        has_transp = await check_image_has_transparency(image_url)

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
            # Text overlay - parent tracking could be added if original image ID is available
            parent_image_id=None,
            has_transparency=has_transp,
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


@router.post("/image-overlay", response_model=ImageImageOverlayResponse, status_code=status.HTTP_201_CREATED)
async def add_image_overlay(
    request: ImageImageOverlayRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add image overlay to a base image using PIL."""
    from PIL import Image, ImageEnhance, ImageDraw
    import httpx
    from io import BytesIO
    import hashlib
    import math

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
        # Download base image from URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            image_response = await client.get(request.image_url)
            image_response.raise_for_status()
            image_data = image_response.content

        # Open base image from bytes
        base_image = Image.open(BytesIO(image_data)).convert("RGBA")

        logger.info(f"🎨 Processing {len(request.image_overlays)} image overlay(s) using PIL")
        logger.info(f"🖼️ Base image size: {base_image.width}x{base_image.height}")
        logger.info(f"🔍 Base image URL: {request.image_url[:100]}...")
        logger.info(f"📐 Base image mode: {base_image.mode}")

        # Process each image overlay
        for overlay_config in request.image_overlays:
            logger.info(f"📥 RECEIVED FROM FRONTEND: x={overlay_config.x}, y={overlay_config.y}, scale={overlay_config.scale}, rotation={overlay_config.rotation}, opacity={overlay_config.opacity}")
            logger.info(f"📥 Overlay image URL: {overlay_config.image_url[:100]}...")

            # Download overlay image
            async with httpx.AsyncClient(timeout=30.0) as client:
                overlay_response = await client.get(overlay_config.image_url)
                overlay_response.raise_for_status()
                overlay_data = overlay_response.content

            # Open overlay image
            overlay_image = Image.open(BytesIO(overlay_data)).convert("RGBA")

            # Apply scale
            if overlay_config.scale != 1.0:
                new_width = int(overlay_image.width * overlay_config.scale)
                new_height = int(overlay_image.height * overlay_config.scale)
                overlay_image = overlay_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"🔍 Scaled overlay from {overlay_image.width}x{overlay_image.height} to {new_width}x{new_height}")

            # Apply rotation
            if overlay_config.rotation != 0.0:
                # Calculate new bounding box after rotation
                angle_rad = math.radians(overlay_config.rotation)
                cos_val = abs(math.cos(angle_rad))
                sin_val = abs(math.sin(angle_rad))
                new_width = int(overlay_image.width * cos_val + overlay_image.height * sin_val)
                new_height = int(overlay_image.width * sin_val + overlay_image.height * cos_val)

                # Rotate the image
                overlay_image = overlay_image.rotate(overlay_config.rotation, expand=True, fillcolor=(0, 0, 0, 0))
                logger.info(f"🔄 Rotated overlay by {overlay_config.rotation}°, new size: {overlay_image.width}x{overlay_image.height}")

            # Apply opacity
            if overlay_config.opacity < 1.0:
                # Create a new image with reduced opacity
                alpha = overlay_image.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(overlay_config.opacity)
                overlay_image.putalpha(alpha)
                logger.info(f"👁️ Applied opacity {overlay_config.opacity}")

            # Position is TOP-LEFT (frontend sends TOP-LEFT coordinates directly)
            x = int(overlay_config.x)
            y = int(overlay_config.y)

            logger.info(f"🎨 Positioning overlay at TOP-LEFT ({x}, {y})")
            logger.info(f"📐 Overlay size: {overlay_image.width}x{overlay_image.height}")

            # Ensure overlay fits within base image bounds
            if x + overlay_image.width > base_image.width:
                x = base_image.width - overlay_image.width
            if y + overlay_image.height > base_image.height:
                y = base_image.height - overlay_image.height
            if x < 0:
                x = 0
            if y < 0:
                y = 0

            # Paste overlay onto base image
            base_image.paste(overlay_image, (x, y), overlay_image)
            logger.info(f"✅ Overlay pasted at ({x}, {y})")

        logger.info(f"✅ Image overlay complete")

        # Convert back to RGB if needed
        if base_image.mode == "RGBA":
            background = Image.new("RGB", base_image.size, (255, 255, 255))
            background.paste(base_image, mask=base_image.split()[3])
            final_image = background
        else:
            final_image = base_image

        logger.info(f"💾 Final image size: {final_image.width}x{final_image.height} (mode={final_image.mode})")

        # Save to bytes buffer
        buffer = BytesIO()
        final_image.save(buffer, format="PNG", quality=95)
        composed_image_data = buffer.getvalue()

        logger.info(f"💾 Saved composed image: {len(composed_image_data)} bytes, format={final_image.format if hasattr(final_image, 'format') else 'N/A'}, mode={final_image.mode}, size={final_image.size}")

        # Upload to R2 using centralized utility
        filename = R2Storage.generate_filename("image_overlay", "png", request.campaign_id, timestamp=time.time())
        r2_key, image_url = await r2_storage.upload_image(
            campaign_id=request.campaign_id or 0,
            folder="edited",
            filename=filename,
            image_bytes=composed_image_data,
            content_type="image/png"
        )

        # Generate thumbnail
        thumbnail_url = await generate_thumbnail(image_url, request.campaign_id or 0)

        # Save to database
        # Check if the composed image has transparency
        has_transp = await check_image_has_transparency(image_url)

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
            # Image overlay - parent tracking could be added if original image ID is available
            parent_image_id=None,
            has_transparency=has_transp,
            meta_data={
                "image_overlay": True,
                "original_image_url": request.image_url,
                "image_overlays": [overlay.dict() for overlay in request.image_overlays]
            },
            ai_generation_cost=0.0,
            content_id=None
        )

        db.add(image_record)
        await db.commit()
        await db.refresh(image_record)

        return ImageImageOverlayResponse(
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
        logger.error(f"Image overlay failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image overlay failed: {str(e)}"
        )


async def generate_thumbnail(image_url: str, campaign_id: int, size: tuple = (256, 256)) -> Optional[str]:
    """Generate thumbnail for image."""
    from PIL import Image
    from io import BytesIO
    import httpx
    import time
    import hashlib

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            image = Image.open(BytesIO(response.content))

            # Resize image
            image.thumbnail(size, Image.Resampling.LANCZOS)

            # Save to bytes
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=80)
            thumbnail_data = buffer.getvalue()

            # Upload to R2
            _, thumbnail_url = await r2_storage.upload_file(
                file_bytes=thumbnail_data,
                key=f"campaignforge-storage/campaigns/{campaign_id}/generated_files/thumbnails/{int(time.time())}_{hashlib.md5(image_url.encode()).hexdigest()[:8]}.jpg",
                content_type="image/jpeg"
            )

            return thumbnail_url
    except Exception as e:
        logger.error(f"Failed to generate thumbnail: {e}")
        return None


@router.post("/trim-transparency", response_model=ImageTrimResponse)
async def trim_transparency(
    request: ImageTrimRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Trim transparent pixels from an image, leaving a specified padding border.

    This is useful for removing excess transparent space around product images
    or other assets that have been extracted from backgrounds.
    """
    from PIL import Image
    from io import BytesIO
    import httpx
    import time
    import hashlib

    try:
        # Download the image
        async with httpx.AsyncClient() as client:
            response = await client.get(request.image_url)
            response.raise_for_status()

        # Open image with PIL
        image = Image.open(BytesIO(response.content))
        original_width, original_height = image.size

        # Ensure image has alpha channel
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        # Get the alpha channel
        alpha = image.split()[3]

        # Get bounding box of non-transparent pixels
        bbox = alpha.getbbox()

        if bbox is None:
            # Image is fully transparent, return original
            return ImageTrimResponse(
                image_url=request.image_url,
                original_width=original_width,
                original_height=original_height,
                trimmed_width=original_width,
                trimmed_height=original_height
            )

        # Expand bbox by padding amount
        left = max(0, bbox[0] - request.padding)
        top = max(0, bbox[1] - request.padding)
        right = min(original_width, bbox[2] + request.padding)
        bottom = min(original_height, bbox[3] + request.padding)

        # Crop the image
        trimmed_image = image.crop((left, top, right, bottom))
        trimmed_width, trimmed_height = trimmed_image.size

        # Save to bytes
        buffer = BytesIO()
        trimmed_image.save(buffer, format="PNG")
        trimmed_data = buffer.getvalue()

        # Generate unique filename
        timestamp = int(time.time())
        hash_suffix = hashlib.md5(request.image_url.encode()).hexdigest()[:8]

        # Determine storage path
        if request.campaign_id:
            key = f"campaignforge-storage/campaigns/{request.campaign_id}/generated_files/trimmed_{timestamp}_{hash_suffix}.png"
        else:
            key = f"temp/trimmed_{timestamp}_{hash_suffix}.png"

        # Upload to R2
        _, trimmed_url = await r2_storage.upload_file(
            file_bytes=trimmed_data,
            key=key,
            content_type="image/png"
        )

        logger.info(f"✂️ Trimmed image from {original_width}x{original_height} to {trimmed_width}x{trimmed_height}")

        return ImageTrimResponse(
            image_url=trimmed_url,
            original_width=original_width,
            original_height=original_height,
            trimmed_width=trimmed_width,
            trimmed_height=trimmed_height
        )

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download image: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Trim transparency failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trim transparency failed: {str(e)}"
        )


@router.post("/composite", response_model=ImageCompositeResponse, status_code=status.HTTP_201_CREATED)
async def composite_image(
    request: ImageCompositeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Composite multiple text and image layers onto a base image, respecting z-order."""
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
    import httpx
    from io import BytesIO
    import hashlib
    import math
    import os
    import glob

    # Font cache for text layers
    _FONT_CACHE = {}

    def _build_font_cache():
        if _FONT_CACHE:
            return
        font_dirs = ["/app/app/fonts", "/tmp/fonts"]
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                for ttf_file in glob.glob(os.path.join(font_dir, "**/*.ttf"), recursive=True):
                    font_basename = os.path.basename(ttf_file).lower()
                    font_name_only = os.path.splitext(font_basename)[0]
                    font_name_normalized = font_name_only.replace("-", "").replace("_", "")
                    _FONT_CACHE[font_name_normalized] = ttf_file

    def _find_font_file(font_family: str):
        _build_font_cache()
        font_name = font_family.lower().strip()
        font_name_normalized = font_name.replace(" ", "").replace("-", "").replace("_", "")
        if font_name_normalized in _FONT_CACHE:
            return _FONT_CACHE[font_name_normalized]
        for cached_font_name, cached_path in _FONT_CACHE.items():
            if font_name_normalized in cached_font_name or cached_font_name in font_name_normalized:
                return cached_path
        return None

    def _hex_to_rgb(hex_color: str):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _draw_text_with_styles(target_image: Image.Image, text: str, position: tuple, font: ImageFont.ImageFont, fill: tuple, stroke_fill: tuple = None, stroke_width: int = 0, bold: bool = False, italic: bool = False, strikethrough: bool = False):
        """Draw text with optional bold, italic, and strikethrough styles."""
        x, y = position

        # Debug logging
        logger.info(f"✏️ Applying styles to '{text}': bold={bold}, italic={italic}, strikethrough={strikethrough}")

        # Get text bounding box
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Create a temporary image for the text with extra padding for bold/italic effects
        padding = 40
        temp_img = Image.new("RGBA", (text_width + padding * 2, text_height + padding * 2), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)

        # Convert fill to RGBA if needed
        fill_rgba = fill + (255,) if len(fill) == 3 else fill

        # Draw stroke if specified
        if stroke_width > 0 and stroke_fill:
            stroke_rgb = stroke_fill + (255,) if len(stroke_fill) == 3 else stroke_fill
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx*dx + dy*dy <= stroke_width * stroke_width:
                        temp_draw.text((padding + dx, padding + dy), text, font=font, fill=stroke_rgb)

        # Draw main text
        temp_draw.text((padding, padding), text, font=font, fill=fill_rgba)

        # Apply bold effect (draw text multiple times with slight offset)
        if bold:
            logger.info("  🟦 Applying BOLD effect")
            bold_overlay = Image.new("RGBA", temp_img.size, (0, 0, 0, 0))
            bold_draw = ImageDraw.Draw(bold_overlay)
            # Draw text multiple times for bold effect (around the main text)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        bold_draw.text((padding + dx, padding + dy), text, font=font, fill=fill_rgba)
            # Composite onto temp image
            temp_img = Image.alpha_composite(temp_img, bold_overlay)

        # Apply italic effect (skew the image to the right)
        if italic:
            logger.info("  🟨 Applying ITALIC effect")
            # Create larger canvas for skew
            skew_factor = 0.3
            new_width = int(temp_img.width * (1 + skew_factor))
            skew_img = Image.new("RGBA", (new_width, temp_img.height), (0, 0, 0, 0))
            # Apply shear transformation manually - slant to the right (top stays, bottom moves left)
            for py in range(temp_img.height):
                offset = -int(py * skew_factor)
                # Copy each row with offset (negative = move left)
                row = temp_img.crop((0, py, temp_img.width, py + 1))
                skew_img.paste(row, (offset, py))
            temp_img = skew_img

        # Apply strikethrough AFTER all other effects
        if strikethrough:
            logger.info("  🟪 Applying STRIKETHROUGH effect (diagonal)")
            # Redraw on the final temp_img to ensure it's centered
            temp_draw_final = ImageDraw.Draw(temp_img)
            # Create diagonal strikethrough from bottom of first letter to top of last letter
            # Start at bottom of first letter, end at top of last letter (lowered)
            start_y = padding + text_height  # Bottom of first letter
            end_y = padding + 20  # Top of last letter (lowered from padding=40 to padding+20)
            line_width = max(4, text_height // 10)  # Thicker line
            temp_draw_final.line(
                [(padding, start_y), (padding + text_width, end_y)],
                fill=fill_rgba,
                width=line_width
            )

        # Paste the styled text onto the target image
        # Clamp position to stay within bounds
        paste_x = max(0, min(x, target_image.width - temp_img.width))
        paste_y = max(0, min(y, target_image.height - temp_img.height))

        logger.info(f"  📤 Pasting styled text at ({paste_x}, {paste_y}), size: {temp_img.width}x{temp_img.height}")

        if temp_img.mode == "RGBA":
            target_image.paste(temp_img, (paste_x, paste_y), temp_img)
        else:
            target_image.paste(temp_img, (paste_x, paste_y))

        logger.info("  ✅ Text styling complete")

    # Verify campaign ownership
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    try:
        # Download base image
        async with httpx.AsyncClient(timeout=30.0) as client:
            image_response = await client.get(request.image_url)
            image_response.raise_for_status()
            image_data = image_response.content

        base_image = Image.open(BytesIO(image_data)).convert("RGBA")
        logger.info(f"🎨 Composite: Processing {len(request.text_layers)} text + {len(request.image_layers)} image layers")
        logger.info(f"🖼️ Base image size: {base_image.width}x{base_image.height}")

        # Combine all layers with type info and sort by z_index
        all_layers = []
        for layer in request.text_layers:
            all_layers.append({"type": "text", "layer": layer, "z_index": layer.z_index})
        for layer in request.image_layers:
            all_layers.append({"type": "image", "layer": layer, "z_index": layer.z_index})

        all_layers.sort(key=lambda x: x["z_index"])
        logger.info(f"📋 Processing {len(all_layers)} layers in z-order")

        # Pre-download all image overlays
        image_cache = {}
        async with httpx.AsyncClient(timeout=30.0) as client:
            for item in all_layers:
                if item["type"] == "image":
                    layer = item["layer"]
                    if layer.image_url not in image_cache:
                        overlay_response = await client.get(layer.image_url)
                        overlay_response.raise_for_status()
                        image_cache[layer.image_url] = overlay_response.content

        # Process each layer in z-order
        for item in all_layers:
            if item["type"] == "text":
                # Process text layer
                text_layer = item["layer"]
                x = int(text_layer.x)
                y = int(text_layer.y)
                font_size = int(text_layer.font_size)

                logger.info(f"📝 Text layer: '{text_layer.text}' at ({x}, {y}), z={text_layer.z_index}")

                # Load font
                font_path = _find_font_file(text_layer.font_family)
                if font_path:
                    font = ImageFont.truetype(font_path, font_size)
                else:
                    font = ImageFont.load_default()

                # Get text bbox for y adjustment
                text_bbox = font.getbbox(text_layer.text)
                y_adjusted = y + text_bbox[1]

                color_rgb = _hex_to_rgb(text_layer.color)
                stroke_rgb = None
                stroke_width = 0

                # Debug: Log text style properties
                logger.info(f"🎨 Text styles for '{text_layer.text}': bold={text_layer.bold}, italic={text_layer.italic}, strikethrough={text_layer.strikethrough}")

                # Draw stroke
                if text_layer.stroke_width > 0 and text_layer.stroke_color:
                    stroke_rgb = _hex_to_rgb(text_layer.stroke_color)
                    stroke_width = int(text_layer.stroke_width)

                # Draw text with styles directly onto a temporary text layer
                text_layer_img = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
                _draw_text_with_styles(
                    target_image=text_layer_img,
                    text=text_layer.text,
                    position=(x, y_adjusted),
                    font=font,
                    fill=color_rgb,
                    stroke_fill=stroke_rgb,
                    stroke_width=stroke_width,
                    bold=text_layer.bold,
                    italic=text_layer.italic,
                    strikethrough=text_layer.strikethrough
                )

                # Apply opacity to the text layer
                if text_layer.opacity < 1.0:
                    alpha = text_layer_img.split()[3]
                    alpha = ImageEnhance.Brightness(alpha).enhance(text_layer.opacity)
                    text_layer_img.putalpha(alpha)

                # Composite text onto base
                base_image = Image.alpha_composite(base_image, text_layer_img)

            elif item["type"] == "image":
                # Process image layer
                img_layer = item["layer"]
                overlay_data = image_cache[img_layer.image_url]
                overlay_image = Image.open(BytesIO(overlay_data)).convert("RGBA")

                logger.info(f"🖼️ Image layer at ({img_layer.x}, {img_layer.y}), scale={img_layer.scale}, z={img_layer.z_index}")

                # Apply scale
                if img_layer.scale != 1.0:
                    new_width = int(overlay_image.width * img_layer.scale)
                    new_height = int(overlay_image.height * img_layer.scale)
                    overlay_image = overlay_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Apply rotation
                if img_layer.rotation != 0.0:
                    overlay_image = overlay_image.rotate(img_layer.rotation, expand=True, fillcolor=(0, 0, 0, 0))

                # Apply opacity
                if img_layer.opacity < 1.0:
                    alpha = overlay_image.split()[3]
                    alpha = ImageEnhance.Brightness(alpha).enhance(img_layer.opacity)
                    overlay_image.putalpha(alpha)

                # Position (TOP-LEFT coordinates)
                x = int(img_layer.x)
                y = int(img_layer.y)

                # Clamp to bounds
                x = max(0, min(x, base_image.width - overlay_image.width))
                y = max(0, min(y, base_image.height - overlay_image.height))

                # Paste overlay
                base_image.paste(overlay_image, (x, y), overlay_image)

        logger.info(f"✅ Composite complete")

        # Convert to RGB for final output
        if base_image.mode == "RGBA":
            background = Image.new("RGB", base_image.size, (255, 255, 255))
            background.paste(base_image, mask=base_image.split()[3])
            final_image = background
        else:
            final_image = base_image

        # Save to bytes
        buffer = BytesIO()
        final_image.save(buffer, format="PNG", quality=95)
        composed_image_data = buffer.getvalue()

        # Upload to R2 using centralized utility
        filename = R2Storage.generate_filename("composite", "png", request.campaign_id, timestamp=time.time())
        r2_key, image_url = await r2_storage.upload_image(
            campaign_id=request.campaign_id or 0,
            folder="edited",
            filename=filename,
            image_bytes=composed_image_data,
            content_type="image/png"
        )

        # Generate thumbnail
        thumbnail_url = await generate_thumbnail(image_url, request.campaign_id or 0)

        # Save to database
        # Check if the composed image has transparency
        has_transp = await check_image_has_transparency(image_url)

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
            # Composite - parent tracking could be added if original image ID is available
            parent_image_id=None,
            has_transparency=has_transp,
            meta_data={
                "composite": True,
                "original_image_url": request.image_url,
                "text_layers": [layer.dict() for layer in request.text_layers],
                "image_layers": [layer.dict() for layer in request.image_layers],
                "width": final_image.width,
                "height": final_image.height
            },
            ai_generation_cost=0.0,
            content_id=None
        )

        db.add(image_record)
        await db.commit()
        await db.refresh(image_record)

        return ImageCompositeResponse(
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to download image: {str(e)}")
    except Exception as e:
        logger.error(f"Composite failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Composite failed: {str(e)}")

