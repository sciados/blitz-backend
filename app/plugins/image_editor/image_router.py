# src/app/plugins/image_editor/image_router.py

"""
Image Editor API Router - ALL OPERATIONS (ASYNC SESSIONS)
FastAPI endpoints for all image editing operations with async SQLAlchemy
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, insert, text
from typing import Optional
import base64
import time
import json
import logging

from app.db.session import get_db  # Your async session dependency
from app.auth import get_current_user
from app.db.models import User, Campaign, GeneratedImage

from .schemas import (
    InpaintingResponse,
    ImageEditRecord,
    EditHistoryResponse,
    EditStatistics,
    OperationType
)
from .services.stability_service import StabilityAIService
# Use centralized R2 storage utility
from app.services.r2_storage import r2_storage, R2Storage

logger = logging.getLogger(__name__)

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

        # Download original image using centralized R2 storage
        if image_url.startswith("http"):
            original_image_data = await r2_storage.download_from_url(image_url)
            r2_path = r2_storage.extract_path_from_url(image_url)
            original_image_path = r2_path or image_url
        else:
            original_image_data = await r2_storage.download_file(image_url)
            original_image_path = image_url

        # Perform the operation
        edited_image_data, metadata = await operation_func(
            stability_service, original_image_data, **operation_params
        )

        # Generate filename and upload edited image using centralized R2 storage
        output_format = operation_params.get('output_format', 'png')
        filename = R2Storage.generate_image_filename(
            operation=operation_type,
            original_filename=original_image_path.split('/')[-1] if original_image_path else None,
            campaign_id=campaign_id,
            extension=output_format
        )
        edited_r2_path, edited_public_url = await r2_storage.upload_image(
            campaign_id=campaign_id,
            folder="edited",
            filename=filename,
            image_bytes=edited_image_data,
            content_type=f"image/{output_format}"
        )

        # Try to find parent image ID from the original image path
        parent_image_id = None
        try:
            # Extract the R2 path if it's a full URL
            r2_path_for_lookup = r2_path if 'r2_path' in locals() else original_image_path

            # Query generated_images to find the parent image
            parent_query = select(GeneratedImage).where(
                GeneratedImage.image_url.like(f'%{r2_path_for_lookup.split("/")[-1]}%'),
                GeneratedImage.campaign_id == campaign_id
            ).limit(1)
            parent_result = await db.execute(parent_query)
            parent_image = parent_result.scalar_one_or_none()
            if parent_image:
                parent_image_id = parent_image.id
        except Exception as e:
            logger.warning(f"Could not find parent image: {e}")
            parent_image_id = None

        # Set transparency flag based on operation type
        has_transparency = operation_type == "background-remove"

        # Calculate processing time and cost
        processing_time_ms = int((time.time() - start_time) * 1000)
        api_cost = stability_service.estimate_cost_credits(operation_type)

        # Save to database (async)
        query = text("""
            INSERT INTO image_edits
            (user_id, campaign_id, original_image_path, edited_image_path,
             operation_type, operation_params, stability_model, api_cost_credits,
             processing_time_ms, success, parent_image_id, has_transparency,
             created_at, updated_at)
            VALUES
            (:user_id, :campaign_id, :original_path, :edited_path,
             :op_type, :params, :model, :cost,
             :time_ms, :success, :parent_id, :has_transparency,
             NOW(), NOW())
            RETURNING id
        """)

        result = await db.execute(
            query,
            {
                "user_id": current_user.id,
                "campaign_id": campaign_id,
                "original_path": original_image_path,
                "edited_path": edited_r2_path,
                "op_type": operation_type,
                "params": json.dumps(operation_params),
                "model": metadata.get("model"),
                "cost": api_cost,
                "time_ms": processing_time_ms,
                "success": True,
                "parent_id": parent_image_id,
                "has_transparency": has_transparency
            }
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
                (:user_id, :campaign_id, :original_path, NULL,
                 :op_type, :params, :time_ms, false, :error,
                 NOW(), NOW())
            """)
            
            await db.execute(
                query,
                {
                    "user_id": current_user.id,
                    "campaign_id": campaign_id,
                    "original_path": image_url,
                    "op_type": operation_type,
                    "params": json.dumps(operation_params),
                    "time_ms": processing_time_ms,
                    "error": str(e)
                }
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
    count_query = text("SELECT COUNT(*) FROM image_edits WHERE campaign_id = :campaign_id")
    count_result = await db.execute(count_query, {"campaign_id": campaign_id})
    total = count_result.scalar()
    
    # Get paginated results (async)
    offset = (page - 1) * page_size
    
    edits_query = text("""
        SELECT id, user_id, campaign_id, original_image_path, edited_image_path,
               operation_type, operation_params, stability_model, api_cost_credits,
               processing_time_ms, success, error_message, parent_image_id,
               has_transparency, created_at, updated_at
        FROM image_edits
        WHERE campaign_id = :campaign_id
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    
    edits_result = await db.execute(
        edits_query,
        {"campaign_id": campaign_id, "limit": page_size, "offset": offset}
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
            parent_image_id=edit.parent_image_id,
            has_transparency=edit.has_transparency if edit.has_transparency is not None else False,
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
        WHERE user_id = :user_id
    """)
    
    stats_result = await db.execute(stats_query, {"user_id": current_user.id})
    stats = stats_result.fetchone()
    
    # Get edits by type (async)
    by_type_query = text("""
        SELECT operation_type, COUNT(*) as count
        FROM image_edits
        WHERE user_id = :user_id 
        GROUP BY operation_type
    """)
    
    by_type_result = await db.execute(by_type_query, {"user_id": current_user.id})
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


@router.delete("/{edit_id}")
async def delete_edit(
    edit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an edited image record"""

    # Get the edit to check ownership and get the file path
    query = text("""
        SELECT edited_image_path, user_id
        FROM image_edits
        WHERE id = :edit_id
    """)

    result = await db.execute(query, {"edit_id": edit_id})
    edit_record = result.fetchone()

    if not edit_record:
        raise HTTPException(status_code=404, detail="Edit not found")

    if edit_record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this edit")

    # Delete the file from R2 using centralized storage
    if edit_record.edited_image_path:
        try:
            r2_path = edit_record.edited_image_path
            await r2_storage.delete_file(r2_path)
        except Exception as e:
            # Log the error but continue with database deletion
            print(f"Warning: Failed to delete file from R2: {e}")

    # Delete from database
    delete_query = text("""
        DELETE FROM image_edits
        WHERE id = :edit_id AND user_id = :user_id
    """)

    await db.execute(delete_query, {"edit_id": edit_id, "user_id": current_user.id})
    await db.commit()

    return {"success": True, "message": "Edit deleted successfully"}

# Add this to your image_router.py file
# Location: blitz-backend/app/plugins/image_editor/image_router.py

from fastapi import UploadFile, File
from typing import List
import asyncio
import zipfile
from io import BytesIO

@router.post("/batch-process")
async def batch_process_images(
    campaign_id: int = Form(...),
    operation_type: str = Form(...),  # inpaint, resize, upscale, etc.
    operation_params: str = Form(...),  # JSON string of parameters
    image_urls: str = Form(...),  # JSON array of image URLs
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Batch process multiple images with the same operation
    
    Args:
        campaign_id: Campaign ID
        operation_type: Type of operation (e.g., 'resize', 'upscale', 'overlay')
        operation_params: JSON string containing operation parameters
        image_urls: JSON array of image URLs to process
    
    Returns:
        ZIP file containing all processed images
    """
    import json
    
    start_time = time.time()
    
    try:
        # Parse inputs
        params = json.loads(operation_params)
        urls = json.loads(image_urls)
        
        # Validate batch size
        if len(urls) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size limited to 50 images"
            )
        
        if len(urls) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No images provided"
            )
        
        # Verify campaign access
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

        # Process images
        processed_images = []
        failed_images = []

        for idx, image_url in enumerate(urls):
            try:
                print(f"Processing image {idx + 1}/{len(urls)}: {image_url}")

                # Download original image using centralized R2 storage
                if image_url.startswith("http"):
                    original_image_data = await r2_storage.download_from_url(image_url)
                    r2_path = r2_storage.extract_path_from_url(image_url)
                    original_image_path = r2_path or image_url
                else:
                    original_image_data = await r2_storage.download_file(image_url)
                    original_image_path = image_url
                
                # Route to appropriate operation
                edited_image_data = None
                metadata = {}
                
                if operation_type == "background-remove":
                    edited_image_data, metadata = await stability_service.remove_background(
                        original_image_data,
                        output_format=params.get('output_format', 'png')
                    )
                
                elif operation_type == "upscale":
                    edited_image_data, metadata = await stability_service.upscale_image(
                        original_image_data,
                        prompt=params.get('prompt', ''),
                        negative_prompt=params.get('negative_prompt'),
                        creativity=params.get('creativity', 0.35),
                        seed=params.get('seed', 0),
                        output_format=params.get('output_format', 'png')
                    )
                
                elif operation_type == "search-replace":
                    edited_image_data, metadata = await stability_service.search_and_replace(
                        original_image_data,
                        search_prompt=params.get('search_prompt', ''),
                        prompt=params.get('prompt', ''),
                        negative_prompt=params.get('negative_prompt'),
                        seed=params.get('seed', 0),
                        output_format=params.get('output_format', 'png')
                    )
                
                elif operation_type == "outpaint":
                    edited_image_data, metadata = await stability_service.outpaint_image(
                        original_image_data,
                        prompt=params.get('prompt', ''),
                        left=params.get('left', 0),
                        right=params.get('right', 0),
                        up=params.get('up', 0),
                        down=params.get('down', 0),
                        creativity=params.get('creativity', 0.5),
                        seed=params.get('seed', 0),
                        output_format=params.get('output_format', 'png')
                    )
                
                # Add more operations as needed
                else:
                    raise ValueError(f"Unsupported operation type: {operation_type}")

                # Upload edited image using centralized R2 storage
                output_format = params.get('output_format', 'png')
                filename = R2Storage.generate_image_filename(
                    operation=f"batch_{operation_type}",
                    original_filename=original_image_path.split('/')[-1] if original_image_path else None,
                    campaign_id=campaign_id,
                    extension=output_format
                )
                edited_r2_path, edited_public_url = await r2_storage.upload_image(
                    campaign_id=campaign_id,
                    folder="edited",
                    filename=filename,
                    image_bytes=edited_image_data,
                    content_type=f"image/{output_format}"
                )
                
                processed_images.append({
                    'original_url': image_url,
                    'edited_url': edited_public_url,
                    'edited_path': edited_r2_path,
                    'filename': f"batch_{idx + 1}_{operation_type}.{output_format}"
                })
                
                # Log to database
                api_cost = stability_service.estimate_cost_credits(operation_type)
                query = text("""
                    INSERT INTO image_edits
                    (user_id, campaign_id, original_image_path, edited_image_path,
                     operation_type, operation_params, stability_model, api_cost_credits,
                     processing_time_ms, success, created_at, updated_at)
                    VALUES
                    (:user_id, :campaign_id, :original_path, :edited_path,
                     :op_type, :params, :model, :cost,
                     :time_ms, :success, NOW(), NOW())
                """)
                
                await db.execute(
                    query,
                    {
                        "user_id": current_user.id,
                        "campaign_id": campaign_id,
                        "original_path": original_image_path,
                        "edited_path": edited_r2_path,
                        "op_type": f"batch_{operation_type}",
                        "params": json.dumps(params),
                        "model": metadata.get("model"),
                        "cost": api_cost,
                        "time_ms": 0,  # Individual time not tracked in batch
                        "success": True
                    }
                )
                
            except Exception as e:
                print(f"Failed to process image {idx + 1}: {str(e)}")
                failed_images.append({
                    'original_url': image_url,
                    'error': str(e)
                })
        
        await db.commit()
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "success": True,
            "total_images": len(urls),
            "processed_count": len(processed_images),
            "failed_count": len(failed_images),
            "processing_time_ms": processing_time_ms,
            "processed_images": processed_images,
            "failed_images": failed_images
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch processing failed: {str(e)}"
        )

