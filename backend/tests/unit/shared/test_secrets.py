"""Tests for AWS Secrets Manager client and credentials routes."""
import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from src.api.main import create_app
from src.api.dependencies.auth import AuthenticatedUser
from src.api.models.credentials import (
    PlatformCredentialsRequest,
    TikTokCredentials,
    ShopeeCredentials,
    FacebookCredentials,
)
from src.shared.secrets import SecretsManager, get_secrets, get_user_credentials_secret_name
from src.shared.exceptions import NotFoundError


@mock_aws
def test_get_secret_success():
    """Test successful secret retrieval."""
    import boto3
    
    # Create a secret in the mock
    client = boto3.client("secretsmanager", region_name="us-east-1")
    secret_name = "test-secret"
    secret_value = "test-value"
    
    client.create_secret(Name=secret_name, SecretString=secret_value)
    
    # Test the SecretsManager client
    sm = SecretsManager()
    result = sm.get_secret(secret_name)
    
    assert result == secret_value


@mock_aws
def test_get_secret_not_found():
    """Test retrieving non-existent secret raises NotFoundError."""
    sm = SecretsManager()
    
    with pytest.raises(NotFoundError):
        sm.get_secret("non-existent-secret")


@mock_aws
def test_get_secret_json_success():
    """Test successful JSON secret retrieval."""
    import boto3
    
    # Create a JSON secret in the mock
    client = boto3.client("secretsmanager", region_name="us-east-1")
    secret_name = "test-json-secret"
    secret_value = {"key": "value", "nested": {"data": "test"}}
    
    client.create_secret(Name=secret_name, SecretString=json.dumps(secret_value))
    
    # Test the SecretsManager client
    sm = SecretsManager()
    result = sm.get_secret_json(secret_name)
    
    assert result == secret_value


@mock_aws
def test_put_secret_new():
    """Test creating a new secret."""
    import boto3
    
    # Create mock client to verify
    client = boto3.client("secretsmanager", region_name="us-east-1")
    sm = SecretsManager()
    
    secret_name = "new-test-secret"
    secret_value = "new-value"
    
    sm.put_secret(secret_name, secret_value)
    
    # Verify secret was created
    response = client.get_secret_value(SecretId=secret_name)
    assert response["SecretString"] == secret_value


@mock_aws
def test_put_secret_update():
    """Test updating an existing secret."""
    import boto3
    
    # Create a secret first
    client = boto3.client("secretsmanager", region_name="us-east-1")
    secret_name = "update-test-secret"
    initial_value = "initial-value"
    
    client.create_secret(Name=secret_name, SecretString=initial_value)
    
    # Update the secret using our client
    sm = SecretsManager()
    updated_value = "updated-value"
    
    sm.put_secret(secret_name, updated_value)
    
    # Verify secret was updated
    response = client.get_secret_value(SecretId=secret_name)
    assert response["SecretString"] == updated_value


@mock_aws
def test_put_secret_json():
    """Test putting a JSON secret."""
    import boto3
    
    # Create mock client to verify
    client = boto3.client("secretsmanager", region_name="us-east-1")
    sm = SecretsManager()
    
    secret_name = "json-test-secret"
    secret_value = {"username": "test", "password": "secure123"}
    
    sm.put_secret(secret_name, secret_value)
    
    # Verify secret was stored as JSON
    response = client.get_secret_value(SecretId=secret_name)
    stored_value = json.loads(response["SecretString"])
    assert stored_value == secret_value


@mock_aws
def test_delete_secret():
    """Test deleting a secret."""
    import boto3
    
    # Create a secret first
    client = boto3.client("secretsmanager", region_name="us-east-1")
    secret_name = "delete-test-secret"
    
    client.create_secret(Name=secret_name, SecretString="to-be-deleted")
    
    # Verify it exists
    response = client.get_secret_value(SecretId=secret_name)
    assert response["SecretString"] == "to-be-deleted"
    
    # Delete the secret using our client
    sm = SecretsManager()
    sm.delete_secret(secret_name)
    
    # Verify it's gone
    with pytest.raises(Exception):
        client.get_secret_value(SecretId=secret_name)


@mock_aws
def test_delete_nonexistent_secret():
    """Test deleting non-existent secret doesn't raise error."""
    sm = SecretsManager()
    
    # Should not raise an exception
    sm.delete_secret("non-existent-secret")


def test_user_credentials_secret_name():
    """Test user credentials secret name generation."""
    user_id = "test-user-123"
    expected = "ai-video/users/test-user-123/platform-credentials"
    result = get_user_credentials_secret_name(user_id)
    
    assert result == expected


@mock_aws
def test_secrets_manager_singleton():
    """Test that get_secrets returns the same instance."""
    sm1 = get_secrets()
    sm2 = get_secrets()
    
    assert sm1 is sm2


