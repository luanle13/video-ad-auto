"""Unit tests for KlingClient polling and convenience methods."""
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
async def test_wait_for_completion_success_variations(kling_client):
    """Test wait_for_completion handles different success status variations."""
    # Test with "success" status
    mock_responses = [
        MagicMock(spec=KlingJobResponse, status="processing", job_id="job-12345"),
        MagicMock(spec=KlingJobResponse, status="success", job_id="job-12345", video_url="https://example.com/video.mp4")
    ]
    
    with patch.object(kling_client, 'get_job_status', side_effect=mock_responses):
        with patch('asyncio.sleep'):
            result = await kling_client.wait_for_completion("job-12345", poll_interval=0.01, max_attempts=5)
            assert result.status == "success"
    
    # Test with "done" status
    mock_responses = [
        MagicMock(spec=KlingJobResponse, status="processing", job_id="job-12345"),
        MagicMock(spec=KlingJobResponse, status="done", job_id="job-12345", video_url="https://example.com/video.mp4")
    ]
    
    with patch.object(kling_client, 'get_job_status', side_effect=mock_responses):
        with patch('asyncio.sleep'):
            result = await kling_client.wait_for_completion("job-12345", poll_interval=0.01, max_attempts=5)
            assert result.status == "done"


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
async def test_wait_for_completion_failure_variations(kling_client):
    """Test wait_for_completion handles different failure status variations."""
    mock_responses = [
        MagicMock(spec=KlingJobResponse, status="processing", job_id="job-12345"),
        MagicMock(spec=KlingJobResponse, status="error", job_id="job-12345")
    ]
    
    with patch.object(kling_client, 'get_job_status', side_effect=mock_responses):
        with patch('asyncio.sleep'):
            with pytest.raises(KlingError, match="Video generation failed: error"):
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
async def test_wait_for_completion_with_progress_callback(kling_client):
    """Test wait_for_completion calls progress callback when provided."""
    mock_responses = [
        MagicMock(spec=KlingJobResponse, status="processing", job_id="job-12345"),
        MagicMock(spec=KlingJobResponse, status="completed", job_id="job-12345", video_url="https://example.com/video.mp4")
    ]
    
    progress_callback = AsyncMock()
    
    with patch.object(kling_client, 'get_job_status', side_effect=mock_responses):
        with patch('asyncio.sleep'):
            result = await kling_client.wait_for_completion(
                "job-12345", 
                poll_interval=0.01, 
                max_attempts=5,
                progress_callback=progress_callback
            )
            
            # Callback should be called twice (once for each status check)
            assert progress_callback.call_count == 2
            # Last call should be with completed status
            progress_callback.assert_called_with(mock_responses[1])


@pytest.mark.asyncio
async def test_wait_for_completion_with_sync_progress_callback(kling_client):
    """Test wait_for_completion calls sync progress callback when provided."""
    mock_responses = [
        MagicMock(spec=KlingJobResponse, status="processing", job_id="job-12345"),
        MagicMock(spec=KlingJobResponse, status="completed", job_id="job-12345", video_url="https://example.com/video.mp4")
    ]
    
    progress_callback = MagicMock()
    
    with patch.object(kling_client, 'get_job_status', side_effect=mock_responses):
        with patch('asyncio.sleep'):
            result = await kling_client.wait_for_completion(
                "job-12345", 
                poll_interval=0.01, 
                max_attempts=5,
                progress_callback=progress_callback
            )
            
            # Callback should be called twice (once for each status check)
            assert progress_callback.call_count == 2


@pytest.mark.asyncio
async def test_generate_and_wait_success(kling_client):
    """Test generate_and_wait successfully generates, waits, and downloads video."""
    # Mock the generate_video call
    with patch.object(kling_client, 'generate_video', return_value="job-12345"):
        # Mock the wait_for_completion call
        mock_job_response = MagicMock(spec=KlingJobResponse, status="completed", video_url="https://example.com/video.mp4")
        
        with patch.object(kling_client, 'wait_for_completion', return_value=mock_job_response):
            # Mock the download_video call
            video_content = b"fake video content"
            with patch.object(kling_client, 'download_video', return_value=video_content):
                with patch('asyncio.sleep'):
                    job_response, downloaded_video = await kling_client.generate_and_wait(
                        prompt="A cat playing with a ball",
                        config={"duration": 5, "resolution": "1080x720"}
                    )
                    
                    assert job_response == mock_job_response
                    assert downloaded_video == video_content


@pytest.mark.asyncio
async def test_generate_and_wait_with_progress_callback(kling_client):
    """Test generate_and_wait passes progress callback to wait_for_completion."""
    # Mock the generate_video call
    with patch.object(kling_client, 'generate_video', return_value="job-12345"):
        # Mock the wait_for_completion call
        mock_job_response = MagicMock(spec=KlingJobResponse, status="completed", video_url="https://example.com/video.mp4")
        
        wait_mock = AsyncMock(return_value=mock_job_response)
        with patch.object(kling_client, 'wait_for_completion', side_effect=wait_mock):
            # Mock the download_video call
            video_content = b"fake video content"
            with patch.object(kling_client, 'download_video', return_value=video_content):
                with patch('asyncio.sleep'):
                    progress_callback = AsyncMock()
                    
                    await kling_client.generate_and_wait(
                        prompt="A cat playing with a ball",
                        config={"duration": 5, "resolution": "1080x720"},
                        progress_callback=progress_callback
                    )
                    
                    # Verify that wait_for_completion was called with the progress callback
                    wait_mock.assert_called_once()
                    args, kwargs = wait_mock.call_args
                    assert kwargs.get('progress_callback') == progress_callback


@pytest.mark.asyncio
async def test_generate_and_wait_failure_in_generation(kling_client):
    """Test generate_and_wait propagates errors from generate_video."""
    with patch.object(kling_client, 'generate_video', side_effect=KlingError("Generation failed")):
        with pytest.raises(KlingError, match="Generation failed"):
            await kling_client.generate_and_wait(
                prompt="A cat playing with a ball",
                config={"duration": 5, "resolution": "1080x720"}
            )


@pytest.mark.asyncio
async def test_generate_and_wait_failure_in_waiting(kling_client):
    """Test generate_and_wait propagates errors from wait_for_completion."""
    # Mock the generate_video call
    with patch.object(kling_client, 'generate_video', return_value="job-12345"):
        # Mock the wait_for_completion to raise an error
        with patch.object(kling_client, 'wait_for_completion', side_effect=KlingError("Wait failed")):
            with pytest.raises(KlingError, match="Wait failed"):
                await kling_client.generate_and_wait(
                    prompt="A cat playing with a ball",
                    config={"duration": 5, "resolution": "1080x720"}
                )


@pytest.mark.asyncio
async def test_generate_and_wait_failure_in_download(kling_client):
    """Test generate_and_wait propagates errors from download_video."""
    # Mock the generate_video call
    with patch.object(kling_client, 'generate_video', return_value="job-12345"):
        # Mock the wait_for_completion call
        mock_job_response = MagicMock(spec=KlingJobResponse, status="completed", video_url="https://example.com/video.mp4")
        
        with patch.object(kling_client, 'wait_for_completion', return_value=mock_job_response):
            # Mock the download_video to raise an error
            with patch.object(kling_client, 'download_video', side_effect=KlingError("Download failed")):
                with patch('asyncio.sleep'):
                    with pytest.raises(KlingError, match="Download failed"):
                        await kling_client.generate_and_wait(
                            prompt="A cat playing with a ball",
                            config={"duration": 5, "resolution": "1080x720"}
                        )