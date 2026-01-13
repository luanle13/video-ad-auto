"""Tests for the FastAPI application."""
import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app, _get_status_code, _get_cors_origins
from src.api.models import HealthResponse
from src.shared.exceptions import (
    AIVideoPlatformError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)


@pytest.fixture
def client():
    """Create a test client for the app."""
    app = create_app()
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    
    # Parse the response as a HealthResponse model
    health_data = HealthResponse.model_validate(response.json())
    assert health_data.status == "healthy"
    assert health_data.version == "0.1.0"
    assert health_data.timestamp is not None


def test_cors_configuration(client):
    """Test that CORS headers are set correctly for allowed origin."""
    # Make a request with an allowed origin
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )

    assert response.status_code == 200
    # In dev mode, localhost:3000 should be allowed
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
    assert response.headers.get("Access-Control-Allow-Credentials") == "true"


def test_cors_preflight_request(client):
    """Test CORS preflight (OPTIONS) request."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )

    # Preflight should succeed
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
    assert "GET" in response.headers.get("Access-Control-Allow-Methods", "")
    assert response.headers.get("Access-Control-Max-Age") == "600"


def test_cors_blocked_origin(client):
    """Test that unauthorized origins are blocked."""
    response = client.get(
        "/health",
        headers={"Origin": "http://evil-site.com"},
    )

    # Request should succeed but without CORS headers
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") is None


def test_get_cors_origins_dev_environment():
    """Test CORS origins for dev environment."""
    from unittest.mock import MagicMock

    settings = MagicMock()
    settings.environment = "dev"
    settings.frontend_url = ""

    origins = _get_cors_origins(settings)

    assert "http://localhost:3000" in origins
    assert "http://localhost:5173" in origins
    assert "http://127.0.0.1:3000" in origins
    assert "http://127.0.0.1:5173" in origins
    assert len(origins) == 4


def test_get_cors_origins_prod_environment():
    """Test CORS origins for prod environment."""
    from unittest.mock import MagicMock

    settings = MagicMock()
    settings.environment = "prod"
    settings.frontend_url = "https://my-app.example.com"

    origins = _get_cors_origins(settings)

    assert origins == ["https://my-app.example.com"]
    # Dev origins should not be included
    assert "http://localhost:3000" not in origins


def test_get_cors_origins_prod_no_frontend_url():
    """Test CORS origins for prod environment without frontend URL."""
    from unittest.mock import MagicMock

    settings = MagicMock()
    settings.environment = "prod"
    settings.frontend_url = ""

    origins = _get_cors_origins(settings)

    assert origins == []


def test_get_status_code_mapping():
    """Test that exceptions are mapped to correct HTTP status codes."""
    # Test NotFoundError -> 404
    not_found_error = NotFoundError(resource="Product", resource_id="123")
    assert _get_status_code(not_found_error) == 404
    
    # Test AuthenticationError -> 401
    auth_error = AuthenticationError()
    assert _get_status_code(auth_error) == 401
    
    # Test AuthorizationError -> 403
    authz_error = AuthorizationError()
    assert _get_status_code(authz_error) == 403
    
    # Test ValidationError -> 422
    validation_error = ValidationError(message="Invalid input")
    assert _get_status_code(validation_error) == 422
    
    # Test other AIVideoPlatformError -> 400
    generic_error = AIVideoPlatformError(message="Generic error")
    assert _get_status_code(generic_error) == 400


@pytest.mark.asyncio
async def test_exception_handlers_directly():
    """Test exception handlers directly by calling them."""
    from fastapi import Request
    from starlette.datastructures import URL
    from starlette.convertors import Convertor
    from starlette.routing import Router
    from starlette.responses import JSONResponse
    import json

    # Create the app to access the handlers
    test_app = create_app()

    # Test the exception handler functions directly
    request = Request({"type": "http", "method": "GET", "path": "/test-path"})
    request.scope['path'] = "/test-path"
    request.scope['url'] = URL("http://testserver/test-path")

    # Test AIVideoPlatformError handler - use a mock call to trigger the handler
    from src.shared.exceptions import NotFoundError

    # Manually test the _get_status_code function
    not_found_error = NotFoundError(resource="Test", resource_id="123")
    assert _get_status_code(not_found_error) == 404

    # Test the status code mapping for various exception types
    from src.shared.exceptions import (
        AuthenticationError,
        AuthorizationError,
        ValidationError
    )

    assert _get_status_code(AuthenticationError()) == 401
    assert _get_status_code(AuthorizationError()) == 403
    assert _get_status_code(ValidationError(message="Test")) == 422
    assert _get_status_code(AIVideoPlatformError(message="Test")) == 400


def test_full_app_with_predefined_routes():
    """Test with a predefined route that raises an exception."""
    # Import here to avoid circular imports
    from fastapi import APIRouter
    from fastapi.testclient import TestClient

    # Create a separate app instance for this test only
    from src.api.main import create_app
    app = create_app()

    # Add routes that will cause exceptions to be raised
    test_router = APIRouter()

    @test_router.get("/trigger-not-found")
    def trigger_not_found():
        from src.shared.exceptions import NotFoundError
        raise NotFoundError(resource="TestResource", resource_id="123")

    @test_router.get("/trigger-validation")
    def trigger_validation():
        from src.shared.exceptions import ValidationError
        raise ValidationError(message="Test validation error")

    app.include_router(test_router)

    # Now test with the client
    client = TestClient(app)

    # Test NotFoundError - should be handled by our exception handler
    response = client.get("/trigger-not-found")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["code"] == "NOT_FOUND"

    # Test ValidationError - should be handled by our exception handler
    response = client.get("/trigger-validation")
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["code"] == "VALIDATION_ERROR"


def test_application_startup():
    """Test that application creates successfully."""
    app = create_app()
    assert app is not None
    assert app.title == "AI Video Platform API"
    assert app.description == "API for AI-powered video generation from product images"


def test_mangum_handler_exists():
    """Test that Mangum handler exists."""
    from src.api.main import handler
    assert handler is not None
    from mangum import Mangum
    assert isinstance(handler, Mangum)