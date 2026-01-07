"""API models."""
from src.api.models.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from src.api.models.common import ErrorResponse, HealthResponse, PaginatedResponse
from src.api.models.credentials import (
    FacebookCredentials,
    PlatformCredentialsRequest,
    PlatformCredentialsResponse,
    ShopeeCredentials,
    TikTokCredentials,
)
from src.api.models.jobs import (
    CreateJobRequest,
    JobAdjustments,
    JobListResponse,
    JobResponse,
    JobStatus,
    RegenerateJobRequest,
)
from src.api.models.products import (
    CreateProductRequest,
    ImageUploadRequest,
    ImageUploadResponse,
    ProductResponse,
    UpdateProductRequest,
)

__all__ = [
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "RefreshRequest",
    "TokenResponse",
    "UserResponse",
    # Common
    "ErrorResponse",
    "HealthResponse",
    "PaginatedResponse",
    # Products
    "CreateProductRequest",
    "UpdateProductRequest",
    "ProductResponse",
    "ImageUploadRequest",
    "ImageUploadResponse",
    # Jobs
    "CreateJobRequest",
    "RegenerateJobRequest",
    "JobResponse",
    "JobListResponse",
    "JobStatus",
    "JobAdjustments",
    # Credentials
    "PlatformCredentialsRequest",
    "PlatformCredentialsResponse",
    "TikTokCredentials",
    "ShopeeCredentials",
    "FacebookCredentials",
]