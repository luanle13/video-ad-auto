"""Tests for the S3 storage client using moto."""
import pytest
from moto import mock_aws

from src.shared.storage import S3Client, get_storage
from src.shared.exceptions import NotFoundError, InvalidFileTypeError


def create_test_buckets():
    """Helper to create test S3 buckets."""
    from src.shared.config import Settings
    import boto3
    
    # Create test buckets
    settings = Settings()
    s3 = boto3.client("s3", region_name="us-east-1")
    
    # Create the required buckets
    # For us-east-1, do not specify LocationConstraint
    s3.create_bucket(Bucket=settings.s3_images_bucket)
    s3.create_bucket(Bucket=settings.s3_videos_bucket)
    
    return settings


@mock_aws
def test_s3_client_initialization():
    """Test S3 client initialization."""
    create_test_buckets()
    
    # Create the client and test basic functionality
    client = S3Client()
    assert client is not None


@mock_aws
def test_presigned_upload_url_generation():
    """Test generating presigned upload URLs."""
    create_test_buckets()
    
    client = S3Client()
    
    # Test image upload URL generation
    upload_data = client.generate_upload_url(
        bucket_type="images",
        key="test/test-image.jpg",
        content_type="image/jpeg",
    )
    
    assert "url" in upload_data
    assert "fields" in upload_data
    assert upload_data["fields"]["Content-Type"] == "image/jpeg"
    
    # Test video upload URL generation
    upload_data = client.generate_upload_url(
        bucket_type="videos",
        key="test/test-video.mp4",
        content_type="video/mp4",
    )
    
    assert "url" in upload_data
    assert "fields" in upload_data
    assert upload_data["fields"]["Content-Type"] == "video/mp4"


@mock_aws
def test_presigned_upload_url_content_type_validation():
    """Test content type validation for presigned upload URLs."""
    create_test_buckets()
    
    client = S3Client()
    
    # Test invalid image content type
    with pytest.raises(InvalidFileTypeError):
        client.generate_upload_url(
            bucket_type="images",
            key="test/invalid.txt",
            content_type="text/plain",
        )
    
    # Test invalid video content type
    with pytest.raises(InvalidFileTypeError):
        client.generate_upload_url(
            bucket_type="videos",
            key="test/invalid.txt",
            content_type="text/plain",
        )


@mock_aws
def test_file_upload_download():
    """Test file upload and download operations."""
    create_test_buckets()
    
    client = S3Client()
    
    # Upload a test image
    test_data = b"fake image data"
    settings = create_test_buckets()  # Just to get settings
    s3_path = client.upload_file(
        bucket_type="images",
        key="test/test-image.jpg",
        body=test_data,
        content_type="image/jpeg",
    )
    
    assert s3_path == f"s3://{settings.s3_images_bucket}/test/test-image.jpg"
    
    # Download the same file
    downloaded_data = client.download_file(
        bucket_type="images",
        key="test/test-image.jpg",
    )
    
    assert downloaded_data == test_data


@mock_aws
def test_file_exists():
    """Test file existence checking."""
    create_test_buckets()
    
    client = S3Client()
    
    # Initially file doesn't exist
    assert not client.file_exists("images", "test/nonexistent.jpg")
    
    # Upload a file
    client.upload_file(
        bucket_type="images",
        key="test/existing.jpg",
        body=b"test data",
        content_type="image/jpeg",
    )
    
    # Now file exists
    assert client.file_exists("images", "test/existing.jpg")


@mock_aws
def test_file_delete():
    """Test file deletion."""
    create_test_buckets()
    
    client = S3Client()
    
    # Upload a file
    client.upload_file(
        bucket_type="images",
        key="test/file-to-delete.jpg",
        body=b"test data",
        content_type="image/jpeg",
    )
    
    # Verify file exists
    assert client.file_exists("images", "test/file-to-delete.jpg")
    
    # Delete the file
    client.delete_file("images", "test/file-to-delete.jpg")
    
    # Verify file no longer exists
    assert not client.file_exists("images", "test/file-to-delete.jpg")


@mock_aws
def test_download_file_not_found():
    """Test downloading non-existent file raises NotFoundError."""
    create_test_buckets()
    
    client = S3Client()
    
    with pytest.raises(NotFoundError):
        client.download_file("images", "nonexistent/file.jpg")


@mock_aws
def test_generate_download_url():
    """Test generating presigned download URLs."""
    create_test_buckets()
    
    client = S3Client()
    
    # Upload a file first
    client.upload_file(
        bucket_type="images",
        key="test/download-test.jpg",
        body=b"test data",
        content_type="image/jpeg",
    )
    
    # Generate download URL
    from src.shared.config import Settings
    settings = Settings()
    url = client.generate_download_url(
        bucket_type="images",
        key="test/download-test.jpg",
    )
    
    assert url.startswith("https://")
    assert settings.s3_images_bucket in url


@mock_aws
def test_generate_download_url_not_found():
    """Test generating download URL for non-existent file raises NotFoundError."""
    create_test_buckets()
    
    client = S3Client()
    
    with pytest.raises(NotFoundError):
        client.generate_download_url(
            bucket_type="images",
            key="nonexistent/file.jpg",
        )


@mock_aws
def test_key_generation():
    """Test key generation methods."""
    create_test_buckets()
    
    client = S3Client()
    
    # Test image key generation
    image_key = client.generate_image_key("user123", "product456", "test.jpg")
    assert image_key.startswith("user123/product456/")
    assert image_key.endswith(".jpg")
    
    image_key_png = client.generate_image_key("user123", "product456", "test.png")
    assert image_key_png.startswith("user123/product456/")
    assert image_key_png.endswith(".png")
    
    # Test video key generation
    video_key = client.generate_video_key("user123", "job789")
    assert video_key == "user123/job789/output.mp4"
    
    # Test audio key generation
    audio_key = client.generate_audio_key("user123", "job789")
    assert audio_key == "user123/job789/voiceover.mp3"


@mock_aws
def test_allowed_content_types():
    """Test allowed content types validation."""
    create_test_buckets()
    
    client = S3Client()
    
    # Valid image types
    for img_type in client.ALLOWED_IMAGE_TYPES:
        # This should not raise an exception
        upload_data = client.generate_upload_url(
            bucket_type="images",
            key="test/valid-image.jpg",
            content_type=img_type,
        )
        assert "url" in upload_data
    
    # Valid video types
    for vid_type in client.ALLOWED_VIDEO_TYPES:
        # This should not raise an exception
        upload_data = client.generate_upload_url(
            bucket_type="videos",
            key="test/valid-video.mp4",
            content_type=vid_type,
        )
        assert "url" in upload_data


@mock_aws
def test_singleton_pattern():
    """Test that get_storage returns singleton instance."""
    create_test_buckets()
    
    storage1 = get_storage()
    storage2 = get_storage()
    
    assert storage1 is storage2


@mock_aws
def test_get_storage():
    """Test get_storage function."""
    create_test_buckets()
    
    storage = get_storage()
    assert isinstance(storage, S3Client)