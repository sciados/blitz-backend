"""
Video Text Overlay API
Handles adding text overlays to videos using ffmpeg
"""

import os
import subprocess
import tempfile
import uuid
import asyncio
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.db.session import get_db
from app.db.models import VideoGeneration, Campaign
from app.auth import get_current_user
from app.db.models import User

router = APIRouter(prefix="/api/videos", tags=["videos"])


class VideoOverlayService:
    """Service for adding text overlays to videos"""

    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.current_user = current_user
        self.temp_dir = tempfile.gettempdir()

    async def add_text_overlays(
        self,
        video_url: str,
        text_layers: List[Dict[str, Any]],
        campaign_id: int
    ) -> Dict[str, Any]:
        """
        Add text overlays to video using ffmpeg

        Args:
            video_url: URL to source video
            text_layers: List of text layer configurations
            campaign_id: Campaign ID for tracking

        Returns:
            Dict with video_url and id of saved video
        """

        try:
            # Verify campaign ownership
            result = await self.db.execute(
                select(Campaign).where(
                    Campaign.id == campaign_id,
                    Campaign.user_id == self.current_user.id
                )
            )
            campaign = result.scalar_one_or_none()

            if not campaign:
                raise HTTPException(
                    status_code=404,
                    detail="Campaign not found"
                )

            # Download video from URL
            video_path = await self._download_video(video_url)

            # Create output path
            output_filename = f"video_overlay_{uuid.uuid4().hex[:8]}.mp4"
            output_path = os.path.join(self.temp_dir, output_filename)

            # Build ffmpeg command with text overlays
            ffmpeg_cmd = self._build_ffmpeg_command(video_path, output_path, text_layers)

            # Execute ffmpeg
            await self._execute_ffmpeg(ffmpeg_cmd)

            # Upload to R2
            final_url = await self._upload_to_r2(output_path, campaign_id, video_url)

            # Save to database
            video_record = VideoGeneration(
                user_id=self.current_user.id,
                campaign_id=campaign_id,
                task_id=f"overlay_{uuid.uuid4().hex[:16]}",  # Generate unique task ID
                provider="ffmpeg",
                model_name="text_overlay",
                generation_mode="text_overlay",
                prompt="Text overlay applied",
                video_url=final_url,
                status="completed",
                progress=100,
                cost=0.0,
                completed_at=datetime.utcnow()
            )

            self.db.add(video_record)
            await self.db.commit()
            await self.db.refresh(video_record)

            # Cleanup temp files
            self._cleanup_temp_files([video_path, output_path])

            return {
                "id": video_record.id,
                "video_url": final_url,
                "status": "success"
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to add text overlays: {str(e)}"
            )

    async def _download_video(self, video_url: str) -> str:
        """Download video from URL to temp file"""
        import aiohttp
        import aiofiles

        filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
        filepath = os.path.join(self.temp_dir, filename)

        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as response:
                response.raise_for_status()

                async with aiofiles.open(filepath, "wb") as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)

        return filepath

    def _build_ffmpeg_command(
        self,
        input_path: str,
        output_path: str,
        text_layers: List[Dict[str, Any]]
    ) -> List[str]:
        """Build ffmpeg command with text overlay filters"""

        # Detect video resolution first
        video_width, video_height = self._get_video_resolution(input_path)

        # Start with basic command
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", "",  # Will be filled with filter_complex
            "-c:a", "copy",  # Copy audio without re-encoding
            "-y",  # Overwrite output file
            output_path
        ]

        # Build filter_complex for text overlays
        filters = []

        for layer in text_layers:
            text = self._escape_text(layer["text"])
            # Use actual video dimensions instead of hard-coded 1920x1080
            x = int((layer["x"] / 100) * video_width)
            y = int((layer["y"] / 100) * video_height)

            font_size = layer["font_size"]
            font_family = layer.get("font_family", "Arial")
            font_color = self._hex_to_ffmpeg_color(layer["color"])

            # Find font path
            font_path = self._find_font_file(font_family)

            # Build text filter with timing
            start_time = layer["start_time"]
            duration = layer["duration"]

            # Basic text overlay with timing
            text_filter = (
                f"drawtext=text='{text}':"
                f"x={x}:y={y}:"
                f"fontsize={font_size}:"
                f"fontcolor={font_color}:"
                f"enable='between(t,{start_time},{start_time + duration})'"
            )

            # Add font if found
            if font_path:
                text_filter += f":fontfile='{font_path}'"

            # Add stroke if specified
            if layer.get("stroke_width", 0) > 0:
                stroke_color = self._hex_to_ffmpeg_color(layer.get("stroke_color", "#000000"))
                text_filter += f":borderw={layer['stroke_width']}:bordercolor={stroke_color}"

            filters.append(text_filter)

        # Join all filters
        filter_complex = ",".join(filters)
        cmd[4] = filter_complex  # Replace empty -vf with filter_complex

        return cmd

    def _get_video_resolution(self, video_path: str) -> tuple[int, int]:
        """Get video resolution using ffprobe"""
        import subprocess

        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=p=0",
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            width, height = map(int, result.stdout.strip().split(","))
            return width, height
        except Exception as e:
            # Fallback to default if detection fails
            print(f"Warning: Could not detect video resolution, using 1920x1080: {e}")
            return 1920, 1080

    def _find_font_file(self, font_family: str) -> str:
        """Find TTF font file for given font family"""
        import glob

        font_name = font_family.lower().strip()
        font_dirs = ["/app/app/fonts", "/tmp/fonts"]

        # Common font file patterns
        possible_names = [
            f"{font_name}.ttf",
            f"{font_name.replace(' ', '')}.ttf",
            f"{font_name.replace(' ', '-').lower()}.ttf",
        ]

        for font_dir in font_dirs:
            if not os.path.exists(font_dir):
                continue

            # Search for font files
            for pattern in possible_names:
                for font_file in glob.glob(os.path.join(font_dir, "**", pattern), recursive=True):
                    return font_file

        # Fallback: use a default font if available
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                # Try to find any TTF file as fallback
                for font_file in glob.glob(os.path.join(font_dir, "**/*.ttf"), recursive=True):
                    if "arial" in os.path.basename(font_file).lower():
                        return font_file

        return ""  # Return empty string if no font found

    async def _execute_ffmpeg(self, cmd: List[str]) -> None:
        """Execute ffmpeg command"""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown ffmpeg error"
            raise Exception(f"ffmpeg failed: {error_msg}")

    async def _upload_to_r2(self, video_path: str, campaign_id: int, original_url: str) -> str:
        """Upload processed video to R2 storage"""
        from app.services.storage_r2 import r2_storage
        import time
        import hashlib

        # Generate R2 key following the same pattern as images
        # Format: campaigns/{campaign_id}/videos/overlays/text_overlay_{timestamp}_{hash}.mp4
        timestamp = int(time.time())
        # Create hash from original URL to link versions
        url_hash = hashlib.md5(original_url.encode()).hexdigest()[:8]
        key = f"campaigns/{campaign_id}/videos/overlays/text_overlay_{timestamp}_{url_hash}.mp4"

        # Read file bytes
        with open(video_path, "rb") as f:
            file_bytes = f.read()

        # Upload to R2
        _, public_url = await r2_storage.upload_file(
            file_bytes=file_bytes,
            key=key,
            content_type="video/mp4"
        )

        # Return public URL
        return public_url

    def _cleanup_temp_files(self, filepaths: List[str]) -> None:
        """Clean up temporary files"""
        for filepath in filepaths:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                print(f"Warning: Failed to remove temp file {filepath}: {e}")

    def _escape_text(self, text: str) -> str:
        """Escape text for ffmpeg"""
        # Escape special characters for ffmpeg
        return text.replace("'", "\\'").replace(":", "\\:")

    def _hex_to_ffmpeg_color(self, hex_color: str) -> str:
        """Convert hex color to ffmpeg format (white@1.0)"""
        # Remove # if present
        hex_color = hex_color.lstrip("#")

        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # ffmpeg uses format like "white@0.5" or "0xRRGGBB"
        return f"0x{hex_color.upper()}"


@router.post("/text-overlay")
async def add_video_text_overlay(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add text overlays to a video

    Expected payload:
    {
        "video_url": "https://...",
        "text_layers": [
            {
                "id": "1",
                "text": "AquaSculpt addresses weight gain",
                "x": 50,
                "y": 85,
                "font_size": 48,
                "font_family": "Arial",
                "color": "#FFFFFF",
                "stroke_width": 2,
                "stroke_color": "#000000",
                "opacity": 1.0,
                "start_time": 0.0,
                "duration": 3.0,
                "animation_in": "fade",
                "animation_out": "fade"
            }
        ],
        "campaign_id": 123
    }
    """

    service = VideoOverlayService(db, current_user)
    result = await service.add_text_overlays(
        video_url=request["video_url"],
        text_layers=request["text_layers"],
        campaign_id=request["campaign_id"]
    )

    return result