@router.post("/save-filtered-image")
async def save_filtered_image(
    image: UploadFile = File(...),
    campaign_id: str = Form(...),
    operation: str = Form(default="filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save a client-side filtered/edited image (collage, filter, etc.) to R2 storage
    
    This endpoint receives an image that has already been processed on the client side
    (via canvas filters, collage creation, etc.) and saves it to R2 storage.
    """
    try:
        # Read the uploaded image bytes
        image_bytes = await image.read()
        
        # Verify campaign ownership
        result = await db.execute(
            select(Campaign).filter(
                Campaign.id == int(campaign_id),
                Campaign.user_id == current_user.id
            )
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found or access denied"
            )
        
        # Generate filename
        filename = r2_storage.generate_image_filename(
            operation=operation,
            campaign_id=campaign_id,
            extension="png"
        )
        
        # Upload to R2 in the "edited" folder
        r2_path, public_url = await r2_storage.upload_image(
            campaign_id=campaign_id,
            folder="edited",
            filename=filename,
            image_bytes=image_bytes,
            content_type="image/png"
        )
        
        # Log to database
        query = text("""
            INSERT INTO image_edits 
            (user_id, campaign_id, original_image_path, edited_image_path, 
             operation_type, operation_params, model_used, api_cost_usd, 
             processing_time_ms, success)
            VALUES 
            (:user_id, :campaign_id, :original_path, :edited_path, 
             :op_type, :params, :model, :cost, :time_ms, :success)
        """)
        
        await db.execute(
            query,
            {
                "user_id": current_user.id,
                "campaign_id": int(campaign_id),
                "original_path": "",  # Client-side operation, no original path
                "edited_path": r2_path,
                "op_type": operation,
                "params": json.dumps({"operation": operation}),
                "model": "client-side",
                "cost": 0.0,  # No API cost for client-side operations
                "time_ms": 0,
                "success": True
            }
        )
        
        await db.commit()
        
        return {
            "success": True,
            "image_url": public_url,
            "r2_path": r2_path,
            "message": f"{operation.capitalize()} image saved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving {operation} image: {str(e)}")
        await db.rollback()
        return {
            "success": False,
            "error": str(e)
        }