"""Tests for BaseAPIClient retry logic."""
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.shared.exceptions import ExternalServiceError
from src.workers.clients.base import BaseAPIClient
from src.workers.clients.retry import RetryConfig


# Test implementation
class TestAPIClient(BaseAPIClient):
    """Concrete implementation for testing."""

    service_name = "TestAPI"
    base_url = "https://api.test.com"
    default_timeout = 30.0

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    def _wrap_exception(self, exc: Exception) -> ExternalServiceError:
        return ExternalServiceError("TestAPI", str(exc))


class TestRequestWithRetrySuccess:
    """Tests for successful requests without retries."""

    @pytest.mark.asyncio
    async def test_successful_get_request(self) -> None:
        """Test successful GET request on first attempt."""
        client = TestAPIClient(api_key="test-key")

        # Mock successful response
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_httpx_client

            response = await client.get("/test")

            assert response.status_code == 200
            mock_httpx_client.request.assert_called_once_with("GET", "/test")

    @pytest.mark.asyncio
    async def test_successful_post_request(self) -> None:
        """Test successful POST request on first attempt."""
        client = TestAPIClient(api_key="test-key")

        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "123"}

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_httpx_client

            response = await client.post("/create", json={"name": "test"})

            assert response.status_code == 201
            mock_httpx_client.request.assert_called_once_with(
                "POST", "/create", json={"name": "test"}
            )

    @pytest.mark.asyncio
    async def test_successful_request_with_kwargs(self) -> None:
        """Test that kwargs are passed through to httpx."""
        client = TestAPIClient(api_key="test-key")

        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_httpx_client

            await client.get(
                "/test",
                params={"q": "search"},
                headers={"X-Custom": "value"},
            )

            mock_httpx_client.request.assert_called_once_with(
                "GET",
                "/test",
                params={"q": "search"},
                headers={"X-Custom": "value"},
            )


class TestRetryOn503:
    """Tests for retry logic on 503 Service Unavailable."""

    @pytest.mark.asyncio
    async def test_retry_on_503_then_success(self) -> None:
        """Test retry on 503, then succeed on second attempt."""
        retry_config = RetryConfig(max_retries=2, base_delay_seconds=0.01)
        client = TestAPIClient(api_key="test-key", retry_config=retry_config)

        # First call returns 503, second returns 200
        mock_response_503 = Mock(spec=httpx.Response)
        mock_response_503.status_code = 503

        mock_response_200 = Mock(spec=httpx.Response)
        mock_response_200.status_code = 200

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(
                side_effect=[mock_response_503, mock_response_200]
            )
            mock_get_client.return_value = mock_httpx_client

            response = await client.get("/test")

            assert response.status_code == 200
            assert mock_httpx_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_503_max_retries_exceeded(self) -> None:
        """Test that 503 failures exceed max retries and raise."""
        retry_config = RetryConfig(max_retries=2, base_delay_seconds=0.01)
        client = TestAPIClient(api_key="test-key", retry_config=retry_config)

        # All attempts return 503
        mock_response_503 = Mock(spec=httpx.Response)
        mock_response_503.status_code = 503
        mock_response_503.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "Service Unavailable", request=Mock(), response=mock_response_503
            )
        )

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(return_value=mock_response_503)
            mock_get_client.return_value = mock_httpx_client

            with pytest.raises(ExternalServiceError):
                await client.get("/test")

            # Should try: initial + 2 retries = 3 times
            assert mock_httpx_client.request.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_on_500_then_success(self) -> None:
        """Test retry on 500 Internal Server Error."""
        retry_config = RetryConfig(max_retries=2, base_delay_seconds=0.01)
        client = TestAPIClient(api_key="test-key", retry_config=retry_config)

        mock_response_500 = Mock(spec=httpx.Response)
        mock_response_500.status_code = 500

        mock_response_200 = Mock(spec=httpx.Response)
        mock_response_200.status_code = 200

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(
                side_effect=[mock_response_500, mock_response_200]
            )
            mock_get_client.return_value = mock_httpx_client

            response = await client.get("/test")

            assert response.status_code == 200
            assert mock_httpx_client.request.call_count == 2


