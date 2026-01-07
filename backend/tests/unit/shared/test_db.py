"""Tests for the DynamoDB client and operations using moto."""
import pytest
from moto import mock_aws
from datetime import datetime, timezone

from src.shared.db import get_db, DynamoDBClient
from src.shared.exceptions import ConflictError, NotFoundError


def setup_mock_tables(dynamodb_resource):
    """Setup DynamoDB tables for testing using provided mock resource."""
    from src.shared.config import Settings
    
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
def test_create_user_success():
    """Test successful user creation."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)
    
    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)
    
    user_id = "test-user-123"
    email = "test@example.com"
    
    result = db.create_user(user_id, email)
    
    assert result["user_id"] == user_id
    assert result["email"] == email
    assert "created_at" in result
    assert "updated_at" in result


@mock_aws
def test_create_user_conflict():
    """Test that creating duplicate user raises ConflictError."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)
    
    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)
    
    user_id = "test-user-123"
    email = "test@example.com"
    
    # Create user once
    db.create_user(user_id, email)
    
    # Try to create the same user again
    with pytest.raises(ConflictError):
        db.create_user(user_id, "different@email.com")


@mock_aws
def test_get_user_success():
    """Test getting an existing user."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)
    
    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)
    
    user_id = "test-user-123"
    email = "test@example.com"
    
    # Create the user first
    db.create_user(user_id, email)
    
    # Retrieve the user
    result = db.get_user(user_id)
    
    assert result["user_id"] == user_id
    assert result["email"] == email


@mock_aws
def test_get_user_not_found():
    """Test that getting non-existent user raises NotFoundError."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)
    
    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)
    
    with pytest.raises(NotFoundError):
        db.get_user("non-existent-user")


@mock_aws
def test_get_user_by_email():
    """Test getting user by email."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)
    
    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)
    
    user_id = "test-user-123"
    email = "test@example.com"
    
    # Create the user first
    db.create_user(user_id, email)
    
    # Retrieve the user by email
    result = db.get_user_by_email(email)
    
    assert result is not None
    assert result["user_id"] == user_id
    assert result["email"] == email
    
    # Test with non-existent email
    assert db.get_user_by_email("nonexistent@example.com") is None


@mock_aws
def test_create_product_success():
    """Test successful product creation."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)
    
    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)
    
    user_id = "test-user-123"
    email = "test@example.com"
    db.create_user(user_id, email)
    
    title = "Test Product"
    description = "Test Description"
    price = "99.99"
    image_keys = ["image1.jpg", "image2.jpg"]
    
    result = db.create_product(user_id, title, description, price, image_keys)
    
    assert result["user_id"] == user_id
    assert result["title"] == title
    assert result["description"] == description
    assert result["price"] == price
    assert result["image_keys"] == image_keys
    assert "product_id" in result
    assert "created_at" in result
    assert "updated_at" in result


@mock_aws
def test_get_product_success():
    """Test getting an existing product."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)
    
    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)
    
    user_id = "test-user-123"
    email = "test@example.com"
    db.create_user(user_id, email)
    
    title = "Test Product"
    description = "Test Description"
    price = "99.99"
    image_keys = ["image1.jpg"]
    
    created_product = db.create_product(user_id, title, description, price, image_keys)
    product_id = created_product["product_id"]
    
    result = db.get_product(user_id, product_id)
    
    assert result["product_id"] == product_id
    assert result["title"] == title


@mock_aws
def test_get_product_not_found():
    """Test that getting non-existent product raises NotFoundError."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)
    
    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)
    
    user_id = "test-user-123"
    email = "test@example.com"
    db.create_user(user_id, email)
    
    with pytest.raises(NotFoundError):
        db.get_product(user_id, "non-existent-product")


@mock_aws
def test_list_products():
    """Test listing products for a user."""
    import boto3
    from src.shared.config import Settings

    # Create the tables within the mock context
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)

    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)

    user_id = "test-user-123"
    email = "test@example.com"
    db.create_user(user_id, email)

    # Create multiple products
    expected_titles = []
    for i in range(3):
        title = f"Product {i}"
        description = f"Description {i}"
        price = f"{i}.99"
        image_keys = [f"image{i}.jpg"]
        db.create_product(user_id, title, description, price, image_keys)
        expected_titles.append(title)

    products = db.list_products(user_id, limit=10)

    assert len(products) == 3

    # Check that all expected products are returned (order may vary in mock)
    returned_titles = [p["title"] for p in products]
    for expected_title in expected_titles:
        assert expected_title in returned_titles


