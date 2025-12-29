# src/app/api/images/move.py

"""
API endpoint for moving images to different R2 folders
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import urllib.parse
from sqlalchemy import select, update
from typing import List
import httpx

from app.db.session import get_db
from app.db.models import User, Campaign, GeneratedImage
from app.auth import get_current_user
from app.utils.r2_storage import r2_storage

router = APIRouter()

# Whitelist of allowed destination folders
ALLOWED_FOLDERS = [
    "campaignforge-storage/stock/",           # Global stock (all users can write)
    "campaignforge-storage/stock/images/",    # Stock images subfolder
    "campaignforge-storage/backgrounds/",     # Backgrounds (all users can write)
    "campaignforge-storage/overlays/",        # Overlays (all users can write)
    "campaignforge-storage/frames/",          # Frames (all users can write)
    "campaignforge-storage/icons/",           # Icons (all users can write)
    "campaignforge-storage/templates/",       # Templates (all users can write)
]

def is_allowed_destination(path: str) -> bool:
    """Check if destination path is in the whitelist"""
    for allowed_path in ALLOWED_FOLDERS:
        if path.startswith(allowed_path):
            return True
    # Also allow user-specific folders
    if "campaignforge-storage/users/" in path:
        return True
    return False


def can_write_to_stock(user: User) -> bool:
    """
    Check if user can write to stock/shared folders
    - Admin: full access
    - Business/Pro subscription: can add but not delete
    - Regular users: no access
    """
    # Admins have full access
    if user.role == "admin":
        return True

    # Check subscription tier (lowercase only - matches database schema)
    if user.subscription_tier in ["pro", "business"]:
        return True

    # Check user_type (for backward compatibility - lowercase)
    if user.user_type in ["business", "admin"]:
        return True

    return False


def can_delete_from_stock(user: User) -> bool:
    """
    Check if user can delete from stock/shared folders
    - Only Admin can delete from stock folders
    - Pro/Business users cannot delete from stock (only add)
    - Regular users: no access
    """
    # Only admins can delete from stock folders
    if user.role == "admin":
        return True

    return False


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

    Access Control:
    - Admin: Full access (read/write/delete)
    - Pro/Business users: Can add to stock folders (read/write)
    - Regular users: Cannot access stock folders
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

    # Validate destination path is in whitelist
    if not is_allowed_destination(destination_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Destination path not allowed. Allowed paths: {', '.join(ALLOWED_FOLDERS)} or user-specific folders under campaignforge-storage/users/"
        )

    # Check if user can write to stock/shared folders
    is_stock_folder = any(
        destination_path.startswith(folder.rstrip("/"))
        for folder in ALLOWED_FOLDERS
        if "stock" in folder or "backgrounds" in folder or "overlays" in folder
    )

    if is_stock_folder and not can_write_to_stock(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Stock folders are only accessible to Pro and Business subscribers. Please upgrade your account to add images to shared folders."
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

            # Handle proxied URLs - extract the actual R2 URL from the proxy parameter
            if "/api/images/proxy?" in current_url:
                # Extract the actual R2 URL from the proxy parameter
                # e.g., /api/images/proxy?url=https://pub-xxx.r2.dev/campaigns/33/generated_images/image.png
                parsed = urllib.parse.urlparse(current_url)
                query_params = urllib.parse.parse_qs(parsed.query)
                if 'url' in query_params:
                    actual_r2_url = query_params['url'][0]
                else:
                    actual_r2_url = current_url
            else:
                actual_r2_url = current_url

            # Extract the R2 key (path) from the actual URL
            if r2_storage.public_url and actual_r2_url.startswith(r2_storage.public_url):
                # Remove public URL prefix to get R2 key
                r2_key = actual_r2_url.replace(f"{r2_storage.public_url}/", "")
            else:
                # Parse from R2.dev URL
                parts = actual_r2_url.split(".r2.dev/")
                if len(parts) > 1:
                    r2_key = parts[1]
                else:
                    # Fallback: treat as filename only
                    r2_key = actual_r2_url.split("/")[-1]

            # Extract filename for destination
            if "/" in actual_r2_url:
                filename = actual_r2_url.split("/")[-1]
            else:
                filename = actual_r2_url

            # Construct new R2 key (not full URL, and NOT including bucket name)
            # Remove bucket name prefix from destination_path if present
            bucket_name = r2_storage.bucket_name
            clean_destination_path = destination_path
            if destination_path.startswith(bucket_name + "/"):
                clean_destination_path = destination_path[len(bucket_name + "/"):]

            # Now construct the R2 key with just the path within the bucket
            if clean_destination_path.endswith("/"):
                new_r2_key = clean_destination_path + filename
            else:
                new_r2_key = clean_destination_path + "/" + filename

            # Move file in R2 using R2 keys
            move_success = r2_storage.move_file(
                source_path=r2_key,
                destination_path=new_r2_key
            )

            # Only update database if move was successful
            if move_success:
                # Construct the full public URL for storage in database
                if r2_storage.public_url:
                    # Ensure public_url uses https:// protocol
                    public_url = r2_storage.public_url
                    if not public_url.startswith(('http://', 'https://')):
                        public_url = f"https://{public_url}"
                    new_image_url = f"{public_url}/{new_r2_key}"
                else:
                    # Fallback to R2.dev URL with https://
                    new_image_url = f"https://{r2_storage.bucket_name}.{r2_storage.account_id}.r2.dev/{new_r2_key}"

                # Update database record with the new full URL
                await db.execute(
                    update(GeneratedImage)
                    .where(GeneratedImage.id == image.id)
                    .values(image_url=new_image_url)
                )
                moved_count += 1
            else:
                # Move failed - this means the source file doesn't exist
                # Check if this is an enhanced image with a base_image_url
                if hasattr(image, 'metadata') and image.metadata and 'base_image_url' in image.metadata:
                    original_url = image.metadata.get('base_image_url')
                    if original_url and original_url != current_url:
                        # Restore to original location
                        await db.execute(
                            update(GeneratedImage)
                            .where(GeneratedImage.id == image.id)
                            .values(image_url=original_url)
                        )
                        errors.append(f"Image {image.id}: Restored to original location (enhanced images cannot be moved from temp storage)")
                    else:
                        errors.append(f"Failed to move image {image.id}: Source file not found at {r2_key}")
                else:
                    errors.append(f"Failed to move image {image.id}: Source file not found at {r2_key}")
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
