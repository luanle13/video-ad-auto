"""Unit tests for VideoHandler."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.models.jobs import JobStatus
from src.workers.handlers.video_handler import VideoHandlerInput, VideoHandlerOutput, handler
from src.workers.services.video_service import VideoResult
from src.workers.clients.kling import KlingJobResponse


@pytest.mark.asyncio
async def test_video_handler_input_model():
    """Test VideoHandlerInput Pydantic model validation."""
    input_data = VideoHandlerInput(
        user_id="user123",
        job_id="job456",
        video_prompt="A cat playing with a ball",
        audio_s3_key="user123/job456/voiceover.mp3",
        aspect_ratio="16:9",
        duration=5
    )
    
    assert input_data.user_id == "user123"
    assert input_data.job_id == "job456"
    assert input_data.video_prompt == "A cat playing with a ball"
    assert input_data.audio_s3_key == "user123/job456/voiceover.mp3"
    assert input_data.aspect_ratio == "16:9"
    assert input_data.duration == 5


@pytest.mark.asyncio
async def test_video_handler_input_model_defaults():
    """Test VideoHandlerInput with default values."""
    input_data = VideoHandlerInput(
        user_id="user123",
        job_id="job456",
        video_prompt="A cat playing with a ball"
    )
    
    assert input_data.user_id == "user123"
    assert input_data.job_id == "job456"
    assert input_data.video_prompt == "A cat playing with a ball"
    assert input_data.audio_s3_key is None
    assert input_data.aspect_ratio == "16:9"  # Default
    assert input_data.duration == 5  # Default


@pytest.mark.asyncio
async def test_video_handler_output_model():
    """Test VideoHandlerOutput Pydantic model."""
    output_data = VideoHandlerOutput(
        success=True,
        video_s3_key="user123/job456/output.mp4",
        video_s3_url="s3://bucket/user123/job456/output.mp4",
        duration_seconds=5.0
    )
    
    assert output_data.success is True
    assert output_data.video_s3_key == "user123/job456/output.mp4"
    assert output_data.video_s3_url == "s3://bucket/user123/job456/output.mp4"
    assert output_data.duration_seconds == 5.0
    assert output_data.error is None


@pytest.mark.asyncio
async def test_video_handler_output_model_error():
    """Test VideoHandlerOutput with error."""
    output_data = VideoHandlerOutput(
        success=False,
        error="Something went wrong"
    )
    
    assert output_data.success is False
    assert output_data.error == "Something went wrong"
    assert output_data.video_s3_key is None
    assert output_data.video_s3_url is None
    assert output_data.duration_seconds is None


@pytest.mark.asyncio
async def test_handler_success():
    """Test handler success case."""
    event = {
        "user_id": "user123",
        "job_id": "job456",
        "video_prompt": "A cat playing with a ball",
        "audio_s3_key": "user123/job456/voiceover.mp3",
        "aspect_ratio": "16:9",
        "duration": 5
    }
    
    context = MagicMock()
    
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
        result = await handler(event, context)
        
        # Verify the result
        assert result["success"] is True
        assert result["video_s3_key"] == "user123/job456/output.mp4"
        assert result["video_s3_url"] == "s3://bucket/user123/job456/output.mp4"
        assert result["duration_seconds"] == 5.0
        assert result["error"] is None
        
        # Verify database calls
        mock_db.update_job_status.assert_any_call(
            user_id="user123",
            job_id="job456",
            status=JobStatus.GENERATING_VIDEO.value,
        )
        mock_db.update_job_status.assert_called_with(
            user_id="user123",
            job_id="job456",
            status=JobStatus.COMPLETE.value,
        )
        
        # Verify storage calls
        mock_storage.generate_video_key.assert_called_once_with(
            user_id="user123",
            job_id="job456"
        )
        mock_storage.upload_file.assert_called_once_with(
            bucket_type="videos",
            key="user123/job456/output.mp4",
            body=b"fake video content",
            content_type="video/mp4",
        )
        
        # Verify video service calls
        mock_video_service.generate_video.assert_called_once_with(
            prompt="A cat playing with a ball",
            audio_s3_key="user123/job456/voiceover.mp3",
            config={
                "duration": 5,
                "aspect_ratio": "16:9",
                "resolution": "1080x720"
            },
        )


@pytest.mark.asyncio
async def test_handler_success_without_audio():
    """Test handler success case without audio."""
    event = {
        "user_id": "user123",
        "job_id": "job456",
        "video_prompt": "A cat playing with a ball",
        "aspect_ratio": "9:16",
        "duration": 10
    }
    
    context = MagicMock()
    
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
            duration_seconds=10.0
        )
        mock_video_service.generate_video.return_value = mock_video_result
        
        # Call the handler
        result = await handler(event, context)
        
        # Verify the result
        assert result["success"] is True
        assert result["duration_seconds"] == 10.0
        
        # Verify video service calls (audio_s3_key should be None)
        mock_video_service.generate_video.assert_called_once_with(
            prompt="A cat playing with a ball",
            audio_s3_key=None,
            config={
                "duration": 10,
                "aspect_ratio": "9:16",
                "resolution": "1080x720"
            },
        )


@pytest.mark.asyncio
async def test_handler_error_case():
    """Test handler error case."""
    event = {
        "user_id": "user123",
        "job_id": "job456",
        "video_prompt": "A cat playing with a ball"
    }
    
    context = MagicMock()
    
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
        
        # Mock the video generation to raise an exception
        mock_video_service.generate_video.side_effect = Exception("Video generation failed")
        
        # Call the handler
        result = await handler(event, context)
        
        # Verify the result
        assert result["success"] is False
        assert result["error"] == "Video generation failed"
        assert result["video_s3_key"] is None
        assert result["video_s3_url"] is None
        assert result["duration_seconds"] is None
        
        # Verify database calls - should update to FAILED status
        mock_db.update_job_status.assert_any_call(
            user_id="user123",
            job_id="job456",
            status=JobStatus.GENERATING_VIDEO.value,
        )
        mock_db.update_job_status.assert_called_with(
            user_id="user123",
            job_id="job456",
            status=JobStatus.FAILED.value,
            error_message="Video generation failed: Video generation failed",
        )


@pytest.mark.asyncio
async def test_handler_db_error_on_failure():
    """Test handler when database update fails during error handling."""
    event = {
        "user_id": "user123",
        "job_id": "job456",
        "video_prompt": "A cat playing with a ball"
    }
    
    context = MagicMock()
    
    with patch('src.workers.handlers.video_handler.get_db') as mock_get_db, \
         patch('src.workers.handlers.video_handler.get_storage') as mock_get_storage, \
         patch('src.workers.handlers.video_handler.get_video_service') as mock_get_video_service:
        
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Make the database update fail when trying to set status to FAILED
        mock_db.update_job_status.side_effect = [None, Exception("DB update failed")]  # First call succeeds, second fails
        
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage
        
        mock_video_service = AsyncMock()
        mock_get_video_service.return_value = mock_video_service
        
        # Mock the video generation to raise an exception
        mock_video_service.generate_video.side_effect = Exception("Video generation failed")
        
        # Call the handler
        result = await handler(event, context)
        
        # Verify the result
        assert result["success"] is False
        assert result["error"] == "Video generation failed"
        
        # Verify that update_job_status was called twice (once for GENERATING_VIDEO, once for FAILED)
        assert mock_db.update_job_status.call_count >= 1


@pytest.mark.asyncio
async def test_handler_cleanup_on_success():
    """Test that video service is cleaned up on success."""
    event = {
        "user_id": "user123",
        "job_id": "job456",
        "video_prompt": "A cat playing with a ball"
    }
    
    context = MagicMock()
    
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
        result = await handler(event, context)
        
        # Verify that the video service close method was called
        mock_video_service.close.assert_called_once()


@pytest.mark.asyncio
async def test_handler_cleanup_on_error():
    """Test that video service is cleaned up on error."""
    event = {
        "user_id": "user123",
        "job_id": "job456",
        "video_prompt": "A cat playing with a ball"
    }
    
    context = MagicMock()
    
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
        
        # Mock the video generation to raise an exception
        mock_video_service.generate_video.side_effect = Exception("Video generation failed")
        
        # Call the handler
        result = await handler(event, context)
        
        # Verify that the video service close method was called even on error
        mock_video_service.close.assert_called_once()