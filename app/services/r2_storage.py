"""
Centralized R2 Storage Utility

Handles all R2 (Cloudflare R2) operations including path construction,
upload, download, and file management across the entire application.
"""

from datetime import datetime
from typing import Optional, Tuple, Union
import hashlib
import time
import logging

from botocore.config import Config
import aioboto3

from app.core.config import settings

logger = logging.getLogger(__name__)


class R2Storage:
    """
    Centralized R2 Storage Manager

    Provides unified interface for all R2 operations across the application.
    Automatically constructs paths using the base path and campaign organization.
    """

    # Base path for all campaign-related files
    BASE_PATH = "campaignforge-storage"

    # Supported folders
    FOLDERS = {
        "generated_files": "generated_files",
        "edited": "edited",
        "thumbnails": "generated_files/thumbnails",
        "temp": "generated_files/temp",
        "videos": "videos",
        "documents": "documents"
    }

    def __init__(self):
        """Initialize R2 storage client"""
        self.account_id = settings.R2_ACCOUNT_ID
        self.access_key_id = settings.R2_ACCESS_KEY_ID
        self.secret_access_key = settings.R2_SECRET_ACCESS_KEY
        self.bucket_name = settings.R2_BUCKET_NAME
        self.public_url_base = settings.R2_PUBLIC_URL_BASE

    def construct_path(
        self,
        campaign_id: Union[int, str],
        folder: str,
        filename: str,
        include_base: bool = True
    ) -> str:
        """
        Construct R2 path for a file

        Args:
            campaign_id: Campaign ID
            folder: Folder name from FOLDERS dict or custom folder
            filename: Name of the file
            include_base: Whether to include the BASE_PATH prefix

        Returns:
            Complete R2 path

        Example:
            construct_path(28, "edited", "image.png")
            # Returns: "campaignforge-storage/campaigns/28/edited/image.png"
        """
        # Get folder path (use FOLDERS dict if valid folder name)
        if folder in self.FOLDERS:
            folder_path = self.FOLDERS[folder]
        else:
            folder_path = folder

        # Build path
        base = f"{self.BASE_PATH}/campaigns/{campaign_id}"
        if folder_path:
            path = f"{base}/{folder_path}/{filename}"
        else:
            path = f"{base}/{filename}"

        return path

    async def upload_file(
        self,
        campaign_id: Union[int, str],
        folder: str,
        filename: str,
        file_bytes: bytes,
        content_type: str = "application/octet-stream",
        include_base: bool = True
    ) -> Tuple[str, str]:
        """
        Upload a file to R2

        Args:
            campaign_id: Campaign ID
            folder: Folder name (edited, generated_files, thumbnails, etc.)
            filename: Name of the file
            file_bytes: File content as bytes
            content_type: MIME type of the file
            include_base: Whether to include BASE_PATH in the key

        Returns:
            Tuple of (r2_path, public_url)
        """
        # Construct path
        r2_path = self.construct_path(campaign_id, folder, filename, include_base)

        logger.info(f"Uploading to R2: {r2_path}")

        # Upload to R2
        session = aioboto3.Session()

        async with session.client(
            's3',
            endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        ) as s3_client:
            await s3_client.put_object(
                Bucket=self.bucket_name,
                Key=r2_path,
                Body=file_bytes,
                ContentType=content_type,
                CacheControl='public, max-age=31536000'  # Cache for 1 year
            )

        # Generate public URL
        public_url = f"{self.public_url_base}/{r2_path}"

        logger.info(f"Uploaded successfully: {public_url}")

        return r2_path, public_url

    async def download_file(self, r2_path: str) -> bytes:
        """
        Download a file from R2

        Args:
            r2_path: R2 path to the file

        Returns:
            File content as bytes
        """
        logger.info(f"Downloading from R2: {r2_path}")

        session = aioboto3.Session()

        async with session.client(
            's3',
            endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        ) as s3_client:
            response = await s3_client.get_object(
                Bucket=self.bucket_name,
                Key=r2_path
            )
            file_bytes = await response['Body'].read()

        logger.info(f"Downloaded {len(file_bytes)} bytes")

        return file_bytes

    # Convenience methods for common operations

    async def upload_image(
        self,
        campaign_id: Union[int, str],
        folder: str,
        filename: str,
        image_bytes: bytes,
        content_type: str = "image/png"
    ) -> Tuple[str, str]:
        """
        Convenience method to upload an image

        Args:
            campaign_id: Campaign ID
            folder: Folder name
            filename: Image filename
            image_bytes: Image content as bytes
            content_type: Image MIME type

        Returns:
            Tuple of (r2_path, public_url)
        """
        return await self.upload_file(
            campaign_id=campaign_id,
            folder=folder,
            filename=filename,
            file_bytes=image_bytes,
            content_type=content_type
        )

    # Helper methods for generating filenames

    @staticmethod
    def generate_filename(
        prefix: str,
        extension: str = "png",
        campaign_id: Optional[Union[int, str]] = None,
        timestamp: Optional[float] = None,
        custom_hash: Optional[str] = None
    ) -> str:
        """
        Generate a standardized filename

        Args:
            prefix: Prefix for the filename (e.g., "draft", "enhanced", "overlay")
            extension: File extension (png, jpg, mp4, etc.)
            campaign_id: Optional campaign ID to include in hash
            timestamp: Optional timestamp (defaults to current time)
            custom_hash: Optional custom hash string

        Returns:
            Generated filename

        Example:
            generate_filename("draft", "png", 28)
            # Returns: "draft_20241223_143055_a1b2c3d4.png"
        """
        if timestamp is None:
            timestamp = time.time()

        # Create timestamp part
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Create hash
        if custom_hash:
            hash_part = custom_hash
        else:
            # Generate hash from timestamp and campaign_id
            hash_source = f"{timestamp}_{campaign_id}" if campaign_id else str(timestamp)
            hash_part = hashlib.md5(hash_source.encode()).hexdigest()[:8]

        # Build filename
        return f"{prefix}_{ts}_{hash_part}.{extension}"

    @staticmethod
    def generate_image_filename(
        operation: str,
        original_filename: Optional[str] = None,
        campaign_id: Optional[Union[int, str]] = None,
        extension: str = "png"
    ) -> str:
        """
        Generate filename for an image operation

        Args:
            operation: Type of operation (inpaint, erase, overlay, etc.)
            original_filename: Optional original filename
            campaign_id: Optional campaign ID
            extension: File extension

        Returns:
            Generated filename
        """
        timestamp = time.time()

        # Create timestamp
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Create hash from source
        if original_filename:
            hash_source = f"{operation}_{original_filename}_{timestamp}_{campaign_id}"
        else:
            hash_source = f"{operation}_{timestamp}_{campaign_id}"

        hash_part = hashlib.md5(hash_source.encode()).hexdigest()[:8]

        # Build filename
        if original_filename:
            # Extract original name without extension
            if "." in original_filename:
                orig_name = original_filename.rsplit(".", 1)[0]
            else:
                orig_name = original_filename
            return f"{operation}_{ts}_{hash_part}_{orig_name}.{extension}"
        else:
            return f"{operation}_{ts}_{hash_part}.{extension}"


# Global instance
r2_storage = R2Storage()
