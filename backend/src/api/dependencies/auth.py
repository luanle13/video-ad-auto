"""Authentication dependencies."""
import time
from typing import Annotated

import boto3
import jwt
from botocore.exceptions import ClientError
from fastapi import Depends, Header
from jwt import PyJWKClient

from src.shared.config import get_settings
from src.shared.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError,
)
from src.shared.logging import get_logger

logger = get_logger(__name__)


class CognitoAuth:
    """Cognito JWT validator."""
    
    def __init__(self) -> None:
        settings = get_settings()
        self._user_pool_id = settings.cognito_user_pool_id
        self._app_client_id = settings.cognito_client_id
        self._region = settings.cognito_region
        self._issuer = f"https://cognito-idp.{self._region}.amazonaws.com/{self._user_pool_id}"
        self._jwks_url = f"{self._issuer}/.well-known/jwks.json"
        self._jwks_client = PyJWKClient(self._jwks_url, cache_keys=True)
        self._cognito_client = boto3.client("cognito-idp", region_name=self._region)
    
    def validate_token(self, token: str) -> dict:
        """
        Validate a Cognito JWT token.
        
        Returns:
            dict: Decoded token claims
            
        Raises:
            TokenExpiredError: If token is expired
            InvalidTokenError : If token is invalid
        """
        try:
            # Get the signing key
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)

            # Decode and validate
            # Note: Cognito access tokens have 'client_id' not 'aud', so we skip audience validation
            # and manually verify client_id after decoding
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=self._issuer,
                options={"require": ["exp", "iss", "sub", "token_use"]},
            )

            # Verify token_use is "access"
            if claims.get("token_use") != "access":
                raise InvalidTokenError()

            # Verify client_id matches our app (Cognito access tokens use client_id, not aud)
            if claims.get("client_id") != self._app_client_id:
                logger.warning("invalid_client_id", expected=self._app_client_id, got=claims.get("client_id"))
                raise InvalidTokenError()

            return claims
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except jwt.InvalidTokenError as e:
            logger.warning("invalid_token", error=str(e))
            raise InvalidTokenError()
    
    def register_user(self, email: str, password: str) -> str:
        """
        Register a new user in Cognito.

        Returns:
            str: User ID (sub)
        """
        try:
            response = self._cognito_client.sign_up(
                ClientId=self._app_client_id,
                Username=email,
                Password=password,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                ],
            )
            
            # For MVP: auto-confirm user (in prod, require email verification)
            self._cognito_client.admin_confirm_sign_up(
                UserPoolId=self._user_pool_id,
                Username=email,
            )
            
            return response["UserSub"]
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "UsernameExistsException":
                raise AuthenticationError("Email already registered")
            elif error_code == "InvalidPasswordException":
                raise AuthenticationError("Password does not meet requirements")
            raise AuthenticationError(f"Registration failed: {error_code}")
    
    def authenticate(self, email: str, password: str) -> dict:
        """
        Authenticate user and get tokens.
        
        Returns:
            dict with access_token, refresh_token, expires_in
        """
        try:
            response = self._cognito_client.initiate_auth(
                ClientId=self._app_client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": email,
                    "PASSWORD": password,
                },
            )
            
            auth_result = response["AuthenticationResult"]
            return {
                "access_token": auth_result["AccessToken"],
                "refresh_token": auth_result["RefreshToken"],
                "expires_in": auth_result["ExpiresIn"],
            }
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("NotAuthorizedException", "UserNotFoundException"):
                raise AuthenticationError("Invalid email or password")
            raise AuthenticationError(f"Authentication failed: {error_code}")
    
    def refresh_tokens(self, refresh_token: str) -> dict:
        """
        Refresh access token using refresh token.
        
        Returns:
            dict with access_token, expires_in
        """
        try:
            response = self._cognito_client.initiate_auth(
                ClientId=self._app_client_id,
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={
                    "REFRESH_TOKEN": refresh_token,
                },
            )
            
            auth_result = response["AuthenticationResult"]
            return {
                "access_token": auth_result["AccessToken"],
                "expires_in": auth_result["ExpiresIn"],
            }
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NotAuthorizedException":
                raise TokenExpiredError()
            raise AuthenticationError(f"Token refresh failed: {error_code}")


# Singleton
_cognito_auth: CognitoAuth | None = None


def get_cognito_auth() -> CognitoAuth:
    """Get Cognito auth singleton."""
    global _cognito_auth
    if _cognito_auth is None:
        _cognito_auth = CognitoAuth()
    return _cognito_auth


class CurrentUser:
    """Current authenticated user."""
    
    def __init__(self, user_id: str, email: str, token_claims: dict) -> None:
        self.user_id = user_id
        self.email = email
        self.claims = token_claims


async def get_current_user(
    authorization: Annotated[str, Header()],
    auth: CognitoAuth = Depends(get_cognito_auth),
) -> CurrentUser:
    """
    FastAPI dependency to get current authenticated user.
    
    Expects header: Authorization: Bearer <token>
    """
    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header format")
    
    token = authorization[7:]  # Remove "Bearer " prefix
    claims = auth.validate_token(token)
    
    return CurrentUser(
        user_id=claims["sub"],
        email=claims.get("email", claims.get("username", "")),
        token_claims=claims,
    )


# Type alias for dependency injection
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]