# 📦 app/api/product_assets.py
# NEW FILE - API endpoints for Product Asset management

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from PIL import Image
import io
import logging

from app.db.session import get_db
from app.db.models import ProductAsset, Campaign, User
from app.auth import get_current_user
from app.services.r2_storage import r2_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/product-assets", tags=["product-assets"])


# ============================================================================
# SCHEMAS
# ============================================================================

from pydantic import BaseModel, Field

class ProductAssetResponse(BaseModel):
    id: int
    campaign_id: int
    asset_url: str
    filename: str
    asset_type: str
    view_angle: Optional[str]
    has_transparency: bool
    width: int
    height: int
    title: Optional[str]
    description: Optional[str]
    is_featured: bool
    display_order: int
    times_used: int
    created_at: str
    
    class Config:
        from_attributes = True


class ProductAssetStats(BaseModel):
    total_assets: int
    transparent_assets: int
    featured_assets: int
    most_used_angle: Optional[str]
    total_uses: int
    quality_score: int  # 0-100


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_transparency(image: Image.Image) -> bool:
    """Check if image has transparent pixels"""
    if image.mode != 'RGBA':
        return False
    
    # Check if any pixel has alpha < 255
    alpha = image.split()[-1]
    return alpha.getextrema()[0] < 255


def calculate_quality_score(
    total_assets: int,
    transparent_count: int,
    unique_angles: int
) -> int:
    """Calculate asset library quality score (0-100)"""
    score = 0
    
    # Quantity (max 40 points)
    if total_assets >= 15:
        score += 40
    elif total_assets >= 10:
        score += 30
    elif total_assets >= 5:
        score += 20
    else:
        score += 10
    
    # Variety (max 30 points)
    if unique_angles >= 5:
        score += 30
    elif unique_angles >= 3:
        score += 20
    else:
        score += 10
    
    # Quality (max 30 points)
    transparency_ratio = transparent_count / total_assets if total_assets > 0 else 0
    if transparency_ratio == 1.0:
        score += 30
    elif transparency_ratio >= 0.8:
        score += 20
    else:
        score += 10
    
    return min(score, 100)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/{campaign_id}", status_code=status.HTTP_201_CREATED)
async def upload_product_asset(
    campaign_id: int,
    file: UploadFile = File(...),
    asset_type: str = Form(...),
    view_angle: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    is_featured: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProductAssetResponse:
    """
    Upload a product asset (transparent PNG)
    
    Product developers upload transparent product images that affiliates
    can use in the overlay tool to create promotional content.
    
    **Requirements:**
    - Must be PNG with transparency
    - Must own the campaign
    - Recommended size: 1024x1024 or larger
    """
    # Verify campaign ownership
    campaign_result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    campaign = campaign_result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found or access denied"
        )
    
    # Read and validate image
    try:
        file_bytes = await file.read()
        image = Image.open(io.BytesIO(file_bytes))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {str(e)}"
        )
    
    # Check format
    if image.format != 'PNG':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PNG images are supported. Please convert your image to PNG format."
        )
    
    # Check for RGBA mode (transparency support)
    if image.mode != 'RGBA':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image must have transparency channel (RGBA). Please remove the background first."
        )
    
    # Check if actually has transparent pixels
    has_transparency = check_transparency(image)
    
    if not has_transparency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image has no transparent areas. Please remove the background before uploading."
        )
    
    # Generate filename
    filename = r2_storage.generate_filename(
        prefix=f"asset_{asset_type}",
        extension="png",
        campaign_id=campaign_id
    )
    
    # Upload to R2: campaigns/{campaign_id}/assets/{filename}
    r2_path, asset_url = await r2_storage.upload_file(
        campaign_id=campaign_id,
        folder="assets",  # New folder for product assets
        filename=filename,
        file_bytes=file_bytes,
        content_type="image/png"
    )
    
    # Create database record
    product_asset = ProductAsset(
        campaign_id=campaign_id,
        user_id=current_user.id,
        asset_url=asset_url,
        r2_path=r2_path,
        filename=filename,
        asset_type=asset_type,
        view_angle=view_angle,
        has_transparency=True,
        width=image.width,
        height=image.height,
        file_size_bytes=len(file_bytes),
        content_type="image/png",
        title=title,
        description=description,
        is_featured=is_featured,
        display_order=0
    )
    
    db.add(product_asset)
    await db.commit()
    await db.refresh(product_asset)
    
    logger.info(f"Product asset uploaded: {asset_url} for campaign {campaign_id}")
    
    return ProductAssetResponse(
        id=product_asset.id,
        campaign_id=product_asset.campaign_id,
        asset_url=product_asset.asset_url,
        filename=product_asset.filename,
        asset_type=product_asset.asset_type,
        view_angle=product_asset.view_angle,
        has_transparency=product_asset.has_transparency,
        width=product_asset.width,
        height=product_asset.height,
        title=product_asset.title,
        description=product_asset.description,
        is_featured=product_asset.is_featured,
        display_order=product_asset.display_order,
        times_used=product_asset.times_used,
        created_at=product_asset.created_at.isoformat()
    )


