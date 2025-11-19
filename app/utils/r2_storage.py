# app/utils/r2_storage.py
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
import os
from datetime import datetime
import uuid
from typing import Optional, BinaryIO
from fastapi import UploadFile
from app.core.config.settings import settings

class R2Storage:
    """Cloudflare R2 storage client for file uploads"""

    def __init__(self):
        # R2 configuration from environment (matches existing Railway env vars)
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.access_key_id = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
        self.secret_access_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME", "campaignforge-storage")
        self.public_url = os.getenv("CLOUDFLARE_R2_PUBLIC_URL")  # e.g., https://pub-xxx.r2.dev

        # Initialize S3 client for R2
        if self.account_id and self.access_key_id and self.secret_access_key:
            self.client = boto3.client(
                's3',
                endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                config=Config(signature_version='s3v4'),
            )
        else:
            self.client = None
            print("Warning: R2 credentials not configured. File uploads will be disabled.")

    def is_configured(self) -> bool:
        """Check if R2 is properly configured"""
        return self.client is not None

    def upload_file(
        self,
        file: UploadFile,
        folder: str = "profile-images",
        allowed_extensions: list = None
    ) -> Optional[str]:
        """
        Upload a file to R2 and return the public URL

        Args:
            file: FastAPI UploadFile object
            folder: Folder/prefix in the bucket
            allowed_extensions: List of allowed file extensions (e.g., ['.jpg', '.png'])

        Returns:
            Public URL of the uploaded file, or None if upload failed
        """
        if not self.is_configured():
            raise Exception("R2 storage is not configured")

        # Validate file extension
        if allowed_extensions:
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_extensions:
                raise ValueError(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")

        # Generate unique filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        file_ext = os.path.splitext(file.filename)[1].lower()
        filename = f"{timestamp}_{unique_id}{file_ext}"

        # Full key (path) in bucket
        key = f"{folder}/{filename}"

        try:
            # Upload file to R2
            self.client.upload_fileobj(
                file.file,
                self.bucket_name,
                key,
                ExtraArgs={
                    'ContentType': file.content_type or 'application/octet-stream',
                    'CacheControl': 'public, max-age=31536000',  # 1 year
                }
            )

            # Return public URL
            if self.public_url:
                return f"{self.public_url}/{key}"
            else:
                # Fallback to R2.dev URL (note: this requires public bucket)
                return f"https://{self.bucket_name}.{self.account_id}.r2.dev/{key}"

        except ClientError as e:
            print(f"Error uploading to R2: {e}")
            raise Exception(f"Failed to upload file: {str(e)}")


    async def upload_image(
        self,
        image_data: bytes,
        filename: str,
        content_type: str = "image/png",
        folder: str = "images"
    ) -> Optional[str]:
        """
        Upload raw image data to R2 and return the public URL

        Args:
            image_data: Raw image bytes
            filename: Name of the file in the bucket
            content_type: MIME type (e.g., 'image/png', 'image/jpeg')
            folder: Folder/prefix in the bucket

        Returns:
            Public URL of the uploaded image, or None if upload failed
        """
        if not self.is_configured():
            raise Exception("R2 storage is not configured")

        try:
            import asyncio
            key = f"{folder.rstrip("/")}/{filename}".lstrip("/")
            # Run sync boto3 operation in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=image_data,
                    ContentType=content_type,
                    CacheControl="public, max-age=31536000"
                )
            )
            if self.public_url:
                return f"{self.public_url}/{key}"
            else:
                return f"https://{self.bucket_name}.{self.account_id}.r2.dev/{key}"
        except ClientError as e:
            print(f"Error uploading to R2: {e}")
            raise Exception(f"Failed to upload image: {str(e)}")



    async def upload_image(
        self,
        image_data: bytes,
        filename: str,
        content_type: str = "image/png",
        folder: str = "images"
    ) -> Optional[str]:
        """
        Upload raw image data to R2 and return the public URL

        Args:
            image_data: Raw image bytes
            filename: Name of the file in the bucket
            content_type: MIME type (e.g., 'image/png', 'image/jpeg')
            folder: Folder/prefix in the bucket

        Returns:
            Public URL of the uploaded image, or None if upload failed
        """
        if not self.is_configured():
            raise Exception("R2 storage is not configured")

        try:
            import asyncio
            key = f"{folder}/{filename}"
            # Run sync boto3 operation in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=image_data,
                    ContentType=content_type,
                    CacheControl="public, max-age=31536000"
                )
            )
            if self.public_url:
                return f"{self.public_url}/{key}"
            else:
                return f"https://{self.bucket_name}.{self.account_id}.r2.dev/{key}"
        except ClientError as e:
            print(f"Error uploading to R2: {e}")
            raise Exception(f"Failed to upload image: {str(e)}")

    def delete_file(self, file_url: str) -> bool:
        """
        Delete a file from R2 by its URL

        Args:
            file_url: Public URL of the file

        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.is_configured():
            return False

        try:
            # Extract key from URL
            if self.public_url and file_url.startswith(self.public_url):
                key = file_url.replace(f"{self.public_url}/", "")
            else:
                # Parse from R2.dev URL
                key = file_url.split(f".r2.dev/")[1] if ".r2.dev/" in file_url else None

            if not key:
                return False

            # Delete from R2
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return True

        except ClientError as e:
            print(f"Error deleting from R2: {e}")
            return False

# Global instance
r2_storage = R2Storage()
