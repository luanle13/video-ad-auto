"""Integration tests for Video service with external API mocks."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.shared.storage import get_storage
from src.workers.clients.kling import KlingClient, KlingJobResponse
from src.workers.services.video_service import VideoService, get_video_service


@pytest.mark.asyncio
async def test_video_service_kling_success():
    """Test Video service with successful Kling API call."""
    with patch('src.workers.services.video_service.get_settings') as mock_settings, \
         patch('src.workers.services.video_service.get_secrets') as mock_secrets, \
         patch('httpx.AsyncClient.post') as mock_post, \
         patch('httpx.AsyncClient.get') as mock_get:
        
        # Setup mocks
        mock_settings.return_value.secrets_kling_key = "test-kling-key"
        mock_secrets.return_value.get_secret.return_value = "test-api-key"
        
        # Mock successful video generation response
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "job-12345", "status": "processing"}
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Mock job status polling responses
        status_responses = [
            {"status": "processing", "id": "job-12345"},
            {"status": "generating", "id": "job-12345"},
            {"status": "completed", "id": "job-12345", "video_url": "https://example.com/video.mp4"}
        ]
        
        # Mock get responses for polling
        mock_get_responses = []
        for resp_data in status_responses:
            mock_resp = MagicMock()
            mock_resp.json.return_value = resp_data
            mock_get_responses.append(mock_resp)
        
        # Cycle through responses for polling
        mock_get_side_effects = mock_get_responses
        mock_get.return_value.__aenter__.side_effect = mock_get_side_effects
        # Reset for multiple calls
        mock_get.return_value.__aenter__.return_value = mock_get_responses[-1]  # For the last call
        
        # Mock video download response
        mock_video_response = MagicMock()
        mock_video_response.content = b"fake video content"
        mock_video_response.raise_for_status.return_value = None
        mock_video_get = AsyncMock()
        mock_video_get.get.return_value = mock_video_response
        mock_video_get.aclose.return_value = None
        
        # Initialize service
        service = get_video_service()
        
        # Test video generation
        with patch('httpx.AsyncClient') as mock_async_client:
            # Mock the video download client
            mock_async_client.return_value = mock_video_get
            
            result = await service.generate_video(
                prompt="A cat playing with a ball",
                config={"duration": 5, "resolution": "1080x720"},
                progress_callback=None
            )
        
        # Verify result
        assert result.video_data == b"fake video content"
        assert result.duration_seconds == 5.0
        assert result.job_response.status == "completed"
        
        # Cleanup
        await service.close()


@pytest.mark.asyncio
async def test_video_service_with_audio_s3_integration():
    """Test Video service with audio S3 integration."""
    with patch('src.workers.services.video_service.get_settings') as mock_settings, \
         patch('src.workers.services.video_service.get_secrets') as mock_secrets, \
         patch('src.workers.services.video_service.get_storage') as mock_get_storage, \
         patch('httpx.AsyncClient.post') as mock_post, \
         patch('httpx.AsyncClient.get') as mock_get:
        
        # Setup mocks
        mock_settings.return_value.secrets_kling_key = "test-kling-key"
        mock_secrets.return_value.get_secret.return_value = "test-api-key"
        
        # Setup mock storage
        mock_storage = MagicMock()
        mock_storage.generate_download_url.return_value = "https://example.com/audio.mp3"
        mock_get_storage.return_value = mock_storage
        
        # Mock successful video generation response
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "job-12345", "status": "processing"}
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Mock job status polling responses
        status_responses = [
            {"status": "processing", "id": "job-12345"},
            {"status": "completed", "id": "job-12345", "video_url": "https://example.com/video.mp4"}
        ]
        
        # Mock get responses for polling
        mock_get_responses = []
        for resp_data in status_responses:
            mock_resp = MagicMock()
            mock_resp.json.return_value = resp_data
            mock_get_responses.append(mock_resp)
        
        # Mock video download response
        mock_video_response = MagicMock()
        mock_video_response.content = b"video with audio content"
        mock_video_response.raise_for_status.return_value = None
        
        # Mock the get calls for polling and video download
        def get_side_effect(url):
            if "job-12345" in url:
                # Return different responses for polling
                mock_resp = MagicMock()
                mock_resp.json.return_value = status_responses[0]  # Just return first for simplicity
                return AsyncMock().__aenter__.return_value
            else:
                # Return video content
                mock_resp = MagicMock()
                mock_resp.content = b"video with audio content"
                mock_resp.raise_for_status.return_value = None
                return AsyncMock().__aenter__.return_value
        
        mock_get.return_value.__aenter__.return_value = MagicMock()
        mock_get.return_value.__aenter__.return_value.json.return_value = status_responses[-1]  # completed status
        
        # Mock video download separately
        with patch('httpx.AsyncClient') as mock_async_client:
            mock_video_client = AsyncMock()
            mock_video_client.get.return_value.__aenter__.return_value.content = b"video with audio content"
            mock_video_client.get.return_value.__aenter__.return_value.raise_for_status.return_value = None
            mock_async_client.return_value = mock_video_client
        
            # Initialize service
            service = get_video_service()
            
            # Test video generation with audio
            result = await service.generate_video(
                prompt="A cat playing with a ball",
                audio_s3_key="user123/job456/voiceover.mp3",
                config={"duration": 10, "resolution": "720x480"},
                progress_callback=None
            )
        
        # Verify result
        assert result.video_data == b"video with audio content"
        assert result.duration_seconds == 10.0
        assert result.job_response.status == "completed"
        
        # Verify S3 URL was generated
        mock_storage.generate_download_url.assert_called_once_with("videos", "user123/job456/voiceover.mp3")
        
        # Cleanup
        await service.close()


@pytest.mark.asyncio
async def test_video_service_polling_loop():
    """Test video service polling loop functionality."""
    with patch('src.workers.services.video_service.get_settings') as mock_settings, \
         patch('src.workers.services.video_service.get_secrets') as mock_secrets, \
         patch('httpx.AsyncClient.post') as mock_post, \
         patch('httpx.AsyncClient.get') as mock_get:
        
        # Setup mocks
        mock_settings.return_value.secrets_kling_key = "test-kling-key"
        mock_secrets.return_value.get_secret.return_value = "test-api-key"
        
        # Mock initial job creation
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "job-67890", "status": "processing"}
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Mock polling responses - simulate multiple polls before completion
        status_responses = [
            {"status": "processing", "id": "job-67890"},
            {"status": "generating", "id": "job-67890"},
            {"status": "generating", "id": "job-67890"},
            {"status": "completed", "id": "job-67890", "video_url": "https://example.com/video.mp4"}
        ]
        
        # Create a counter to cycle through responses
        counter = iter(status_responses)
        
        def get_json_side_effect():
            try:
                return next(counter)
            except StopIteration:
                return {"status": "completed", "id": "job-67890", "video_url": "https://example.com/video.mp4"}
        
        mock_get_response = MagicMock()
        mock_get_response.json.side_effect = get_json_side_effect
        mock_get.return_value.__aenter__.return_value = mock_get_response
        
        # Mock video download response
        mock_video_response = MagicMock()
        mock_video_response.content = b"polled video content"
        mock_video_response.raise_for_status.return_value = None
        
        # Initialize service
        service = get_video_service()
        
        # Test video generation with polling
        with patch('httpx.AsyncClient') as mock_async_client:
            mock_video_client = AsyncMock()
            mock_video_client.get.return_value.__aenter__.return_value.content = b"polled video content"
            mock_video_client.get.return_value.__aenter__.return_value.raise_for_status.return_value = None
            mock_async_client.return_value = mock_video_client
        
            result = await service.generate_video(
                prompt="A dog running in the park",
                config={"duration": 8, "resolution": "1080x720"},
                poll_interval=0.01,  # Fast polling for tests
                max_attempts=10
            )
        
        # Verify result
        assert result.video_data == b"polled video content"
        assert result.duration_seconds == 8.0
        assert result.job_response.status == "completed"
        
        # Cleanup
        await service.close()


@pytest.mark.asyncio
async def test_video_service_video_download_and_s3_upload():
    """Test full video flow with download and S3 upload."""
    with patch('src.workers.services.video_service.get_settings') as mock_settings, \
         patch('src.workers.services.video_service.get_secrets') as mock_secrets, \
         patch('httpx.AsyncClient.post') as mock_post, \
         patch('httpx.AsyncClient.get') as mock_get:
        
        # Setup mocks
        mock_settings.return_value.secrets_kling_key = "test-kling-key"
        mock_secrets.return_value.get_secret.return_value = "test-api-key"
        
        # Mock initial job creation
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "job-55555", "status": "processing"}
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Mock completed job status
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "status": "completed", 
            "id": "job-55555", 
            "video_url": "https://example.com/video.mp4"
        }
        mock_get.return_value.__aenter__.return_value = mock_get_response
        
        # Initialize service
        service = get_video_service()
        
        # Test video generation
        with patch('httpx.AsyncClient') as mock_async_client:
            mock_video_client = AsyncMock()
            mock_video_client.get.return_value.__aenter__.return_value.content = b"video for s3 upload"
            mock_video_client.get.return_value.__aenter__.return_value.raise_for_status.return_value = None
            mock_async_client.return_value = mock_video_client
        
            result = await service.generate_video(
                prompt="A beautiful sunset over mountains",
                config={"duration": 15, "resolution": "1080x720"},
                progress_callback=None
            )
        
        # Verify result
        assert result.video_data == b"video for s3 upload"
        assert result.duration_seconds == 15.0
        assert result.job_response.status == "completed"
        
        # Test S3 upload using storage client
        storage = get_storage()
        video_key = storage.generate_video_key("test-user", "job-55555")
        video_url = storage.upload_file(
            bucket_type="videos",
            key=video_key,
            body=result.video_data,
            content_type="video/mp4"
        )
        
        # Verify S3 operations were called
        assert video_key.startswith("test-user/job-55555/")
        assert video_url.startswith("s3://")
        
        # Cleanup
        await service.close()


@pytest.mark.asyncio
async def test_video_service_kling_failure():
    """Test Video service with Kling API failure."""
    with patch('src.workers.services.video_service.get_settings') as mock_settings, \
         patch('src.workers.services.video_service.get_secrets') as mock_secrets, \
         patch('httpx.AsyncClient.post') as mock_post:
        
        # Setup mocks
        mock_settings.return_value.secrets_kling_key = "test-kling-key"
        mock_secrets.return_value.get_secret.return_value = "test-api-key"
        
        # Mock API failure
        mock_post.side_effect = Exception("Kling API error")
        
        # Initialize service
        service = get_video_service()
        
        # Test video generation failure
        with pytest.raises(Exception, match="Kling API error"):
            await service.generate_video(
                prompt="A cat playing with a ball",
                config={"duration": 5, "resolution": "1080x720"}
            )
        
        # Cleanup
        await service.close()