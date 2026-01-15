"""Tests for the application configuration."""
import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.shared.config import Settings, get_settings


def test_default_values():
    """Test that settings load with correct default values."""
    settings = Settings()
    
    # Environment defaults
    assert settings.environment == "dev"
    assert settings.debug is False
    
    # AWS defaults
    assert settings.aws_region == "ap-southeast-1"
    assert settings.aws_access_key_id is None
    assert settings.aws_secret_access_key is None
    
    # DynamoDB defaults
    assert settings.dynamodb_users_table == "ai-video-users"
    assert settings.dynamodb_products_table == "ai-video-products"
    assert settings.dynamodb_jobs_table == "ai-video-jobs"
    
    # Redis defaults
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.cache_ttl == 3600
    assert settings.cache_image_ttl == 7200
    assert settings.cache_regen_ttl == 86400
    
    # Cognito defaults
    assert settings.cognito_user_pool_id == ""
    assert settings.cognito_app_client_id == ""
    assert settings.cognito_region == "ap-southeast-1"
    
    # Step Functions defaults
    assert settings.stepfunctions_state_machine_arn == ""
    
    # Secrets Manager defaults
    assert settings.secrets_openai_key == "ai-video/openai-api-key"
    assert settings.secrets_kling_key == "ai-video/kling-api-key"
    assert settings.secrets_elevenlabs_key == "ai-video/elevenlabs-api-key"

    # OpenAI configuration defaults
    assert settings.openai_model == "gpt-4o"
    assert settings.openai_max_tokens == 4096
    assert settings.openai_temperature == 0.7

    # External API keys defaults
    assert settings.openai_api_key is None
    assert settings.kling_api_key is None
    assert settings.elevenlabs_api_key is None
    
    # Rate limits defaults
    assert settings.max_images_per_product == 5
    assert settings.max_image_size_mb == 5
    assert settings.max_video_duration_seconds == 60
    
    # Timeouts defaults
    assert settings.agent_timeout_seconds == 180
    assert settings.tts_timeout_seconds == 120
    assert settings.video_generation_timeout_seconds == 600


def test_environment_variable_override():
    """Test that environment variables override default values."""
    with patch.dict(os.environ, {
        "ENVIRONMENT": "prod",
        "DEBUG": "true",
        "AWS_REGION": "us-west-2",
        "DYNAMODB_USERS_TABLE": "ai-video-users-prod",
        "REDIS_URL": "redis://redis.prod:6379/0",
        "COGNITO_USER_POOL_ID": "us-west-2_XXXXXXXXX",
        "COGNITO_APP_CLIENT_ID": "xxxxxxxxxxxxxxxxxxxxxxxxxx",
        "STEPFUNCTIONS_STATE_MACHINE_ARN": "arn:aws:states:us-west-2:123456789012:stateMachine:test"
    }):
        settings = Settings()

        assert settings.environment == "prod"
        assert settings.debug is True
        assert settings.aws_region == "us-west-2"
        assert settings.dynamodb_users_table == "ai-video-users-prod"
        assert settings.redis_url == "redis://redis.prod:6379/0"
        assert settings.cognito_user_pool_id == "us-west-2_XXXXXXXXX"
        assert settings.cognito_app_client_id == "xxxxxxxxxxxxxxxxxxxxxxxxxx"
        assert settings.stepfunctions_state_machine_arn == "arn:aws:states:us-west-2:123456789012:stateMachine:test"


def test_validation_errors_for_invalid_values():
    """Test that validation errors are raised for invalid values."""
    # Test invalid environment value
    with patch.dict(os.environ, {"ENVIRONMENT": "invalid"}):
        with pytest.raises(ValueError):
            Settings()


def test_settings_singleton():
    """Test that get_settings returns a cached singleton instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    
    assert settings1 is settings2
    assert settings1.environment == settings2.environment