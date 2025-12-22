"""
Image Editor API Router - ALL OPERATIONS (ASYNC SESSIONS)
FastAPI endpoints for all image editing operations with async SQLAlchemy
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, insert, text
from typing import Optional
import base64
import time
import json

from app.db.session import get_db  # Your async session dependency
from app.auth import get_current_user
from app.db.models import User, Campaign

from .schemas import (
    InpaintingResponse,
    ImageEditRecord,
    EditHistoryResponse,
    EditStatistics,
    OperationType
)
from .services.stability_service import StabilityAIService
from .services.r2_service import R2StorageService

router = APIRouter(prefix="/api/image-editor", tags=["image-editor"])


async def _process_edit(
    image_url: str,
    campaign_id: int,
    operation_type: str,
    operation_func,
    operation_params: dict,
    db: AsyncSession,
    current_user: User
) -> InpaintingResponse:
    """
    Common processing function for all edit operations (ASYNC)
    """
    start_time = time.time()
    
    try:
        # Verify campaign (async query)
        result = await db.execute(
            select(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.user_id == current_user.id
            )
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found or access denied"
            )
        
        # Initialize services
        stability_service = StabilityAIService()
        r2_service = R2StorageService()
        
        # Download original image
        if image_url.startswith("http"):
            original_image_data = await r2_service.download_image_from_url(image_url)
            r2_path = r2_service.extract_r2_path_from_url(image_url)
            original_image_path = r2_path or image_url
        else:
            original_image_data = await r2_service.download_image_from_r2(image_url)
            original_image_path = image_url
        
        # Perform the operation
        edited_image_data, metadata = await operation_func(
            stability_service, original_image_data, **operation_params
        )
        
        # Upload edited image
        output_format = operation_params.get('output_format', 'png')
        edited_r2_path, edited_public_url = await r2_service.upload_edited_image(
            image_data=edited_image_data,
            campaign_id=campaign_id,
            original_filename=original_image_path,
            operation_type=operation_type,
            content_type=f"image/{output_format}"
        )
        
        # Calculate processing time and cost
        processing_time_ms = int((time.time() - start_time) * 1000)
        api_cost = stability_service.estimate_cost_credits(operation_type)
        
        # Save to database (async)
        query = text("""
            INSERT INTO image_edits
            (user_id, campaign_id, original_image_path, edited_image_path,
             operation_type, operation_params, stability_model, api_cost_credits,
             processing_time_ms, success, created_at, updated_at)
            VALUES
            ($1, $2, $3, $4,
             $5, $6::jsonb, $7, $8,
             $9, $10, NOW(), NOW())
            RETURNING id
        """)
        
        result = await db.execute(
            query,
            [
                current_user.id,
                campaign_id,
                original_image_path,
                edited_r2_path,
                operation_type,
                json.dumps(operation_params),  # Convert to JSON string
                metadata.get("model"),
                api_cost,
                processing_time_ms,
                True
            ]
        )
        edit_id = result.scalar_one()
        await db.commit()
        
        return InpaintingResponse(
            success=True,
            edited_image_url=edited_public_url,
            edited_image_path=edited_r2_path,
            original_image_path=original_image_path,
            edit_id=edit_id,
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        await db.rollback()
        
        # Log failed edit
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        try:
            query = text("""
                INSERT INTO image_edits
                (user_id, campaign_id, original_image_path, edited_image_path,
                 operation_type, operation_params, processing_time_ms, success, error_message,
                 created_at, updated_at)
                VALUES
                ($1, $2, $3, '',
                 $4, $5::jsonb, $6, false, $7,
                 NOW(), NOW())
            """)
            
            await db.execute(
                query,
                [
                    current_user.id,
                    campaign_id,
                    image_url,
                    operation_type,
                    json.dumps(operation_params),
                    processing_time_ms,
                    str(e)
                ]
            )
            await db.commit()
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{operation_type} failed: {str(e)}"
        )


@router.post("/inpaint", response_model=InpaintingResponse)
async def inpaint_image(
    image_url: str = Form(...),
    campaign_id: int = Form(...),
    prompt: str = Form(...),
    mask_image_data: str = Form(...),
    negative_prompt: Optional[str] = Form(None),
    seed: int = Form(0),
    output_format: str = Form("png"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform inpainting operation"""
    
    # Decode mask
    try:
        if "base64," in mask_image_data:
            mask_image_data = mask_image_data.split("base64,")[1]
        mask_data = base64.b64decode(mask_image_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mask image data: {str(e)}"
        )
    
    async def operation(service, image_data, **params):
        return await service.inpaint_image(image_data, mask_data, **params)
    
    return await _process_edit(
        image_url, campaign_id, "inpainting", operation,
        {"prompt": prompt, "negative_prompt": negative_prompt, "seed": seed, "output_format": output_format},
        db, current_user
    )