# Tests for credentials routes
def test_update_credentials_success():
    """Test successful credential update."""
    app = create_app()
    
    # Mock current user
    mock_current_user = AuthenticatedUser(
        user_id="test-user-123",
        email="test@example.com",
        token_claims={}
    )
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Mock the secrets client
        with patch('src.shared.secrets.get_secrets') as mock_get_secrets:
            mock_sm = MagicMock()
            mock_get_secrets.return_value = mock_sm
            mock_sm.get_secret_json.return_value = {}
            
            client = TestClient(app)
            
            # Prepare request data
            request_data = {
                "tiktok": {
                    "access_token": "test-tiktok-token"
                },
                "shopee": {
                    "shop_id": "test-shop-id",
                    "access_token": "test-shopee-token"
                },
                "facebook": {
                    "page_id": "test-page-id",
                    "access_token": "test-facebook-token"
                }
            }
            
            response = client.put("/auth/credentials", json=request_data)
            
            # Should return 200 for success
            assert response.status_code == 200
            data = response.json()
            
            # Verify response
            assert data["tiktok_configured"] is True
            assert data["shopee_configured"] is True
            assert data["facebook_configured"] is True
            
            # Verify the secret was updated
            mock_sm.put_secret.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_get_credentials_status():
    """Test getting credentials status."""
    app = create_app()
    
    # Mock current user
    mock_current_user = AuthenticatedUser(
        user_id="test-user-123",
        email="test@example.com",
        token_claims={}
    )
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Mock the secrets client
        with patch('src.shared.secrets.get_secrets') as mock_get_secrets:
            mock_sm = MagicMock()
            mock_get_secrets.return_value = mock_sm
            mock_sm.get_secret_json.return_value = {
                "tiktok": {"access_token": "redacted"},
                "facebook": {"access_token": "redacted", "page_id": "test-page"}
            }
            
            client = TestClient(app)
            
            response = client.get("/auth/credentials")
            
            # Should return 200 for success
            assert response.status_code == 200
            data = response.json()
            
            # Verify response shows only configuration status
            assert data["tiktok_configured"] is True
            assert data["shopee_configured"] is False  # Not in stored credentials
            assert data["facebook_configured"] is True
            # Actual credential values should not be in response
            assert "tiktok" not in data or "access_token" not in data.get("tiktok", {})
    finally:
        app.dependency_overrides.clear()


def test_delete_credentials_success():
    """Test successful credential deletion."""
    app = create_app()
    
    # Mock current user
    mock_current_user = AuthenticatedUser(
        user_id="test-user-123",
        email="test@example.com",
        token_claims={}
    )
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Mock the secrets client
        with patch('src.shared.secrets.get_secrets') as mock_get_secrets:
            mock_sm = MagicMock()
            mock_get_secrets.return_value = mock_sm
            mock_sm.get_secret_json.return_value = {
                "tiktok": {"access_token": "test-token"},
                "facebook": {"access_token": "test-facebook-token", "page_id": "test-page"}
            }
            
            client = TestClient(app)
            
            response = client.delete("/auth/credentials/tiktok")
            
            # Should return 200 for success
            assert response.status_code == 200
            data = response.json()
            
            # Verify response
            assert data["message"] == "tiktok credentials deleted"
            
            # Verify the secret was updated to remove tiktok
            mock_sm.put_secret.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_delete_credentials_invalid_platform():
    """Test deleting credentials for invalid platform raises ValidationError."""
    app = create_app()
    
    # Mock current user
    mock_current_user = AuthenticatedUser(
        user_id="test-user-123",
        email="test@example.com",
        token_claims={}
    )
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        client = TestClient(app)
        
        response = client.delete("/auth/credentials/invalid-platform")
        
        # Should return 422 for validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data  # FastAPI validation error format
    finally:
        app.dependency_overrides.clear()


def test_credentials_are_user_specific():
    """Test that credentials are stored separately per user."""
    app = create_app()
    
    # Mock current user with specific ID
    mock_current_user = AuthenticatedUser(
        user_id="user123",
        email="user1@example.com",
        token_claims={}
    )
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        with patch('src.shared.secrets.get_secrets') as mock_get_secrets:
            mock_sm = MagicMock()
            mock_get_secrets.return_value = mock_sm
            mock_sm.get_secret_json.return_value = {}
            
            # When updating credentials, check that the correct secret name is used
            client = TestClient(app)
            
            request_data = {
                "tiktok": {
                    "access_token": "user1-token"
                }
            }
            
            response = client.put("/auth/credentials", json=request_data)
            
            # Check that the call was made with the expected secret name
            assert response.status_code == 200
            
            # Verify that the secret name includes the user ID
            call_args = mock_sm.put_secret.call_args
            secret_name = call_args[0][0]  # First positional argument
            assert "user123" in secret_name
    finally:
        app.dependency_overrides.clear()