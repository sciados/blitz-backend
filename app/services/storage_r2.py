"""
Cloudflare R2 Storage Service
Handles image and video uploads to R2
"""
import boto3
import asyncio
from botocore.exceptions import ClientError
from app.core.config.settings import settings
import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)


class R2StorageService:
    """Service for interacting with Cloudflare R2 storage"""
    
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint_url,
            aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        self.bucket = settings.CLOUDFLARE_R2_BUCKET_NAME
        self.public_url = settings.CLOUDFLARE_R2_PUBLIC_URL

    async def upload_file(
        self,
        file_bytes: bytes,
        key: str,
        content_type: str,
        meta_data: Optional[dict] = None
    ) -> tuple[str, str]:
        """
        Upload a file to R2

        Args:
            file_bytes: File content as bytes
            key: R2 object key (path)
            content_type: MIME type
            meta_data: Optional meta_data dict

        Returns:
            Tuple of (r2_key, public_url)
        """
        try:
            extra_args = {
                "ContentType": content_type,
            }

            if meta_data:
                extra_args["Metadata"] = {k: str(v) for k, v in meta_data.items()}

            # Use asyncio to run sync boto3 operation (like Blitz)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=file_bytes,
                    **extra_args
                )
            )

            public_url = f"{self.public_url}/{key}"
            logger.info(f"✅ Uploaded to R2: {key}")
            return key, public_url

        except ClientError as e:
            logger.error(f"❌ R2 upload failed: {e}")
            raise

    def generate_key(
        self,
        campaign_id: str,
        asset_type: str,
        extension: str,
        prefix: Optional[str] = None
    ) -> str:
        """
        Generate a unique R2 key
        
        Args:
            campaign_id: Campaign UUID
            asset_type: Type of asset (image, video, etc.)
            extension: File extension (jpg, mp4, etc.)
            prefix: Optional prefix
            
        Returns:
            R2 key string
        """
        unique_id = str(uuid.uuid4())
        
        if prefix:
            return f"{prefix}/{campaign_id}/{asset_type}/{unique_id}.{extension}"
        
        return f"{campaign_id}/{asset_type}/{unique_id}.{extension}"

    def delete_file(self, key: str) -> bool:
        """
        Delete a file from R2
        
        Args:
            key: R2 object key
            
        Returns:
            True if successful
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"✅ Deleted from R2: {key}")
            return True
        except ClientError as e:
            logger.error(f"❌ R2 delete failed: {e}")
            return False

    def get_signed_url(self, key: str, expiration: int = 3600) -> str:
        """
        Generate a signed URL for private access
        
        Args:
            key: R2 object key
            expiration: URL expiration in seconds (default 1 hour)
            
        Returns:
            Signed URL string
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"❌ Failed to generate signed URL: {e}")
            raise

    def file_exists(self, key: str) -> bool:
        """
        Check if a file exists in R2

        Args:
            key: R2 object key

        Returns:
            True if file exists
        """
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
