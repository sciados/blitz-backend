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

from app.db.session import get_db

router = APIRouter(prefix="/api/videos", tags=["videos"])


class VideoOverlayService:
    """Service for adding text overlays to videos"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.temp_dir = tempfile.gettempdir()

    async def add_text_overlays(
        self,
        video_url: str,
        text_layers: List[Dict[str, Any]],
        campaign_id: int
    ) -> Dict[str, str]:
        """
        Add text overlays to video using ffmpeg

        Args:
            video_url: URL to source video
            text_layers: List of text layer configurations
            campaign_id: Campaign ID for tracking

        Returns:
            Dict with video_url of processed video
        """

        try:
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
            final_url = await self._upload_to_r2(output_path)

            # Cleanup temp files
            self._cleanup_temp_files([video_path, output_path])

            return {
                "video_url": final_url,
                "status": "success"
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to add text overlays: {str(e)}"
            )

    async def _download_video(self, video_url: str) -> str:
        """Download video from URL to temp file"""
        import requests

        response = requests.get(video_url)
        response.raise_for_status()

        filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
        filepath = os.path.join(self.temp_dir, filename)

        with open(filepath, "wb") as f:
            f.write(response.content)

        return filepath

    def _build_ffmpeg_command(
        self,
        input_path: str,
        output_path: str,
        text_layers: List[Dict[str, Any]]
    ) -> List[str]:
        """Build ffmpeg command with text overlay filters"""

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
            x = int((layer["x"] / 100) * 1920)  # Assuming 1920px width, adjust as needed
            y = int((layer["y"] / 100) * 1080)  # Assuming 1080px height

            font_size = layer["font_size"]
            font_color = self._hex_to_ffmpeg_color(layer["color"])

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

            # Add stroke if specified
            if layer.get("stroke_width", 0) > 0:
                stroke_color = self._hex_to_ffmpeg_color(layer.get("stroke_color", "#000000"))
                text_filter += f":borderw={layer['stroke_width']}:bordercolor={stroke_color}"

            filters.append(text_filter)

        # Join all filters
        filter_complex = ",".join(filters)
        cmd[4] = filter_complex  # Replace empty -vf with filter_complex

        return cmd

    async def _execute_ffmpeg(self, cmd: List[str]) -> None:
        """Execute ffmpeg command"""
        process = await subprocess.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            loop=asyncio.get_event_loop()
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown ffmpeg error"
            raise Exception(f"ffmpeg failed: {error_msg}")

    async def _upload_to_r2(self, video_path: str) -> str:
        """Upload processed video to R2 storage"""
        from app.utils.r2_storage import r2_client

        # Generate R2 key
        key = f"videos/overlays/{uuid.uuid4().hex[:8]}.mp4"

        # Upload to R2
        with open(video_path, "rb") as f:
            await r2_client.upload_file(key, f, "video/mp4")

        # Return public URL
        return r2_client.get_public_url(key)

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

    service = VideoOverlayService(db)
    result = await service.add_text_overlays(
        video_url=request["video_url"],
        text_layers=request["text_layers"],
        campaign_id=request["campaign_id"]
    )

    return result
