"""Tests for the custom exception hierarchy."""
from src.shared.exceptions import (
    AIVideoPlatformError,
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    InvalidTokenError,
    NotFoundError,
    ConflictError,
    ValidationError,
    FileTooLargeError,
    InvalidFileTypeError,
    ExternalServiceError,
    AnthropicError,
    KlingError,
    ElevenLabsError,
    JobError,
    JobTimeoutError,
    AgentError,
)


def test_exception_inheritance():
    """Test that all exceptions inherit from AIVideoPlatformError."""
    # Base exception
    assert issubclass(AIVideoPlatformError, Exception)
    
    # Authentication & Authorization
    assert issubclass(AuthenticationError, AIVideoPlatformError)
    assert issubclass(AuthorizationError, AIVideoPlatformError)
    assert issubclass(TokenExpiredError, AuthenticationError)
    assert issubclass(InvalidTokenError, AuthenticationError)
    
    # Resource errors
    assert issubclass(NotFoundError, AIVideoPlatformError)
    assert issubclass(ConflictError, AIVideoPlatformError)
    
    # Validation errors
    assert issubclass(ValidationError, AIVideoPlatformError)
    assert issubclass(FileTooLargeError, ValidationError)
    assert issubclass(InvalidFileTypeError, ValidationError)
    
    # External service errors
    assert issubclass(ExternalServiceError, AIVideoPlatformError)
    assert issubclass(AnthropicError, ExternalServiceError)
    assert issubclass(KlingError, ExternalServiceError)
    assert issubclass(ElevenLabsError, ExternalServiceError)
    
    # Job/processing errors
    assert issubclass(JobError, AIVideoPlatformError)
    assert issubclass(JobTimeoutError, JobError)
    assert issubclass(AgentError, AIVideoPlatformError)


def test_base_exception_attributes():
    """Test that the base exception has the correct attributes."""
    exception = AIVideoPlatformError("Test message", code="TEST_CODE", details={"test": "value"})
    
    assert exception.message == "Test message"
    assert exception.code == "TEST_CODE"
    assert exception.details == {"test": "value"}
    
    # Test default values
    exception_default = AIVideoPlatformError("Test message")
    assert exception_default.code == "INTERNAL_ERROR"
    assert exception_default.details == {}


def test_code_and_details_attributes():
    """Test that each exception has appropriate code and details."""
    # Authentication & Authorization
    auth_error = AuthenticationError()
    assert auth_error.code == "AUTHENTICATION_ERROR"
    
    authz_error = AuthorizationError()
    assert authz_error.code == "AUTHORIZATION_ERROR"
    
    token_expired = TokenExpiredError()
    assert token_expired.code == "TOKEN_EXPIRED"
    
    invalid_token = InvalidTokenError()
    assert invalid_token.code == "INVALID_TOKEN"
    
    # Resource errors
    not_found = NotFoundError("user", "123")
    assert not_found.code == "NOT_FOUND"
    assert not_found.details == {"resource": "user", "id": "123"}
    
    conflict = ConflictError("Resource already exists")
    assert conflict.code == "CONFLICT"
    
    # Validation errors
    validation_error = ValidationError("Invalid input", field="email")
    assert validation_error.code == "VALIDATION_ERROR"
    assert validation_error.details == {"field": "email"}
    
    file_too_large = FileTooLargeError(5)
    assert file_too_large.code == "FILE_TOO_LARGE"
    
    invalid_file_type = InvalidFileTypeError(["jpg", "png"])
    assert invalid_file_type.code == "INVALID_FILE_TYPE"
    
    # External service errors
    external_error = ExternalServiceError("TestService", "Test error")
    assert external_error.code == "EXTERNAL_SERVICE_ERROR"
    assert external_error.details == {"service": "TestService"}
    
    anthropic_error = AnthropicError("API error")
    assert anthropic_error.details == {"service": "Anthropic"}
    
    kling_error = KlingError("API error")
    assert kling_error.details == {"service": "Kling"}
    
    elevenlabs_error = ElevenLabsError("API error")
    assert elevenlabs_error.details == {"service": "ElevenLabs"}
    
    # Job/processing errors
    job_error = JobError("job123", "Processing failed")
    assert job_error.code == "JOB_ERROR"
    assert job_error.details == {"job_id": "job123"}
    
    job_timeout = JobTimeoutError("job123", 300)
    assert job_timeout.code == "JOB_TIMEOUT"
    
    agent_error = AgentError("ResearchAgent", "Failed to process")
    assert agent_error.code == "AGENT_ERROR"
    assert agent_error.details == {"agent": "ResearchAgent"}


def test_string_representation():
    """Test string representation of exceptions."""
    # Base exception
    base_error = AIVideoPlatformError("Test message")
    assert "Test message" in str(base_error)
    
    # Authentication errors
    auth_error = AuthenticationError()
    assert "Authentication failed" in str(auth_error)
    
    auth_error_custom = AuthenticationError("Custom auth error")
    assert "Custom auth error" in str(auth_error_custom)
    
    # Resource errors
    not_found = NotFoundError("user", "123")
    assert "user not found: 123" in str(not_found)
    
    # Validation errors
    validation = ValidationError("Invalid input", field="email")
    assert "Invalid input" in str(validation)
    
    file_large = FileTooLargeError(5)
    assert "File exceeds maximum size of 5MB" in str(file_large)
    
    # External service errors
    external = ExternalServiceError("TestService", "Test error")
    assert "TestService error: Test error" in str(external)
    
    # Job errors
    job_error = JobError("job123", "Processing failed")
    assert "Processing failed" in str(job_error)
    
    # Agent errors
    agent_error = AgentError("ResearchAgent", "Failed to process")
    assert "Agent 'ResearchAgent' failed: Failed to process" in str(agent_error)