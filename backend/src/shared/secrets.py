"""AWS Secrets Manager client."""
import json
from typing import Any

import boto3
from botocore.exceptions import ClientError

from src.shared.config import get_settings
from src.shared.exceptions import NotFoundError
from src.shared.logging import get_logger

logger = get_logger(__name__)


class SecretsManager:
    """AWS Secrets Manager client wrapper."""
    
    def __init__(self) -> None:
        settings = get_settings()
        self._client = boto3.client(
            "secretsmanager",
            region_name=settings.aws_region,
        )
    
    def get_secret(self, secret_name: str) -> str:
        """Get a secret value."""
        try:
            response = self._client.get_secret_value(SecretId=secret_name)
            return response["SecretString"]
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                raise NotFoundError("Secret", secret_name)
            raise
    
    def get_secret_json(self, secret_name: str) -> dict[str, Any]:
        """Get a secret value as JSON dict."""
        value = self.get_secret(secret_name)
        return json.loads(value)
    
    def put_secret(self, secret_name: str, value: str | dict[str, Any]) -> None:
        """Create or update a secret."""
        secret_string = value if isinstance(value, str) else json.dumps(value)
        
        try:
            self._client.put_secret_value(
                SecretId=secret_name,
                SecretString=secret_string,
            )
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                # Create new secret if it doesn't exist
                self._client.create_secret(
                    Name=secret_name,
                    SecretString=secret_string,
                )
            else:
                raise
        
        logger.info("secret_updated", secret_name=secret_name)
    
    def delete_secret(self, secret_name: str) -> None:
        """Delete a secret."""
        try:
            self._client.delete_secret(
                SecretId=secret_name,
                ForceDeleteWithoutRecovery=True,
            )
            logger.info("secret_deleted", secret_name=secret_name)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code != "ResourceNotFoundException":
                raise


# Singleton instance
_secrets_manager: SecretsManager | None = None


def get_secrets() -> SecretsManager:
    """Get Secrets Manager client singleton."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def get_user_credentials_secret_name(user_id: str) -> str:
    """Generate secret name for user platform credentials."""
    return f"ai-video/users/{user_id}/platform-credentials"