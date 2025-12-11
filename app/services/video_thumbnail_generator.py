"""
Video Thumbnail Generator Service
Extracts thumbnail images from videos using ffmpeg
"""

import asyncio
import subprocess
import tempfile
import os
import httpx
from typing import Optional
import logging

from app.services.storage_r2 import r2_storage

logger = logging.getLogger(__name__)


class VideoThumbnailGenerator:
    """Generate thumbnail images from video files"""

    async def generate_thumbnail(
        self,
        video_url: str,
        campaign_id: int,
        timestamp: float = 1.0,
        width: int = 320,
        height: int = 180
    ) -> str:
        """
        Generate a thumbnail from a video URL

        Args:
            video_url: URL of the video
            campaign_id: Campaign ID for R2 storage path
            timestamp: Time in seconds to extract frame from
            width: Thumbnail width
            height: Thumbnail height

        Returns:
            Public URL of the thumbnail in R2
        """
        temp_dir = tempfile.gettempdir()
        input_path = None
        output_path = None

        try:
            # Download video to temp file
            input_path = await self._download_video(video_url, temp_dir)

            # Generate thumbnail path
            import time
            import hashlib
            import uuid

            timestamp_str = int(time.time())
            url_hash = hashlib.md5(video_url.encode()).hexdigest()[:8]
            output_filename = f"thumb_{timestamp_str}_{url_hash}.jpg"
            output_path = os.path.join(temp_dir, output_filename)

            # Build ffmpeg command to extract frame
            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-ss", str(timestamp),
                "-vframes", "1",
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                "-q:v", "2",  # High quality
                "-y",  # Overwrite output
                output_path
            ]

            logger.info(f"Generating thumbnail: {' '.join(cmd)}")

            # Execute ffmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown ffmpeg error"
                raise Exception(f"ffmpeg failed: {error_msg}")

            if not os.path.exists(output_path):
                raise Exception("Thumbnail file was not created")

            # Upload to R2
            r2_key = f"campaigns/{campaign_id}/videos/thumbnails/{output_filename}"

            with open(output_path, "rb") as f:
                file_bytes = f.read()

            _, public_url = await r2_storage.upload_file(
                file_bytes=file_bytes,
                key=r2_key,
                content_type="image/jpeg"
            )

            logger.info(f"✅ Thumbnail generated and uploaded: {public_url}")
            return public_url

        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            raise

        finally:
            # Cleanup temp files
            if input_path and os.path.exists(input_path):
                os.remove(input_path)
            if output_path and os.path.exists(output_path):
                os.remove(output_path)

    async def _download_video(self, video_url: str, temp_dir: str) -> str:
        """Download video from URL to temp file"""
        import uuid

        filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
        filepath = os.path.join(temp_dir, filename)

        async with httpx.AsyncClient(timeout=60.0) as session:
            async with session.get(video_url) as response:
                response.raise_for_status()

                with open(filepath, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)

        return filepath

    async def generate_thumbnail_from_file(
        self,
        video_path: str,
        campaign_id: int,
        timestamp: float = 1.0,
        width: int = 320,
        height: int = 180
    ) -> str:
        """
        Generate a thumbnail from a local video file

        Args:
            video_path: Path to local video file
            campaign_id: Campaign ID for R2 storage path
            timestamp: Time in seconds to extract frame from
            width: Thumbnail width
            height: Thumbnail height

        Returns:
            Public URL of the thumbnail in R2
        """
        import time
        import hashlib
        import uuid

        temp_dir = tempfile.gettempdir()
        output_filename = f"thumb_{int(time.time())}_{uuid.uuid4().hex[:8]}.jpg"
        output_path = os.path.join(temp_dir, output_filename)

        try:
            # Build ffmpeg command
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-ss", str(timestamp),
                "-vframes", "1",
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                "-q:v", "2",
                "-y",
                output_path
            ]

            logger.info(f"Generating thumbnail from file: {' '.join(cmd)}")

            # Execute ffmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown ffmpeg error"
                raise Exception(f"ffmpeg failed: {error_msg}")

            # Upload to R2
            r2_key = f"campaigns/{campaign_id}/videos/thumbnails/{output_filename}"

            with open(output_path, "rb") as f:
                file_bytes = f.read()

            _, public_url = await r2_storage.upload_file(
                file_bytes=file_bytes,
                key=r2_key,
                content_type="image/jpeg"
            )

            logger.info(f"✅ Thumbnail generated and uploaded: {public_url}")
            return public_url

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    async def extract_thumbnail_options(
        self,
        video_path: str,
        video_duration: float,
        campaign_id: int,
        num_options: int = 5,
        width: int = 320,
        height: int = 180
    ) -> list[dict]:
        """
        Extract multiple thumbnail options from a video

        Args:
            video_path: Path to local video file
            video_duration: Duration of the video in seconds
            campaign_id: Campaign ID for R2 storage path
            num_options: Number of thumbnail options to generate
            width: Thumbnail width
            height: Thumbnail height

        Returns:
            List of dicts with {timestamp, url, file_path}
        """
        import time
        import uuid
        import base64

        temp_dir = tempfile.gettempdir()
        thumbnail_urls = []

        try:
            # Calculate timestamps to sample (avoiding very beginning and end)
            # Start at 1 second or 10% of duration, whichever is smaller
            start_time = min(1.0, video_duration * 0.1)
            # End at 90% of duration
            end_time = video_duration * 0.9

            # Generate evenly spaced timestamps
            timestamps = []
            for i in range(num_options):
                if num_options == 1:
                    timestamp = start_time
                else:
                    timestamp = start_time + (i * (end_time - start_time) / (num_options - 1))
                timestamps.append(timestamp)

            # Generate thumbnails at each timestamp
            for i, timestamp in enumerate(timestamps):
                output_filename = f"thumb_preview_{int(time.time())}_{i}_{uuid.uuid4().hex[:8]}.jpg"
                output_path = os.path.join(temp_dir, output_filename)

                # Build ffmpeg command
                cmd = [
                    "ffmpeg",
                    "-i", video_path,
                    "-ss", str(timestamp),
                    "-vframes", "1",
                    "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                    "-q:v", "2",
                    "-y",
                    output_path
                ]

                # Execute ffmpeg
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Unknown ffmpeg error"
                    logger.warning(f"Failed to generate thumbnail at {timestamp}s: {error_msg}")
                    continue

                # Read file and encode as base64 for preview (don't upload yet)
                with open(output_path, "rb") as f:
                    file_bytes = f.read()
                    base64_data = base64.b64encode(file_bytes).decode("utf-8")
                    data_url = f"data:image/jpeg;base64,{base64_data}"

                thumbnail_urls.append({
                    "timestamp": round(timestamp, 2),
                    "data_url": data_url,
                    "file_path": output_path
                })

                # Clean up file after adding to list
                if os.path.exists(output_path):
                    os.remove(output_path)

            return thumbnail_urls

        except Exception as e:
            logger.error(f"Failed to extract thumbnail options: {e}")
            # Clean up any remaining files
            for thumb in thumbnail_urls:
                if os.path.exists(thumb.get("file_path")):
                    os.remove(thumb.get("file_path"))
            raise


# Global instance
video_thumbnail_generator = VideoThumbnailGenerator()
