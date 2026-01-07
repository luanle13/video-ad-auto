"""Authentication models."""
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """User registration request."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """User login request."""
    
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Authentication token response."""
    
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(..., description="Token expiry in seconds")


class RefreshRequest(BaseModel):
    """Token refresh request."""
    
    refresh_token: str


class UserResponse(BaseModel):
    """User profile response."""
    
    user_id: str
    email: str
    created_at: str