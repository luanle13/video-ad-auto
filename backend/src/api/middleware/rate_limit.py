"""Rate limiting middleware."""
import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.shared.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    In-memory rate limiter.

    Note: In production with multiple Lambda instances, use Redis or
    DynamoDB for distributed rate limiting.
    """

    def __init__(self, requests_per_minute: int = 60) -> None:
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute per identifier.
        """
        self.rpm = requests_per_minute
        self._requests: dict[str, int] = defaultdict(int)
        self._current_minute: str = ""

    def _get_minute_key(self) -> str:
        """Get current minute key for bucketing."""
        return datetime.now(timezone.utc).strftime("%Y%m%d%H%M")

    def _cleanup_old_entries(self, current_minute: str) -> None:
        """Clean up entries from previous minutes."""
        if self._current_minute != current_minute:
            self._requests.clear()
            self._current_minute = current_minute

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed for the given identifier.

        Args:
            identifier: Unique identifier (e.g., IP address, user ID).

        Returns:
            True if request is allowed, False if rate limit exceeded.
        """
        current_minute = self._get_minute_key()
        self._cleanup_old_entries(current_minute)

        key = f"{identifier}:{current_minute}"
        count = self._requests[key]

        if count >= self.rpm:
            return False

        self._requests[key] = count + 1
        return True

    def get_remaining(self, identifier: str) -> int:
        """
        Get remaining requests for the identifier.

        Args:
            identifier: Unique identifier.

        Returns:
            Number of remaining requests in current minute.
        """
        current_minute = self._get_minute_key()
        key = f"{identifier}:{current_minute}"
        count = self._requests.get(key, 0)
        return max(0, self.rpm - count)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting to all requests."""

    # Endpoints exempt from rate limiting
    EXEMPT_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}

    # Stricter limits for auth endpoints (prevent brute force)
    AUTH_PATHS = {"/auth/login", "/auth/register"}
    AUTH_RPM = 10  # 10 requests per minute for auth endpoints

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        auth_requests_per_minute: int = 10,
    ) -> None:
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application.
            requests_per_minute: Default RPM for general endpoints.
            auth_requests_per_minute: RPM for authentication endpoints.
        """
        super().__init__(app)
        self.general_limiter = RateLimiter(requests_per_minute)
        self.auth_limiter = RateLimiter(auth_requests_per_minute)

    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for the client.

        Uses a hash of IP + User-Agent for better identification.
        """
        # Get client IP (consider X-Forwarded-For for proxied requests)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        # Add User-Agent for additional differentiation
        user_agent = request.headers.get("User-Agent", "")

        # Create a hash for the identifier
        identifier = f"{client_ip}:{user_agent}"
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]

    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from rate limiting."""
        return path in self.EXEMPT_PATHS

    def _is_auth_path(self, path: str) -> bool:
        """Check if path is an authentication endpoint."""
        return path in self.AUTH_PATHS

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to the request."""
        path = request.url.path

        # Skip exempt paths
        if self._is_exempt(path):
            return await call_next(request)

        identifier = self._get_client_identifier(request)

        # Use stricter limiter for auth endpoints
        if self._is_auth_path(path):
            limiter = self.auth_limiter
            limit_type = "auth"
        else:
            limiter = self.general_limiter
            limit_type = "general"

        if not limiter.is_allowed(identifier):
            logger.warning(
                "rate_limit_exceeded",
                identifier=identifier,
                path=path,
                limit_type=limit_type,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too many requests",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "details": {"retry_after_seconds": 60},
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(limiter.rpm),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # Process the request
        response = await call_next(request)

        # Add rate limit headers to response
        remaining = limiter.get_remaining(identifier)
        response.headers["X-RateLimit-Limit"] = str(limiter.rpm)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


# Singleton rate limiter instances for testing
_general_limiter: RateLimiter | None = None
_auth_limiter: RateLimiter | None = None


def get_rate_limiter(auth: bool = False) -> RateLimiter:
    """Get rate limiter singleton for testing purposes."""
    global _general_limiter, _auth_limiter
    if auth:
        if _auth_limiter is None:
            _auth_limiter = RateLimiter(10)
        return _auth_limiter
    else:
        if _general_limiter is None:
            _general_limiter = RateLimiter(60)
        return _general_limiter


def reset_rate_limiters() -> None:
    """Reset rate limiters (for testing)."""
    global _general_limiter, _auth_limiter
    _general_limiter = None
    _auth_limiter = None
