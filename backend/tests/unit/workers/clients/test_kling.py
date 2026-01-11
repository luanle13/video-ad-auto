"""Unit tests for KlingClient."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.shared.exceptions import JobTimeoutError, KlingError
from src.workers.clients.kling import KlingClient, KlingJobResponse


@pytest.fixture
def kling_client():
    """Fixture to create a KlingClient instance for testing."""
    return KlingClient(api_key="test-api-key")


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
async def test_get_job_status(kling_client):
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
async def test_wait_for_completion_success(kling_client):
    """Test wait_for_completion returns job response when job completes."""
    # Mock job responses for different statuses
    mock_responses = [
        MagicMock(spec=KlingJobResponse, status="processing", job_id="job-12345"),
        MagicMock(spec=KlingJobResponse, status="generating", job_id="job-12345"),
        MagicMock(spec=KlingJobResponse, status="completed", job_id="job-12345", video_url="https://example.com/video.mp4")
    ]

    with patch.object(kling_client, 'get_job_status', side_effect=mock_responses):
        with patch('asyncio.sleep'):  # Mock sleep to avoid actual delays
            result = await kling_client.wait_for_completion("job-12345", poll_interval=0.01, max_attempts=5)

            assert result.status == "completed"
            assert result.video_url == "https://example.com/video.mp4"


@pytest.mark.asyncio
async def test_wait_for_completion_failure(kling_client):
    """Test wait_for_completion raises KlingError when job fails."""
    mock_responses = [
        MagicMock(spec=KlingJobResponse, status="processing", job_id="job-12345"),
        MagicMock(spec=KlingJobResponse, status="failed", job_id="job-12345")
    ]

    with patch.object(kling_client, 'get_job_status', side_effect=mock_responses):
        with patch('asyncio.sleep'):
            with pytest.raises(KlingError, match="Video generation failed: failed"):
                await kling_client.wait_for_completion("job-12345", poll_interval=0.01, max_attempts=5)


@pytest.mark.asyncio
async def test_wait_for_completion_timeout(kling_client):
    """Test wait_for_completion raises JobTimeoutError when max attempts exceeded."""
    mock_response = MagicMock(spec=KlingJobResponse, status="processing", job_id="job-12345")

    with patch.object(kling_client, 'get_job_status', return_value=mock_response):
        with patch('asyncio.sleep'):
            with pytest.raises(JobTimeoutError, match="Video generation timed out"):
                await kling_client.wait_for_completion("job-12345", poll_interval=0.01, max_attempts=3)


@pytest.mark.asyncio
async def test_download_video(kling_client):
    """Test download_video returns video bytes on success."""
    video_content = b"fake video content"

    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client_instance = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = video_content
        mock_response.raise_for_status = AsyncMock()  # Make this an async method
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        downloaded_content = await kling_client.download_video("https://example.com/video.mp4")

        assert downloaded_content == video_content