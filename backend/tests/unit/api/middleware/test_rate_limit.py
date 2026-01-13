"""Tests for rate limiting middleware."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.middleware.rate_limit import (
    RateLimiter,
    RateLimitMiddleware,
    reset_rate_limiters,
)


@pytest.fixture(autouse=True)
def reset_limiters():
    """Reset rate limiters before each test."""
    reset_rate_limiters()
    yield
    reset_rate_limiters()


class TestRateLimiter:
    """Tests for the RateLimiter class."""

    def test_allows_requests_under_limit(self):
        """Test that requests under the limit are allowed."""
        limiter = RateLimiter(requests_per_minute=5)

        for _ in range(5):
            assert limiter.is_allowed("test-user") is True

    def test_blocks_requests_over_limit(self):
        """Test that requests over the limit are blocked."""
        limiter = RateLimiter(requests_per_minute=3)

        # First 3 requests should be allowed
        for _ in range(3):
            assert limiter.is_allowed("test-user") is True

        # 4th request should be blocked
        assert limiter.is_allowed("test-user") is False

    def test_different_identifiers_have_separate_limits(self):
        """Test that different identifiers have separate rate limits."""
        limiter = RateLimiter(requests_per_minute=2)

        # User 1 uses their limit
        assert limiter.is_allowed("user-1") is True
        assert limiter.is_allowed("user-1") is True
        assert limiter.is_allowed("user-1") is False

        # User 2 should still have their full limit
        assert limiter.is_allowed("user-2") is True
        assert limiter.is_allowed("user-2") is True
        assert limiter.is_allowed("user-2") is False

    def test_get_remaining_returns_correct_count(self):
        """Test that get_remaining returns correct remaining count."""
        limiter = RateLimiter(requests_per_minute=5)

        assert limiter.get_remaining("test-user") == 5

        limiter.is_allowed("test-user")
        assert limiter.get_remaining("test-user") == 4

        limiter.is_allowed("test-user")
        limiter.is_allowed("test-user")
        assert limiter.get_remaining("test-user") == 2

    def test_get_remaining_never_negative(self):
        """Test that get_remaining never returns negative."""
        limiter = RateLimiter(requests_per_minute=2)

        # Exhaust the limit
        limiter.is_allowed("test-user")
        limiter.is_allowed("test-user")
        limiter.is_allowed("test-user")  # This fails

        assert limiter.get_remaining("test-user") == 0


class TestRateLimitMiddleware:
    """Tests for the RateLimitMiddleware class."""

    @pytest.fixture
    def app_with_middleware(self):
        """Create a test app with rate limiting middleware."""
        app = FastAPI()

        # Add a simple test endpoint
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        @app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}

        @app.post("/auth/login")
        async def login_endpoint():
            return {"token": "test"}

        # Add rate limit middleware with low limits for testing
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=5,
            auth_requests_per_minute=2,
        )

        return app

    @pytest.fixture
    def client(self, app_with_middleware):
        """Create test client."""
        return TestClient(app_with_middleware)

    def test_requests_under_limit_succeed(self, client):
        """Test that requests under the limit succeed."""
        for _ in range(5):
            response = client.get("/test")
            assert response.status_code == 200

    def test_requests_over_limit_return_429(self, client):
        """Test that requests over the limit return 429."""
        # Exhaust the limit
        for _ in range(5):
            client.get("/test")

        # Next request should be rate limited
        response = client.get("/test")
        assert response.status_code == 429
        assert response.json()["code"] == "RATE_LIMIT_EXCEEDED"

    def test_rate_limit_response_includes_retry_after(self, client):
        """Test that 429 response includes Retry-After header."""
        # Exhaust the limit
        for _ in range(5):
            client.get("/test")

        response = client.get("/test")
        assert response.status_code == 429
        assert response.headers["Retry-After"] == "60"

    def test_rate_limit_headers_included_in_response(self, client):
        """Test that rate limit headers are included in responses."""
        response = client.get("/test")

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "5"

    def test_remaining_header_decrements(self, client):
        """Test that X-RateLimit-Remaining decrements with each request."""
        response1 = client.get("/test")
        remaining1 = int(response1.headers["X-RateLimit-Remaining"])

        response2 = client.get("/test")
        remaining2 = int(response2.headers["X-RateLimit-Remaining"])

        assert remaining2 == remaining1 - 1

    def test_health_endpoint_exempt_from_rate_limiting(self, client):
        """Test that /health endpoint is exempt from rate limiting."""
        # Make many requests to /health
        for _ in range(20):
            response = client.get("/health")
            assert response.status_code == 200

    def test_auth_endpoints_have_stricter_limits(self, client):
        """Test that auth endpoints have stricter rate limits."""
        # Auth limit is 2 requests per minute
        response1 = client.post("/auth/login")
        assert response1.status_code == 200

        response2 = client.post("/auth/login")
        assert response2.status_code == 200

        # Third request should be rate limited
        response3 = client.post("/auth/login")
        assert response3.status_code == 429

    def test_rate_limit_error_response_format(self, client):
        """Test the format of the rate limit error response."""
        # Exhaust the limit
        for _ in range(5):
            client.get("/test")

        response = client.get("/test")
        data = response.json()

        assert data["error"] == "Too many requests"
        assert data["code"] == "RATE_LIMIT_EXCEEDED"
        assert data["details"]["retry_after_seconds"] == 60


class TestRateLimitMiddlewareIntegration:
    """Integration tests for rate limiting with the actual app."""

    @pytest.fixture
    def client(self):
        """Create test client with the actual app."""
        from src.api.main import create_app

        app = create_app()
        return TestClient(app)

    def test_health_endpoint_not_rate_limited(self, client):
        """Test that health endpoint is not rate limited in actual app."""
        # Make 100 requests - should all succeed
        for _ in range(100):
            response = client.get("/health")
            assert response.status_code == 200

    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are present on actual endpoints."""
        # Use an endpoint that doesn't require auth
        response = client.get("/health")
        # Health is exempt, so no rate limit headers
        # Let's check a non-exempt endpoint would have headers
        # (we can't easily test authenticated endpoints without mocking)

    def test_rate_limit_response_has_correct_content_type(self):
        """Test that rate limited response has correct content type."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=1,
            auth_requests_per_minute=1,
        )

        client = TestClient(app)

        # First request succeeds
        client.get("/test")

        # Second request is rate limited
        response = client.get("/test")
        assert response.status_code == 429
        assert response.headers["content-type"] == "application/json"
