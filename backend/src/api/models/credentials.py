"""Platform credentials models."""
from pydantic import BaseModel, Field


class TikTokCredentials(BaseModel):
    """TikTok API credentials."""

    access_token: str = Field(..., min_length=1, max_length=2048)


class ShopeeCredentials(BaseModel):
    """Shopee Vietnam credentials."""

    shop_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^\d+$",
        description="Numeric shop ID",
    )
    access_token: str = Field(..., min_length=1, max_length=2048)


class FacebookCredentials(BaseModel):
    """Facebook/Meta credentials."""

    page_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^\d+$",
        description="Numeric page ID",
    )
    access_token: str = Field(..., min_length=1, max_length=2048)


class PlatformCredentialsRequest(BaseModel):
    """Update platform credentials request."""
    
    tiktok: TikTokCredentials | None = None
    shopee: ShopeeCredentials | None = None
    facebook: FacebookCredentials | None = None


class PlatformCredentialsResponse(BaseModel):
    """Platform credentials response (masked)."""
    
    tiktok_configured: bool = False
    shopee_configured: bool = False
    facebook_configured: bool = False