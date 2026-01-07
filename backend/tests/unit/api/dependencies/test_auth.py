"""Tests for the authentication dependencies using moto and mock."""
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Header
from jwt import PyJWKClient
from pydantic import ValidationError

from src.api.dependencies.auth import (
    CognitoAuth,
    CurrentUser,
    get_cognito_auth,
    get_current_user,
)
from src.shared.exceptions import AuthenticationError, InvalidTokenError, TokenExpiredError


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch("src.api.dependencies.auth.get_settings") as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.cognito_user_pool_id = "ap-southeast-1_testpool"
        mock_settings.cognito_app_client_id = "test-client-id"
        mock_settings.cognito_region = "ap-southeast-1"
        mock_get_settings.return_value = mock_settings
        yield mock_settings


@pytest.fixture
def cognito_auth(mock_settings):
    """Create a CognitoAuth instance with mocked dependencies."""
    with patch("src.api.dependencies.auth.boto3.client") as mock_cognito_client:
        mock_client = MagicMock()
        mock_cognito_client.return_value = mock_client
        
        auth = CognitoAuth()
        auth._cognito_client = mock_client
        yield auth, mock_client


def test_cognito_auth_initialization(mock_settings):
    """Test CognitoAuth initialization."""
    with patch("src.api.dependencies.auth.boto3.client"):
        auth = CognitoAuth()
        
        assert auth._user_pool_id == "ap-southeast-1_testpool"
        assert auth._app_client_id == "test-client-id"
        assert auth._region == "ap-southeast-1"
        assert "ap-southeast-1_testpool" in auth._issuer
        assert "https://cognito-idp.ap-southeast-1.amazonaws.com/ap-southeast-1_testpool" in auth._issuer


def test_validate_token_success(cognito_auth):
    """Test successful token validation."""
    auth, mock_client = cognito_auth

    # Patch the entire process since get_signing_key_from_jwt is called first
    with patch.object(auth._jwks_client, 'get_signing_key_from_jwt') as mock_get_signing_key:
        mock_signing_key = MagicMock()
        mock_signing_key.key = "test-key"
        mock_get_signing_key.return_value = mock_signing_key

        # Mock jwt.decode to return valid claims
        with patch("src.api.dependencies.auth.jwt.decode") as mock_decode:
            expected_claims = {
                "sub": "test-sub-123",
                "email": "test@example.com",
                "exp": int(time.time()) + 3600,  # 1 hour from now
                "token_use": "access",
                "iss": auth._issuer,
                "aud": auth._app_client_id,
            }
            mock_decode.return_value = expected_claims

            token = "eyJheader.eyJpayload.signature"  # Valid JWT format
            result = auth.validate_token(token)

            assert result == expected_claims
            mock_decode.assert_called_once()
            mock_get_signing_key.assert_called_once_with(token)


def test_validate_token_expired(cognito_auth):
    """Test token validation with expired token."""
    auth, mock_client = cognito_auth

    # Patch the entire process since get_signing_key_from_jwt is called first
    with patch.object(auth._jwks_client, 'get_signing_key_from_jwt') as mock_get_signing_key:
        mock_signing_key = MagicMock()
        mock_signing_key.key = "test-key"
        mock_get_signing_key.return_value = mock_signing_key

        # Mock jwt.decode to raise ExpiredSignatureError
        with patch("src.api.dependencies.auth.jwt.decode") as mock_decode:
            from jwt import ExpiredSignatureError
            mock_decode.side_effect = ExpiredSignatureError()

            token = "eyJheader.eyJpayload.signature"  # Valid JWT format
            with pytest.raises(TokenExpiredError):
                auth.validate_token(token)


def test_validate_token_invalid(cognito_auth):
    """Test token validation with invalid token."""
    auth, mock_client = cognito_auth
    
    # Mock the PyJWKClient
    with patch("src.api.dependencies.auth.PyJWKClient") as mock_jwks_class:
        mock_jwks_instance = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = "test-key"
        mock_jwks_instance.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwks_class.return_value = mock_jwks_instance
        
        # Mock jwt.decode to raise InvalidTokenError
        with patch("src.api.dependencies.auth.jwt.decode") as mock_decode:
            from jwt import InvalidTokenError as JwtInvalidTokenError
            mock_decode.side_effect = JwtInvalidTokenError()
            
            token = "invalid-token"
            
            with pytest.raises(InvalidTokenError):
                auth.validate_token(token)


