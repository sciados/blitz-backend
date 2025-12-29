# app/api/images/stock.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import re

from app.db.session import get_db
from app.db.models import User, GeneratedImage, Campaign
from app.auth import get_current_user
from app.utils.r2_storage import r2_storage

router = APIRouter()

# List of stock folder paths to search
STOCK_FOLDER_PATHS = [
    "stock/images",
    "backgrounds",
    "overlays",
    "frames",
    "icons",
    "templates",
]


@router.get("/stock", status_code=status.HTTP_200_OK)
async def get_stock_images(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all images from stock folders in R2 that users can use as backgrounds.

    Returns images from:
    - stock/images
    - backgrounds
    - overlays
    - frames
    - icons
    - templates

    Note: This returns images from the database that have been moved to stock folders.
    The actual image retrieval is done via the proxy endpoint using the stored URLs.
    """
    stock_images = []

    try:
        # Query database for images in stock folders
        # We look for images whose image_url contains stock folder paths
        for stock_path in STOCK_FOLDER_PATHS:
            # Search for images with URLs containing the stock path
            query = select(GeneratedImage).where(
                GeneratedImage.image_url.like(f"%{stock_path}%")
            )

            result = await db.execute(query)
            images = result.scalars().all()

            for img in images:
                # Extract just the filename from the full URL
                image_url = img.image_url
                # Get filename from URL
                if "/" in image_url:
                    filename = image_url.split("/")[-1]
                else:
                    filename = image_url

                stock_images.append({
                    "id": f"stock-{img.id}",
                    "url": image_url,
                    "prompt": getattr(img, 'prompt', f'Stock image: {filename}'),
                    "provider": getattr(img, 'provider', 'unknown'),
                    "created_at": img.created_at.isoformat() if img.created_at else None,
                })

        # Remove duplicates based on URL
        unique_images = []
        seen_urls = set()
        for img in stock_images:
            if img["url"] not in seen_urls:
                unique_images.append(img)
                seen_urls.add(img["url"])

        return {
            "images": unique_images,
            "total": len(unique_images),
            "folders_searched": STOCK_FOLDER_PATHS,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stock images: {str(e)}"
        )
