"""Authentication routes."""
from fastapi import APIRouter, Depends

from src.api.dependencies.auth import (
    AuthenticatedUser,
    CognitoAuth,
    get_cognito_auth,
)
from src.api.models import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from src.shared.db import get_db
from src.shared.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    auth: CognitoAuth = Depends(get_cognito_auth),
) -> TokenResponse:
    """
    Register a new user.
    
    Creates user in Cognito and DynamoDB, then returns tokens.
    """
    db = get_db()
    
    # Register in Cognito
    user_id = auth.register_user(request.email, request.password)
    
    # Create user record in DynamoDB
    db.create_user(user_id=user_id, email=request.email)
    
    # Log user in to get tokens
    tokens = auth.authenticate(request.email, request.password)
    
    logger.info("user_registered", user_id=user_id, email=request.email)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="Bearer",
        expires_in=tokens["expires_in"],
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    auth: CognitoAuth = Depends(get_cognito_auth),
) -> TokenResponse:
    """
    Login with email and password.
    
    Returns access and refresh tokens.
    """
    tokens = auth.authenticate(request.email, request.password)
    
    logger.info("user_logged_in", email=request.email)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="Bearer",
        expires_in=tokens["expires_in"],
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    auth: CognitoAuth = Depends(get_cognito_auth),
) -> TokenResponse:
    """
    Refresh access token using refresh token.
    """
    tokens = auth.refresh_tokens(request.refresh_token)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=request.refresh_token,  # Refresh token doesn't change
        token_type="Bearer",
        expires_in=tokens["expires_in"],
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: AuthenticatedUser,
) -> UserResponse:
    """
    Get current user profile.
    
    Requires authentication.
    """
    db = get_db()
    user = db.get_user(current_user.user_id)
    
    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        created_at=user["created_at"],
    )