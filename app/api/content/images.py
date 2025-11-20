"""Image generation API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import List, Optional
import logging
import random
import time

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
    ImageSaveDraftRequest
)
from app.services.image_generator import ImageGenerator, ImageGenerationResult
from app.services.image_prompt_builder import ImagePromptBuilder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/content/images", tags=["images"])


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
    """Generate image for campaign using saved intelligence."""
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

    # Get intelligence data from ProductIntelligence via product_intelligence_id
    intelligence_data = None
    logger.info(f"Campaign ID: {campaign.id}, product_intelligence_id: {campaign.product_intelligence_id}")

    if campaign.product_intelligence_id:
        # Get the linked ProductIntelligence
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

    logger.info(f"Final intelligence_data: {intelligence_data is not None}")

    # Build prompt using intelligence data
    prompt = prompt_builder.build_prompt(
        campaign_intelligence=intelligence_data,
        image_type=request.image_type,
        user_prompt=request.custom_prompt,
        style=request.style,
        aspect_ratio=request.aspect_ratio,
        quality_boost=request.quality_boost or False
    )

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
        meta_data=result.metadata,
        ai_generation_cost=result.cost
    )

    db.add(image_record)
    await db.commit()
    await db.refresh(image_record)

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

    # Build prompt - use concise version for preview (free providers)
    prompt = prompt_builder.build_prompt(
        campaign_intelligence=intelligence_data,
        image_type=request.image_type,
        user_prompt=request.custom_prompt,
        style=request.style,
        aspect_ratio=request.aspect_ratio,
        quality_boost=False,  # Preview always uses free/low-cost providers
        concise=True  # Use shorter prompts for free providers
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

    # Build prompt - use concise version for preview (free providers)
    prompt = prompt_builder.build_prompt(
        campaign_intelligence=intelligence_data,
        image_type=request.image_type,
        user_prompt=request.custom_prompt,
        style=request.style,
        aspect_ratio=request.aspect_ratio,
        quality_boost=False,  # Preview always uses free/low-cost providers
        concise=True  # Use shorter prompts for free providers
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

    try:
        # Download the image from the provider URL and save to R2
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save draft image: {str(e)}"
        )

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
        meta_data=result.metadata,
        ai_generation_cost=0.0,  # Draft images are free
        content_id=None
    )

    db.add(image_record)
    await db.commit()
    await db.refresh(image_record)

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
    # 1. Download draft and save to: campaigns/{id}/generated_images/temp/  (intermediate)
    # 2. Enhance image and save to: campaigns/{id}/generated_images/         (final result)
    # This keeps the main folder clean with only final enhanced images
    logger.info(f"💾 Preparing draft for enhancement...")
    try:
        import httpx
        import hashlib
        import time
        import re

        # Shorten extremely long URLs (e.g., Pollinations URLs) before downloading
        # This prevents "URL too long" errors from HTTP clients
        draft_url = request.draft_image_url
        logger.info(f"📏 Original draft URL length: {len(request.draft_image_url)} chars")

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

        # Upload to temp folder (not main generated_images)
        draft_filename = f"draft_for_enhancement_{int(time.time())}_{hashlib.md5(request.draft_image_url.encode()).hexdigest()[:8]}.png"
        _, draft_url = await image_generator.r2_storage.upload_file(
            file_bytes=image_data,
            key=f"campaigns/{request.campaign_id}/generated_images/temp/{draft_filename}",
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
            image_type="hero",  # Default type for enhancement
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

    # Save enhanced image to database
    image_record = GeneratedImage(
        campaign_id=request.campaign_id,
        image_type="hero",
        image_url=result.image_url,
        thumbnail_url=result.thumbnail_url,
        provider=result.provider,
        model=result.model,
        prompt=result.prompt,
        style=request.style,
        aspect_ratio=request.aspect_ratio,
        meta_data=result.metadata,
        ai_generation_cost=result.cost,
        content_id=None
    )

    db.add(image_record)
    await db.commit()
    await db.refresh(image_record)

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

    # Get intelligence data (consistent with other endpoints)
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

    # Build generation requests
    generation_requests = []
    for img_request in request.images:
        # Build prompt
        prompt = prompt_builder.build_prompt(
            campaign_intelligence=intelligence_data,
            image_type=img_request["image_type"],
            user_prompt=img_request.get("custom_prompt"),
            style=img_request.get("style", "photorealistic"),
            aspect_ratio=img_request.get("aspect_ratio", "1:1")
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
            meta_data=result.metadata,
            ai_generation_cost=result.cost
        )

        db.add(image_record)
        image_records.append(image_record)

    await db.commit()

    # Refresh all records
    for record in image_records:
        await db.refresh(record)

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


@router.get("/campaign/{campaign_id}", response_model=ImageListResponse)
async def list_campaign_images(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    image_type: Optional[str] = Query(None, description="Filter by image type"),
    skip: int = 0,
    limit: int = 50
):
    """List all generated images for a campaign."""
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

    # Build query
    query = select(GeneratedImage).where(GeneratedImage.campaign_id == campaign_id)

    if image_type:
        query = query.where(GeneratedImage.image_type == image_type)

    # Get total count
    count_result = await db.execute(
        select(GeneratedImage).where(GeneratedImage.campaign_id == campaign_id)
    )
    total = len(count_result.scalars().all())

    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(GeneratedImage.created_at.desc())

    result = await db.execute(query)
    images = result.scalars().all()

    return ImageListResponse(
        images=[
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
        ],
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )


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