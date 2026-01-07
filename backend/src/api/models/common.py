"""Common response models."""
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str
    code: str
    details: dict[str, Any] = Field(default_factory=dict)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""
    
    items: list[T]
    count: int
    next_token: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = "healthy"
    version: str = "0.1.0"
    timestamp: datetime