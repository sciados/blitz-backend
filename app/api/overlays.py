# app/api/overlays.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.db.session import get_db
from app.db.models import User, Campaign, ProductImageOverlay
from app.auth import get_current_user

router = APIRouter(prefix="/api", tags=["overlays"])

@router.post("/campaigns/{campaign_id}/overlays")
async def create_overlay(
    campaign_id: int,
    image_url: str,
    image_source: str,
    position_x: float = 0.5,
    position_y: float = 0.5,
    scale: float = 1.0,
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
        image_url=image_url,
        image_source=image_source,
        position_x=position_x,
        position_y=position_y,
        scale=scale,
        created_by=current_user.id
    )
    db.add(overlay)
    await db.commit()
    return {"id": overlay.id}

@router.get("/campaigns/{campaign_id}/overlays")
async def get_overlays(campaign_id: int, current_user=Depends(get_current_user), db=Depends(get_db)):
    result = await db.execute(
        select(ProductImageOverlay).where(ProductImageOverlay.campaign_id == campaign_id)
    )
    overlays = result.scalars().all()
    return [{"id": o.id, "image_url": o.image_url, "position_x": o.position_x, "position_y": o.position_y, "scale": o.scale} for o in overlays]
