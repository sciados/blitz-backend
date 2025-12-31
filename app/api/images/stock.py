# app/api/images/stock.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import re
from datetime import datetime

from app.db.session import get_db
from app.db.models import User, GeneratedImage, Campaign
from app.auth import get_current_user
from app.utils.r2_storage import r2_storage

router = APIRouter()

# List of stock folder paths to search
STOCK_FOLDER_PATHS = [
    "backgrounds",
    "stock/images",
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
    - backgrounds
    - stock/images
    - overlays
    - frames
    - icons
    - templates

    This endpoint scans both:
    1. Database records for images that have been moved to stock folders
    2. Direct R2 folder listing to find existing stock images
    """
    stock_images = []
    seen_urls = set()

    try:
        # First, get database records for images in stock folders
        for stock_path in STOCK_FOLDER_PATHS:
            # Search for images with URLs containing the stock path
            query = select(GeneratedImage).where(
                GeneratedImage.image_url.like(f"%{stock_path}%")
            )

            result = await db.execute(query)
            images = result.scalars().all()

            for img in images:
                image_url = img.image_url
                if image_url not in seen_urls:
                    # Get filename from URL
                    if "/" in image_url:
                        filename = image_url.split("/")[-1]
                        # Extract folder path to determine category
                        folder_path = "/".join(image_url.split("/")[:-1])
                    else:
                        filename = image_url
                        folder_path = ""

                    # Determine folder category from path
                    folder_category = "Uncategorized"
                    for stock_path in STOCK_FOLDER_PATHS:
                        if stock_path in folder_path:
                            # Convert path to readable category name
                            if stock_path == "backgrounds":
                                folder_category = "Backgrounds"
                            elif stock_path == "stock/images":
                                folder_category = "Stock Images"
                            elif stock_path == "overlays":
                                folder_category = "Overlays"
                            elif stock_path == "frames":
                                folder_category = "Frames"
                            elif stock_path == "icons":
                                folder_category = "Icons"
                            elif stock_path == "templates":
                                folder_category = "Templates"
                            break

                    # Remove extension from filename for display name
                    name = filename
                    if "." in filename:
                        name = filename.rsplit(".", 1)[0]

                    stock_images.append({
                        "id": f"stock-{img.id}",
                        "url": image_url,
                        "name": name,
                        "folder": folder_category,
                        "prompt": getattr(img, 'prompt', f'Stock image: {filename}'),
                        "provider": getattr(img, 'provider', 'unknown'),
                        "created_at": img.created_at.isoformat() if img.created_at else None,
                    })
                    seen_urls.add(image_url)

        # Second, scan R2 folders directly to find images not in database
        if r2_storage.is_configured():
            import boto3
            from botocore.exceptions import ClientError

            for stock_path in STOCK_FOLDER_PATHS:
                try:
                    # List objects in this stock folder
                    paginator = r2_storage.client.get_paginator('list_objects_v2')
                    page_iterator = paginator.paginate(
                        Bucket=r2_storage.bucket_name,
                        Prefix=f"{stock_path}/"
                    )

                    for page in page_iterator:
                        if 'Contents' in page:
                            for obj in page['Contents']:
                                key = obj['Key']
                                # Skip if this is a folder marker
                                if key.endswith('/'):
                                    continue

                                # Construct the full URL
                                if r2_storage.public_url:
                                    image_url = f"{r2_storage.public_url}/{key}"
                                else:
                                    image_url = f"https://{r2_storage.bucket_name}.{r2_storage.account_id}.r2.dev/{key}"

                                # Only add if not already in the list
                                if image_url not in seen_urls:
                                    # Get filename from key
                                    filename = key.split('/')[-1]

                                    # Determine folder category from the stock path
                                    folder_category = "Uncategorized"
                                    for stock_path in STOCK_FOLDER_PATHS:
                                        if key.startswith(f"{stock_path}/"):
                                            # Convert path to readable category name
                                            if stock_path == "backgrounds":
                                                folder_category = "Backgrounds"
                                            elif stock_path == "stock/images":
                                                folder_category = "Stock Images"
                                            elif stock_path == "overlays":
                                                folder_category = "Overlays"
                                            elif stock_path == "frames":
                                                folder_category = "Frames"
                                            elif stock_path == "icons":
                                                folder_category = "Icons"
                                            elif stock_path == "templates":
                                                folder_category = "Templates"
                                            break

                                    # Remove extension from filename for display name
                                    name = filename
                                    if "." in filename:
                                        name = filename.rsplit(".", 1)[0]

                                    stock_images.append({
                                        "id": f"r2-{key}",
                                        "url": image_url,
                                        "name": name,
                                        "folder": folder_category,
                                        "prompt": f'Stock image: {filename}',
                                        "provider": 'r2-storage',
                                        "created_at": obj.get('LastModified', datetime.utcnow()).isoformat() if obj.get('LastModified') else None,
                                    })
                                    seen_urls.add(image_url)

                except ClientError as e:
                    print(f"Error scanning R2 folder {stock_path}: {e}")
                    # Continue with other folders even if one fails

        return {
            "images": stock_images,
            "total": len(stock_images),
            "folders_searched": STOCK_FOLDER_PATHS,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stock images: {str(e)}"
        )


@router.delete("/stock", status_code=status.HTTP_200_OK)
async def delete_stock_image(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a stock image from R2 storage.

    Expects a JSON body with:
    {
        "url": "full_url_to_image_in_r2"
    }

    Only accessible by admin users.
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete stock images"
        )

    # Get the image URL from request body
    image_url = request.get("url")
    if not image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image URL is required"
        )

    try:
        # Extract the R2 key from the full URL
        # URLs are in format: https://pub-c0ddba9f039845bda33be436955187cb.r2.dev/{key}
        # or: https://{bucket}.{account}.r2.dev/{key}
        if "/r2.dev/" in image_url:
            r2_key = image_url.split("/r2.dev/")[1]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image URL format"
            )

        # Delete from R2 storage if configured
        if r2_storage.is_configured():
            import boto3
            from botocore.exceptions import ClientError

            try:
                r2_storage.client.delete_object(
                    Bucket=r2_storage.bucket_name,
                    Key=r2_key
                )
            except ClientError as e:
                # If the file doesn't exist, that's okay (idempotent)
                if e.response['Error']['Code'] != 'NoSuchKey':
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to delete image from storage: {str(e)}"
                    )

        # Also check if there's a database record and delete it
        # Look for the image URL in generated_images table
        query = select(GeneratedImage).where(
            GeneratedImage.image_url == image_url
        )
        result = await db.execute(query)
        db_image = result.scalar_one_or_none()

        if db_image:
            await db.delete(db_image)
            await db.commit()

        return {
            "success": True,
            "message": "Stock image deleted successfully",
            "deleted_url": image_url
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete stock image: {str(e)}"
        )
