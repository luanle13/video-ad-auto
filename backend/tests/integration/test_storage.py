"""Integration tests for S3 storage functionality using moto mock."""
import os
from unittest.mock import patch

import boto3
import pytest
from moto import mock_aws

from src.shared.storage import S3Client, get_storage
from src.shared.config import Settings


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch.dict(os.environ, {
        "S3_IMAGES_BUCKET": "test-images-bucket",
        "S3_VIDEOS_BUCKET": "test-videos-bucket",
        "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing"
    }):
        yield Settings()


@pytest.fixture
def s3_client():
    """Create a mock S3 client."""
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        yield client


@pytest.fixture
def storage_client(mock_settings, s3_client):
    """Create an S3Client instance with mocked settings and S3 client."""
    # Create the buckets first
    s3_client.create_bucket(Bucket="test-images-bucket")
    s3_client.create_bucket(Bucket="test-videos-bucket")
    
    # Patch the S3Client to use the mocked S3 client
    with patch('src.shared.storage.boto3.client', return_value=s3_client):
        client = S3Client()
        yield client


def test_upload_file_success(storage_client, s3_client):
    """Test successful file upload to S3."""
    # Test data
    bucket_type = "images"
    key = "test/user123/product456/image.jpg"
    content = b"test image content"
    content_type = "image/jpeg"
    
    # Upload the file
    result = storage_client.upload_file(bucket_type, key, content, content_type)
    
    # Verify the result
    assert result == f"s3://test-images-bucket/{key}"
    
    # Verify the file was uploaded to S3
    response = s3_client.get_object(Bucket="test-images-bucket", Key=key)
    assert response["Body"].read() == content
    assert response["ContentType"] == content_type


def test_download_file_success(storage_client, s3_client):
    """Test successful file download from S3."""
    # Setup: Upload a file first
    bucket_type = "images"
    key = "test/user123/product456/image.jpg"
    original_content = b"test image content"
    content_type = "image/jpeg"
    
    s3_client.put_object(
        Bucket="test-images-bucket",
        Key=key,
        Body=original_content,
        ContentType=content_type
    )
    
    # Download the file
    downloaded_content = storage_client.download_file(bucket_type, key)
    
    # Verify the content matches
    assert downloaded_content == original_content


def test_generate_presigned_upload_url(storage_client):
    """Test generating presigned upload URL."""
    bucket_type = "images"
    key = "test/user123/product456/image.jpg"
    content_type = "image/jpeg"
    
    # Generate presigned upload URL
    result = storage_client.generate_upload_url(bucket_type, key, content_type)
    
    # Verify the response structure
    assert "url" in result
    assert "fields" in result
    assert result["fields"]["key"] == key
    assert result["fields"]["Content-Type"] == content_type


def test_generate_presigned_download_url(storage_client, s3_client):
    """Test generating presigned download URL."""
    # Setup: Upload a file first
    bucket_type = "images"
    key = "test/user123/product456/image.jpg"
    content = b"test image content"
    
    s3_client.put_object(
        Bucket="test-images-bucket",
        Key=key,
        Body=content
    )
    
    # Generate presigned download URL
    url = storage_client.generate_download_url(bucket_type, key)
    
    # Verify the URL is generated
    assert isinstance(url, str)
    assert "https://" in url
    assert "test-images-bucket" in url


def test_presigned_url_expiration(storage_client):
    """Test presigned URL expiration."""
    bucket_type = "images"
    key = "test/user123/product456/image.jpg"
    content_type = "image/jpeg"

    # Generate presigned upload URL
    result = storage_client.generate_upload_url(bucket_type, key, content_type)

    # Check that the policy contains expiration information
    # The expiration is embedded in the policy for presigned POST URLs
    assert "url" in result
    assert "fields" in result
    assert "policy" in result["fields"]

    # The policy is base64 encoded, so decode it first
    import json
    import base64

    policy_b64 = result["fields"]["policy"]
    policy_decoded = base64.b64decode(policy_b64).decode('utf-8')
    policy_data = json.loads(policy_decoded)

    # The policy should have an expiration time
    assert "expiration" in policy_data


def test_file_exists_check(storage_client, s3_client):
    """Test checking if a file exists in S3."""
    # Setup: Upload a file
    bucket_type = "images"
    existing_key = "test/user123/product456/existing.jpg"
    non_existing_key = "test/user123/product456/non-existing.jpg"
    content = b"test image content"
    
    s3_client.put_object(
        Bucket="test-images-bucket",
        Key=existing_key,
        Body=content
    )
    
    # Test existing file
    assert storage_client.file_exists(bucket_type, existing_key) is True
    
    # Test non-existing file
    assert storage_client.file_exists(bucket_type, non_existing_key) is False


def test_delete_file(storage_client, s3_client):
    """Test deleting a file from S3."""
    # Setup: Upload a file
    bucket_type = "images"
    key = "test/user123/product456/image.jpg"
    content = b"test image content"
    
    s3_client.put_object(
        Bucket="test-images-bucket",
        Key=key,
        Body=content
    )
    
    # Verify file exists before deletion
    assert storage_client.file_exists(bucket_type, key) is True
    
    # Delete the file
    storage_client.delete_file(bucket_type, key)
    
    # Verify file no longer exists
    assert storage_client.file_exists(bucket_type, key) is False


def test_list_files_by_prefix(storage_client, s3_client):
    """Test listing files by prefix."""
    # Setup: Upload multiple files with different prefixes
    bucket_type = "images"
    user_prefix = "user123/"

    files_to_create = [
        f"{user_prefix}product1/img1.jpg",
        f"{user_prefix}product1/img2.png",
        f"{user_prefix}product2/img3.jpg",
        "other-user/product4/img4.jpg"  # Different user, should not appear in results
    ]

    content = b"test content"
    for file_key in files_to_create:
        s3_client.put_object(
            Bucket="test-images-bucket",
            Key=file_key,
            Body=content
        )

    # Test the list_files_by_prefix method
    returned_keys = storage_client.list_files_by_prefix(bucket_type, user_prefix)

    # Verify that only files with the correct prefix are returned
    assert len(returned_keys) == 3  # 3 files with "user123/" prefix
    for key in returned_keys:
        assert key.startswith(user_prefix)

    # Verify that the other-user file is not in the results
    assert "other-user/product4/img4.jpg" not in returned_keys