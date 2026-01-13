"""Tests for security headers middleware."""
import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app


@pytest.fixture
def client():
    """Create a test client for the app."""
    app = create_app()
    return TestClient(app)


def test_security_headers_present(client):
    """Test that security headers are present on responses."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    assert response.headers["Content-Security-Policy"] == "default-src 'self'"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "geolocation=()" in response.headers["Permissions-Policy"]


def test_x_content_type_options_header(client):
    """Test X-Content-Type-Options header prevents MIME sniffing."""
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_x_frame_options_header(client):
    """Test X-Frame-Options header prevents clickjacking."""
    response = client.get("/health")
    assert response.headers["X-Frame-Options"] == "DENY"


def test_x_xss_protection_header(client):
    """Test X-XSS-Protection header enables browser XSS filtering."""
    response = client.get("/health")
    assert response.headers["X-XSS-Protection"] == "1; mode=block"


def test_strict_transport_security_header(client):
    """Test Strict-Transport-Security header enforces HTTPS."""
    response = client.get("/health")
    hsts = response.headers["Strict-Transport-Security"]
    assert "max-age=31536000" in hsts
    assert "includeSubDomains" in hsts


def test_content_security_policy_header(client):
    """Test Content-Security-Policy header restricts resources."""
    response = client.get("/health")
    assert response.headers["Content-Security-Policy"] == "default-src 'self'"


def test_referrer_policy_header(client):
    """Test Referrer-Policy header controls referrer information."""
    response = client.get("/health")
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_permissions_policy_header(client):
    """Test Permissions-Policy header restricts browser features."""
    response = client.get("/health")
    policy = response.headers["Permissions-Policy"]
    assert "geolocation=()" in policy
    assert "microphone=()" in policy
    assert "camera=()" in policy


def test_security_headers_on_error_response(client):
    """Test that security headers are present on error responses."""
    response = client.get("/nonexistent-endpoint")

    # Even on 404 responses, security headers should be present
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"


def test_security_headers_on_post_request(client):
    """Test that security headers are present on POST responses."""
    # Use an endpoint that doesn't require external services
    # Even on a validation error, security headers should be present
    response = client.post(
        "/products",
        json={},  # Invalid payload to trigger validation error
    )

    # Security headers should be present regardless of the response status
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
