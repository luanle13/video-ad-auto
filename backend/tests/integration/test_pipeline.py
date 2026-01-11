"""Integration tests for the complete AI video generation pipeline using moto and mocked external APIs."""
import asyncio
import json
import os
from unittest.mock import AsyncMock, Mock, patch

import boto3
import pytest
from moto import mock_aws

from src.agents.handler import handler as agent_handler
from src.shared.db import get_db, DynamoDBClient
from src.shared.storage import get_storage
from src.workers.handlers.tts_handler import handler as tts_handler
from src.workers.handlers.video_handler import handler as video_handler
from src.api.models.jobs import JobStatus
from src.shared.config import get_settings


@pytest.fixture(autouse=True)
def reset_cached_instances():
    """Reset cached instances before and after each test."""
    from src.shared.db import _db_client
    from src.shared.storage import _s3_client
    from src.shared.secrets import _secrets_manager

    # Save original values
    orig_db_client = _db_client
    orig_s3_client = _s3_client
    orig_secrets_manager = _secrets_manager

    # Reset to None
    _db_client = None
    _s3_client = None
    _secrets_manager = None

    yield

    # Restore original values
    _db_client = orig_db_client
    _s3_client = orig_s3_client
    _secrets_manager = orig_secrets_manager


@pytest.fixture
def dynamodb_client(aws_credentials):
    """Create mock DynamoDB client."""
    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        yield client


@pytest.fixture
def s3_client(aws_credentials):
    """Create mock S3 client."""
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        yield client


