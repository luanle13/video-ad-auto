"""Input validation utilities for the AI Video Platform."""
import html
import re
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, Field

# === Constants ===

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/webm"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB

UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
SAFE_FILENAME_PATTERN = r"^[\w\-. ]+\.(jpg|jpeg|png|webp)$"


# === Validation Functions ===


def validate_no_html(value: str) -> str:
    """Strip HTML tags from input to prevent XSS."""
    clean = re.sub(r"<[^>]+>", "", value)
    return clean


def sanitize_html(value: str) -> str:
    """Escape HTML entities to prevent XSS."""
    return html.escape(value)


def validate_file_type(content_type: str, allowed: list[str]) -> bool:
    """Validate file content type against allowed list."""
    return content_type in allowed


def validate_file_size(size: int, max_bytes: int) -> bool:
    """Validate file size is within limit."""
    return 0 < size <= max_bytes


def validate_uuid_format(value: str) -> str:
    """Validate string is a valid UUID format."""
    if not re.match(UUID_PATTERN, value.lower()):
        raise ValueError("Invalid UUID format")
    return value


def validate_safe_filename(value: str) -> str:
    """Validate filename is safe (no path traversal)."""
    # Remove any path components
    filename = value.split("/")[-1].split("\\")[-1]
    # Check against safe pattern
    if not re.match(SAFE_FILENAME_PATTERN, filename, re.IGNORECASE):
        raise ValueError("Invalid filename format")
    return filename


def sanitize_for_prompt(value: str) -> str:
    """
    Sanitize text that will be used in AI prompts.

    Removes potential prompt injection patterns while preserving
    legitimate content.
    """
    # Remove HTML tags
    clean = validate_no_html(value)
    # Limit consecutive special characters
    clean = re.sub(r"[#\-=]{3,}", "", clean)
    # Remove markdown-style headers that could confuse prompts
    clean = re.sub(r"^#+\s+", "", clean, flags=re.MULTILINE)
    return clean.strip()


def validate_no_script_tags(value: str) -> str:
    """Validate input contains no script tags."""
    if re.search(r"<script\b", value, re.IGNORECASE):
        raise ValueError("Script tags not allowed")
    return value


def validate_positive_integer(value: int) -> int:
    """Validate integer is positive."""
    if value <= 0:
        raise ValueError("Value must be positive")
    return value


# === Pydantic Annotated Types ===

# String that has HTML stripped
NoHtmlStr = Annotated[str, AfterValidator(validate_no_html)]

# String with HTML entities escaped
SafeHtmlStr = Annotated[str, AfterValidator(sanitize_html)]

# String validated as UUID format
UUIDStr = Annotated[str, AfterValidator(validate_uuid_format)]

# String safe for use in prompts
PromptSafeStr = Annotated[str, AfterValidator(sanitize_for_prompt)]

# Safe filename
SafeFilename = Annotated[str, AfterValidator(validate_safe_filename)]


# === Field Factories ===


def uuid_field(description: str = "UUID identifier") -> Field:
    """Create a Field for UUID strings with validation."""
    return Field(
        ...,
        pattern=UUID_PATTERN,
        description=description,
    )


def bounded_string_field(
    max_length: int,
    min_length: int = 1,
    description: str | None = None,
) -> Field:
    """Create a Field for bounded-length strings."""
    return Field(
        ...,
        min_length=min_length,
        max_length=max_length,
        description=description,
    )


def optional_bounded_string_field(
    max_length: int,
    min_length: int = 1,
    description: str | None = None,
) -> Field:
    """Create an optional Field for bounded-length strings."""
    return Field(
        None,
        min_length=min_length,
        max_length=max_length,
        description=description,
    )