class TestRetryOnTimeout:
    """Tests for retry logic on timeout exceptions."""

    @pytest.mark.asyncio
    async def test_retry_on_timeout_then_success(self) -> None:
        """Test retry after timeout, then succeed."""
        retry_config = RetryConfig(max_retries=2, base_delay_seconds=0.01)
        client = TestAPIClient(api_key="test-key", retry_config=retry_config)

        mock_response_200 = Mock(spec=httpx.Response)
        mock_response_200.status_code = 200

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(
                side_effect=[
                    httpx.TimeoutException("Request timeout"),
                    mock_response_200,
                ]
            )
            mock_get_client.return_value = mock_httpx_client

            response = await client.get("/test")

            assert response.status_code == 200
            assert mock_httpx_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_timeout_max_retries_exceeded(self) -> None:
        """Test that timeout failures exceed max retries and raise."""
        retry_config = RetryConfig(max_retries=2, base_delay_seconds=0.01)
        client = TestAPIClient(api_key="test-key", retry_config=retry_config)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )
            mock_get_client.return_value = mock_httpx_client

            with pytest.raises(ExternalServiceError) as exc_info:
                await client.get("/test")

            assert "Request timeout" in str(exc_info.value)
            # Should try: initial + 2 retries = 3 times
            assert mock_httpx_client.request.call_count == 3


class TestRetryOnNetworkError:
    """Tests for retry logic on network errors."""

    @pytest.mark.asyncio
    async def test_retry_on_network_error_then_success(self) -> None:
        """Test retry after network error, then succeed."""
        retry_config = RetryConfig(max_retries=2, base_delay_seconds=0.01)
        client = TestAPIClient(api_key="test-key", retry_config=retry_config)

        mock_response_200 = Mock(spec=httpx.Response)
        mock_response_200.status_code = 200

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(
                side_effect=[
                    httpx.NetworkError("Network unreachable"),
                    mock_response_200,
                ]
            )
            mock_get_client.return_value = mock_httpx_client

            response = await client.get("/test")

            assert response.status_code == 200
            assert mock_httpx_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_connect_error(self) -> None:
        """Test retry after connection error."""
        retry_config = RetryConfig(max_retries=2, base_delay_seconds=0.01)
        client = TestAPIClient(api_key="test-key", retry_config=retry_config)

        mock_response_200 = Mock(spec=httpx.Response)
        mock_response_200.status_code = 200

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(
                side_effect=[
                    httpx.ConnectError("Connection refused"),
                    mock_response_200,
                ]
            )
            mock_get_client.return_value = mock_httpx_client

            response = await client.get("/test")

            assert response.status_code == 200


class TestNonRetryableErrors:
    """Tests for errors that should not be retried."""

    @pytest.mark.asyncio
    async def test_404_not_retried(self) -> None:
        """Test that 404 Not Found is not retried."""
        retry_config = RetryConfig(
            max_retries=2,
            base_delay_seconds=0.01,
            retryable_status_codes=[500, 503],  # 404 not in list
        )
        client = TestAPIClient(api_key="test-key", retry_config=retry_config)

        mock_response_404 = Mock(spec=httpx.Response)
        mock_response_404.status_code = 404

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Not Found",
                    request=Mock(),
                    response=mock_response_404,
                )
            )
            mock_get_client.return_value = mock_httpx_client

            with pytest.raises(ExternalServiceError):
                await client.get("/test")

            # Should only try once - no retries for 404
            assert mock_httpx_client.request.call_count == 1

    @pytest.mark.asyncio
    async def test_400_not_retried(self) -> None:
        """Test that 400 Bad Request is not retried."""
        retry_config = RetryConfig(max_retries=2, base_delay_seconds=0.01)
        client = TestAPIClient(api_key="test-key", retry_config=retry_config)

        mock_response_400 = Mock(spec=httpx.Response)
        mock_response_400.status_code = 400

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Bad Request",
                    request=Mock(),
                    response=mock_response_400,
                )
            )
            mock_get_client.return_value = mock_httpx_client

            with pytest.raises(ExternalServiceError):
                await client.get("/test")

            # Should only try once
            assert mock_httpx_client.request.call_count == 1


