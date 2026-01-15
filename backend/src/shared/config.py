"""Application configuration using pydantic-settings."""
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Environment
    environment: Literal["dev", "prod"] = "dev"
    debug: bool = False

    # Frontend
    frontend_url: str = Field(
        default="",
        description="Production frontend URL for CORS",
    )
    
    # AWS
    aws_region: str = "ap-southeast-1"
    aws_access_key_id: str | None = None  # None = use IAM role
    aws_secret_access_key: SecretStr | None = None
    
    # DynamoDB
    dynamodb_users_table: str = "ai-video-users"
    dynamodb_products_table: str = "ai-video-products"
    dynamodb_jobs_table: str = "ai-video-jobs"
    
    # Redis Cache
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600
    cache_image_ttl: int = 7200
    cache_regen_ttl: int = 86400
    
    # Cognito
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""
    cognito_region: str = "ap-southeast-1"
    
    # Step Functions
    stepfunctions_state_machine_arn: str = ""
    
    # Secrets Manager keys (ARN or name)
    secrets_openai_key: str = "ai-video/openai-api-key"
    secrets_kling_key: str = "ai-video/kling-api-key"
    secrets_elevenlabs_key: str = "ai-video/elevenlabs-api-key"

    # OpenAI Configuration
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 4096
    openai_temperature: float = 0.7

    # External APIs (loaded from Secrets Manager at runtime, not env)
    # These are placeholders for local development only
    openai_api_key: SecretStr | None = None
    kling_api_key: SecretStr | None = None
    elevenlabs_api_key: SecretStr | None = None
    
    # Rate limits
    max_images_per_product: int = 5
    max_image_size_mb: int = 5
    max_video_duration_seconds: int = 60
    
    # Timeouts
    agent_timeout_seconds: int = 180
    tts_timeout_seconds: int = 120
    video_generation_timeout_seconds: int = 600
    
    # Azure OpenAI
    azure_openai_api_key: SecretStr | None = None
    azure_openai_endpoint: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()