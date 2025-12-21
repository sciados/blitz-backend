"""
Cloudflare R2 Storage Service for Image Editor
Handles uploading and managing edited images in R2
"""
import os
import httpx
from typing import Optional
from datetime import datetime
import hashlib


class R2StorageService:
    """Service for storing edited images in Cloudflare R2"""
    
    def __init__(self):
        # These should match your existing R2 configuration
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.access_key_id = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
        self.secret_access_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")
        self.public_url_base = os.getenv("CLOUDFLARE_R2_PUBLIC_URL")
        
        if not all([self.account_id, self.access_key_id, self.secret_access_key, self.bucket_name]):
            raise ValueError("R2 environment variables not properly configured")
    
    def generate_edited_image_path(
        self,
        campaign_id: int,
        original_filename: str,
        operation_type: str
    ) -> str:
        """
        Generate the R2 path for an edited image
        
        Args:
            campaign_id: Campaign ID
            original_filename: Name of the original file
            operation_type: Type of edit operation
        
        Returns:
            Path in format: campaigns/{campaign_id}/edited/{timestamp}_{operation}_{filename}
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Extract filename without path
        if "/" in original_filename:
            filename = original_filename.split("/")[-1]
        else:
            filename = original_filename
        
        # Remove extension and add operation type
        name_parts = filename.rsplit(".", 1)
        if len(name_parts) == 2:
            base_name, extension = name_parts
        else:
            base_name = filename
            extension = "png"
        
        edited_filename = f"{timestamp}_{operation_type}_{base_name}.{extension}"
        
        return f"campaigns/{campaign_id}/edited/{edited_filename}"
    
    async def upload_edited_image(
        self,
        image_data: bytes,
        campaign_id: int,
        original_filename: str,
        operation_type: str,
        content_type: str = "image/png"
    ) -> tuple[str, str]:
        """
        Upload an edited image to R2
        
        Args:
            image_data: Image bytes to upload
            campaign_id: Campaign ID for organizing
            original_filename: Original filename
            operation_type: Type of operation performed
            content_type: MIME type of the image
        
        Returns:
            Tuple of (r2_path, public_url)
        """
        # Generate the path
        r2_path = self.generate_edited_image_path(
            campaign_id, 
            original_filename, 
            operation_type
        )
        
        # Use boto3 for S3-compatible upload to R2
        import boto3
        from botocore.client import Config
        
        # Create S3 client configured for R2
        s3_client = boto3.client(
            's3',
            endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )
        
        # Upload the file
        s3_client.put_object(
            Bucket=self.bucket_name,
            Key=r2_path,
            Body=image_data,
            ContentType=content_type
        )
        
        # Generate public URL
        public_url = f"{self.public_url_base}/{r2_path}"
        
        return r2_path, public_url
    
    async def download_image_from_r2(self, r2_path: str) -> bytes:
        """
        Download an image from R2
        
        Args:
            r2_path: Path to the image in R2
        
        Returns:
            Image bytes
        """
        import boto3
        from botocore.client import Config
        
        s3_client = boto3.client(
            's3',
            endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )
        
        response = s3_client.get_object(
            Bucket=self.bucket_name,
            Key=r2_path
        )
        
        return response['Body'].read()
    
    async def download_image_from_url(self, url: str) -> bytes:
        """
        Download an image from a URL (could be R2 public URL or external)
        
        Args:
            url: URL of the image
        
        Returns:
            Image bytes
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                raise Exception(f"Failed to download image from {url}: {response.status_code}")
            
            return response.content
    
    def extract_r2_path_from_url(self, url: str) -> Optional[str]:
        """
        Extract R2 path from a public URL
        
        Args:
            url: Public URL like https://your-bucket.r2.dev/campaigns/123/image.png
        
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
