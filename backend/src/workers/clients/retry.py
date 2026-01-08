"""Retry configuration for external API clients."""
from pydantic import BaseModel, Field


class RetryConfig(BaseModel):
    """Configuration for retry logic with exponential backoff.

    Attributes:
        max_retries: Maximum number of retry attempts
        base_delay_seconds: Initial delay between retries in seconds
        max_delay_seconds: Maximum delay between retries in seconds (cap)
        exponential_base: Base for exponential backoff calculation
        retryable_status_codes: HTTP status codes that trigger a retry

    Example:
        >>> config = RetryConfig()
        >>> config.calculate_delay(1)  # First retry
        1.0
        >>> config.calculate_delay(2)  # Second retry
        2.0
        >>> config.calculate_delay(3)  # Third retry
        4.0
    """

    max_retries: int = Field(default=3, ge=0, description="Maximum number of retry attempts")
    base_delay_seconds: float = Field(default=1.0, gt=0, description="Initial delay between retries")
    max_delay_seconds: float = Field(default=30.0, gt=0, description="Maximum delay cap")
    exponential_base: float = Field(default=2.0, gt=1.0, description="Exponential backoff base")
    retryable_status_codes: list[int] = Field(
        default=[429, 500, 502, 503, 504],
        description="HTTP status codes that trigger retry",
    )

    def calculate_delay(self, attempt: int) -> float:
        """Calculate retry delay using exponential backoff.

        Formula: delay = min(base_delay * (exponential_base ^ attempt), max_delay)

        Args:
            attempt: Current attempt number (1-indexed)

        Returns:
            Delay in seconds, capped at max_delay_seconds

        Example:
            >>> config = RetryConfig(base_delay_seconds=1.0, exponential_base=2.0)
            >>> config.calculate_delay(1)
            1.0
            >>> config.calculate_delay(2)
            2.0
            >>> config.calculate_delay(3)
            4.0
            >>> config.calculate_delay(10)  # Capped at max_delay_seconds
            30.0
        """
        if attempt < 1:
            return 0.0

        # Calculate exponential backoff: base_delay * (exponential_base ^ attempt)
        delay = self.base_delay_seconds * (self.exponential_base ** attempt)

        # Cap at max_delay_seconds
        return min(delay, self.max_delay_seconds)
