"""Tests for platform credentials routes."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


def test_update_credentials_success():
    """Test successful platform credentials update."""
    from src.api.main import create_app
    from src.api.dependencies.auth import AuthenticatedUser
    
    app = create_app()
    
    # Mock the current user
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
            mock_secrets_manager = MagicMock()
            mock_get_secrets.return_value = mock_secrets_manager
            mock_secrets_manager.get_secret_json.return_value = {}
            
            client = TestClient(app)
            
            # Request data for updating credentials
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
            
            response = client.put("/credentials/", json=request_data)
            
            # Should return 200 for successful update
            assert response.status_code == 200
            data = response.json()
            
            # Verify response includes configuration status
            assert data["tiktok_configured"] is True
            assert data["shopee_configured"] is True
            assert data["facebook_configured"] is True
            
            # Verify secrets manager was called to update credentials
            mock_secrets_manager.put_secret.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_update_credentials_partial():
    """Test updating credentials for only some platforms."""
    from src.api.main import create_app
    from src.api.dependencies.auth import AuthenticatedUser
    
    app = create_app()
    
    # Mock the current user
    mock_current_user = AuthenticatedUser(
        user_id="test-user-456",
        email="test@example.com",
        token_claims={}
    )
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Mock the secrets client with existing credentials
        with patch('src.shared.secrets.get_secrets') as mock_get_secrets:
            mock_secrets_manager = MagicMock()
            mock_get_secrets.return_value = mock_secrets_manager
            mock_secrets_manager.get_secret_json.return_value = {
                "facebook": {
                    "page_id": "existing-page",
                    "access_token": "existing-facebook-token"
                }
            }
            
            client = TestClient(app)
            
            # Request data for only one platform
            request_data = {
                "tiktok": {
                    "access_token": "new-tiktok-token"
                }
            }
            
            response = client.put("/credentials/", json=request_data)
            
            # Should return 200
            assert response.status_code == 200
            data = response.json()
            
            # Verify response reflects merged credentials
            assert data["tiktok_configured"] is True
            assert data["facebook_configured"] is True
            assert data["shopee_configured"] is False
            
            # Verify secrets manager was called to update credentials
            mock_secrets_manager.put_secret.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_get_credentials_status():
    """Test getting credentials configuration status."""
    from src.api.main import create_app
    from src.api.dependencies.auth import AuthenticatedUser
    
    app = create_app()
    
    # Mock the current user
    mock_current_user = AuthenticatedUser(
        user_id="test-user-789",
        email="test@example.com",
        token_claims={}
    )
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Mock the secrets client with existing credentials
        with patch('src.shared.secrets.get_secrets') as mock_get_secrets:
            mock_secrets_manager = MagicMock()
            mock_get_secrets.return_value = mock_secrets_manager
            mock_secrets_manager.get_secret_json.return_value = {
                "tiktok": {
                    "access_token": "some-redacted-token"
                },
                "facebook": {
                    "page_id": "test-page",
                    "access_token": "some-redacted-token"
                }
            }
            
            client = TestClient(app)
            
            response = client.get("/credentials/")
            
            # Should return 200
            assert response.status_code == 200
            data = response.json()
            
            # Verify response includes only configuration status, not actual credentials
            assert data["tiktok_configured"] is True
            assert data["facebook_configured"] is True
            assert data["shopee_configured"] is False
            
            # Verify that actual credential values are not exposed in response
            assert "tiktok" not in data
            assert "facebook" not in data
            assert "shopee" not in data
    finally:
        app.dependency_overrides.clear()


def test_get_credentials_status_empty():
    """Test getting credentials status when none are configured."""
    from src.api.main import create_app
    from src.api.dependencies.auth import AuthenticatedUser
    
    app = create_app()
    
    # Mock the current user
    mock_current_user = AuthenticatedUser(
        user_id="test-user-empty",
        email="test@example.com",
        token_claims={}
    )
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Mock the secrets client to raise an exception (no credentials exist)
        with patch('src.shared.secrets.get_secrets') as mock_get_secrets:
            mock_secrets_manager = MagicMock()
            mock_get_secrets.return_value = mock_secrets_manager
            from src.shared.exceptions import NotFoundError
            mock_secrets_manager.get_secret_json.side_effect = NotFoundError("Secret", "fake-secret")
            
            client = TestClient(app)
            
            response = client.get("/credentials/")
            
            # Should return 200 with all platforms marked as not configured
            assert response.status_code == 200
            data = response.json()
            
            # Verify all platform configurations are False
            assert data["tiktok_configured"] is False
            assert data["shopee_configured"] is False
            assert data["facebook_configured"] is False
    finally:
        app.dependency_overrides.clear()


def test_delete_credentials_success():
    """Test successful credential deletion."""
    from src.api.main import create_app
    from src.api.dependencies.auth import AuthenticatedUser
    
    app = create_app()
    
    # Mock the current user
    mock_current_user = AuthenticatedUser(
        user_id="test-user-delete",
        email="test@example.com",
        token_claims={}
    )
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Mock the secrets client with existing credentials
        with patch('src.shared.secrets.get_secrets') as mock_get_secrets:
            mock_secrets_manager = MagicMock()
            mock_get_secrets.return_value = mock_secrets_manager
            mock_secrets_manager.get_secret_json.return_value = {
                "tiktok": {
                    "access_token": "tiktok-token"
                },
                "facebook": {
                    "page_id": "facebook-page",
                    "access_token": "facebook-token"
                }
            }
            
            client = TestClient(app)
            
            response = client.delete("/credentials/tiktok")
            
            # Should return 200 with success message
            assert response.status_code == 200
            data = response.json()
            
            # Verify message in response
            assert data["message"] == "tiktok credentials deleted"
            
            # Verify secrets manager was called to update credentials (removing tiktok)
            # put_secret should be called to update with tiktok removed
            mock_secrets_manager.put_secret.assert_called()
    finally:
        app.dependency_overrides.clear()


def test_delete_credentials_invalid_platform():
    """Test deleting credentials for invalid platform returns validation error."""
    from src.api.main import create_app
    from src.api.dependencies.auth import AuthenticatedUser
    
    app = create_app()
    
    # Mock the current user
    mock_current_user = AuthenticatedUser(
        user_id="test-user-invalid",
        email="test@example.com",
        token_claims={}
    )
    
    def override_get_current_user():
        return mock_current_user
    
    try:
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        client = TestClient(app)
        
        response = client.delete("/credentials/invalid-platform")
        
        # Should return 422 for validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data  # FastAPI validation error format
    finally:
        app.dependency_overrides.clear()


def test_credentials_authentication_required():
    """Test that credentials endpoints require authentication."""
    from src.api.main import create_app
    
    app = create_app()
    client = TestClient(app)
    
    # Try to access endpoints without authentication
    response = client.put("/credentials/", json={})
    
    # Should return 401 or 403 for unauthenticated access
    assert response.status_code in [401, 403]
    
    response2 = client.get("/credentials/")
    assert response2.status_code in [401, 403]
    
    response3 = client.delete("/credentials/facebook")
    assert response3.status_code in [401, 403]