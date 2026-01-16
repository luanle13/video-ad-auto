"""Unit tests for TTS Lambda handler focusing on specific requirements."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.models.jobs import JobStatus
from src.workers.handlers.tts_handler import TTSHandlerInput, TTSHandlerOutput, handler
from src.workers.services.tts_models import TTSProvider, TTSResult


@pytest.mark.asyncio
async def test_handler_success():
    """Test successful TTS handler execution."""
    event = {
        "user_id": "user123",
        "job_id": "job456",
        "tts_script": "Hello, this is a test script for TTS generation.",
        "voice_gender": "female",
        "voice_style": "professional",
        "speaking_rate": 1.2,
        "provider": "elevenlabs",
    }

    with patch('src.workers.handlers.tts_handler.get_db') as mock_get_db, \
         patch('src.workers.handlers.tts_handler.get_storage') as mock_get_storage, \
         patch('src.workers.handlers.tts_handler.get_tts_service') as mock_get_service:

        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage
        mock_storage.generate_audio_key.return_value = "user123/job456/voiceover.mp3"
        mock_storage.upload_file.return_value = "s3://bucket/user123/job456/voiceover.mp3"

        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        # Mock the TTS result
        mock_result = TTSResult(
            audio_data=b"fake audio data",
            content_type="audio/mpeg",
            provider_used=TTSProvider.ELEVENLABS,
            character_count=50,
            voice_id="voice123",
            duration_estimate_seconds=4.0
        )
        mock_service.generate_speech.return_value = mock_result

        # Call the handler
        result = await handler(event, {})

        # Verify the result
        assert result["success"] is True
        assert result["audio_s3_key"] == "user123/job456/voiceover.mp3"
        assert result["audio_s3_url"] == "s3://bucket/user123/job456/voiceover.mp3"
        assert result["provider_used"] == "elevenlabs"
        assert result["character_count"] == 50
        assert result["duration_estimate_seconds"] == 4.0
        assert result["error"] is None


@pytest.mark.asyncio
async def test_handler_input_validation_error():
    """Test TTS handler with invalid input that causes validation error."""
    event = {
        "user_id": "user123",
        "job_id": "job456",
        "tts_script": "",  # Invalid: empty script
        "voice_gender": "invalid_gender",  # Invalid: not male/female
    }

    with patch('src.workers.handlers.tts_handler.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Call the handler
        result = await handler(event, {})

        # Verify the result
        assert result["success"] is False
        assert result["error"] is not None
        assert "validation" in result["error"].lower() or "required" in result["error"].lower()


@pytest.mark.asyncio
async def test_handler_service_error():
    """Test TTS handler when service throws an error."""
    event = {
        "user_id": "user123",
        "job_id": "job456",
        "tts_script": "Valid script",
        "voice_gender": "female",
    }

    with patch('src.workers.handlers.tts_handler.get_db') as mock_get_db, \
         patch('src.workers.handlers.tts_handler.get_storage') as mock_get_storage, \
         patch('src.workers.handlers.tts_handler.get_tts_service') as mock_get_service:

        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage

        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        # Mock the service to raise an exception
        mock_service.generate_speech.side_effect = Exception("TTS service unavailable")

        # Call the handler
        result = await handler(event, {})

        # Verify the result
        assert result["success"] is False
        assert result["error"] == "TTS service unavailable"


@pytest.mark.asyncio
async def test_job_status_updated():
    """Test that job status is updated during TTS handler execution."""
    event = {
        "user_id": "user123",
        "job_id": "job456",
        "tts_script": "Test script",
        "voice_gender": "female",
    }

    with patch('src.workers.handlers.tts_handler.get_db') as mock_get_db, \
         patch('src.workers.handlers.tts_handler.get_storage') as mock_get_storage, \
         patch('src.workers.handlers.tts_handler.get_tts_service') as mock_get_service:

        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage
        mock_storage.generate_audio_key.return_value = "user123/job456/voiceover.mp3"
        mock_storage.upload_file.return_value = "s3://bucket/user123/job456/voiceover.mp3"

        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        # Mock the TTS result
        mock_result = TTSResult(
            audio_data=b"fake audio data",
            content_type="audio/mpeg",
            provider_used=TTSProvider.POLLY,
            character_count=10,
            voice_id="voice123",
            duration_estimate_seconds=1.0
        )
        mock_service.generate_speech.return_value = mock_result

        # Call the handler
        await handler(event, {})

        # Verify that job status was updated to GENERATING_TTS
        mock_db.update_job_status.assert_any_call(
            user_id="user123",
            job_id="job456",
            status=JobStatus.GENERATING_TTS.value,
        )


@pytest.mark.asyncio
async def test_result_stored_in_job():
    """Test that TTS result is stored in job step output."""
    event = {
        "user_id": "user123",
        "job_id": "job456",
        "tts_script": "Test script",
        "voice_gender": "female",
    }

    with patch('src.workers.handlers.tts_handler.get_db') as mock_get_db, \
         patch('src.workers.handlers.tts_handler.get_storage') as mock_get_storage, \
         patch('src.workers.handlers.tts_handler.get_tts_service') as mock_get_service:

        # Setup mocks
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage
        mock_storage.generate_audio_key.return_value = "user123/job456/voiceover.mp3"
        mock_storage.upload_file.return_value = "s3://bucket/user123/job456/voiceover.mp3"

        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        # Mock the TTS result
        mock_result = TTSResult(
            audio_data=b"fake audio data",
            content_type="audio/mpeg",
            provider_used=TTSProvider.ELEVENLABS,
            character_count=20,
            voice_id="voice123",
            duration_estimate_seconds=2.0
        )
        mock_service.generate_speech.return_value = mock_result

        # Call the handler
        await handler(event, {})

        # Verify that job step output was updated with TTS metadata
        mock_db.update_job_step_output.assert_called_once()
        call_args = mock_db.update_job_step_output.call_args
        assert call_args.kwargs["user_id"] == "user123"
        assert call_args.kwargs["job_id"] == "job456"
        assert call_args.kwargs["step_name"] == "tts"
        
        output_data = call_args.kwargs["output"]
        assert output_data["provider_used"] == "elevenlabs"
        assert output_data["character_count"] == 20
        assert output_data["duration_estimate_seconds"] == 2.0
        assert output_data["audio_s3_key"] == "user123/job456/voiceover.mp3"