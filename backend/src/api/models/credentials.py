"""Platform credentials models."""
from pydantic import BaseModel, Field


class TikTokCredentials(BaseModel):
    """TikTok API credentials."""
    
    access_token: str = Field(..., min_length=1)
    # Add other fields as needed by TikTok API


class ShopeeCredentials(BaseModel):
    """Shopee Vietnam credentials."""
    
    shop_id: str
    access_token: str = Field(..., min_length=1)
    # Add other fields as needed


class FacebookCredentials(BaseModel):
    """Facebook/Meta credentials."""
    
    page_id: str
    access_token: str = Field(..., min_length=1)


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