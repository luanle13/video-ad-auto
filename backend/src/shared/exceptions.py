"""Custom exceptions for the AI Video Platform."""
from typing import Any


class AIVideoPlatformError(Exception):
    """Base exception for all application errors."""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


# === Authentication & Authorization ===

class AuthenticationError(AIVideoPlatformError):
    """Authentication failed."""
    
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, code="AUTHENTICATION_ERROR")


class AuthorizationError(AIVideoPlatformError):
    """User not authorized for this action."""
    
    def __init__(self, message: str = "Not authorized") -> None:
        super().__init__(message, code="AUTHORIZATION_ERROR")


class TokenExpiredError(AuthenticationError):
    """JWT token has expired."""
    
    def __init__(self) -> None:
        super().__init__("Token has expired")
        self.code = "TOKEN_EXPIRED"


class InvalidTokenError(AuthenticationError):
    """JWT token is invalid."""
    
    def __init__(self) -> None:
        super().__init__("Invalid token")
        self.code = "INVALID_TOKEN"


# === Resource Errors ===

class NotFoundError(AIVideoPlatformError):
    """Resource not found."""
    
    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(
            f"{resource} not found: {resource_id}",
            code="NOT_FOUND",
            details={"resource": resource, "id": resource_id},
        )


class ConflictError(AIVideoPlatformError):
    """Resource conflict (e.g., duplicate)."""
    
    def __init__(self, message: str) -> None:
        super().__init__(message, code="CONFLICT")


# === Validation Errors ===

class ValidationError(AIVideoPlatformError):
    """Input validation failed."""
    
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            details={"field": field} if field else {},
        )


class FileTooLargeError(ValidationError):
    """Uploaded file exceeds size limit."""
    
    def __init__(self, max_size_mb: int) -> None:
        super().__init__(
            f"File exceeds maximum size of {max_size_mb}MB",
            field="file",
        )
        self.code = "FILE_TOO_LARGE"


class InvalidFileTypeError(ValidationError):
    """Uploaded file type not allowed."""
    
    def __init__(self, allowed_types: list[str]) -> None:
        super().__init__(
            f"File type not allowed. Allowed: {', '.join(allowed_types)}",
            field="file",
        )
        self.code = "INVALID_FILE_TYPE"


# === External Service Errors ===

class ExternalServiceError(AIVideoPlatformError):
    """External API call failed."""
    
    def __init__(self, service: str, message: str) -> None:
        super().__init__(
            f"{service} error: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service},
        )


class AnthropicError(ExternalServiceError):
    """Claude API error."""
    
    def __init__(self, message: str) -> None:
        super().__init__("Anthropic", message)


class KlingError(ExternalServiceError):
    """Kling AI error."""
    
    def __init__(self, message: str) -> None:
        super().__init__("Kling", message)


class ElevenLabsError(ExternalServiceError):
    """ElevenLabs API error."""

    def __init__(self, message: str) -> None:
        super().__init__("ElevenLabs", message)


class PollyError(ExternalServiceError):
    """AWS Polly error."""

    def __init__(self, message: str) -> None:
        super().__init__("Polly", message)


# === Job/Processing Errors ===

class JobError(AIVideoPlatformError):
    """Job processing error."""
    
    def __init__(self, job_id: str, message: str) -> None:
        super().__init__(
            message,
            code="JOB_ERROR",
            details={"job_id": job_id},
        )


class JobTimeoutError(JobError):
    """Job exceeded timeout."""
    
    def __init__(self, job_id: str, timeout_seconds: int) -> None:
        super().__init__(job_id, f"Job timed out after {timeout_seconds}s")
        self.code = "JOB_TIMEOUT"


class AgentError(AIVideoPlatformError):
    """CrewAI agent error."""
    
    def __init__(self, agent_name: str, message: str) -> None:
        super().__init__(
            f"Agent '{agent_name}' failed: {message}",
            code="AGENT_ERROR",
            details={"agent": agent_name},
        )