"""Integration tests for DynamoDB operations using moto."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
import time
from moto import mock_aws
import boto3
import pytest

from src.shared.db import DynamoDBClient
from src.shared.config import Settings
from src.shared.exceptions import ConflictError, NotFoundError


def setup_mock_tables(dynamodb_resource):
    """Setup DynamoDB tables for testing using provided mock resource."""
    settings = Settings()

    # Create users table
    dynamodb_resource.create_table(
        TableName=settings.dynamodb_users_table,
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "email-index",
                "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create products table
    dynamodb_resource.create_table(
        TableName=settings.dynamodb_products_table,
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "product_id", "KeyType": "RANGE"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "product_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Create jobs table
    dynamodb_resource.create_table(
        TableName=settings.dynamodb_jobs_table,
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "job_id", "KeyType": "RANGE"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "job_id", "AttributeType": "S"},
            {"AttributeName": "status", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "status-index",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "status", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )


@mock_aws
def test_user_crud_operations():
    """Test all CRUD operations for users."""
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)

    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)

    # Test CREATE
    user_id = "test-user-123"
    email = "test@example.com"
    created_user = db.create_user(user_id, email)
    
    assert created_user["user_id"] == user_id
    assert created_user["email"] == email
    assert "created_at" in created_user
    assert "updated_at" in created_user

    # Test READ
    retrieved_user = db.get_user(user_id)
    assert retrieved_user["user_id"] == user_id
    assert retrieved_user["email"] == email

    # Test READ by email (GSI)
    user_by_email = db.get_user_by_email(email)
    assert user_by_email is not None
    assert user_by_email["user_id"] == user_id

    # Test CONFLICT (duplicate user)
    with pytest.raises(ConflictError):
        db.create_user(user_id, "different@email.com")


@mock_aws
def test_product_crud_operations():
    """Test all CRUD operations for products."""
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)

    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)

    # Create a user first
    user_id = "test-user-123"
    email = "test@example.com"
    db.create_user(user_id, email)

    # Test CREATE
    title = "Test Product"
    description = "Test Description"
    price = "99.99"
    image_keys = ["image1.jpg", "image2.jpg"]
    created_product = db.create_product(user_id, title, description, price, image_keys)
    
    assert created_product["user_id"] == user_id
    assert created_product["title"] == title
    assert created_product["description"] == description
    assert created_product["price"] == price
    assert created_product["image_keys"] == image_keys
    assert "product_id" in created_product

    # Test READ
    product_id = created_product["product_id"]
    retrieved_product = db.get_product(user_id, product_id)
    assert retrieved_product["product_id"] == product_id
    assert retrieved_product["title"] == title

    # Test DELETE
    db.delete_product(user_id, product_id)

    # Verify deletion
    with pytest.raises(NotFoundError):
        db.get_product(user_id, product_id)


@mock_aws
def test_job_crud_operations():
    """Test all CRUD operations for jobs."""
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)

    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)

    # Create a user and product first
    user_id = "test-user-123"
    email = "test@example.com"
    db.create_user(user_id, email)

    title = "Test Product"
    description = "Test Description"
    price = "99.99"
    image_keys = ["image1.jpg"]
    created_product = db.create_product(user_id, title, description, price, image_keys)
    product_id = created_product["product_id"]

    # Test CREATE
    adjustments = {"aspect_ratio": "9:16", "duration": 30}
    created_job = db.create_job(user_id, product_id, adjustments)
    
    assert created_job["user_id"] == user_id
    assert created_job["product_id"] == product_id
    assert created_job["status"] == "PENDING"
    assert created_job["adjustments"] == adjustments
    assert "job_id" in created_job
    assert "expires_at" in created_job  # TTL should be set

    # Test READ
    job_id = created_job["job_id"]
    retrieved_job = db.get_job(user_id, job_id)
    assert retrieved_job["job_id"] == job_id
    assert retrieved_job["status"] == "PENDING"

    # Test UPDATE status
    updated_job = db.update_job_status(user_id, job_id, "PROCESSING")
    assert updated_job["status"] == "PROCESSING"

    # Test UPDATE with error message
    error_updated_job = db.update_job_status(user_id, job_id, "FAILED", "Some error occurred")
    assert error_updated_job["status"] == "FAILED"
    assert error_updated_job["error_message"] == "Some error occurred"

    # Test UPDATE step output
    step_output = db.update_job_step_output(user_id, job_id, "tts", {"audio_key": "audio.mp3"})
    assert step_output["step_outputs"]["tts"]["audio_key"] == "audio.mp3"

    # Test UPDATE video
    video_updated_job = db.update_job_video(user_id, job_id, "video.mp4", "audio.mp3")
    assert video_updated_job["video_key"] == "video.mp4"
    assert video_updated_job["audio_key"] == "audio.mp3"
    assert video_updated_job["status"] == "COMPLETE"


@mock_aws
def test_list_products_by_user():
    """Test listing products for a specific user."""
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)

    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)

    # Create a user
    user_id = "test-user-123"
    email = "test@example.com"
    db.create_user(user_id, email)

    # Create multiple products for the user
    expected_titles = []
    for i in range(3):
        title = f"Product {i}"
        description = f"Description {i}"
        price = f"{i}.99"
        image_keys = [f"image{i}.jpg"]
        db.create_product(user_id, title, description, price, image_keys)
        expected_titles.append(title)

    # Create a product for a different user (should not appear in results)
    other_user_id = "other-user-456"
    db.create_user(other_user_id, "other@example.com")
    db.create_product(other_user_id, "Other User Product", "Other Desc", "19.99", ["other.jpg"])

    # List products for the original user
    products = db.list_products(user_id, limit=10)

    assert len(products) == 3

    # Check that all expected products are returned
    returned_titles = [p["title"] for p in products]
    for expected_title in expected_titles:
        assert expected_title in returned_titles

    # Check that other user's product is not in the results
    assert "Other User Product" not in returned_titles


@mock_aws
def test_list_jobs_by_status():
    """Test querying jobs by status using GSI."""
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)

    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)

    # Create a user and product first
    user_id = "test-user-123"
    email = "test@example.com"
    db.create_user(user_id, email)

    title = "Test Product"
    description = "Test Description"
    price = "99.99"
    image_keys = ["image1.jpg"]
    created_product = db.create_product(user_id, title, description, price, image_keys)
    product_id = created_product["product_id"]

    # Create jobs with different statuses
    job_ids_by_status = {}
    for status in ["PENDING", "PROCESSING", "COMPLETE", "FAILED"]:
        created_job = db.create_job(user_id, product_id)
        job_id = created_job["job_id"]
        job_ids_by_status[status] = job_id
        
        # Update the job to the desired status
        db.update_job_status(user_id, job_id, status)

    # Test querying jobs by each status
    for status in ["PENDING", "PROCESSING", "COMPLETE", "FAILED"]:
        jobs = db.list_jobs(user_id, limit=10, status=status)
        
        # Should only return jobs with the specified status
        assert len(jobs) == 1
        assert jobs[0]["status"] == status
        assert jobs[0]["job_id"] == job_ids_by_status[status]


@mock_aws
def test_job_ttl_attribute():
    """Test that jobs have TTL attribute set correctly."""
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)

    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)

    # Create a user and product first
    user_id = "test-user-123"
    email = "test@example.com"
    db.create_user(user_id, email)

    title = "Test Product"
    description = "Test Description"
    price = "99.99"
    image_keys = ["image1.jpg"]
    created_product = db.create_product(user_id, title, description, price, image_keys)
    product_id = created_product["product_id"]

    # Create a job
    created_job = db.create_job(user_id, product_id)
    
    # Verify TTL attribute is present and is a reasonable timestamp
    assert "expires_at" in created_job
    expires_at = created_job["expires_at"]
    assert isinstance(expires_at, int)
    
    # Verify it's approximately 30 days from now (within a day's tolerance)
    import time
    current_time = int(time.time())
    expected_ttl = current_time + (30 * 24 * 60 * 60)  # 30 days in seconds
    
    # Allow for some variance in timing
    assert abs(expires_at - expected_ttl) < (24 * 60 * 60)  # Within 1 day tolerance


@mock_aws
def test_update_job_step_output():
    """Test updating job with step output data."""
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)

    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)

    # Create a user, product, and job first
    user_id = "test-user-123"
    email = "test@example.com"
    db.create_user(user_id, email)

    title = "Test Product"
    description = "Test Description"
    price = "99.99"
    image_keys = ["image1.jpg"]
    created_product = db.create_product(user_id, title, description, price, image_keys)
    product_id = created_product["product_id"]

    created_job = db.create_job(user_id, product_id)
    job_id = created_job["job_id"]

    # Test updating with step output
    step_name = "tts_generation"
    output_data = {
        "audio_s3_key": "user123/job456/voiceover.mp3",
        "audio_s3_url": "s3://bucket/user123/job456/voiceover.mp3",
        "provider_used": "elevenlabs",
        "character_count": 150,
        "duration_estimate_seconds": 12  # Use int instead of float
    }
    
    result = db.update_job_step_output(user_id, job_id, step_name, output_data)

    # Verify the step output was added
    assert step_name in result["step_outputs"]
    assert result["step_outputs"][step_name] == output_data
    assert result["job_id"] == job_id

    # Test updating with another step
    another_step_name = "video_generation"
    another_output_data = {
        "video_s3_key": "user123/job456/video.mp4",
        "video_s3_url": "s3://bucket/user123/job456/video.mp4",
        "duration_seconds": 10  # Use int instead of float
    }
    
    result = db.update_job_step_output(user_id, job_id, another_step_name, another_output_data)

    # Verify both step outputs are present
    assert step_name in result["step_outputs"]
    assert another_step_name in result["step_outputs"]
    assert result["step_outputs"][step_name] == output_data
    assert result["step_outputs"][another_step_name] == another_output_data


@mock_aws
def test_concurrent_updates():
    """Test concurrent updates to the same record."""
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)

    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)

    # Create a user and product first
    user_id = "test-user-123"
    email = "test@example.com"
    db.create_user(user_id, email)

    title = "Test Product"
    description = "Test Description"
    price = "99.99"
    image_keys = ["image1.jpg"]
    created_product = db.create_product(user_id, title, description, price, image_keys)
    product_id = created_product["product_id"]

    # Create a job
    created_job = db.create_job(user_id, product_id)
    job_id = created_job["job_id"]

    # Define a function to update job status
    def update_job_status(status):
        return db.update_job_status(user_id, job_id, status)

    # Simulate concurrent updates using threads
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(5):
            status = f"STATUS_{i}"
            future = executor.submit(update_job_status, status)
            futures.append(future)

        # Wait for all updates to complete
        results = [future.result() for future in futures]

    # Get the final job to verify one of the updates succeeded
    final_job = db.get_job(user_id, job_id)
    
    # At least one update should have succeeded
    assert final_job["status"] in [f"STATUS_{i}" for i in range(5)]
    
    # Verify that the updated_at field was updated
    assert "updated_at" in final_job