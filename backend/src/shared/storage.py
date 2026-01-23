"""S3 storage client for images and videos."""
from typing import Literal

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from src.shared.config import get_settings
from src.shared.exceptions import NotFoundError
from src.shared.logging import get_logger

logger = get_logger(__name__)

BucketType = Literal["images", "videos"]


class S3Client:
    """S3 client for file storage operations."""
    
    ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
    ALLOWED_VIDEO_TYPES = ["video/mp4", "video/webm"]
    
    def __init__(self) -> None:
        settings = get_settings()
        # Use s3v4 signature for presigned URLs
        self._s3 = boto3.client(
            "s3",
            region_name=settings.aws_region,
            config=Config(signature_version="s3v4"),
        )
        self._buckets = {
            "images": settings.s3_images_bucket,
            "videos": settings.s3_videos_bucket,
        }
        self._presigned_expiry = settings.s3_presigned_expiry
    
    def _get_bucket(self, bucket_type: BucketType) -> str:
        """Get bucket name by type."""
        return self._buckets[bucket_type]
    
    def generate_upload_url(
        self,
        bucket_type: BucketType,
        key: str,
        content_type: str,
    ) -> dict[str, str]:
        """
        Generate a presigned URL for uploading a file.
        
        Returns:
            dict with 'url' and 'fields' for POST upload, or 'url' for PUT upload
        """
        bucket = self._get_bucket(bucket_type)
        
        # Validate content type
        allowed = (
            self.ALLOWED_IMAGE_TYPES
            if bucket_type == "images" else self.ALLOWED_VIDEO_TYPES
        )
        if content_type not in allowed:
            from src.shared.exceptions import InvalidFileTypeError
            raise InvalidFileTypeError(allowed)
        
        # Generate presigned POST (more secure, supports conditions)
        response = self._s3.generate_presigned_post(
            Bucket=bucket,
            Key=key,
            Fields={"Content-Type": content_type},
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", 1, 5 * 1024 * 1024],  # 1 byte to 5MB
            ],
            ExpiresIn=self._presigned_expiry,
        )
        
        logger.info(
            "presigned_upload_generated",
            bucket=bucket,
            key=key,
            content_type=content_type,
        )
        return response
    
    def generate_download_url(
        self,
        bucket_type: BucketType,
        key: str,
    ) -> str:
        """Generate a presigned URL for downloading a file."""
        bucket = self._get_bucket(bucket_type)
        
        # Verify object exists
        try:
            self._s3.head_object(Bucket=bucket, Key=key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise NotFoundError("File", key)
            raise
        
        url = self._s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=self._presigned_expiry,
        )
        
        logger.info("presigned_download_generated", bucket=bucket, key=key)
        return url
    
    def upload_file(
        self,
        bucket_type: BucketType,
        key: str,
        body: bytes,
        content_type: str,
    ) -> str:
        """Upload a file directly (for server-side uploads)."""
        bucket = self._get_bucket(bucket_type)
        
        self._s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )
        
        logger.info(
            "file_uploaded",
            bucket=bucket,
            key=key,
            size=len(body),
            content_type=content_type,
        )
        return f"s3://{bucket}/{key}"
    
    def download_file(self, bucket_type: BucketType, key: str) -> bytes:
        """Download a file's content."""
        bucket = self._get_bucket(bucket_type)
        
        try:
            response = self._s3.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise NotFoundError("File", key)
            raise
    
    def delete_file(self, bucket_type: BucketType, key: str) -> None:
        """Delete a file."""
        bucket = self._get_bucket(bucket_type)
        self._s3.delete_object(Bucket=bucket, Key=key)
        logger.info("file_deleted", bucket=bucket, key=key)
    
    def file_exists(self, bucket_type: BucketType, key: str) -> bool:
        """Check if a file exists."""
        bucket = self._get_bucket(bucket_type)
        try:
            self._s3.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False

    def list_files_by_prefix(self, bucket_type: BucketType, prefix: str) -> list[str]:
        """List files by prefix."""
        bucket = self._get_bucket(bucket_type)

        response = self._s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        return [obj["Key"] for obj in response.get("Contents", [])]
    
    def generate_image_key(self, user_id: str, filename: str, product_id: str | None = None) -> str:
        """Generate a unique key for a product image.

        If product_id is not provided, images are stored in a 'pending' folder
        for uploads before product creation.
        """
        from uuid import uuid4
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
        folder = product_id if product_id else "pending"
        return f"{user_id}/{folder}/{uuid4()}.{ext}"
    
    def generate_video_key(self, user_id: str, job_id: str) -> str:
        """Generate a key for a generated video."""
        return f"{user_id}/{job_id}/output.mp4"
    
    def generate_audio_key(self, user_id: str, job_id: str) -> str:
        """Generate a key for generated audio."""
        return f"{user_id}/{job_id}/voiceover.mp3"


# Singleton instance
_s3_client: S3Client | None = None


def get_storage() -> S3Client:
    """Get S3 client singleton."""
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client