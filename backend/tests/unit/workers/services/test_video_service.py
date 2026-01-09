"""Unit tests for VideoService."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.shared.exceptions import KlingError
from src.workers.clients.kling import KlingJobResponse
from src.workers.services.video_service import VideoResult, VideoService, get_video_service


@pytest.fixture
def video_service():
    """Fixture to create a VideoService instance for testing."""
    return VideoService()


@pytest.mark.asyncio
async def test_video_result_model():
    """Test VideoResult Pydantic model creation."""
    job_response = MagicMock(spec=KlingJobResponse)
    video_data = b"fake video content"
    
    result = VideoResult(
        video_data=video_data,
        job_response=job_response,
        duration_seconds=5.0
    )
    
    assert result.video_data == video_data
    assert result.job_response == job_response
    assert result.duration_seconds == 5.0


@pytest.mark.asyncio
async def test_video_service_initialization():
    """Test VideoService initialization."""
    service = VideoService()
    
    assert service._kling_client is None


@pytest.mark.asyncio
async def test_get_kling_client_lazy_init(video_service):
    """Test _get_kling_client creates client on first call."""
    with patch('src.workers.services.video_service.get_settings') as mock_settings, \
         patch('src.workers.services.video_service.get_secrets') as mock_secrets, \
         patch('src.workers.services.video_service.KlingClient') as mock_client_class:
        
        # Setup mocks
        mock_settings.return_value.secrets_kling_key = "test-kling-key"
        mock_secrets.return_value.get_secret.return_value = "test-api-key"
        
        mock_client_instance = AsyncMock()
        mock_client_class.return_value = mock_client_instance
        
        # First call should create the client
        client1 = await video_service._get_kling_client()
        
        # Second call should return the same client
        client2 = await video_service._get_kling_client()
        
        # Verify client was created once
        mock_client_class.assert_called_once_with(api_key="test-api-key")
        assert client1 == client2
        assert video_service._kling_client == mock_client_instance


@pytest.mark.asyncio
async def test_get_kling_client_error_handling(video_service):
    """Test _get_kling_client handles errors properly."""
    with patch('src.workers.services.video_service.get_settings') as mock_settings, \
         patch('src.workers.services.video_service.get_secrets') as mock_secrets:
        
        # Setup mocks to raise an exception
        mock_secrets.return_value.get_secret.side_effect = Exception("Secret retrieval failed")
        
        with pytest.raises(KlingError, match="Failed to initialize Kling client"):
            await video_service._get_kling_client()


@pytest.mark.asyncio
async def test_generate_video_success(video_service):
    """Test generate_video successfully creates video."""
    with patch.object(video_service, '_get_kling_client') as mock_get_client, \
         patch('src.workers.services.video_service.get_storage') as mock_get_storage:
        
        # Setup mocks
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        
        mock_storage = MagicMock()
        mock_storage.generate_download_url.return_value = "https://example.com/audio.mp3"
        mock_get_storage.return_value = mock_storage
        
        # Mock the generate_and_wait response
        mock_job_response = MagicMock(spec=KlingJobResponse)
        mock_job_response.job_id = "job-12345"
        video_data = b"fake video content"
        mock_client.generate_and_wait.return_value = (mock_job_response, video_data)
        
        # Call the method
        result = await video_service.generate_video(
            prompt="A cat playing with a ball",
            config={"duration": 5, "resolution": "1080x720"},
            audio_s3_key="user123/job456/voiceover.mp3"
        )
        
        # Verify the result
        assert isinstance(result, VideoResult)
        assert result.video_data == video_data
        assert result.job_response == mock_job_response
        assert result.duration_seconds == 5.0  # From config
        
        # Verify the client method was called correctly
        mock_client.generate_and_wait.assert_called_once_with(
            prompt="A cat playing with a ball",
            config={"duration": 5, "resolution": "1080x720"},
            audio_url="https://example.com/audio.mp3",
            progress_callback=None,
        )


@pytest.mark.asyncio
async def test_generate_video_without_audio(video_service):
    """Test generate_video works without audio file."""
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
async def test_generate_video_with_defaults(video_service):
    """Test generate_video uses default config when none provided."""
    with patch.object(video_service, '_get_kling_client') as mock_get_client:
        
        # Setup mocks
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        
        # Mock the generate_and_wait response
        mock_job_response = MagicMock(spec=KlingJobResponse)
        mock_job_response.job_id = "job-12345"
        video_data = b"fake video content"
        mock_client.generate_and_wait.return_value = (mock_job_response, video_data)
        
        # Call the method without config (should use defaults)
        result = await video_service.generate_video(
            prompt="A cat playing with a ball"
        )
        
        # Verify the result
        assert isinstance(result, VideoResult)
        assert result.video_data == video_data
        assert result.job_response == mock_job_response
        assert result.duration_seconds == 5.0  # From default config
        
        # Verify the client method was called with default config
        expected_config = {
            "duration": 5,
            "resolution": "1080x720",
            "aspect_ratio": "16:9"
        }
        mock_client.generate_and_wait.assert_called_once_with(
            prompt="A cat playing with a ball",
            config=expected_config,
            audio_url=None,
            progress_callback=None,
        )


@pytest.mark.asyncio
async def test_generate_video_with_progress_callback(video_service):
    """Test generate_video passes progress callback to client."""
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


@pytest.mark.asyncio
async def test_close_closes_client(video_service):
    """Test close method closes the Kling client."""
    # Manually assign a mock client to the service
    mock_client = AsyncMock()
    video_service._kling_client = mock_client

    # Close the service
    await video_service.close()

    # Verify the client was closed
    mock_client.close.assert_called_once()
    assert video_service._kling_client is None


@pytest.mark.asyncio
async def test_close_no_client(video_service):
    """Test close method works when no client exists."""
    # Close the service without initializing client
    await video_service.close()
    
    # Should not raise an exception
    assert video_service._kling_client is None


def test_get_video_service_singleton():
    """Test get_video_service returns singleton instance."""
    service1 = get_video_service()
    service2 = get_video_service()
    
    # Both should be the same instance
    assert service1 is service2