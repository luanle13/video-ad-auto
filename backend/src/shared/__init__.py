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
    ValidationError,
)
from src.shared.logging import configure_logging, get_logger
from src.shared.secrets import SecretsManager, get_secrets
from src.shared.stepfunctions import StepFunctionsClient, get_stepfunctions_client
from src.shared.storage import S3Client, get_storage

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
    "ValidationError",
    # Logging
    "configure_logging",
    "get_logger",
    # Secrets
    "SecretsManager",
    "get_secrets",
    # Step Functions
    "StepFunctionsClient",
    "get_stepfunctions_client",
    # Storage
    "S3Client",
    "get_storage",
]
