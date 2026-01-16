"""Unit tests for Video Lambda handler focusing on specific requirements."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.models.jobs import JobStatus
from src.workers.handlers.video_handler import VideoHandlerInput, VideoHandlerOutput, handler
from src.workers.services.video_service import VideoResult
from src.workers.clients.kling import KlingJobResponse


@pytest.mark.asyncio
async def test_handler_success():
    """Test successful video handler execution."""
    event = {
        "user_id": "user123",
        "job_id": "job456",
        "video_prompt": "A cat playing with a ball",
        "audio_s3_key": "user123/job456/voiceover.mp3",
        "aspect_ratio": "16:9",
        "duration": 5
    }

    with patch('src.workers.handlers.video_handler.get_db') as mock_get_db, \
         patch('src.workers.handlers.video_handler.get_storage') as mock_get_storage, \
         patch('src.workers.handlers.video_handler.get_video_service') as mock_get_video_service:

        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage
        mock_storage.generate_video_key.return_value = "user123/job456/output.mp4"
        mock_storage.upload_file.return_value = "s3://bucket/user123/job456/output.mp4"

        mock_video_service = AsyncMock()
        mock_get_video_service.return_value = mock_video_service

        # Mock the video generation result
        mock_job_response = MagicMock(spec=KlingJobResponse)
        mock_job_response.data = {"status": "completed", "id": "job-12345"}
        mock_video_result = VideoResult(
            video_data=b"fake video content",
            job_response=mock_job_response,
            duration_seconds=5.0
        )
        mock_video_service.generate_video.return_value = mock_video_result

        # Call the handler
        result = await handler(event, {})

        # Verify the result
        assert result["success"] is True
        assert result["video_s3_key"] == "user123/job456/output.mp4"
        assert result["video_s3_url"] == "s3://bucket/user123/job456/output.mp4"
        assert result["duration_seconds"] == 5.0
        assert result["error"] is None


@pytest.mark.asyncio
async def test_handler_timeout_error():
    """Test video handler when timeout occurs."""
    event = {
        "user_id": "user123",
        "job_id": "job456",
        "video_prompt": "A cat playing with a ball",
        "duration": 5
    }

    with patch('src.workers.handlers.video_handler.get_db') as mock_get_db, \
         patch('src.workers.handlers.video_handler.get_storage') as mock_get_storage, \
         patch('src.workers.handlers.video_handler.get_video_service') as mock_get_video_service:

        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage

        mock_video_service = AsyncMock()
        mock_get_video_service.return_value = mock_video_service

        # Mock the video service to raise a timeout exception
        mock_video_service.generate_video.side_effect = Exception("Video generation timed out")

        # Call the handler
        result = await handler(event, {})

        # Verify the result
        assert result["success"] is False
        assert result["error"] == "Video generation timed out"
        assert result["video_s3_key"] is None
        assert result["video_s3_url"] is None
        assert result["duration_seconds"] is None


@pytest.mark.asyncio
async def test_job_marked_complete():
    """Test that job is marked as complete when video handler succeeds."""
    event = {
        "user_id": "user123",
        "job_id": "job456",
        "video_prompt": "A cat playing with a ball",
        "duration": 5
    }

    with patch('src.workers.handlers.video_handler.get_db') as mock_get_db, \
         patch('src.workers.handlers.video_handler.get_storage') as mock_get_storage, \
         patch('src.workers.handlers.video_handler.get_video_service') as mock_get_video_service:

        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage
        mock_storage.generate_video_key.return_value = "user123/job456/output.mp4"
        mock_storage.upload_file.return_value = "s3://bucket/user123/job456/output.mp4"

        mock_video_service = AsyncMock()
        mock_get_video_service.return_value = mock_video_service

        # Mock the video generation result
        mock_job_response = MagicMock(spec=KlingJobResponse)
        mock_job_response.data = {"status": "completed", "id": "job-12345"}
        mock_video_result = VideoResult(
            video_data=b"fake video content",
            job_response=mock_job_response,
            duration_seconds=5.0
        )
        mock_video_service.generate_video.return_value = mock_video_result

        # Call the handler
        await handler(event, {})

        # Verify that job status was updated to COMPLETE
        calls = mock_db.update_job_status.call_args_list
        
        # First call should be to GENERATING_VIDEO
        assert calls[0][1]["status"] == JobStatus.GENERATING_VIDEO.value
        
        # Second call should be to COMPLETE
        assert calls[1][1]["status"] == JobStatus.COMPLETE.value


@pytest.mark.asyncio
async def test_job_marked_failed_on_error():
    """Test that job is marked as failed when video handler encounters an error."""
    event = {
        "user_id": "user123",
        "job_id": "job456",
        "video_prompt": "A cat playing with a ball",
        "duration": 5
    }

    with patch('src.workers.handlers.video_handler.get_db') as mock_get_db, \
         patch('src.workers.handlers.video_handler.get_storage') as mock_get_storage, \
         patch('src.workers.handlers.video_handler.get_video_service') as mock_get_video_service:

        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage

        mock_video_service = AsyncMock()
        mock_get_video_service.return_value = mock_video_service

        # Mock the video service to raise an exception
        mock_video_service.generate_video.side_effect = Exception("Video generation failed")

        # Call the handler
        await handler(event, {})

        # Verify that job status was updated to FAILED
        calls = mock_db.update_job_status.call_args_list
        
        # First call should be to GENERATING_VIDEO
        assert calls[0][1]["status"] == JobStatus.GENERATING_VIDEO.value
        
        # Second call should be to FAILED
        assert calls[1][1]["status"] == JobStatus.FAILED.value
        assert "Video generation failed: Video generation failed" in calls[1][1]["error_message"]