class TestRetryBackoff:
    """Tests for exponential backoff between retries."""

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self) -> None:
        """Test that retry delays follow exponential backoff."""
        retry_config = RetryConfig(
            max_retries=3,
            base_delay_seconds=0.1,
            exponential_base=2.0,
        )
        client = TestAPIClient(api_key="test-key", retry_config=retry_config)

        mock_response_200 = Mock(spec=httpx.Response)
        mock_response_200.status_code = 200

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(
                side_effect=[
                    httpx.TimeoutException("timeout"),
                    httpx.TimeoutException("timeout"),
                    httpx.TimeoutException("timeout"),
                    mock_response_200,
                ]
            )
            mock_get_client.return_value = mock_httpx_client

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                response = await client.get("/test")

                assert response.status_code == 200

                # Check sleep was called with exponential delays
                # attempt 1: 0.1 * 2^1 = 0.2
                # attempt 2: 0.1 * 2^2 = 0.4
                # attempt 3: 0.1 * 2^3 = 0.8
                assert mock_sleep.call_count == 3
                calls = [call.args[0] for call in mock_sleep.call_args_list]
                assert calls == [0.2, 0.4, 0.8]


class TestZeroRetries:
    """Tests for client with no retries configured."""

    @pytest.mark.asyncio
    async def test_zero_retries_on_timeout(self) -> None:
        """Test that zero retries means no retry attempts."""
        retry_config = RetryConfig(max_retries=0)
        client = TestAPIClient(api_key="test-key", retry_config=retry_config)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(
                side_effect=httpx.TimeoutException("timeout")
            )
            mock_get_client.return_value = mock_httpx_client

            with pytest.raises(ExternalServiceError):
                await client.get("/test")

            # Should only try once - no retries
            assert mock_httpx_client.request.call_count == 1

    @pytest.mark.asyncio
    async def test_zero_retries_on_503(self) -> None:
        """Test zero retries on 503."""
        retry_config = RetryConfig(max_retries=0)
        client = TestAPIClient(api_key="test-key", retry_config=retry_config)

        mock_response_503 = Mock(spec=httpx.Response)
        mock_response_503.status_code = 503
        mock_response_503.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "Service Unavailable",
                request=Mock(),
                response=mock_response_503,
            )
        )

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(return_value=mock_response_503)
            mock_get_client.return_value = mock_httpx_client

            with pytest.raises(ExternalServiceError):
                await client.get("/test")

            # Should only try once
            assert mock_httpx_client.request.call_count == 1


class TestMixedFailures:
    """Tests for mixed failure scenarios."""

    @pytest.mark.asyncio
    async def test_timeout_then_503_then_success(self) -> None:
        """Test retry through different failure types."""
        retry_config = RetryConfig(max_retries=3, base_delay_seconds=0.01)
        client = TestAPIClient(api_key="test-key", retry_config=retry_config)

        mock_response_503 = Mock(spec=httpx.Response)
        mock_response_503.status_code = 503

        mock_response_200 = Mock(spec=httpx.Response)
        mock_response_200.status_code = 200

        with patch.object(client, "_get_client") as mock_get_client:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(
                side_effect=[
                    httpx.TimeoutException("timeout"),
                    mock_response_503,
                    mock_response_200,
                ]
            )
            mock_get_client.return_value = mock_httpx_client

            response = await client.get("/test")

            assert response.status_code == 200
            assert mock_httpx_client.request.call_count == 3


class TestConvenienceMethods:
    """Tests for get() and post() convenience methods."""

    @pytest.mark.asyncio
    async def test_get_method_calls_request_with_retry(self) -> None:
        """Test that get() calls _request_with_retry with GET."""
        client = TestAPIClient(api_key="test-key")

        with patch.object(
            client, "_request_with_retry", new_callable=AsyncMock
        ) as mock_retry:
            mock_response = Mock(spec=httpx.Response)
            mock_retry.return_value = mock_response

            result = await client.get("/test", params={"q": "search"})

            mock_retry.assert_called_once_with("GET", "/test", params={"q": "search"})
            assert result is mock_response

    @pytest.mark.asyncio
    async def test_post_method_calls_request_with_retry(self) -> None:
        """Test that post() calls _request_with_retry with POST."""
        client = TestAPIClient(api_key="test-key")

        with patch.object(
            client, "_request_with_retry", new_callable=AsyncMock
        ) as mock_retry:
            mock_response = Mock(spec=httpx.Response)
            mock_retry.return_value = mock_response

            result = await client.post("/create", json={"name": "test"})

            mock_retry.assert_called_once_with(
                "POST", "/create", json={"name": "test"}
            )
            assert result is mock_response
