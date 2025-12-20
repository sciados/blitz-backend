"""
Admin endpoint to generate thumbnails for existing videos
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any
import logging

from app.db.session import get_db
from app.db.models import User, VideoGeneration
from app.auth import get_current_user
from app.services.video_thumbnail_generator import video_thumbnail_generator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/videos/generate-thumbnails")
async def generate_missing_thumbnails(
    background_tasks: BackgroundTasks,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate thumbnails for videos that don't have them

    This is an admin-only endpoint that:
    1. Finds videos without thumbnails
    2. Generates thumbnails using ffmpeg
    3. Uploads them to R2
    4. Updates the database

    Args:
        limit: Maximum number of videos to process (default: 50)

    Returns:
        Information about the batch job
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    try:
        # Find videos without thumbnails
        result = await db.execute(
            text("""
                SELECT id, video_url, campaign_id
                FROM video_generations
                WHERE thumbnail_url IS NULL
                AND status = 'completed'
                AND video_url IS NOT NULL
                LIMIT :limit
            """),
            {"limit": limit}
        )
        videos = result.fetchall()

        if not videos:
            return {
                "status": "no_videos",
                "message": "No videos found without thumbnails",
                "processed": 0
            }

        # Start background task to process videos
        background_tasks.add_task(
            process_thumbnail_batch,
            videos=videos,
            db=db
        )

        return {
            "status": "started",
            "message": f"Started thumbnail generation for {len(videos)} videos",
            "count": len(videos),
            "job_id": f"thumbnails_{len(videos)}_{len(videos[0]) if videos else 0}"
        }

    except Exception as e:
        logger.error(f"Failed to start thumbnail generation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start thumbnail generation: {str(e)}"
        )


async def process_thumbnail_batch(videos: List, db: AsyncSession):
    """
    Background task to process thumbnail generation

    Args:
        videos: List of video tuples (id, video_url, campaign_id)
        db: Database session
    """
    from app.services.video_thumbnail_generator import video_thumbnail_generator

    success_count = 0
    error_count = 0
    errors = []

    for video_id, video_url, campaign_id in videos:
        try:
            logger.info(f"Generating thumbnail for video {video_id}")

            # Generate thumbnail
            thumbnail_url = await video_thumbnail_generator.generate_thumbnail(
                video_url=video_url,
                campaign_id=campaign_id or 0,
                timestamp=1.0,
                width=320,
                height=180
            )

            # Update database
            await db.execute(
                text("UPDATE video_generations SET thumbnail_url = :thumb WHERE id = :id"),
                {"thumb": thumbnail_url, "id": video_id}
            )
            await db.commit()

            logger.info(f"✅ Video {video_id} thumbnail generated")
            success_count += 1

        except Exception as e:
            logger.error(f"❌ Failed to generate thumbnail for video {video_id}: {e}")
            error_count += 1
            errors.append({
                "video_id": video_id,
                "error": str(e)
            })

    logger.info(
        f"Thumbnail generation complete: {success_count} success, {error_count} errors"
    )


@router.get("/videos/thumbnails/status")
async def get_thumbnail_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics about thumbnail coverage

    Returns:
        Statistics about which videos have thumbnails
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    try:
        # Get counts
        result = await db.execute(
            text("""
                SELECT
                    COUNT(*) as total_videos,
                    COUNT(thumbnail_url) as videos_with_thumbnails,
                    COUNT(*) - COUNT(thumbnail_url) as videos_without_thumbnails
                FROM video_generations
                WHERE status = 'completed'
            """)
        )
        stats = result.fetchone()

        return {
            "total_videos": stats[0],
            "videos_with_thumbnails": stats[1],
            "videos_without_thumbnails": stats[2],
            "coverage_percentage": round((stats[1] / stats[0] * 100) if stats[0] > 0 else 0, 2)
        }

    except Exception as e:
        logger.error(f"Failed to get thumbnail status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get thumbnail status: {str(e)}"
        )
