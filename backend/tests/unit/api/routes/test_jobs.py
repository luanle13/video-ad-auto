"""Tests for job routes using moto."""
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from moto import mock_aws
import boto3

from src.api.main import create_app
from src.api.models.jobs import CreateJobRequest, JobAdjustments, RegenerateJobRequest
from src.shared.exceptions import NotFoundError, ValidationError


@mock_aws
def test_create_job_success():
    """Test successful job creation."""
    # Set up mocked resources
    from src.shared.config import Settings
    settings = Settings()
    
    # Mock DynamoDB tables
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    
    # Create required tables
    dynamodb.create_table(
        TableName=settings.dynamodb_users_table,
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    
    dynamodb.create_table(
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
    
    jobs_table = dynamodb.create_table(
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
                "BillingMode": "PAY_PER_REQUEST",
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    
    # Create user and product first
    from src.shared.db import get_db
    db = get_db()
    user_id = "test-user-123"
    db.create_user(user_id=user_id, email="test@example.com")
    
    product = db.create_product(
        user_id=user_id,
        title="Test Product",
        description="Test Description",
        price="99.99",
        image_keys=["test-image.jpg"]
    )
    product_id = product["product_id"]
    
    # Create a test app with mocked dependencies
    app = create_app()
    
    # Mock the auth dependency to return a test user
    mock_current_user = MagicMock()
    mock_current_user.user_id = user_id
    def override_get_current_user():
        return mock_current_user
    
    # Apply the override
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        client = TestClient(app)
        
        # Create job request with adjustments
        request_data = {
            "product_id": product_id,
            "adjustments": {
                "background_style": "minimal",
                "tone": "energetic",
                "duration_preference": 30
            }
        }
        
        response = client.post("/jobs/", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "job_id" in data
        assert data["user_id"] == user_id
        assert data["product_id"] == product_id
        assert data["status"] == "PENDING"
        assert data["adjustments"]["background_style"] == "minimal"
        
        # Verify job was created in DB
        job_item = jobs_table.get_item(
            Key={"user_id": user_id, "job_id": data["job_id"]}
        )["Item"]
        assert job_item["user_id"] == user_id
        assert job_item["product_id"] == product_id
        assert job_item["status"] == "PENDING"
    finally:
        # Clean up dependency override
        app.dependency_overrides.clear()


def test_create_job_product_not_found():
    """Test creating job with non-existent product raises NotFoundError."""
    app = create_app()
    
    # Mock the auth and DB dependencies
    mock_current_user = MagicMock()
    mock_current_user.user_id = "test-user-123"
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Mock DB to raise NotFoundError
        with patch('src.shared.db.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.get_product.side_effect = NotFoundError("Product", "non-existent-product")
            
            client = TestClient(app)
            
            request_data = {
                "product_id": "non-existent-product",
                "adjustments": {}
            }
            
            response = client.post("/jobs/", json=request_data)
            
            assert response.status_code == 404
            data = response.json()
            assert "error" in data
    finally:
        app.dependency_overrides.clear()


def test_list_jobs():
    """Test listing user's jobs."""
    app = create_app()
    
    # Mock auth dependency
    mock_current_user = MagicMock()
    mock_current_user.user_id = "test-user-123"
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Mock DB
        with patch('src.shared.db.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.list_jobs.return_value = [
                {
                    "job_id": "job-1",
                    "user_id": "test-user-123",
                    "product_id": "product-1",
                    "status": "COMPLETE",
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:05:00Z"
                },
                {
                    "job_id": "job-2", 
                    "user_id": "test-user-123",
                    "product_id": "product-2",
                    "status": "PENDING",
                    "created_at": "2023-01-02T00:00:00Z",
                    "updated_at": "2023-01-02T00:00:00Z"
                }
            ]
            
            with patch('src.shared.storage.get_storage'):
                client = TestClient(app)
                
                response = client.get("/jobs/")
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["count"] == 2
                assert len(data["jobs"]) == 2
                
                # Check first job
                job1 = data["jobs"][0]
                assert job1["job_id"] == "job-1"
                assert job1["status"] == "COMPLETE"
                
                # Check second job
                job2 = data["jobs"][1]
                assert job2["job_id"] == "job-2"
                assert job2["status"] == "PENDING"
    finally:
        app.dependency_overrides.clear()


def test_get_job():
    """Test getting a specific job."""
    app = create_app()
    
    # Mock auth dependency
    mock_current_user = MagicMock()
    mock_current_user.user_id = "test-user-123"
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Mock DB
        with patch('src.shared.db.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            job_data = {
                "job_id": "test-job-123",
                "user_id": "test-user-123",
                "product_id": "test-product-456",
                "status": "PROCESSING",
                "adjustments": {"aspect_ratio": "9:16"},
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:01:00Z"
            }
            mock_db.get_job.return_value = job_data
            
            with patch('src.shared.storage.get_storage') as mock_get_storage:
                mock_storage = MagicMock()
                mock_get_storage.return_value = mock_storage
                mock_storage.generate_download_url.return_value = "https://example.com/video.mp4"
                
                client = TestClient(app)
                
                response = client.get("/jobs/test-job-123")
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["job_id"] == "test-job-123"
                assert data["user_id"] == "test-user-123"
                assert data["status"] == "PROCESSING"
                assert data["adjustments"]["aspect_ratio"] == "9:16"
    finally:
        app.dependency_overrides.clear()


def test_get_job_not_found():
    """Test getting non-existent job raises NotFoundError."""
    app = create_app()
    
    # Mock auth dependency
    mock_current_user = MagicMock()
    mock_current_user.user_id = "test-user-123"
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Mock DB to raise NotFoundError
        with patch('src.shared.db.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.get_job.side_effect = NotFoundError("Job", "non-existent-job")
            
            client = TestClient(app)
            
            response = client.get("/jobs/non-existent-job")
            
            assert response.status_code == 404
            data = response.json()
            assert "error" in data
    finally:
        app.dependency_overrides.clear()


@mock_aws
def test_regenerate_job_success():
    """Test successful job regeneration."""
    # Set up mocked resources
    from src.shared.config import Settings
    settings = Settings()
    
    # Mock DynamoDB tables
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    
    # Create required tables
    dynamodb.create_table(
        TableName=settings.dynamodb_users_table,
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    
    dynamodb.create_table(
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
    
    jobs_table = dynamodb.create_table(
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
                "BillingMode": "PAY_PER_REQUEST",
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    
    # Create user, product, and original job
    from src.shared.db import get_db
    db = get_db()
    user_id = "test-user-123"
    db.create_user(user_id=user_id, email="test@example.com")
    
    product = db.create_product(
        user_id=user_id,
        title="Test Product",
        description="Test Description", 
        price="99.99",
        image_keys=["test-image.jpg"]
    )
    product_id = product["product_id"]
    
    original_job = db.create_job(
        user_id=user_id,
        product_id=product_id,
        status="COMPLETE",  # Completed jobs can be regenerated
        video_key="test-video.mp4"
    )
    original_job_id = original_job["job_id"]
    
    # Create test app
    app = create_app()
    
    # Mock the auth dependency
    mock_current_user = MagicMock()
    mock_current_user.user_id = user_id
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        client = TestClient(app)
        
        # Make regeneration request
        request_data = {
            "adjustments": {
                "background_style": "vibrant",
                "tone": "calm"
            }
        }
        
        response = client.post(f"/jobs/{original_job_id}/regenerate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify it's a new job
        assert data["job_id"] != original_job_id
        assert data["user_id"] == user_id
        assert data["product_id"] == product_id
        assert data["status"] == "PENDING"  # New jobs start as pending
        
        # Verify that the new job was created in DB with merged adjustments
        new_job_id = data["job_id"]
        new_job = jobs_table.get_item(
            Key={"user_id": user_id, "job_id": new_job_id}
        )["Item"]
        assert new_job["status"] == "PENDING"
        assert "regeneration_of" in new_job  # Should reference original job
    finally:
        app.dependency_overrides.clear()


def test_regenerate_job_invalid_status():
    """Test regenerating job with invalid status raises ValidationError."""
    app = create_app()
    
    # Mock auth dependency
    mock_current_user = MagicMock()
    mock_current_user.user_id = "test-user-123"
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Mock DB to return job with invalid status for regeneration
        with patch('src.shared.db.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.get_job.return_value = {
                "job_id": "test-job-123",
                "user_id": "test-user-123",
                "product_id": "test-product-456",
                "status": "PENDING",  # Cannot regenerate pending jobs
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
            
            client = TestClient(app)
            
            request_data = {
                "adjustments": {"background_style": "vibrant"}
            }
            
            response = client.post("/jobs/test-job-123/regenerate", json=request_data)
            
            assert response.status_code == 422  # ValidationError
            data = response.json()
            assert "detail" in data  # Pydantic validation error format
    finally:
        app.dependency_overrides.clear()


def test_get_video_download_url_success():
    """Test getting video download URL for completed job."""
    app = create_app()
    
    # Mock auth dependency
    mock_current_user = MagicMock()
    mock_current_user.user_id = "test-user-123"
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Mock DB
        with patch('src.shared.db.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.get_job.return_value = {
                "job_id": "test-job-123",
                "user_id": "test-user-123", 
                "status": "COMPLETE",
                "video_key": "generated/test-video.mp4",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:05:00Z"
            }
            
            # Mock storage
            with patch('src.shared.storage.get_storage') as mock_get_storage:
                mock_storage = MagicMock()
                mock_get_storage.return_value = mock_storage
                mock_storage.generate_download_url.return_value = "https://example.com/download/test-video.mp4"
                
                client = TestClient(app)
                
                response = client.get(f"/jobs/{'test-job-123'}/video")
                
                assert response.status_code == 200
                data = response.json()
                
                assert "data" in data
                assert "download_url" in data["data"]
                assert "test-video.mp4" in data["data"]["download_url"]
    finally:
        app.dependency_overrides.clear()


def test_get_video_download_url_not_complete():
    """Test getting video download URL for non-complete job raises ValidationError."""
    app = create_app()
    
    # Mock auth dependency
    mock_current_user = MagicMock()
    mock_current_user.user_id = "test-user-123"
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Mock DB
        with patch('src.shared.db.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.get_job.return_value = {
                "job_id": "test-job-123",
                "user_id": "test-user-123",
                "status": "PENDING",  # Not complete yet
                "video_key": "generated/test-video.mp4",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
            
            client = TestClient(app)
            
            response = client.get(f"/jobs/{'test-job-123'}/video")
            
            assert response.status_code == 422  # ValidationError
            data = response.json()
            assert "detail" in data
    finally:
        app.dependency_overrides.clear()


def test_get_video_download_url_job_not_found():
    """Test getting video download URL for non-existent job raises NotFoundError."""
    app = create_app()
    
    # Mock auth dependency
    mock_current_user = MagicMock()
    mock_current_user.user_id = "test-user-123"
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Mock DB to raise NotFoundError
        with patch('src.shared.db.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.get_job.side_effect = NotFoundError("Job", "non-existent-job")
            
            client = TestClient(app)
            
            response = client.get("/jobs/non-existent-job/video")
            
            assert response.status_code == 404
            data = response.json()
            assert "error" in data
    finally:
        app.dependency_overrides.clear()