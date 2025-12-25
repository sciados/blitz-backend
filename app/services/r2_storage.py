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

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class R2Storage:
    """
    Centralized R2 Storage Manager

    Provides unified interface for all R2 operations across the application.
    Automatically constructs paths using the base path and campaign organization.
    """

    # Base path for all campaign-related files
    BASE_PATH = ""

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
        self.account_id = settings.CLOUDFLARE_ACCOUNT_ID
        self.access_key_id = settings.CLOUDFLARE_R2_ACCESS_KEY_ID
        self.secret_access_key = settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY
        self.bucket_name = settings.CLOUDFLARE_R2_BUCKET_NAME
        self.public_url_base = settings.CLOUDFLARE_R2_PUBLIC_URL

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
        if self.BASE_PATH:
            base = f"{self.BASE_PATH}campaigns/{campaign_id}"
        else:
            base = f"campaigns/{campaign_id}"

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

    async def download_from_url(self, url: str) -> bytes:
        """
        Download a file from a URL (R2 public URL or external)

        Args:
            url: URL of the file

        Returns:
            File content as bytes
        """
        import httpx

        logger.info(f"Downloading from URL: {url}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)

            if response.status_code != 200:
                raise Exception(f"Failed to download from {url}: {response.status_code}")

            return response.content

    def extract_path_from_url(self, url: str) -> Optional[str]:
        """
        Extract R2 path from a public URL

        Args:
            url: Public URL like https://pub-xxx.r2.dev/campaigns/123/image.png

        Returns:
            R2 path like campaigns/123/image.png
        """
        if self.public_url_base and url.startswith(self.public_url_base):
            return url.replace(f"{self.public_url_base}/", "")

        # Try to extract path after domain
        parts = url.split("/", 3)
        if len(parts) >= 4:
            return parts[3]

        return None

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
        Generate a shortened filename

        Args:
            prefix: Prefix for the filename (e.g., "draft", "enhanced", "overlay")
            extension: File extension (png, jpg, mp4, etc.)
            campaign_id: Optional campaign ID to include in hash
            timestamp: Optional timestamp (defaults to current time)
            custom_hash: Optional custom hash string

        Returns:
            Shortened filename

        Example:
            generate_filename("enhanced", "png", 28)
            # Returns: "enh_1225_001.png"
        """
        if timestamp is None:
            timestamp = time.time()

        # Create short date part (MMDD)
        ts = datetime.utcnow().strftime("%m%d")

        # Create short hash (4 chars)
        if custom_hash:
            hash_part = custom_hash[:4]
        else:
            # Generate hash from timestamp and campaign_id
            hash_source = f"{timestamp}_{campaign_id}" if campaign_id else str(timestamp)
            hash_part = hashlib.md5(hash_source.encode()).hexdigest()[:4]

        # Build shortened filename
        return f"{prefix}_{ts}_{hash_part}.{extension}"

    @staticmethod
    def generate_image_filename(
        operation: str,
        original_filename: Optional[str] = None,
        campaign_id: Optional[Union[int, str]] = None,
        extension: str = "png"
    ) -> str:
        """
        Generate shortened filename for an image operation

        Args:
            operation: Type of operation (inpaint, erase, overlay, etc.)
            original_filename: Optional original filename
            campaign_id: Optional campaign ID
            extension: File extension

        Returns:
            Shortened filename

        Example:
            generate_image_filename("inpaint", "hero.png", 28)
            # Returns: "inp_1225_a1b2.png"
        """
        timestamp = time.time()

        # Create short date part (MMDD)
        ts = datetime.utcnow().strftime("%m%d")

        # Create short hash (4 chars)
        hash_source = f"{operation}_{original_filename}_{timestamp}_{campaign_id}" if original_filename else f"{operation}_{timestamp}_{campaign_id}"
        hash_part = hashlib.md5(hash_source.encode()).hexdigest()[:4]

        # Build shortened filename (no original name to keep it short)
        return f"{operation}_{ts}_{hash_part}.{extension}"

    async def delete_file(self, r2_path: str) -> bool:
        """
        Delete a file from R2

        Args:
            r2_path: R2 path to the file

        Returns:
            True if deleted successfully, False otherwise
        """
        logger.info(f"Deleting from R2: {r2_path}")

        try:
            session = aioboto3.Session()

            async with session.client(
                's3',
                endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                config=Config(signature_version='s3v4'),
                region_name='auto'
            ) as s3_client:
                await s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=r2_path
                )

            logger.info(f"Deleted successfully: {r2_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {r2_path}: {e}")
            return False

# Global instance
r2_storage = R2Storage()
