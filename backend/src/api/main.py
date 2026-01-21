"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from src.api.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from src.api.models import ErrorResponse, HealthResponse
from src.api.routes import auth, credentials, jobs, products
from src.shared.config import get_settings
from src.shared.exceptions import (
    AIVideoPlatformError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from src.shared.logging import configure_logging, get_logger

# Configure logging on module load
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("application_starting")
    yield
    logger.info("application_shutting_down")


def _get_cors_origins(settings) -> list[str]:
    """Get allowed CORS origins based on environment."""
    # In development, allow all origins for easier testing
    if settings.environment == "dev":
        return ["*"]

    # Production origins from environment
    prod_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    if settings.frontend_url:
        prod_origins.append(settings.frontend_url)

    return prod_origins


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="AI Video Platform API",
        description="API for AI-powered video generation from product images",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        redirect_slashes=False,  # Don't redirect /jobs to /jobs/ (breaks with API Gateway)
    )

    # CORS middleware configuration
    cors_origins = _get_cors_origins(settings)
    # Note: allow_credentials cannot be True when origins is ["*"]
    allow_credentials = "*" not in cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
        max_age=600,  # Cache preflight requests for 10 minutes
    )

    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # Rate limiting middleware
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=60,
        auth_requests_per_minute=10,
    )

    # Exception handlers
    @app.exception_handler(AIVideoPlatformError)
    async def handle_app_error(
        request: Request, exc: AIVideoPlatformError
    ) -> JSONResponse:
        """Handle application errors."""
        status_code = _get_status_code(exc)
        logger.warning(
            "application_error",
            error_code=exc.code,
            message=exc.message,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(
                error=exc.message,
                code=exc.code,
                details=exc.details,
            ).model_dump(),
        )
    
    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected errors."""
        logger.exception(
            "unexpected_error",
            error=str(exc),
            path=request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
            ).model_dump(),
        )
    
    # Health check
    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            timestamp=datetime.now(timezone.utc),
        )
    
    # Include routers
    app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    app.include_router(products.router, prefix="/products", tags=["Products"])
    app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
    app.include_router(credentials.router, prefix="/credentials", tags=["Credentials"])
    
    return app


def _get_status_code(exc: AIVideoPlatformError) -> int:
    """Map exception to HTTP status code."""
    if isinstance(exc, NotFoundError):
        return 404
    if isinstance(exc, AuthenticationError):
        return 401
    if isinstance(exc, AuthorizationError):
        return 403
    if isinstance(exc, ValidationError):
        return 422
    return 400  # Default for other app errors


# Create app instance
app = create_app()

# Lambda handler
handler = Mangum(app, lifespan="off")