def test_validate_token_wrong_use(cognito_auth):
    """Test token validation with wrong token_use."""
    auth, mock_client = cognito_auth
    
    # Mock the PyJWKClient
    with patch("src.api.dependencies.auth.PyJWKClient") as mock_jwks_class:
        mock_jwks_instance = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = "test-key"
        mock_jwks_instance.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwks_class.return_value = mock_jwks_instance
        
        # Mock jwt.decode to return claims with wrong token_use
        with patch("src.api.dependencies.auth.jwt.decode") as mock_decode:
            invalid_claims = {
                "sub": "test-sub-123",
                "email": "test@example.com",
                "exp": int(time.time()) + 3600,
                "token_use": "id",  # Wrong token_use
                "iss": auth._issuer,
                "aud": auth._app_client_id,
            }
            mock_decode.return_value = invalid_claims
            
            token = "wrong-use-token"
            
            with pytest.raises(InvalidTokenError):
                auth.validate_token(token)


def test_register_user_success(cognito_auth):
    """Test successful user registration."""
    auth, mock_client = cognito_auth
    
    mock_client.sign_up.return_value = {
        "UserConfirmed": False,
        "UserSub": "test-sub-123",
    }
    mock_client.admin_confirm_sign_up.return_value = {}
    
    email = "test@example.com"
    password = "SecurePassword123!"
    
    result = auth.register_user(email, password)
    
    assert result == "test-sub-123"
    
    mock_client.sign_up.assert_called_once_with(
        ClientId=auth._app_client_id,
        Username=email,
        Password=password,
        UserAttributes=[
            {"Name": "email", "Value": email},
        ],
    )
    
    mock_client.admin_confirm_sign_up.assert_called_once_with(
        UserPoolId=auth._user_pool_id,
        Username=email,
    )


def test_register_user_already_exists(cognito_auth):
    """Test user registration with existing email."""
    auth, mock_client = cognito_auth
    
    # Mock the ClientError for username exists
    from botocore.exceptions import ClientError
    mock_client.sign_up.side_effect = ClientError(
        error_response={
            "Error": {
                "Code": "UsernameExistsException",
                "Message": "User already exists"
            }
        },
        operation_name="SignUp"
    )
    
    with pytest.raises(AuthenticationError, match="Email already registered"):
        auth.register_user("existing@example.com", "password")


def test_register_user_invalid_password(cognito_auth):
    """Test user registration with invalid password."""
    auth, mock_client = cognito_auth
    
    # Mock the ClientError for invalid password
    from botocore.exceptions import ClientError
    mock_client.sign_up.side_effect = ClientError(
        error_response={
            "Error": {
                "Code": "InvalidPasswordException",
                "Message": "Password does not meet requirements"
            }
        },
        operation_name="SignUp"
    )
    
    with pytest.raises(AuthenticationError, match="Password does not meet requirements"):
        auth.register_user("test@example.com", "weak")


def test_authenticate_success(cognito_auth):
    """Test successful authentication."""
    auth, mock_client = cognito_auth
    
    mock_client.initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "test-access-token",
            "RefreshToken": "test-refresh-token",
            "ExpiresIn": 3600,
        }
    }
    
    email = "test@example.com"
    password = "password"
    
    result = auth.authenticate(email, password)
    
    expected = {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "expires_in": 3600,
    }
    
    assert result == expected
    
    mock_client.initiate_auth.assert_called_once_with(
        ClientId=auth._app_client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": email,
            "PASSWORD": password,
        },
    )


