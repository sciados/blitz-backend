# app/api/overlays.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from typing import Optional, List
from pydantic import BaseModel
from app.db.session import get_db
from app.db.models import User, Campaign, ProductImageOverlay
from app.auth import get_current_user

router = APIRouter(prefix="/api", tags=["overlays"])

class CreateOverlayRequest(BaseModel):
    image_url: str
    image_source: str
    position_x: float = 0.5
    position_y: float = 0.5
    scale: float = 1.0
    rotation: float = 0.0
    opacity: float = 1.0
    z_index: int = 1

@router.post("/campaigns/{campaign_id}/overlays")
async def create_overlay(
    campaign_id: int,
    request: CreateOverlayRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    overlay = ProductImageOverlay(
        campaign_id=campaign_id,
        image_url=request.image_url,
        image_source=request.image_source,
        position_x=request.position_x,
        position_y=request.position_y,
        scale=request.scale,
        rotation=request.rotation,
        opacity=request.opacity,
        z_index=request.z_index,
        created_by=current_user.id
    )
    db.add(overlay)
    await db.commit()
    await db.refresh(overlay)
    return overlay

@router.get("/campaigns/{campaign_id}/overlays")
async def get_overlays(campaign_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductImageOverlay).where(ProductImageOverlay.campaign_id == campaign_id)
    )
    overlays = result.scalars().all()
    return overlays

@router.get("/overlays/{overlay_id}")
async def get_overlay(overlay_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductImageOverlay).where(ProductImageOverlay.id == overlay_id)
    )
    overlay = result.scalar_one_or_none()
    if not overlay:
        raise HTTPException(status_code=404, detail="Overlay not found")

    # Check campaign ownership
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == overlay.campaign_id, Campaign.user_id == current_user.id)
    )
    if not campaign_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized")

    return overlay

@router.put("/overlays/{overlay_id}")
async def update_overlay(
    overlay_id: int,
    image_url: Optional[str] = None,
    position_x: Optional[float] = None,
    position_y: Optional[float] = None,
    scale: Optional[float] = None,
    rotation: Optional[float] = None,
    opacity: Optional[float] = None,
    z_index: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ProductImageOverlay).where(ProductImageOverlay.id == overlay_id)
    )
    overlay = result.scalar_one_or_none()
    if not overlay:
        raise HTTPException(status_code=404, detail="Overlay not found")

    # Check campaign ownership
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == overlay.campaign_id, Campaign.user_id == current_user.id)
    )
    if not campaign_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized")

    # Build update dict with non-None values
    update_data = {}
    if image_url is not None:
        update_data['image_url'] = image_url
    if position_x is not None:
        update_data['position_x'] = position_x
    if position_y is not None:
        update_data['position_y'] = position_y
    if scale is not None:
        update_data['scale'] = scale
    if rotation is not None:
        update_data['rotation'] = rotation
    if opacity is not None:
        update_data['opacity'] = opacity
    if z_index is not None:
        update_data['z_index'] = z_index

    if update_data:
        update_data['updated_at'] = func.now()
        await db.execute(
            update(ProductImageOverlay).where(ProductImageOverlay.id == overlay_id).values(**update_data)
        )
        await db.commit()

    result = await db.execute(
        select(ProductImageOverlay).where(ProductImageOverlay.id == overlay_id)
    )
    return result.scalar_one_or_none()

@router.delete("/overlays/{overlay_id}")
async def delete_overlay(overlay_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductImageOverlay).where(ProductImageOverlay.id == overlay_id)
    )
    overlay = result.scalar_one_or_none()
    if not overlay:
        raise HTTPException(status_code=404, detail="Overlay not found")

    # Check campaign ownership
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == overlay.campaign_id, Campaign.user_id == current_user.id)
    )
    if not campaign_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.execute(
        delete(ProductImageOverlay).where(ProductImageOverlay.id == overlay_id)
    )
    await db.commit()
    return {"message": "Overlay deleted successfully"}