@router.get("/{campaign_id}", response_model=List[ProductAssetResponse])
async def get_product_assets(
    campaign_id: int,
    asset_type: Optional[str] = None,
    view_angle: Optional[str] = None,
    featured_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all product assets for a campaign
    
    Affiliates with access to the campaign can retrieve these assets
    to use in the overlay tool for creating promotional content.
    """
    # Verify campaign access (user must have campaign or it must be in product library)
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = campaign_result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Build query with filters
    conditions = [ProductAsset.campaign_id == campaign_id]
    
    if asset_type:
        conditions.append(ProductAsset.asset_type == asset_type)
    
    if view_angle:
        conditions.append(ProductAsset.view_angle == view_angle)
    
    if featured_only:
        conditions.append(ProductAsset.is_featured == True)
    
    # Get assets ordered by featured, then display_order
    query = select(ProductAsset).where(
        and_(*conditions)
    ).order_by(
        ProductAsset.is_featured.desc(),
        ProductAsset.display_order,
        ProductAsset.created_at.desc()
    )
    
    result = await db.execute(query)
    assets = result.scalars().all()
    
    return [
        ProductAssetResponse(
            id=asset.id,
            campaign_id=asset.campaign_id,
            asset_url=asset.asset_url,
            filename=asset.filename,
            asset_type=asset.asset_type,
            view_angle=asset.view_angle,
            has_transparency=asset.has_transparency,
            width=asset.width,
            height=asset.height,
            title=asset.title,
            description=asset.description,
            is_featured=asset.is_featured,
            display_order=asset.display_order,
            times_used=asset.times_used,
            created_at=asset.created_at.isoformat()
        )
        for asset in assets
    ]


@router.get("/{campaign_id}/stats", response_model=ProductAssetStats)
async def get_asset_stats(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics about product assets for a campaign"""
    # Verify campaign ownership
    campaign_result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    campaign = campaign_result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found or access denied"
        )
    
    # Get all assets
    result = await db.execute(
        select(ProductAsset).where(ProductAsset.campaign_id == campaign_id)
    )
    assets = result.scalars().all()
    
    total_assets = len(assets)
    transparent_assets = sum(1 for a in assets if a.has_transparency)
    featured_assets = sum(1 for a in assets if a.is_featured)
    total_uses = sum(a.times_used for a in assets)
    
    # Get unique view angles
    unique_angles = len(set(a.view_angle for a in assets if a.view_angle))
    
    # Find most used angle
    angle_usage = {}
    for asset in assets:
        if asset.view_angle:
            angle_usage[asset.view_angle] = angle_usage.get(asset.view_angle, 0) + asset.times_used
    
    most_used_angle = max(angle_usage, key=angle_usage.get) if angle_usage else None
    
    # Calculate quality score
    quality_score = calculate_quality_score(
        total_assets=total_assets,
        transparent_count=transparent_assets,
        unique_angles=unique_angles
    )
    
    return ProductAssetStats(
        total_assets=total_assets,
        transparent_assets=transparent_assets,
        featured_assets=featured_assets,
        most_used_angle=most_used_angle,
        total_uses=total_uses,
        quality_score=quality_score
    )


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a product asset"""
    # Find asset
    result = await db.execute(
        select(ProductAsset).where(ProductAsset.id == asset_id)
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # Verify ownership
    if asset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this asset"
        )
    
    # Delete from R2
    try:
        await r2_storage.delete_file(asset.r2_path)
    except Exception as e:
        logger.warning(f"Failed to delete asset from R2: {e}")
    
    # Delete from database
    await db.delete(asset)
    await db.commit()
    
    logger.info(f"Deleted product asset {asset_id}")
    
    return None