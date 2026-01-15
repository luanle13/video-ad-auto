"""Shared utilities and infrastructure."""
from src.shared.config import Settings, get_settings
from src.shared.db import DynamoDBClient, get_db
from src.shared.exceptions import (
    AIVideoPlatformError,
    AgentError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ExternalServiceError,
    NotFoundError,
    RateLimitExceededError,
    ValidationError,
)
from src.shared.logging import configure_logging, get_logger
from src.shared.secrets import SecretsManager, get_secrets
from src.shared.stepfunctions import get_execution_status, get_sfn_client, start_execution
from src.shared.validators import (
    ALLOWED_IMAGE_TYPES,
    ALLOWED_VIDEO_TYPES,
    MAX_IMAGE_SIZE,
    MAX_VIDEO_SIZE,
    NoHtmlStr,
    PromptSafeStr,
    SafeFilename,
    SafeHtmlStr,
    UUIDStr,
    sanitize_for_prompt,
    sanitize_html,
    validate_file_size,
    validate_file_type,
    validate_no_html,
    validate_safe_filename,
    validate_uuid_format,
)

__all__ = [
    # Configuration
    "Settings",
    "get_settings",
    # Database
    "DynamoDBClient",
    "get_db",
    # Exceptions
    "AIVideoPlatformError",
    "AgentError",
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    "ExternalServiceError",
    "NotFoundError",
    "RateLimitExceededError",
    "ValidationError",
    # Logging
    "configure_logging",
    "get_logger",
    # Secrets
    "SecretsManager",
    "get_secrets",
    # Step Functions
    "get_execution_status",
    "get_sfn_client",
    "start_execution",
    # Validators
    "ALLOWED_IMAGE_TYPES",
    "ALLOWED_VIDEO_TYPES",
    "MAX_IMAGE_SIZE",
    "MAX_VIDEO_SIZE",
    "NoHtmlStr",
    "PromptSafeStr",
    "SafeFilename",
    "SafeHtmlStr",
    "UUIDStr",
    "sanitize_for_prompt",
    "sanitize_html",
    "validate_file_size",
    "validate_file_type",
    "validate_no_html",
    "validate_safe_filename",
    "validate_uuid_format",
]
