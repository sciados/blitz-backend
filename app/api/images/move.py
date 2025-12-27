"""
API endpoint for moving images to different R2 folders
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List
import httpx

from app.db.session import get_db
from app.db.models import User, Campaign, GeneratedImage
from app.api.deps import get_current_user
from app.utils.r2_storage import r2_client

router = APIRouter()


@router.post("/move", status_code=status.HTTP_200_OK)
async def move_images(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Move selected images to a different R2 folder.

    Expected payload:
    {
        "image_ids": [1, 2, 3],
        "destination_path": "campaignforge-storage/stock/"
    }
    """
    image_ids: List[int] = request.get("image_ids", [])
    destination_path: str = request.get("destination_path", "")

    if not image_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image IDs provided"
        )

    if not destination_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No destination path provided"
        )

    # Verify ownership of all images
    result = await db.execute(
        select(GeneratedImage)
        .join(Campaign)
        .where(
            GeneratedImage.id.in_(image_ids),
            Campaign.user_id == current_user.id
        )
    )
    images = result.scalars().all()

    if len(images) != len(image_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more images not found or access denied"
        )

    moved_count = 0
    errors = []

    for image in images:
        try:
            # Get current image URL
            current_url = image.image_url

            # Extract filename from current URL
            if "/" in current_url:
                filename = current_url.split("/")[-1]
            else:
                filename = current_url

            # Construct new path
            if destination_path.endswith("/"):
                new_path = destination_path + filename
            else:
                new_path = destination_path + "/" + filename

            # Move file in R2
            await r2_client.move_file(
                source_path=current_url,
                destination_path=new_path
            )

            # Update database record
            await db.execute(
                update(GeneratedImage)
                .where(GeneratedImage.id == image.id)
                .values(image_url=new_path)
            )

            moved_count += 1

        except Exception as e:
            errors.append(f"Failed to move image {image.id}: {str(e)}")

    await db.commit()

    if errors:
        return {
            "message": f"Moved {moved_count} out of {len(image_ids)} images",
            "moved_count": moved_count,
            "total_count": len(image_ids),
            "errors": errors
        }

    return {
        "message": f"Successfully moved {moved_count} images to {destination_path}",
        "moved_count": moved_count,
        "total_count": len(image_ids),
        "destination_path": destination_path
    }