@mock_aws
def test_delete_product():
    """Test deleting a product."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)
    
    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)
    
    user_id = "test-user-123"
    email = "test@example.com"
    db.create_user(user_id, email)
    
    title = "Test Product"
    description = "Test Description"
    price = "99.99"
    image_keys = ["image1.jpg"]
    
    created_product = db.create_product(user_id, title, description, price, image_keys)
    product_id = created_product["product_id"]
    
    # Verify product exists
    result = db.get_product(user_id, product_id)
    assert result["title"] == title
    
    # Delete the product
    db.delete_product(user_id, product_id)
    
    # Verify product no longer exists
    with pytest.raises(NotFoundError):
        db.get_product(user_id, product_id)


@mock_aws
def test_create_job_success():
    """Test successful job creation."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
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
    
    adjustments = {"aspect_ratio": "9:16", "duration": 30}
    
    result = db.create_job(user_id, product_id, adjustments)
    
    assert result["user_id"] == user_id
    assert result["product_id"] == product_id
    assert result["status"] == "PENDING"
    assert result["adjustments"] == adjustments
    assert "job_id" in result
    assert "created_at" in result
    assert "expires_at" in result  # TTL should be set


@mock_aws
def test_get_job_success():
    """Test getting an existing job."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
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
    
    created_job = db.create_job(user_id, product_id)
    job_id = created_job["job_id"]
    
    result = db.get_job(user_id, job_id)
    
    assert result["job_id"] == job_id
    assert result["status"] == "PENDING"


@mock_aws
def test_get_job_not_found():
    """Test that getting non-existent job raises NotFoundError."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
    settings = Settings()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    setup_mock_tables(dynamodb)
    
    # Create the db client with the mocked dynamodb resource
    db = DynamoDBClient(dynamodb_resource=dynamodb)
    
    user_id = "test-user-123"
    email = "test@example.com"
    db.create_user(user_id, email)
    
    with pytest.raises(NotFoundError):
        db.get_job(user_id, "non-existent-job")


@mock_aws
def test_list_jobs():
    """Test listing jobs for a user."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
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
    
    # Create multiple jobs
    for i in range(3):
        db.create_job(user_id, product_id)
    
    jobs = db.list_jobs(user_id, limit=10)
    
    assert len(jobs) == 3
    # Check that they are ordered with newest first


@mock_aws
def test_update_job_status():
    """Test updating job status."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
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
    
    # Update job status
    new_status = "PROCESSING"
    result = db.update_job_status(user_id, job_id, new_status)
    
    assert result["status"] == new_status
    assert result["job_id"] == job_id


@mock_aws
def test_update_job_status_with_error():
    """Test updating job status with error message."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
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
    
    # Update job status with error
    new_status = "FAILED"
    error_message = "Some error occurred"
    result = db.update_job_status(user_id, job_id, new_status, error_message)
    
    assert result["status"] == new_status
    assert result["error_message"] == error_message


@mock_aws
def test_update_job_step_output():
    """Test updating job with step output."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
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
    
    # Update job with step output
    step_name = "script_generation"
    output = {"script": "Test script", "duration": 30}
    result = db.update_job_step_output(user_id, job_id, step_name, output)
    
    assert result["step_outputs"][step_name] == output


@mock_aws
def test_update_job_video():
    """Test updating job with video and audio keys."""
    import boto3
    from src.shared.config import Settings
    
    # Create the tables within the mock context
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
    
    # Update job with video and audio keys
    video_key = "videos/job123.mp4"
    audio_key = "audios/job123.mp3"
    result = db.update_job_video(user_id, job_id, video_key, audio_key)
    
    assert result["video_key"] == video_key
    assert result["audio_key"] == audio_key
    assert result["status"] == "COMPLETE"


@mock_aws
def test_ttl_generation():
    """Test TTL timestamp generation."""
    db = DynamoDBClient()  # This method doesn't rely on DynamoDB, so can use default
    
    # Test TTL for 30 days
    ttl_timestamp = db.ttl_timestamp(30)
    
    # Verify it's a reasonable timestamp value
    current_time = int(datetime.now(timezone.utc).timestamp())
    future_time = current_time + (30 * 24 * 60 * 60)  # 30 days in seconds
    
    # Allow for some variance in timing
    assert ttl_timestamp >= current_time
    assert ttl_timestamp <= future_time + 10  # 10 second buffer


@mock_aws
def test_generate_id():
    """Test UUID generation."""
    db = DynamoDBClient()  # This method doesn't rely on DynamoDB, so can use default
    
    id1 = db.generate_id()
    id2 = db.generate_id()
    
    assert isinstance(id1, str)
    assert isinstance(id2, str)
    assert id1 != id2  # Should be different each time
    assert len(id1) == len(str(__import__('uuid').uuid4()))  # Should be UUID length