"""
API endpoint for moving videos to different R2 folders
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from typing import List
import httpx

from app.db.session import get_db
from app.db.models import User, Campaign, VideoGeneration
from app.auth import get_current_user
from app.utils.r2_storage import r2_storage

router = APIRouter()

# Whitelist of allowed destination folders
ALLOWED_FOLDERS = [
    "campaignforge-storage/stock/",           # Global stock (all users can write)
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

    # Check subscription tier
    if user.subscription_tier in ["pro", "business", "Pro Marketer"]:
        return True

    # Check user_type (for backward compatibility)
    if user.user_type in ["Business", "Admin", "Pro Marketer"]:
        return True

    return False


@router.post("/move", status_code=status.HTTP_200_OK)
async def move_videos(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Move selected videos to a different R2 folder.

    Expected payload:
    {
        "video_ids": [1, 2, 3],
        "destination_path": "campaignforge-storage/stock/"
    }

    Access Control:
    - Admin: Full access (read/write/delete)
    - Pro/Business users: Can add to stock folders (read/write)
    - Regular users: Cannot access stock folders
    """
    video_ids: List[int] = request.get("video_ids", [])
    destination_path: str = request.get("destination_path", "")

    if not video_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No video IDs provided"
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
            detail="Stock folders are only accessible to Pro and Business subscribers. Please upgrade your account to add videos to shared folders."
        )

    # Verify ownership of all videos
    result = await db.execute(
        text("""
            SELECT id, video_url, r2_key
            FROM video_generations
            WHERE id = ANY(:video_ids)
            AND user_id = :user_id
        """),
        {"video_ids": video_ids, "user_id": current_user.id}
    )
    videos = result.fetchall()

    if len(videos) != len(video_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more videos not found or access denied"
        )

    moved_count = 0
    errors = []

    for video_id, video_url, r2_key in videos:
        try:
            # Get current video URL
            current_url = video_url or r2_key

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
            r2_storage.move_file(
                source_path=current_url,
                destination_path=new_path
            )

            # Update database record
            await db.execute(
                text("""
                    UPDATE video_generations
                    SET video_url = :new_url, r2_key = :new_key
                    WHERE id = :video_id
                """),
                {
                    "video_id": video_id,
                    "new_url": new_path,
                    "new_key": new_path
                }
            )

            moved_count += 1

        except Exception as e:
            errors.append(f"Failed to move video {video_id}: {str(e)}")

    await db.commit()

    if errors:
        return {
            "message": f"Moved {moved_count} out of {len(video_ids)} videos",
            "moved_count": moved_count,
            "total_count": len(video_ids),
            "errors": errors
        }

    return {
        "message": f"Successfully moved {moved_count} videos to {destination_path}",
        "moved_count": moved_count,
        "total_count": len(video_ids),
        "destination_path": destination_path
    }