@router.post("/remove-background", response_model=InpaintingResponse)
async def remove_background(
    image_url: str = Form(...),
    campaign_id: int = Form(...),
    output_format: str = Form("png"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove background from an image"""
    
    async def operation(service, image_data, **params):
        return await service.remove_background(image_data, **params)
    
    return await _process_edit(
        image_url, campaign_id, "background_removal", operation,
        {"output_format": output_format},
        db, current_user
    )


@router.post("/search-replace", response_model=InpaintingResponse)
async def search_and_replace(
    image_url: str = Form(...),
    campaign_id: int = Form(...),
    search_prompt: str = Form(...),
    prompt: str = Form(...),
    negative_prompt: Optional[str] = Form(None),
    seed: int = Form(0),
    output_format: str = Form("png"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for an object and replace it"""
    
    async def operation(service, image_data, **params):
        return await service.search_and_replace(image_data, **params)
    
    return await _process_edit(
        image_url, campaign_id, "search_replace", operation,
        {"search_prompt": search_prompt, "prompt": prompt, "negative_prompt": negative_prompt, "seed": seed, "output_format": output_format},
        db, current_user
    )


@router.post("/outpaint", response_model=InpaintingResponse)
async def outpaint_image(
    image_url: str = Form(...),
    campaign_id: int = Form(...),
    prompt: str = Form(...),
    left: int = Form(0),
    right: int = Form(0),
    up: int = Form(0),
    down: int = Form(0),
    creativity: float = Form(0.5),
    seed: int = Form(0),
    output_format: str = Form("png"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Extend image borders with AI-generated content"""
    
    async def operation(service, image_data, **params):
        return await service.outpaint_image(image_data, **params)
    
    return await _process_edit(
        image_url, campaign_id, "outpainting", operation,
        {"prompt": prompt, "left": left, "right": right, "up": up, "down": down, "creativity": creativity, "seed": seed, "output_format": output_format},
        db, current_user
    )


@router.post("/erase", response_model=InpaintingResponse)
async def erase_objects(
    image_url: str = Form(...),
    campaign_id: int = Form(...),
    mask_image_data: str = Form(...),
    seed: int = Form(0),
    output_format: str = Form("png"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Erase objects from image using mask"""
    
    # Decode mask
    try:
        if "base64," in mask_image_data:
            mask_image_data = mask_image_data.split("base64,")[1]
        mask_data = base64.b64decode(mask_image_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mask image data: {str(e)}"
        )
    
    async def operation(service, image_data, **params):
        return await service.erase_objects(image_data, mask_data, **params)
    
    return await _process_edit(
        image_url, campaign_id, "erase", operation,
        {"seed": seed, "output_format": output_format},
        db, current_user
    )


@router.post("/upscale", response_model=InpaintingResponse)
async def upscale_image(
    image_url: str = Form(...),
    campaign_id: int = Form(...),
    prompt: str = Form(...),
    negative_prompt: Optional[str] = Form(None),
    creativity: float = Form(0.35),
    seed: int = Form(0),
    output_format: str = Form("png"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creative upscaling - enhance and upscale image"""
    
    async def operation(service, image_data, **params):
        return await service.upscale_image(image_data, **params)
    
    return await _process_edit(
        image_url, campaign_id, "upscaling", operation,
        {"prompt": prompt, "negative_prompt": negative_prompt, "creativity": creativity, "seed": seed, "output_format": output_format},
        db, current_user
    )


@router.post("/sketch-to-image", response_model=InpaintingResponse)
async def sketch_to_image(
    image_url: str = Form(...),
    campaign_id: int = Form(...),
    prompt: str = Form(...),
    negative_prompt: Optional[str] = Form(None),
    control_strength: float = Form(0.7),
    seed: int = Form(0),
    output_format: str = Form("png"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Convert sketch/drawing to realistic image"""
    
    async def operation(service, image_data, **params):
        return await service.sketch_to_image(image_data, **params)
    
    return await _process_edit(
        image_url, campaign_id, "sketch_to_image", operation,
        {"prompt": prompt, "negative_prompt": negative_prompt, "control_strength": control_strength, "seed": seed, "output_format": output_format},
        db, current_user
    )


@router.get("/history/{campaign_id}", response_model=EditHistoryResponse)
async def get_edit_history(
    campaign_id: int,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get edit history for a campaign"""
    
    # Verify campaign access (async)
    result = await db.execute(
        select(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found or access denied"
        )
    
    # Get total count (async)
    count_query = text("SELECT COUNT(*) FROM image_edits WHERE campaign_id = $1")
    count_result = await db.execute(count_query, [campaign_id])
    total = count_result.scalar()
    
    # Get paginated results (async)
    offset = (page - 1) * page_size
    
    edits_query = text("""
        SELECT * FROM image_edits
        WHERE campaign_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
    """)
    
    edits_result = await db.execute(
        edits_query,
        [campaign_id, page_size, offset]
    )
    edits = edits_result.fetchall()
    
    edit_records = []
    for edit in edits:
        edit_records.append(ImageEditRecord(
            id=edit.id,
            user_id=edit.user_id,
            campaign_id=edit.campaign_id,
            original_image_path=edit.original_image_path,
            edited_image_path=edit.edited_image_path,
            operation_type=edit.operation_type,
            operation_params=edit.operation_params,
            stability_model=edit.stability_model,
            api_cost_credits=edit.api_cost_credits,
            processing_time_ms=edit.processing_time_ms,
            success=edit.success,
            error_message=edit.error_message,
            created_at=edit.created_at,
            updated_at=edit.updated_at
        ))
    
    return EditHistoryResponse(
        edits=edit_records,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/statistics", response_model=EditStatistics)
async def get_edit_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get editing statistics for the current user"""
    
    # Get overall stats (async)
    stats_query = text("""
        SELECT 
            COUNT(*) as total_edits,
            COUNT(CASE WHEN success = true THEN 1 END) as successful_edits,
            COUNT(CASE WHEN success = false THEN 1 END) as failed_edits,
            COALESCE(SUM(api_cost_credits), 0) as total_credits_used,
            COALESCE(AVG(processing_time_ms), 0) as avg_processing_time_ms
        FROM image_edits
        WHERE user_id = $1
    """)
    
    stats_result = await db.execute(stats_query, [current_user.id])
    stats = stats_result.fetchone()
    
    # Get edits by type (async)
    by_type_query = text("""
        SELECT operation_type, COUNT(*) as count
        FROM image_edits
        WHERE user_id = $1 
        GROUP BY operation_type
    """)
    
    by_type_result = await db.execute(by_type_query, [current_user.id])
    edits_by_type = by_type_result.fetchall()
    
    edits_by_type_dict = {row.operation_type: row.count for row in edits_by_type}
    
    return EditStatistics(
        total_edits=stats.total_edits,
        successful_edits=stats.successful_edits,
        failed_edits=stats.failed_edits,
        total_credits_used=float(stats.total_credits_used),
        avg_processing_time_ms=float(stats.avg_processing_time_ms),
        edits_by_type=edits_by_type_dict
    )