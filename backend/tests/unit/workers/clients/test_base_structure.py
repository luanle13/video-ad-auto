"""Tests for BaseAPIClient structure and functionality."""
import pytest

from src.shared.exceptions import ExternalServiceError
from src.workers.clients.base import BaseAPIClient
from src.workers.clients.retry import RetryConfig


# Test implementation of BaseAPIClient
class TestAPIClient(BaseAPIClient):
    """Concrete implementation for testing."""

    service_name = "TestAPI"
    base_url = "https://api.test.com"
    default_timeout = 30.0

    @property
    def headers(self) -> dict[str, str]:
        """Return test headers with API key."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _wrap_exception(self, exc: Exception) -> ExternalServiceError:
        """Wrap exception as ExternalServiceError."""
        return ExternalServiceError("TestAPI", str(exc))


class TestBaseAPIClientInitialization:
    """Tests for BaseAPIClient initialization."""

    def test_init_with_api_key_only(self) -> None:
        """Test initialization with only API key."""
        client = TestAPIClient(api_key="test-key-123")

        assert client._api_key == "test-key-123"
        assert client._timeout == 30.0  # default_timeout
        assert client._retry_config.max_retries == 3  # default RetryConfig
        assert client._client is None

    def test_init_with_custom_timeout(self) -> None:
        """Test initialization with custom timeout."""
        client = TestAPIClient(api_key="test-key", timeout=60.0)

        assert client._timeout == 60.0

    def test_init_with_custom_retry_config(self) -> None:
        """Test initialization with custom retry config."""
        retry_config = RetryConfig(max_retries=5, base_delay_seconds=2.0)
        client = TestAPIClient(api_key="test-key", retry_config=retry_config)

        assert client._retry_config.max_retries == 5
        assert client._retry_config.base_delay_seconds == 2.0

    def test_init_with_all_parameters(self) -> None:
        """Test initialization with all parameters."""
        retry_config = RetryConfig(max_retries=10)
        client = TestAPIClient(
            api_key="test-key-abc",
            timeout=45.0,
            retry_config=retry_config,
        )

        assert client._api_key == "test-key-abc"
        assert client._timeout == 45.0
        assert client._retry_config.max_retries == 10

    def test_class_attributes_set(self) -> None:
        """Test that class attributes are properly set."""
        client = TestAPIClient(api_key="test-key")

        assert client.service_name == "TestAPI"
        assert client.base_url == "https://api.test.com"
        assert client.default_timeout == 30.0

    def test_client_initially_none(self) -> None:
        """Test that httpx client is not created on init."""
        client = TestAPIClient(api_key="test-key")

        assert client._client is None


class TestBaseAPIClientHeaders:
    """Tests for headers property."""

    def test_headers_includes_api_key(self) -> None:
        """Test that headers include API key."""
        client = TestAPIClient(api_key="secret-key-456")

        headers = client.headers

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer secret-key-456"

    def test_headers_includes_content_type(self) -> None:
        """Test that headers include content type."""
        client = TestAPIClient(api_key="test-key")

        headers = client.headers

        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"

    def test_headers_is_dict(self) -> None:
        """Test that headers returns a dictionary."""
        client = TestAPIClient(api_key="test-key")

        headers = client.headers

        assert isinstance(headers, dict)
        assert all(isinstance(k, str) for k in headers.keys())
        assert all(isinstance(v, str) for v in headers.values())


class TestGetClient:
    """Tests for _get_client method."""

    @pytest.mark.asyncio
    async def test_get_client_creates_client(self) -> None:
        """Test that _get_client creates httpx client."""
        client = TestAPIClient(api_key="test-key")

        httpx_client = await client._get_client()

        assert httpx_client is not None
        assert client._client is not None
        assert client._client is httpx_client

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    async def test_get_client_returns_same_instance(self) -> None:
        """Test that _get_client returns same instance on multiple calls."""
        client = TestAPIClient(api_key="test-key")

        httpx_client1 = await client._get_client()
        httpx_client2 = await client._get_client()

        assert httpx_client1 is httpx_client2

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    async def test_get_client_configures_base_url(self) -> None:
        """Test that client is configured with base URL."""
        client = TestAPIClient(api_key="test-key")

        httpx_client = await client._get_client()

        # httpx normalizes base_url without trailing slash
        assert str(httpx_client.base_url) == "https://api.test.com"

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    async def test_get_client_configures_timeout(self) -> None:
        """Test that client is configured with timeout."""
        client = TestAPIClient(api_key="test-key", timeout=45.0)

        httpx_client = await client._get_client()

        assert httpx_client.timeout.read == 45.0

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    async def test_get_client_configures_headers(self) -> None:
        """Test that client is configured with headers."""
        client = TestAPIClient(api_key="secret-123")

        httpx_client = await client._get_client()

        assert "Authorization" in httpx_client.headers
        assert httpx_client.headers["Authorization"] == "Bearer secret-123"

        # Cleanup
        await client.close()

    @pytest.mark.asyncio
    async def test_get_client_follows_redirects(self) -> None:
        """Test that client is configured to follow redirects."""
        client = TestAPIClient(api_key="test-key")

        httpx_client = await client._get_client()

        assert httpx_client.follow_redirects is True

        # Cleanup
        await client.close()


class TestClose:
    """Tests for close method."""

    @pytest.mark.asyncio
    async def test_close_without_client(self) -> None:
        """Test that close works when no client exists."""
        client = TestAPIClient(api_key="test-key")

        # Should not raise
        await client.close()

        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_with_client(self) -> None:
        """Test that close closes the httpx client."""
        client = TestAPIClient(api_key="test-key")

        # Create client
        await client._get_client()
        assert client._client is not None

        # Close it
        await client.close()

        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_multiple_times(self) -> None:
        """Test that close can be called multiple times safely."""
        client = TestAPIClient(api_key="test-key")

        await client._get_client()

        # Close multiple times - should not raise
        await client.close()
        await client.close()
        await client.close()

        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_after_close(self) -> None:
        """Test that client can be recreated after close."""
        client = TestAPIClient(api_key="test-key")

        # Create and close
        httpx_client1 = await client._get_client()
        await client.close()

        # Create again
        httpx_client2 = await client._get_client()

        assert httpx_client2 is not None
        assert httpx_client2 is not httpx_client1  # New instance

        # Cleanup
        await client.close()


class TestContextManager:
    """Tests for async context manager functionality."""

    @pytest.mark.asyncio
    async def test_context_manager_enter(self) -> None:
        """Test that __aenter__ returns self."""
        client = TestAPIClient(api_key="test-key")

        async with client as entered_client:
            assert entered_client is client

    @pytest.mark.asyncio
    async def test_context_manager_exit_closes_client(self) -> None:
        """Test that __aexit__ closes the client."""
        client = TestAPIClient(api_key="test-key")

        async with client:
            # Create client inside context
            await client._get_client()
            assert client._client is not None

        # After context, client should be closed
        assert client._client is None

    @pytest.mark.asyncio
    async def test_context_manager_without_creating_client(self) -> None:
        """Test context manager when client is never created."""
        client = TestAPIClient(api_key="test-key")

        # Should not raise even if client was never created
        async with client:
            pass

        assert client._client is None

    @pytest.mark.asyncio
    async def test_context_manager_with_exception(self) -> None:
        """Test that client is closed even when exception occurs."""
        client = TestAPIClient(api_key="test-key")

        with pytest.raises(ValueError):
            async with client:
                await client._get_client()
                assert client._client is not None
                raise ValueError("Test error")

        # Client should still be closed
        assert client._client is None

    @pytest.mark.asyncio
    async def test_context_manager_typical_usage(self) -> None:
        """Test typical context manager usage pattern."""
        async with TestAPIClient(api_key="test-key") as client:
            # Client is available
            assert client._api_key == "test-key"

            # Can get httpx client
            httpx_client = await client._get_client()
            assert httpx_client is not None

        # After context, client is closed
        assert client._client is None


class TestWrapException:
    """Tests for _wrap_exception method."""

    def test_wrap_exception_returns_external_service_error(self) -> None:
        """Test that _wrap_exception returns ExternalServiceError."""
        client = TestAPIClient(api_key="test-key")

        original_error = ValueError("Something went wrong")
        wrapped = client._wrap_exception(original_error)

        assert isinstance(wrapped, ExternalServiceError)

    def test_wrap_exception_includes_message(self) -> None:
        """Test that wrapped exception includes original message."""
        client = TestAPIClient(api_key="test-key")

        original_error = RuntimeError("Connection failed")
        wrapped = client._wrap_exception(original_error)

        assert "Connection failed" in str(wrapped)

    def test_wrap_exception_with_different_errors(self) -> None:
        """Test wrapping different exception types."""
        client = TestAPIClient(api_key="test-key")

        errors = [
            ValueError("Invalid value"),
            RuntimeError("Runtime error"),
            ConnectionError("Connection lost"),
        ]

        for error in errors:
            wrapped = client._wrap_exception(error)
            assert isinstance(wrapped, ExternalServiceError)
            assert str(error) in str(wrapped)


class TestAbstractMethods:
    """Tests for abstract method enforcement."""

    def test_cannot_instantiate_base_class(self) -> None:
        """Test that BaseAPIClient cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            BaseAPIClient(api_key="test-key")  # type: ignore

        assert "abstract" in str(exc_info.value).lower()

    def test_must_implement_headers(self) -> None:
        """Test that subclass must implement headers property."""

        class IncompleteClient(BaseAPIClient):
            service_name = "Incomplete"
            base_url = "https://api.incomplete.com"
            default_timeout = 30.0

            def _wrap_exception(self, exc: Exception) -> ExternalServiceError:
                return ExternalServiceError("Incomplete", str(exc))

        with pytest.raises(TypeError) as exc_info:
            IncompleteClient(api_key="test-key")  # type: ignore

        assert "abstract" in str(exc_info.value).lower()

    def test_must_implement_wrap_exception(self) -> None:
        """Test that subclass must implement _wrap_exception method."""

        class IncompleteClient(BaseAPIClient):
            service_name = "Incomplete"
            base_url = "https://api.incomplete.com"
            default_timeout = 30.0

            @property
            def headers(self) -> dict[str, str]:
                return {}

        with pytest.raises(TypeError) as exc_info:
            IncompleteClient(api_key="test-key")  # type: ignore

        assert "abstract" in str(exc_info.value).lower()


class TestMultipleClients:
    """Tests for using multiple client instances."""

    @pytest.mark.asyncio
    async def test_multiple_clients_independent(self) -> None:
        """Test that multiple client instances are independent."""
        client1 = TestAPIClient(api_key="key-1")
        client2 = TestAPIClient(api_key="key-2")

        httpx_client1 = await client1._get_client()
        httpx_client2 = await client2._get_client()

        assert httpx_client1 is not httpx_client2
        assert client1.headers["Authorization"] != client2.headers["Authorization"]

        # Cleanup
        await client1.close()
        await client2.close()

    @pytest.mark.asyncio
    async def test_closing_one_client_does_not_affect_other(self) -> None:
        """Test that closing one client doesn't affect others."""
        client1 = TestAPIClient(api_key="key-1")
        client2 = TestAPIClient(api_key="key-2")

        await client1._get_client()
        await client2._get_client()

        # Close first client
        await client1.close()

        assert client1._client is None
        assert client2._client is not None

        # Cleanup
        await client2.close()
