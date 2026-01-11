from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest
from src.api.main import app  # Assuming the FastAPI app is in src.api.main


@pytest.fixture
def client():
    """Create test client."""
    with TestClient(app) as c:
        yield c


class TestAuthRoutes:
    
    def test_register_success(self, client):
        """Test successful registration."""
        with patch('src.api.auth.create_user') as mock_create_user, \
             patch('src.api.auth.generate_tokens') as mock_generate_tokens:
            
            mock_create_user.return_value = {
                "user_id": "test-user-id",
                "email": "test@example.com",
                "created_at": "2023-01-01T00:00:00Z"
            }
            mock_generate_tokens.return_value = {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "token_type": "bearer"
            }
            
            response = client.post("/auth/register", json={
                "email": "test@example.com",
                "password": "SecurePass123"
            })
            assert response.status_code == 201
            assert "access_token" in response.json()
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post("/auth/register", json={
            "email": "invalid-email",
            "password": "SecurePass123"
        })
        assert response.status_code == 422  # Validation error
    
    def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = client.post("/auth/register", json={
            "email": "test@example.com"
            # Missing password
        })
        assert response.status_code == 422  # Validation error
    
    def test_login_success(self, client):
        """Test successful login."""
        with patch('src.api.auth.authenticate_user') as mock_authenticate, \
             patch('src.api.auth.generate_tokens') as mock_generate_tokens:
            
            mock_authenticate.return_value = {
                "user_id": "test-user-id",
                "email": "test@example.com",
                "created_at": "2023-01-01T00:00:00Z"
            }
            mock_generate_tokens.return_value = {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "token_type": "bearer"
            }
            
            response = client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "SecurePass123"
            })
            assert response.status_code == 200
            assert "access_token" in response.json()
    
    def test_login_invalid_credentials(self, client):
        """Test login with wrong password."""
        with patch('src.api.auth.authenticate_user') as mock_authenticate:
            mock_authenticate.return_value = None  # Authentication failed
            
            response = client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "wrongpassword"
            })
            assert response.status_code == 401
            assert response.json()["detail"] == "Incorrect email or password"
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        with patch('src.api.auth.authenticate_user') as mock_authenticate:
            mock_authenticate.return_value = None  # User doesn't exist
            
            response = client.post("/auth/login", json={
                "email": "nonexistent@example.com",
                "password": "any-password"
            })
            assert response.status_code == 401
            assert response.json()["detail"] == "Incorrect email or password"
    
    def test_me_authenticated(self, client):
        """Test get current user with valid token."""
        with patch('src.api.auth.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = {
                "user_id": "test-user-id",
                "email": "test@example.com",
                "created_at": "2023-01-01T00:00:00Z"
            }
            
            response = client.get("/auth/me", headers={
                "Authorization": "Bearer valid-token"
            })
            assert response.status_code == 200
            assert response.json()["email"] == "test@example.com"
    
    def test_me_unauthenticated(self, client):
        """Test get current user without token."""
        response = client.get("/auth/me")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
    
    def test_me_invalid_token(self, client):
        """Test get current user with invalid token."""
        with patch('src.api.auth.get_current_user') as mock_get_current_user:
            mock_get_current_user.side_effect = Exception("Invalid token")
            
            response = client.get("/auth/me", headers={
                "Authorization": "Bearer invalid-token"
            })
            assert response.status_code == 401
            assert response.json()["detail"] == "Not authenticated"
    
    def test_refresh_token_success(self, client):
        """Test refreshing access token with valid refresh token."""
        with patch('src.api.auth.refresh_access_token') as mock_refresh:
            mock_refresh.return_value = {
                "access_token": "new-access-token",
                "refresh_token": "new-refresh-token",
                "token_type": "bearer"
            }
            
            response = client.post("/auth/refresh", json={
                "refresh_token": "valid-refresh-token"
            })
            assert response.status_code == 200
            assert "access_token" in response.json()
    
    def test_refresh_token_invalid(self, client):
        """Test refreshing access token with invalid refresh token."""
        with patch('src.api.auth.refresh_access_token') as mock_refresh:
            mock_refresh.return_value = None  # Invalid refresh token
            
            response = client.post("/auth/refresh", json={
                "refresh_token": "invalid-refresh-token"
            })
            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid refresh token"