def test_authenticate_failure(cognito_auth):
    """Test authentication failure."""
    auth, mock_client = cognito_auth
    
    # Mock the ClientError for authentication failure
    from botocore.exceptions import ClientError
    mock_client.initiate_auth.side_effect = ClientError(
        error_response={
            "Error": {
                "Code": "NotAuthorizedException",
                "Message": "Incorrect username or password"
            }
        },
        operation_name="InitiateAuth"
    )
    
    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        auth.authenticate("test@example.com", "wrong-password")


def test_refresh_tokens_success(cognito_auth):
    """Test successful token refresh."""
    auth, mock_client = cognito_auth
    
    mock_client.initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "new-access-token",
            "ExpiresIn": 3600,
        }
    }
    
    refresh_token = "test-refresh-token"
    
    result = auth.refresh_tokens(refresh_token)
    
    expected = {
        "access_token": "new-access-token",
        "expires_in": 3600,
    }
    
    assert result == expected
    
    mock_client.initiate_auth.assert_called_once_with(
        ClientId=auth._app_client_id,
        AuthFlow="REFRESH_TOKEN_AUTH",
        AuthParameters={
            "REFRESH_TOKEN": refresh_token,
        },
    )


def test_refresh_tokens_failed_authorization(cognito_auth):
    """Test token refresh with failed authorization."""
    auth, mock_client = cognito_auth
    
    # Mock the ClientError for refresh failure
    from botocore.exceptions import ClientError
    mock_client.initiate_auth.side_effect = ClientError(
        error_response={
            "Error": {
                "Code": "NotAuthorizedException",
                "Message": "Refresh token is not valid"
            }
        },
        operation_name="InitiateAuth"
    )
    
    with pytest.raises(TokenExpiredError):
        auth.refresh_tokens("invalid-refresh-token")


@patch("src.api.dependencies.auth.get_cognito_auth")
@pytest.mark.asyncio
async def test_get_current_user_success(mock_get_cognito_auth):
    """Test get_current_user dependency with valid token."""
    # Create a mock auth instance
    mock_auth = MagicMock()
    expected_claims = {
        "sub": "test-sub-123",
        "email": "test@example.com",
        "exp": int(time.time()) + 3600,
        "token_use": "access",
    }
    mock_auth.validate_token.return_value = expected_claims
    mock_get_cognito_auth.return_value = mock_auth
    
    # Simulate Authorization header
    auth_header = "Bearer test-valid-token"
    
    current_user = await get_current_user(authorization=auth_header, auth=mock_auth)
    
    assert isinstance(current_user, CurrentUser)
    assert current_user.user_id == "test-sub-123"
    assert current_user.email == "test@example.com"
    assert current_user.claims == expected_claims
    
    mock_auth.validate_token.assert_called_once_with("test-valid-token")


@patch("src.api.dependencies.auth.get_cognito_auth")
@pytest.mark.asyncio
async def test_get_current_user_invalid_format(mock_get_cognito_auth):
    """Test get_current_user dependency with invalid header format."""
    # Create a mock auth instance
    mock_auth = MagicMock()
    mock_get_cognito_auth.return_value = mock_auth
    
    # Simulate invalid Authorization header
    auth_header = "Basic invalid-format"
    
    with pytest.raises(AuthenticationError, match="Invalid authorization header format"):
        await get_current_user(authorization=auth_header, auth=mock_auth)


@patch("src.api.dependencies.auth.get_cognito_auth")
@pytest.mark.asyncio
async def test_get_current_user_validation_fails(mock_get_cognito_auth):
    """Test get_current_user dependency when token validation fails."""
    # Create a mock auth instance
    mock_auth = MagicMock()
    mock_auth.validate_token.side_effect = TokenExpiredError()
    mock_get_cognito_auth.return_value = mock_auth
    
    # Simulate Authorization header
    auth_header = "Bearer expired-token"
    
    with pytest.raises(TokenExpiredError):
        await get_current_user(authorization=auth_header, auth=mock_auth)


def test_get_cognito_auth_singleton():
    """Test that get_cognito_auth returns a singleton instance."""
    auth1 = get_cognito_auth()
    auth2 = get_cognito_auth()
    
    assert auth1 is auth2