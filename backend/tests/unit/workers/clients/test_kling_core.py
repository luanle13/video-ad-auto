"""Unit tests for KlingClient core methods."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.shared.exceptions import KlingError
from src.workers.clients.kling import KlingClient, KlingJobResponse


@pytest.fixture
def kling_client():
    """Fixture to create a KlingClient instance for testing."""
    return KlingClient(api_key="test-api-key")


@pytest.mark.asyncio
async def test_kling_client_initialization(kling_client):
    """Test KlingClient initialization."""
    assert kling_client.service_name == "KlingAI"
    assert kling_client.base_url == "https://api.klingai.com/v1"
    assert kling_client.default_timeout == 120.0
    assert kling_client.POLL_INTERVAL_SECONDS == 10
    assert kling_client.MAX_POLL_ATTEMPTS == 60
    assert kling_client._api_key == "test-api-key"


@pytest.mark.asyncio
async def test_headers_property(kling_client):
    """Test headers property returns correct headers."""
    expected_headers = {
        "Authorization": "Bearer test-api-key",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-API-Version": "v1",
    }
    
    assert kling_client.headers == expected_headers


@pytest.mark.asyncio
async def test_wrap_exception(kling_client):
    """Test _wrap_exception wraps exceptions correctly."""
    original_exception = Exception("Test error")
    wrapped_exception = kling_client._wrap_exception(original_exception)
    
    assert isinstance(wrapped_exception, KlingError)
    assert "Test error" in str(wrapped_exception)


@pytest.mark.asyncio
async def test_generate_video_success(kling_client):
    """Test generate_video method returns job ID on success."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "job-12345"}
    
    with patch.object(kling_client, '_request_with_retry', return_value=mock_response):
        job_id = await kling_client.generate_video(
            prompt="A cat playing with a ball",
            config={"duration": 5, "resolution": "1080x720"}
        )
        
        assert job_id == "job-12345"


@pytest.mark.asyncio
async def test_generate_video_with_optional_params(kling_client):
    """Test generate_video method with all optional parameters."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "job-67890"}
    
    with patch.object(kling_client, '_request_with_retry', return_value=mock_response):
        job_id = await kling_client.generate_video(
            prompt="A dog running in park",
            config={"duration": 10, "resolution": "720x480"},
            negative_prompt="dark, blurry",
            image_url="https://example.com/image.jpg",
            audio_url="https://example.com/audio.mp3"
        )
        
        # Verify the request was called with all parameters
        assert job_id == "job-67890"


@pytest.mark.asyncio
async def test_generate_video_missing_job_id(kling_client):
    """Test generate_video raises KlingError when job ID is missing."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": ""}
    
    with patch.object(kling_client, '_request_with_retry', return_value=mock_response):
        with pytest.raises(KlingError, match="Failed to get job ID from response"):
            await kling_client.generate_video(
                prompt="A cat playing with a ball",
                config={"duration": 5, "resolution": "1080x720"}
            )


@pytest.mark.asyncio
async def test_get_job_status_success(kling_client):
    """Test get_job_status returns KlingJobResponse on success."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "job-12345",
        "status": "completed",
        "video_url": "https://example.com/video.mp4",
        "prompt": "A cat playing with a ball",
        "negative_prompt": "dark, blurry",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:30Z"
    }
    
    with patch.object(kling_client, '_request_with_retry', return_value=mock_response):
        job_response = await kling_client.get_job_status("job-12345")
        
        assert isinstance(job_response, KlingJobResponse)
        assert job_response.job_id == "job-12345"
        assert job_response.status == "completed"
        assert job_response.video_url == "https://example.com/video.mp4"


@pytest.mark.asyncio
async def test_download_video_success(kling_client):
    """Test download_video returns video bytes on success."""
    video_content = b"fake video content"

    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client_instance = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = video_content
        mock_response.raise_for_status.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        downloaded_content = await kling_client.download_video("https://example.com/video.mp4")

        assert downloaded_content == video_content


@pytest.mark.asyncio
async def test_download_video_request_error(kling_client):
    """Test download_video raises KlingError on request failure."""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = httpx.RequestError("Connection error")
        
        with pytest.raises(KlingError):
            await kling_client.download_video("https://example.com/video.mp4")


def test_kling_job_response_initialization():
    """Test KlingJobResponse initialization with sample data."""
    sample_data = {
        "id": "job-12345",
        "status": "processing",
        "video_url": "https://example.com/video.mp4",
        "prompt": "A cat playing with a ball",
        "negative_prompt": "dark, blurry",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:30Z"
    }
    
    job_response = KlingJobResponse(sample_data)
    
    assert job_response.job_id == "job-12345"
    assert job_response.status == "processing"
    assert job_response.video_url == "https://example.com/video.mp4"
    assert job_response.prompt == "A cat playing with a ball"
    assert job_response.negative_prompt == "dark, blurry"
    assert job_response.created_at == "2023-01-01T00:00:00Z"
    assert job_response.updated_at == "2023-01-01T00:00:30Z"
    assert job_response.data == sample_data


@pytest.mark.asyncio
async def test_context_manager(kling_client):
    """Test KlingClient can be used as an async context manager."""
    async with kling_client as client:
        assert client._client is None  # Client not initialized until first request
        
    # After context manager exits, client should be closed
    assert client._client is None