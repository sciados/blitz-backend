"""Image generation API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import List, Optional
import logging

from app.db.session import get_db
from app.db.models import User, Campaign, GeneratedImage, ProductIntelligence
from app.auth import get_current_user
from app.schemas import (
    ImageGenerateRequest,
    ImageBatchRequest,
    ImageVariationRequest,
    ImageResponse,
    ImageListResponse,
    ImageDeleteResponse
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
        meta_data=result.meta_data,
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

    # Generate image (NOT saved to database)
    try:
        result = await image_generator.generate_image(
            prompt=prompt,
            image_type=request.image_type,
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            campaign_intelligence=intelligence_data,
            quality_boost=False,  # Preview mode - no quality boost
            campaign_id=request.campaign_id
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
        metadata=result.meta_data or {},
        ai_generation_cost=result.cost,
        content_id=None,
        created_at=datetime.utcnow()  # Required field for preview
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

    # Build generation requests
    generation_requests = []
    for img_request in request.images:
        # Build prompt
        prompt = prompt_builder.build_prompt(
            campaign_intelligence=campaign.intelligence_data,
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
            "campaign_intelligence": campaign.intelligence_data,
            "custom_params": img_request.get("custom_params", {})
        })

    # Generate images in batch
    try:
        results = await image_generator.batch_generate(generation_requests)
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
            meta_data=result.meta_data,
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