"""Base HTTP client for external API integrations."""
from abc import ABC, abstractmethod
from typing import Any

import httpx

from src.shared.exceptions import ExternalServiceError
from src.shared.logging import get_logger
from src.workers.clients.retry import RetryConfig

logger = get_logger(__name__)


class BaseAPIClient(ABC):
    """Abstract base class for external API clients.

    Provides common HTTP client functionality with:
    - Async httpx client management
    - Automatic retry configuration
    - Context manager support
    - Structured logging
    - Exception wrapping

    Subclasses must implement:
    - service_name: Class attribute for service identification
    - base_url: Class attribute for API base URL
    - default_timeout: Class attribute for default timeout
    - headers: Property returning request headers
    - _wrap_exception: Method to wrap exceptions as ExternalServiceError

    Example:
        >>> class MyAPIClient(BaseAPIClient):
        ...     service_name = "MyAPI"
        ...     base_url = "https://api.example.com"
        ...     default_timeout = 30.0
        ...
        ...     @property
        ...     def headers(self) -> dict[str, str]:
        ...         return {"Authorization": f"Bearer {self._api_key}"}
        ...
        ...     def _wrap_exception(self, exc: Exception) -> ExternalServiceError:
        ...         return ExternalServiceError("MyAPI", str(exc))
        ...
        >>> async with MyAPIClient(api_key="secret") as client:
        ...     # Use client
        ...     pass
    """

    # Class attributes - must be overridden by subclasses
    service_name: str
    base_url: str
    default_timeout: float

    def __init__(
        self,
        api_key: str,
        timeout: float | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialize API client.

        Args:
            api_key: API key for authentication
            timeout: Request timeout in seconds (uses default_timeout if None)
            retry_config: Retry configuration (uses default if None)
        """
        self._api_key = api_key
        self._timeout = timeout if timeout is not None else self.default_timeout
        self._retry_config = retry_config or RetryConfig()
        self._client: httpx.AsyncClient | None = None

        logger.info(
            "api_client_initialized",
            service=self.service_name,
            timeout=self._timeout,
            max_retries=self._retry_config.max_retries,
        )

    @property
    @abstractmethod
    def headers(self) -> dict[str, str]:
        """Return HTTP headers for requests.

        Must include authentication headers and any required service headers.

        Returns:
            Dictionary of HTTP headers
        """
        pass

    @abstractmethod
    def _wrap_exception(self, exc: Exception) -> ExternalServiceError:
        """Wrap exception as service-specific error.

        Args:
            exc: Original exception

        Returns:
            ExternalServiceError with service context
        """
        pass

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx AsyncClient.

        Creates a new client if one doesn't exist. The client is configured with:
        - Base URL from class attribute
        - Headers from headers property
        - Timeout from constructor
        - Follow redirects enabled

        Returns:
            Configured httpx.AsyncClient instance
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=self._timeout,
                follow_redirects=True,
            )
            logger.debug(
                "httpx_client_created",
                service=self.service_name,
                base_url=self.base_url,
            )

        return self._client

    async def close(self) -> None:
        """Close the HTTP client and release resources.

        Safe to call multiple times. Does nothing if client is already closed.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.debug("httpx_client_closed", service=self.service_name)

    async def __aenter__(self) -> "BaseAPIClient":
        """Enter async context manager.

        Returns:
            Self for use in async with statement
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager and close client.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        await self.close()