@pytest.fixture
def create_tables(dynamodb_client):
    """Create all test tables."""
    # Create users table
    dynamodb_client.create_table(
        TableName="ai-video-users",
        KeySchema=[
            {
                'AttributeName': 'user_id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    # Create products table
    dynamodb_client.create_table(
        TableName="ai-video-products",
        KeySchema=[
            {
                'AttributeName': 'user_id',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'product_id',
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'product_id',
                'AttributeType': 'S'
            }
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'UserIdIndex',
                'KeySchema': [
                    {
                        'AttributeName': 'user_id',
                        'KeyType': 'HASH'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                }
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    # Create jobs table
    dynamodb_client.create_table(
        TableName="ai-video-jobs",
        KeySchema=[
            {
                'AttributeName': 'user_id',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'job_id',
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'job_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'status',
                'AttributeType': 'S'
            }
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'status-index',
                'KeySchema': [
                    {
                        'AttributeName': 'user_id',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'status',
                        'KeyType': 'RANGE'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                }
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    yield {
        "users": "ai-video-users",
        "products": "ai-video-products",
        "jobs": "ai-video-jobs"
    }


@pytest.fixture
def create_buckets(s3_client):
    """Create test S3 buckets."""
    s3_client.create_bucket(Bucket="ai-video-images")
    s3_client.create_bucket(Bucket="ai-video-videos")
    return {"images": "ai-video-images", "videos": "ai-video-videos"}


@pytest.fixture
def mock_settings():
    """Mock application settings."""
    with patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_DEFAULT_REGION": "us-east-1",
        "DYNAMODB_USERS_TABLE": "ai-video-users",
        "DYNAMODB_PRODUCTS_TABLE": "ai-video-products",
        "DYNAMODB_JOBS_TABLE": "ai-video-jobs",
        "S3_IMAGES_BUCKET": "ai-video-images",
        "S3_VIDEOS_BUCKET": "ai-video-videos"
    }):
        # Clear the settings cache to force reload with new environment variables
        get_settings.cache_clear()
        yield
        # Clear the cache again after test
        get_settings.cache_clear()


@pytest.fixture
def mock_external_apis():
    """Mock external APIs (Anthropic, ElevenLabs, Kling)."""
    with patch('src.workers.clients.elevenlabs.ElevenLabsClient.text_to_speech') as mock_elevenlabs, \
         patch('src.workers.clients.polly.PollyClient.text_to_speech') as mock_polly, \
         patch('src.workers.services.video_service.VideoService.generate_video') as mock_kling:
        
        # Mock ElevenLabs response
        mock_elevenlabs_response = Mock()
        mock_elevenlabs_response.audio_data = b"mocked audio data from elevenlabs"
        mock_elevenlabs_response.character_count = 100
        mock_elevenlabs.return_value = mock_elevenlabs_response
        
        # Mock Polly response
        mock_polly_response = Mock()
        mock_polly_response.audio_data = b"mocked audio data from polly"
        mock_polly_response.request_characters = 100
        mock_polly.return_value = mock_polly_response
        
        # Mock Kling response
        mock_kling_response = Mock()
        mock_kling_response.video_data = b"mocked video data from kling"
        mock_kling_response.duration_seconds = 5.0
        mock_kling_response.job_response = Mock()
        mock_kling_response.job_response.data = {"job_id": "mock_kling_job_123"}
        mock_kling.return_value = mock_kling_response
        
        yield {
            "elevenlabs": mock_elevenlabs,
            "polly": mock_polly,
            "kling": mock_kling
        }


def test_complete_pipeline_success(mock_settings, mock_external_apis):
    """Test the complete pipeline from product analysis to video generation."""
    # Setup test data
    user_id = "test_user_123"
    job_id = "test_job_456"
    product_id = "test_product_789"

    with mock_aws():
        # Create a fresh DynamoDB resource inside the mock context
        import boto3
        from src.shared.db import DynamoDBClient
        dynamodb_resource = boto3.resource('dynamodb', region_name='us-east-1')

        # Create the tables using the same resource
        dynamodb_resource.create_table(
            TableName='ai-video-users',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        dynamodb_resource.create_table(
            TableName='ai-video-products',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'product_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'product_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        dynamodb_resource.create_table(
            TableName='ai-video-jobs',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'job_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'job_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # Create S3 resource and buckets
        s3_resource = boto3.resource('s3', region_name='us-east-1')
        s3_resource.create_bucket(Bucket='ai-video-images')
        s3_resource.create_bucket(Bucket='ai-video-videos')

        # Create the DB client with the mocked resources
        db = DynamoDBClient(dynamodb_resource=dynamodb_resource)

        # Temporarily patch the get_db function to return our mocked instance
        import src.shared.db
        original_get_db = src.shared.db.get_db

        def mock_get_db():
            return db

        # Temporarily patch the get_storage function to use the mocked S3 resource
        from src.shared.storage import S3Client
        import src.shared.storage
        original_get_storage = src.shared.storage.get_storage
        original_s3_client_init = S3Client.__init__

        def mock_get_storage():
            # Create S3Client with mocked resource
            s3_client_instance = S3Client.__new__(S3Client)
            original_s3_client_init(s3_client_instance)
            s3_client_instance._s3 = s3_resource.meta.client
            return s3_client_instance

        # Patch both functions temporarily
        src.shared.db.get_db = mock_get_db
        src.shared.storage.get_storage = mock_get_storage

        try:
            db.create_job(user_id=user_id, product_id=product_id, adjustments={})
        finally:
            # Restore the original functions
            src.shared.db.get_db = original_get_db
            src.shared.storage.get_storage = original_get_storage

        # Mock product data
        product_data = {
            "id": product_id,
            "title": "Wireless Bluetooth Headphones",
            "description": "High-quality wireless headphones with noise cancellation",
            "price": "199.99",
            "image_keys": ["images/test_user_123/test_product_789/headphone1.jpg"]
        }

        # Mock context to pass between steps
        context = {}

        # Step 1: Product Analysis
        analyze_event = {
            "task": "analyze",
            "user_id": user_id,
            "job_id": job_id,
            "product": product_data,
            "context": context,
            "adjustments": {}
        }

        analyze_result = agent_handler(analyze_event, {})
        assert analyze_result["success"] is True
        context["analyze"] = {"output": analyze_result["output"]}

        # Verify job status was updated
        job = db.get_job(user_id, job_id)
        assert job["status"] == "ANALYZING"

        # Step 2: Market Insight
        market_insight_event = {
            "task": "market_insight",
            "user_id": user_id,
            "job_id": job_id,
            "product": product_data,
            "context": context,
            "adjustments": {}
        }

        market_insight_result = agent_handler(market_insight_event, {})
        assert market_insight_result["success"] is True
        context["market_insight"] = {"output": market_insight_result["output"]}

        # Step 3: Script Generation
        generate_event = {
            "task": "generate",
            "user_id": user_id,
            "job_id": job_id,
            "product": product_data,
            "context": context,
            "adjustments": {"target_duration": 45, "tone": "energetic"}
        }

        generate_result = agent_handler(generate_event, {})
        assert generate_result["success"] is True
        context["generate"] = {"output": generate_result["output"]}

        # Step 4: Script Optimization
        optimize_event = {
            "task": "optimize",
            "user_id": user_id,
            "job_id": job_id,
            "product": product_data,
            "context": context,
            "adjustments": {"target_duration": 45, "tone": "energetic"}
        }

        optimize_result = agent_handler(optimize_event, {})
        assert optimize_result["success"] is True
        context["optimize"] = {"output": optimize_result["output"]}

        # Step 5: Script Review
        review_event = {
            "task": "review",
            "user_id": user_id,
            "job_id": job_id,
            "product": product_data,
            "context": context,
            "adjustments": {"target_duration": 45, "tone": "energetic"}
        }

        review_result = agent_handler(review_event, {})
        assert review_result["success"] is True
        context["review"] = {"output": review_result["output"]}

        # Step 6: TTS Generation
        tts_script = context["optimize"]["output"]["optimized_voiceover"]
        tts_event = {
            "user_id": user_id,
            "job_id": job_id,
            "tts_script": tts_script,
            "voice_gender": "female",
            "voice_style": "professional",
            "speaking_rate": 1.0,
        }

        tts_result = asyncio.run(tts_handler(tts_event, {}))
        assert tts_result["success"] is True
        assert tts_result["audio_s3_key"] is not None

        # Step 7: Video Generation
        video_prompt = "A promotional video for wireless headphones with dynamic transitions and modern graphics"
        video_event = {
            "user_id": user_id,
            "job_id": job_id,
            "video_prompt": video_prompt,
            "audio_s3_key": tts_result["audio_s3_key"],
            "aspect_ratio": "9:16",
            "duration": 5
        }

        video_result = asyncio.run(video_handler(video_event, {}))
        assert video_result["success"] is True
        assert video_result["video_s3_key"] is not None

        # Final verification: Job should be complete
        final_job = db.get_job(user_id, job_id)
        assert final_job["status"] == "COMPLETE"
        assert "video" in final_job["step_outputs"]
        assert "tts" in final_job["step_outputs"]


def test_pipeline_agent_failure_handling(mock_settings):
    """Test pipeline handling of agent failures."""
    user_id = "test_user_123"
    job_id = "test_job_456"
    product_id = "test_product_789"

    with mock_aws():
        # Create the tables first
        import boto3
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='ai-video-users',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        dynamodb.create_table(
            TableName='ai-video-products',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'product_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'product_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        dynamodb.create_table(
            TableName='ai-video-jobs',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'job_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'job_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # Reset the cached DB client to ensure it gets recreated with mocked resources
        from src.shared.db import _db_client
        global _db_client
        _db_client = None

        # Create a job in the database
        db = get_db()
        db.create_job(user_id=user_id, product_id=product_id, adjustments={})

        # Mock product data
        product_data = {
            "id": product_id,
            "title": "Wireless Bluetooth Headphones",
            "description": "High-quality wireless headphones with noise cancellation",
            "price": "199.99",
            "image_keys": ["images/test_user_123/test_product_789/headphone1.jpg"]
        }

        # Mock an agent that raises an exception
        with patch('src.agents.product_analyzer.ProductAnalyzerAgent.run', side_effect=Exception("Test error")):
            analyze_event = {
                "task": "analyze",
                "user_id": user_id,
                "job_id": job_id,
                "product": product_data,
                "context": {},
                "adjustments": {}
            }

            # This should raise an exception which is caught by the handler
            with pytest.raises(Exception):
                agent_handler(analyze_event, {})

            # Verify job status was updated to FAILED
            job = db.get_job(user_id, job_id)
            assert job["status"] == "FAILED"
            assert "error_message" in job
            assert "Test error" in job["error_message"]


def test_pipeline_tts_fallback(mock_settings, mock_external_apis):
    """Test TTS service fallback from ElevenLabs to Polly."""
    user_id = "test_user_123"
    job_id = "test_job_456"
    product_id = "test_product_789"

    with mock_aws():
        # Create the tables first
        import boto3
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='ai-video-users',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        dynamodb.create_table(
            TableName='ai-video-products',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'product_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'product_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        dynamodb.create_table(
            TableName='ai-video-jobs',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'job_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'job_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # Create S3 buckets
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='ai-video-images')
        s3.create_bucket(Bucket='ai-video-videos')

        # Reset the cached DB client to ensure it gets recreated with mocked resources
        from src.shared.db import _db_client
        global _db_client
        _db_client = None

        # Reset the cached S3 client too
        from src.shared.storage import _s3_client
        global _s3_client
        _s3_client = None

        # Create a job in the database
        db = get_db()
        db.create_job(user_id=user_id, product_id=product_id, adjustments={})

        # Mock ElevenLabs to fail, but Polly to succeed
        mock_external_apis["elevenlabs"].side_effect = Exception("ElevenLabs API error")

        # TTS event with AUTO provider (should fallback to Polly)
        tts_event = {
            "user_id": user_id,
            "job_id": job_id,
            "tts_script": "This is a test script for TTS fallback",
            "voice_gender": "female",
            "voice_style": "professional",
            "speaking_rate": 1.0,
        }

        tts_result = asyncio.run(tts_handler(tts_event, {}))

        # Should succeed using Polly fallback
        assert tts_result["success"] is True
        assert tts_result["provider_used"] == "POLLY"
        assert tts_result["audio_s3_key"] is not None

        # Verify Polly was called
        mock_external_apis["polly"].assert_called_once()


def test_pipeline_video_generation(mock_settings, mock_external_apis):
    """Test video generation step with mocked Kling API."""
    user_id = "test_user_123"
    job_id = "test_job_456"
    product_id = "test_product_789"

    with mock_aws():
        # Create the tables first
        import boto3
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='ai-video-users',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        dynamodb.create_table(
            TableName='ai-video-products',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'product_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'product_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        dynamodb.create_table(
            TableName='ai-video-jobs',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'job_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'job_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # Create S3 buckets
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='ai-video-images')
        s3.create_bucket(Bucket='ai-video-videos')

        # Reset the cached DB client to ensure it gets recreated with mocked resources
        from src.shared.db import _db_client
        global _db_client
        _db_client = None

        # Reset the cached S3 client too
        from src.shared.storage import _s3_client
        global _s3_client
        _s3_client = None

        # Create a job in the database
        db = get_db()
        db.create_job(user_id=user_id, product_id=product_id, adjustments={})

        # Create an audio file first
        storage = get_storage()
        audio_key = storage.generate_audio_key(user_id, job_id)
        storage.upload_file(
            bucket_type="videos",
            key=audio_key,
            body=b"mock audio data",
            content_type="audio/mpeg"
        )

        # Video generation event
        video_event = {
            "user_id": user_id,
            "job_id": job_id,
            "video_prompt": "A promotional video for wireless headphones with dynamic transitions",
            "audio_s3_key": audio_key,
            "aspect_ratio": "9:16",
            "duration": 5
        }

        video_result = asyncio.run(video_handler(video_event, {}))

        # Verify video generation succeeded
        assert video_result["success"] is True
        assert video_result["video_s3_key"] is not None
        assert video_result["duration_seconds"] == 5.0

        # Verify job status is COMPLETE
        job = db.get_job(user_id, job_id)
        assert job["status"] == "COMPLETE"

        # Verify video was stored in S3
        storage_client = get_storage()
        assert storage_client.file_exists("videos", video_result["video_s3_key"])


def test_pipeline_job_status_progression(mock_settings, mock_external_apis):
    """Test that job status progresses correctly through the pipeline."""
    user_id = "test_user_123"
    job_id = "test_job_456"
    product_id = "test_product_789"

    with mock_aws():
        # Create the tables first
        import boto3
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='ai-video-users',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        dynamodb.create_table(
            TableName='ai-video-products',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'product_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'product_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        dynamodb.create_table(
            TableName='ai-video-jobs',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'job_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'job_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # Create S3 buckets
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='ai-video-images')
        s3.create_bucket(Bucket='ai-video-videos')

        # Reset the cached DB client to ensure it gets recreated with mocked resources
        from src.shared.db import _db_client
        global _db_client
        _db_client = None

        # Reset the cached S3 client too
        from src.shared.storage import _s3_client
        global _s3_client
        _s3_client = None

        # Create a job in the database
        db = get_db()
        db.create_job(user_id=user_id, product_id=product_id, adjustments={})

        # Mock product data
        product_data = {
            "id": product_id,
            "title": "Wireless Bluetooth Headphones",
            "description": "High-quality wireless headphones with noise cancellation",
            "price": "199.99",
            "image_keys": ["images/test_user_123/test_product_789/headphone1.jpg"]
        }

        # Verify initial status
        job = db.get_job(user_id, job_id)
        assert job["status"] == "PENDING"

        # Step 1: Product Analysis
        analyze_event = {
            "task": "analyze",
            "user_id": user_id,
            "job_id": job_id,
            "product": product_data,
            "context": {},
            "adjustments": {}
        }

        agent_handler(analyze_event, {})
        job = db.get_job(user_id, job_id)
        assert job["status"] == "ANALYZING"

        # Step 2: Script Generation
        generate_event = {
            "task": "generate",
            "user_id": user_id,
            "job_id": job_id,
            "product": product_data,
            "context": {"analyze": {"output": {"key_features": ["noise cancellation", "wireless"]}}},
            "adjustments": {}
        }

        agent_handler(generate_event, {})
        job = db.get_job(user_id, job_id)
        assert job["status"] == "SCRIPTING"

        # Step 3: TTS Generation
        tts_event = {
            "user_id": user_id,
            "job_id": job_id,
            "tts_script": "This is a test script",
            "voice_gender": "female",
            "voice_style": "professional",
            "speaking_rate": 1.0,
        }

        asyncio.run(tts_handler(tts_event, {}))
        job = db.get_job(user_id, job_id)
        assert job["status"] == "GENERATING_TTS"

        # Step 4: Video Generation
        video_event = {
            "user_id": user_id,
            "job_id": job_id,
            "video_prompt": "A promotional video for wireless headphones",
            "aspect_ratio": "9:16",
            "duration": 5
        }

        asyncio.run(video_handler(video_event, {}))
        job = db.get_job(user_id, job_id)
        assert job["status"] == "COMPLETE"


def test_pipeline_output_storage(mock_settings, mock_external_apis):
    """Test that pipeline outputs are properly stored in S3 and DynamoDB."""
    user_id = "test_user_123"
    job_id = "test_job_456"
    product_id = "test_product_789"

    with mock_aws():
        # Create the tables first
        import boto3
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='ai-video-users',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        dynamodb.create_table(
            TableName='ai-video-products',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'product_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'product_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        dynamodb.create_table(
            TableName='ai-video-jobs',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'job_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'job_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # Create S3 buckets
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='ai-video-images')
        s3.create_bucket(Bucket='ai-video-videos')

        # Reset the cached DB client to ensure it gets recreated with mocked resources
        from src.shared.db import _db_client
        global _db_client
        _db_client = None

        # Reset the cached S3 client too
        from src.shared.storage import _s3_client
        global _s3_client
        _s3_client = None

        # Create a job in the database
        db = get_db()
        db.create_job(user_id=user_id, product_id=product_id, adjustments={})

        # Mock product data
        product_data = {
            "id": product_id,
            "title": "Wireless Bluetooth Headphones",
            "description": "High-quality wireless headphones with noise cancellation",
            "price": "199.99",
            "image_keys": ["images/test_user_123/test_product_789/headphone1.jpg"]
        }

        # Run script generation agent
        generate_event = {
            "task": "generate",
            "user_id": user_id,
            "job_id": job_id,
            "product": product_data,
            "context": {"analyze": {"output": {"key_features": ["noise cancellation", "wireless"]}}},
            "adjustments": {"target_duration": 45, "tone": "energetic"}
        }

        generate_result = agent_handler(generate_event, {})
        assert generate_result["success"] is True

        # Verify agent output was stored in DynamoDB
        job = db.get_job(user_id, job_id)
        assert "generate" in job["step_outputs"]
        assert "hook" in job["step_outputs"]["generate"]

        # Run TTS generation
        tts_script = generate_result["output"]["full_voiceover_text"]
        tts_event = {
            "user_id": user_id,
            "job_id": job_id,
            "tts_script": tts_script,
            "voice_gender": "female",
            "voice_style": "professional",
            "speaking_rate": 1.0,
        }

        tts_result = asyncio.run(tts_handler(tts_event, {}))
        assert tts_result["success"] is True
        assert tts_result["audio_s3_key"] is not None

        # Verify TTS output was stored in DynamoDB
        job = db.get_job(user_id, job_id)
        assert "tts" in job["step_outputs"]
        assert job["step_outputs"]["tts"]["audio_s3_key"] == tts_result["audio_s3_key"]

        # Verify audio file exists in S3
        storage = get_storage()
        assert storage.file_exists("videos", tts_result["audio_s3_key"])

        # Run video generation
        video_event = {
            "user_id": user_id,
            "job_id": job_id,
            "video_prompt": "A promotional video for wireless headphones",
            "audio_s3_key": tts_result["audio_s3_key"],
            "aspect_ratio": "9:16",
            "duration": 5
        }

        video_result = asyncio.run(video_handler(video_event, {}))
        assert video_result["success"] is True
        assert video_result["video_s3_key"] is not None

        # Verify video output was stored in DynamoDB
        job = db.get_job(user_id, job_id)
        assert "video" in job["step_outputs"]
        assert job["step_outputs"]["video"]["video_s3_key"] == video_result["video_s3_key"]

        # Verify video file exists in S3
        assert storage.file_exists("videos", video_result["video_s3_key"])