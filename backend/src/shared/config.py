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
    
    # S3
    s3_images_bucket: str = "ai-video-images"
    s3_videos_bucket: str = "ai-video-videos"
    s3_presigned_expiry: int = Field(default=900, description="Presigned URL expiry in seconds")
    
    # Cognito
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""  # Maps to COGNITO_CLIENT_ID env var
    cognito_region: str = "ap-southeast-1"
    
    # Step Functions
    stepfunctions_state_machine_arn: str = ""
    
    # Secrets Manager keys (ARN or name)
    secrets_openai_key: str = "ai-video/openai-api-key"
    secrets_kling_key: str = "ai-video/kling-api-key"
    secrets_elevenlabs_key: str = "ai-video/elevenlabs-api-key"
    secrets_piapi_key: str = "ai-video/piapi-api-key"
    secrets_azure_image_key: str = "ai-video/azure-image-api-key"
    secrets_deepinfra_key: str = "ai-video/deepinfra-api-key"

    # OpenAI Configuration (Azure OpenAI)
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 4096
    openai_temperature: float = 0.7

    # External APIs (loaded from environment for Azure)
    openai_api_key: SecretStr | None = None  # Deprecated - use Azure
    kling_api_key: SecretStr | None = None
    elevenlabs_api_key: SecretStr | None = None
    
    # Rate limits
    max_images_per_product: int = 5
    max_image_size_mb: int = 5
    max_video_duration_seconds: int = 20  # Updated for 15-20s kitchen product videos
    
    # Timeouts
    agent_timeout_seconds: int = 180
    tts_timeout_seconds: int = 120
    video_generation_timeout_seconds: int = 600
    
    # Azure OpenAI (for both GPT-4o and FLUX-1.1-pro)
    azure_openai_api_key: SecretStr | None = None
    azure_openai_endpoint: str | None = None  # e.g., https://your-resource.openai.azure.com/openai/v1/
    azure_gpt_deployment_name: str = "gpt-4.1"  # Deployment name for GPT model
    azure_flux_deployment_name: str = "FLUX-1.1-pro"  # Deployment name for FLUX-1.1-pro
    
    # PiAPI (for Wan 2.6 video generation) - deprecated, kept for compatibility
    piapi_api_key: SecretStr | None = None

    # DeepInfra (for Veo 3.1 Fast video generation)
    deepinfra_api_key: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()