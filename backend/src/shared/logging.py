"""Structured logging configuration."""
import hashlib
import logging
import re
import sys
from typing import Any

import structlog
from structlog.types import Processor

from src.shared.config import get_settings

# === Sensitive Data Patterns ===

# Keys that should have their values masked
SENSITIVE_KEYS = frozenset({
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "authorization",
    "credential",
    "private_key",
    "secret_key",
})

# Keys that contain email addresses (mask but preserve domain)
EMAIL_KEYS = frozenset({"email", "user_email", "email_address"})

# Regex patterns for detecting sensitive data in values
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
JWT_PATTERN = re.compile(r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+")
API_KEY_PATTERN = re.compile(r"(sk|pk|api)[_-]?[a-zA-Z0-9_-]{20,}")
AWS_KEY_PATTERN = re.compile(r"AKIA[0-9A-Z]{16}")

# JSON string patterns for sanitizing serialized log output (defense-in-depth)
# These patterns catch sensitive data in JSON-formatted strings
JSON_SENSITIVE_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Password fields in JSON
    (re.compile(r'"password"\s*:\s*"[^"]*"'), '"password": "***REDACTED***"'),
    (re.compile(r'"pass"\s*:\s*"[^"]*"'), '"pass": "***REDACTED***"'),
    # API keys in JSON
    (re.compile(r'"api_key"\s*:\s*"[^"]*"'), '"api_key": "***REDACTED***"'),
    (re.compile(r'"apikey"\s*:\s*"[^"]*"'), '"apikey": "***REDACTED***"'),
    (re.compile(r'"api-key"\s*:\s*"[^"]*"'), '"api-key": "***REDACTED***"'),
    # Tokens in JSON
    (re.compile(r'"access_token"\s*:\s*"[^"]*"'), '"access_token": "***TOKEN***"'),
    (re.compile(r'"refresh_token"\s*:\s*"[^"]*"'), '"refresh_token": "***TOKEN***"'),
    (re.compile(r'"token"\s*:\s*"[^"]*"'), '"token": "***TOKEN***"'),
    (re.compile(r'"id_token"\s*:\s*"[^"]*"'), '"id_token": "***TOKEN***"'),
    # Authorization headers
    (re.compile(r'"[Aa]uthorization"\s*:\s*"[^"]*"'), '"Authorization": "***REDACTED***"'),
    # Secrets
    (re.compile(r'"secret"\s*:\s*"[^"]*"'), '"secret": "***REDACTED***"'),
    (re.compile(r'"secret_key"\s*:\s*"[^"]*"'), '"secret_key": "***REDACTED***"'),
    (re.compile(r'"private_key"\s*:\s*"[^"]*"'), '"private_key": "***REDACTED***"'),
    # Credentials
    (re.compile(r'"credential"\s*:\s*"[^"]*"'), '"credential": "***REDACTED***"'),
    (re.compile(r'"credentials"\s*:\s*"[^"]*"'), '"credentials": "***REDACTED***"'),
    # Email addresses anywhere in string (catch-all)
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "***@***.***"),
    # JWT tokens anywhere in string
    (re.compile(r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"), "***TOKEN***"),
    # API keys with common prefixes
    (re.compile(r"(sk|pk|api)[_-][a-zA-Z0-9_-]{20,}"), "***APIKEY***"),
    # AWS access keys
    (re.compile(r"AKIA[0-9A-Z]{16}"), "***AWSKEY***"),
]


# === Masking Functions ===


def sanitize_log_string(data: str) -> str:
    """
    Remove sensitive data from serialized log strings.

    This provides defense-in-depth by sanitizing the final JSON output
    in case any sensitive data slipped through earlier sanitization.

    Args:
        data: Serialized log string (typically JSON).

    Returns:
        Sanitized string with sensitive patterns replaced.
    """
    result = data
    for pattern, replacement in JSON_SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def mask_email(email: str) -> str:
    """
    Mask email address while preserving domain for debugging.

    Example: user@example.com -> u***@example.com
    """
    if not email or "@" not in email:
        return "***@***.***"

    local, domain = email.rsplit("@", 1)
    if len(local) <= 1:
        masked_local = "*"
    else:
        masked_local = local[0] + "***"

    return f"{masked_local}@{domain}"


def mask_token(value: str) -> str:
    """Mask tokens completely."""
    return "***TOKEN***"


def mask_secret(value: str) -> str:
    """Mask secrets completely."""
    return "***REDACTED***"


def hash_email(email: str) -> str:
    """
    Hash email address for correlation without exposing PII.

    Returns first 8 characters of SHA256 hash.
    """
    if not email:
        return "no-email"
    return hashlib.sha256(email.lower().encode()).hexdigest()[:8]


def sanitize_value(key: str, value: Any) -> Any:
    """
    Sanitize a single value based on its key name.

    Args:
        key: The field name (lowercase).
        value: The value to potentially sanitize.

    Returns:
        Sanitized value or original if no sanitization needed.
    """
    if value is None:
        return value

    key_lower = key.lower()

    # Check if key indicates sensitive data
    if any(sensitive in key_lower for sensitive in SENSITIVE_KEYS):
        return mask_secret(str(value))

    # Check if key indicates email
    if key_lower in EMAIL_KEYS or "email" in key_lower:
        return mask_email(str(value))

    # For string values, check for embedded sensitive patterns
    if isinstance(value, str):
        # Mask JWT tokens
        if JWT_PATTERN.search(value):
            return JWT_PATTERN.sub("***TOKEN***", value)

        # Mask API keys
        if API_KEY_PATTERN.search(value):
            return API_KEY_PATTERN.sub("***APIKEY***", value)

        # Mask AWS keys
        if AWS_KEY_PATTERN.search(value):
            return AWS_KEY_PATTERN.sub("***AWSKEY***", value)

    return value


def sanitize_log_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize a log data dictionary, masking sensitive fields.

    Args:
        data: Dictionary of log data.

    Returns:
        New dictionary with sensitive data masked.
    """
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_log_data(item) if isinstance(item, dict) else sanitize_value(key, item)
                for item in value
            ]
        else:
            sanitized[key] = sanitize_value(key, value)
    return sanitized


def sanitize_processor(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Structlog processor to sanitize sensitive data from logs."""
    return sanitize_log_data(event_dict)


def add_environment(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add environment to all log entries."""
    settings = get_settings()
    event_dict["environment"] = settings.environment
    return event_dict


class SanitizingJSONRenderer:
    """
    JSON renderer that applies string-level sanitization after serialization.

    This provides defense-in-depth by catching any sensitive data that might
    have slipped through the dictionary-level sanitization.
    """

    def __init__(self, **json_kw: Any) -> None:
        """Initialize with optional JSON encoder kwargs."""
        self._json_renderer = structlog.processors.JSONRenderer(**json_kw)

    def __call__(
        self,
        logger: logging.Logger,
        method_name: str,
        event_dict: dict[str, Any],
    ) -> str:
        """Render event dict to JSON and apply string sanitization."""
        # First, render to JSON using structlog's JSONRenderer
        json_output = self._json_renderer(logger, method_name, event_dict)
        # Then apply string-level sanitization as defense-in-depth
        return sanitize_log_string(json_output)


def configure_logging() -> None:
    """Configure structlog for the application."""
    settings = get_settings()
    
    # Determine processors based on environment
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        add_environment,
        sanitize_processor,  # Sanitize sensitive data before output
    ]
    
    if settings.environment == "prod":
        # JSON for CloudWatch with sanitization
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            SanitizingJSONRenderer(),  # Custom renderer with string-level sanitization
        ]
    else:
        # Pretty print for local development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.debug else logging.INFO,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a logger instance."""
    return structlog.get_logger(name)