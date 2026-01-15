"""Unit tests for VideoService."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.shared.exceptions import KlingError
from src.workers.clients.kling import KlingJobResponse
from src.workers.services.video_service import VideoResult, VideoService


@pytest.fixture
def video_service():
    """Fixture to create a VideoService instance for testing."""
    return VideoService()


@pytest.mark.asyncio
async def test_generate_video_with_audio(video_service):
    """Test generate_video creates video (audio_s3_key is ignored now)."""
    with patch.object(video_service, '_get_kling_client') as mock_get_client:

        # Setup mocks
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        # Mock the generate_and_wait response
        mock_job_response = MagicMock(spec=KlingJobResponse)
        mock_job_response.job_id = "job-12345"
        video_data = b"fake video content"
        mock_client.generate_and_wait.return_value = (mock_job_response, video_data)

        # Call the method
        result = await video_service.generate_video(
            prompt="A cat playing with a ball",
            config={"duration": 5, "resolution": "1080x720"},
            audio_s3_key="user123/job456/voiceover.mp3"  # Now ignored
        )

        # Verify the result
        assert isinstance(result, VideoResult)
        assert result.video_data == video_data
        assert result.job_response == mock_job_response
        assert result.duration_seconds == 5.0  # From config

        # Verify the client method was called correctly (audio_url should be None)
        mock_client.generate_and_wait.assert_called_once_with(
            prompt="A cat playing with a ball",
            config={"duration": 5, "resolution": "1080x720"},
            audio_url=None,  # Audio URL support removed
            progress_callback=None,
        )


@pytest.mark.asyncio
async def test_generate_video_without_audio(video_service):
    """Test generate_video successfully creates video without audio."""
    with patch.object(video_service, '_get_kling_client') as mock_get_client:

        # Setup mocks
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        # Mock the generate_and_wait response
        mock_job_response = MagicMock(spec=KlingJobResponse)
        mock_job_response.job_id = "job-12345"
        video_data = b"fake video content"
        mock_client.generate_and_wait.return_value = (mock_job_response, video_data)

        # Call the method without audio
        result = await video_service.generate_video(
            prompt="A cat playing with a ball",
            config={"duration": 10, "resolution": "720x480"}
        )

        # Verify the result
        assert isinstance(result, VideoResult)
        assert result.video_data == video_data
        assert result.job_response == mock_job_response
        assert result.duration_seconds == 10.0  # From config

        # Verify the client method was called correctly (audio_url should be None)
        mock_client.generate_and_wait.assert_called_once_with(
            prompt="A cat playing with a ball",
            config={"duration": 10, "resolution": "720x480"},
            audio_url=None,
            progress_callback=None,
        )


@pytest.mark.asyncio
async def test_progress_callback_called(video_service):
    """Test progress callback is called during video generation."""
    with patch.object(video_service, '_get_kling_client') as mock_get_client:

        # Setup mocks
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        # Mock the generate_and_wait response
        mock_job_response = MagicMock(spec=KlingJobResponse)
        mock_job_response.job_id = "job-12345"
        video_data = b"fake video content"
        mock_client.generate_and_wait.return_value = (mock_job_response, video_data)

        # Create a progress callback
        progress_callback = AsyncMock()

        # Call the method with progress callback
        result = await video_service.generate_video(
            prompt="A cat playing with a ball",
            config={"duration": 5},
            progress_callback=progress_callback
        )

        # Verify the client method was called with the progress callback
        mock_client.generate_and_wait.assert_called_once_with(
            prompt="A cat playing with a ball",
            config={"duration": 5},
            audio_url=None,
            progress_callback=progress_callback,
        )

        # Verify the callback was actually passed to the client
        args, kwargs = mock_client.generate_and_wait.call_args
        assert kwargs.get('progress_callback') == progress_callback
