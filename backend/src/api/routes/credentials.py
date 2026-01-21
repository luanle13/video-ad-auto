"""Platform credentials routes."""
from fastapi import APIRouter, Depends
from src.api.dependencies.auth import AuthenticatedUser
from src.api.models.credentials import (
    PlatformCredentialsRequest,
    PlatformCredentialsResponse,
)
from src.api.models.common import ErrorResponse
from src.shared.exceptions import ValidationError
from src.shared.logging import get_logger
from src.shared.secrets import get_secrets, get_user_credentials_secret_name

router = APIRouter()
logger = get_logger(__name__)


@router.put("", response_model=PlatformCredentialsResponse)
async def update_credentials(
    request: PlatformCredentialsRequest,
    current_user: AuthenticatedUser,
) -> PlatformCredentialsResponse:
    """
    Update platform credentials.
    
    Credentials are stored securely in AWS Secrets Manager.
    """
    secrets = get_secrets()
    secret_name = get_user_credentials_secret_name(current_user.user_id)
    
    # Get existing credentials
    try:
        existing = secrets.get_secret_json(secret_name)
    except Exception:
        # If secret doesn't exist, start with empty dict
        existing = {}
    
    # Merge with new credentials
    updated = existing.copy()
    
    if request.tiktok:
        updated["tiktok"] = request.tiktok.model_dump()
    if request.shopee:
        updated["shopee"] = request.shopee.model_dump()
    if request.facebook:
        updated["facebook"] = request.facebook.model_dump()
    
    # Store updated credentials
    secrets.put_secret(secret_name, updated)
    
    logger.info(
        "credentials_updated",
        user_id=current_user.user_id,
        platforms=list(updated.keys()),
    )
    
    return PlatformCredentialsResponse(
        tiktok_configured="tiktok" in updated,
        shopee_configured="shopee" in updated,
        facebook_configured="facebook" in updated,
    )


@router.get("", response_model=PlatformCredentialsResponse)
async def get_credentials_status(
    current_user: AuthenticatedUser,
) -> PlatformCredentialsResponse:
    """
    Get platform credentials configuration status.
    
    Returns which platforms have credentials configured (not the actual credentials).
    """
    secrets = get_secrets()
    secret_name = get_user_credentials_secret_name(current_user.user_id)
    
    try:
        existing = secrets.get_secret_json(secret_name)
    except Exception:
        # If secret doesn't exist, return empty status
        existing = {}

    return PlatformCredentialsResponse(
        tiktok_configured="tiktok" in existing,
        shopee_configured="shopee" in existing,
        facebook_configured="facebook" in existing,
    )


@router.delete("/{platform}")
async def delete_credentials(
    platform: str,
    current_user: AuthenticatedUser,
) -> dict[str, str]:
    """
    Delete credentials for a specific platform.
    """
    if platform not in ("tiktok", "shopee", "facebook"):
        raise ValidationError(f"Invalid platform: {platform}", field="platform")
    
    secrets = get_secrets()
    secret_name = get_user_credentials_secret_name(current_user.user_id)
    
    try:
        existing = secrets.get_secret_json(secret_name)
        if platform in existing:
            del existing[platform]
            secrets.put_secret(secret_name, existing)
    except Exception:
        # If credentials don't exist or platform not found, continue silently
        pass
    
    logger.info("credentials_deleted", user_id=current_user.user_id, platform=platform)
    
    return {"message": f"{platform} credentials deleted"}