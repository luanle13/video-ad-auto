"""Unit tests for VideoService."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.shared.exceptions import DeepInfraError
from src.workers.clients.deepinfra import DeepInfraJobResponse
from src.workers.services.video_service import VideoResult, VideoService


@pytest.fixture
def video_service():
    """Fixture to create a VideoService instance for testing."""
    return VideoService()


@pytest.mark.asyncio
async def test_generate_video_basic(video_service):
    """Test generate_video successfully creates video."""
    with patch.object(video_service, '_get_deepinfra_client') as mock_get_client:

        # Setup mocks
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        # Mock the generate_and_download response
        mock_job_response = DeepInfraJobResponse(
            status="ok",
            videos=["https://example.com/video.mp4"],
            request_id="req-12345",
        )
        video_data = b"fake video content"
        mock_client.generate_and_download.return_value = (mock_job_response, video_data)

        # Call the method
        result = await video_service.generate_video(
            prompt="A cat playing with a ball",
            config={"resolution": "720p", "aspect_ratio": "9:16"},
        )

        # Verify the result
        assert isinstance(result, VideoResult)
        assert result.video_data == video_data
        assert result.job_response == mock_job_response
        assert result.duration_seconds == 8.0  # Veo 3.1 generates 8-second videos

        # Verify the client method was called correctly
        mock_client.generate_and_download.assert_called_once()
        call_args = mock_client.generate_and_download.call_args
        assert call_args.kwargs["prompt"] == "A cat playing with a ball"


@pytest.mark.asyncio
async def test_generate_video_with_opening_frame_logged(video_service):
    """Test generate_video logs when opening_frame_url is provided but not used."""
    with patch.object(video_service, '_get_deepinfra_client') as mock_get_client, \
         patch('src.workers.services.video_service.logger') as mock_logger:

        # Setup mocks
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        # Mock the generate_and_download response
        mock_job_response = DeepInfraJobResponse(
            status="ok",
            videos=["https://example.com/video.mp4"],
            request_id="req-12345",
        )
        video_data = b"fake video content"
        mock_client.generate_and_download.return_value = (mock_job_response, video_data)

        # Call the method with opening_frame_url
        result = await video_service.generate_video(
            prompt="A cat playing with a ball",
            opening_frame_url="https://example.com/frame.jpg",
            config={"resolution": "720p"},
        )

        # Verify the result
        assert isinstance(result, VideoResult)
        assert result.video_data == video_data

        # Verify log was called about opening_frame_url not being used
        mock_logger.info.assert_any_call(
            "opening_frame_url_provided_but_not_used",
            reason="Veo 3.1 Fast is text-to-video only; image input not supported",
        )


@pytest.mark.asyncio
async def test_generate_video_uses_default_config(video_service):
    """Test generate_video uses default config when none provided."""
    with patch.object(video_service, '_get_deepinfra_client') as mock_get_client:

        # Setup mocks
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        # Mock the generate_and_download response
        mock_job_response = DeepInfraJobResponse(
            status="ok",
            videos=["https://example.com/video.mp4"],
            request_id="req-12345",
        )
        video_data = b"fake video content"
        mock_client.generate_and_download.return_value = (mock_job_response, video_data)

        # Call the method without config
        result = await video_service.generate_video(
            prompt="A cat playing with a ball",
        )

        # Verify the result
        assert isinstance(result, VideoResult)
        assert result.duration_seconds == 8.0  # Veo 3.1 generates 8-second videos

        # Verify the client was called
        mock_client.generate_and_download.assert_called_once()


@pytest.mark.asyncio
async def test_generate_video_with_negative_prompt(video_service):
    """Test generate_video passes negative_prompt correctly."""
    with patch.object(video_service, '_get_deepinfra_client') as mock_get_client:

        # Setup mocks
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        # Mock the generate_and_download response
        mock_job_response = DeepInfraJobResponse(
            status="ok",
            videos=["https://example.com/video.mp4"],
            request_id="req-12345",
        )
        video_data = b"fake video content"
        mock_client.generate_and_download.return_value = (mock_job_response, video_data)

        # Call the method with negative_prompt in config
        result = await video_service.generate_video(
            prompt="A cat playing with a ball",
            config={
                "resolution": "720p",
                "negative_prompt": "blurry, low quality",
            },
        )

        # Verify the client was called with negative_prompt
        mock_client.generate_and_download.assert_called_once()
        call_args = mock_client.generate_and_download.call_args
        assert call_args.kwargs["negative_prompt"] == "blurry, low quality"


@pytest.mark.asyncio
async def test_generate_extended_video(video_service):
    """Test generate_extended_video returns 8-second video (Veo 3.1 limit)."""
    with patch.object(video_service, '_get_deepinfra_client') as mock_get_client:

        # Setup mocks
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        # Mock the generate_and_download response
        mock_job_response = DeepInfraJobResponse(
            status="ok",
            videos=["https://example.com/video.mp4"],
            request_id="req-12345",
        )
        video_data = b"fake video content"
        mock_client.generate_and_download.return_value = (mock_job_response, video_data)

        # Call generate_extended_video
        result = await video_service.generate_extended_video(
            prompt="A hand picks up a product",
            opening_frame_url="https://example.com/frame.jpg",
            target_duration=18,  # Requested 18 seconds
        )

        # Verify the result - should be 8 seconds (Veo 3.1 limit)
        assert isinstance(result, VideoResult)
        assert result.duration_seconds == 8.0


@pytest.mark.asyncio
async def test_map_config_aspect_ratio(video_service):
    """Test _map_config handles aspect ratio correctly."""
    # Valid aspect ratios
    config = video_service._map_config({"aspect_ratio": "16:9"})
    assert config["aspect_ratio"] == "16:9"

    config = video_service._map_config({"aspect_ratio": "9:16"})
    assert config["aspect_ratio"] == "9:16"

    # Invalid aspect ratio defaults to 9:16
    config = video_service._map_config({"aspect_ratio": "4:3"})
    assert config["aspect_ratio"] == "9:16"


@pytest.mark.asyncio
async def test_map_config_resolution(video_service):
    """Test _map_config handles resolution correctly."""
    # Valid resolutions
    config = video_service._map_config({"resolution": "720p"})
    assert config["resolution"] == "720p"

    config = video_service._map_config({"resolution": "1080p"})
    assert config["resolution"] == "1080p"

    # Invalid resolution defaults to 720p
    config = video_service._map_config({"resolution": "480p"})
    assert config["resolution"] == "720p"


@pytest.mark.asyncio
async def test_close_client(video_service):
    """Test close properly cleans up the client."""
    with patch.object(video_service, '_get_deepinfra_client') as mock_get_client:
        # Setup mock client
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        # First, get the client to initialize it
        video_service._deepinfra_client = mock_client

        # Close the service
        await video_service.close()

        # Verify client was closed
        mock_client.close.assert_called_once()
        assert video_service._deepinfra_client is None
