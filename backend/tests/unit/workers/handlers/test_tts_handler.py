"""Tests for TTS Lambda handler."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import ValidationError

from src.api.models.jobs import JobStatus
from src.workers.handlers.tts_handler import (
    TTSHandlerInput,
    TTSHandlerOutput,
    handler,
)
from src.workers.services.tts_models import TTSProvider, TTSResult


class TestTTSHandlerInput:
    """Tests for TTSHandlerInput model."""

    def test_valid_input_minimal(self) -> None:
        """Test valid input with minimal required fields."""
        input_data = TTSHandlerInput(
            user_id="user-123",
            job_id="job-456",
            tts_script="Hello world",
            voice_gender="female",
        )

        assert input_data.user_id == "user-123"
        assert input_data.job_id == "job-456"
        assert input_data.tts_script == "Hello world"
        assert input_data.voice_gender == "female"
        assert input_data.voice_style is None
        assert input_data.speaking_rate == 1.0
        assert input_data.provider == TTSProvider.AUTO
        assert input_data.tts_ssml is None

    def test_valid_input_all_fields(self) -> None:
        """Test valid input with all fields."""
        input_data = TTSHandlerInput(
            user_id="user-123",
            job_id="job-456",
            tts_script="Test script",
            tts_ssml="<speak>Test</speak>",
            voice_gender="male",
            voice_style="professional",
            speaking_rate=1.5,
            provider=TTSProvider.ELEVENLABS,
        )

        assert input_data.tts_ssml == "<speak>Test</speak>"
        assert input_data.voice_style == "professional"
        assert input_data.speaking_rate == 1.5
        assert input_data.provider == TTSProvider.ELEVENLABS

    def test_invalid_empty_script(self) -> None:
        """Test that empty script raises error."""
        with pytest.raises(ValidationError):
            TTSHandlerInput(
                user_id="user-123",
                job_id="job-456",
                tts_script="",
                voice_gender="female",
            )

    def test_invalid_gender(self) -> None:
        """Test that invalid gender raises error."""
        with pytest.raises(ValidationError):
            TTSHandlerInput(
                user_id="user-123",
                job_id="job-456",
                tts_script="Hello",
                voice_gender="other",
            )

    def test_invalid_speaking_rate_too_low(self) -> None:
        """Test that speaking rate below 0.5 raises error."""
        with pytest.raises(ValidationError):
            TTSHandlerInput(
                user_id="user-123",
                job_id="job-456",
                tts_script="Hello",
                voice_gender="female",
                speaking_rate=0.3,
            )

    def test_invalid_speaking_rate_too_high(self) -> None:
        """Test that speaking rate above 2.0 raises error."""
        with pytest.raises(ValidationError):
            TTSHandlerInput(
                user_id="user-123",
                job_id="job-456",
                tts_script="Hello",
                voice_gender="female",
                speaking_rate=2.5,
            )

    def test_missing_required_fields(self) -> None:
        """Test that missing required fields raises error."""
        with pytest.raises(ValidationError):
            TTSHandlerInput(
                user_id="user-123",
                job_id="job-456",
                # Missing tts_script and voice_gender
            )


class TestTTSHandlerOutput:
    """Tests for TTSHandlerOutput model."""

    def test_success_output(self) -> None:
        """Test successful output model."""
        output = TTSHandlerOutput(
            success=True,
            audio_s3_key="user/job/voiceover.mp3",
            audio_s3_url="s3://bucket/user/job/voiceover.mp3",
            provider_used="elevenlabs",
            character_count=100,
            duration_estimate_seconds=8.0,
        )

        assert output.success is True
        assert output.audio_s3_key == "user/job/voiceover.mp3"
        assert output.audio_s3_url == "s3://bucket/user/job/voiceover.mp3"
        assert output.provider_used == "elevenlabs"
        assert output.character_count == 100
        assert output.duration_estimate_seconds == 8.0
        assert output.error is None

    def test_error_output(self) -> None:
        """Test error output model."""
        output = TTSHandlerOutput(
            success=False,
            error="TTS generation failed",
        )

        assert output.success is False
        assert output.error == "TTS generation failed"
        assert output.audio_s3_key is None
        assert output.audio_s3_url is None
        assert output.provider_used is None


class TestHandler:
    """Tests for TTS Lambda handler function."""

    @pytest.mark.asyncio
    async def test_handler_success_with_plain_text(self) -> None:
        """Test successful handler execution with plain text."""
        event = {
            "user_id": "user-123",
            "job_id": "job-456",
            "tts_script": "This is a test script for TTS generation.",
            "voice_gender": "female",
            "voice_style": "professional",
            "speaking_rate": 1.2,
            "provider": "elevenlabs",
        }

        # Mock dependencies
        with patch("src.workers.handlers.tts_handler.get_db") as mock_get_db, \
             patch("src.workers.handlers.tts_handler.get_storage") as mock_get_storage, \
             patch("src.workers.handlers.tts_handler.get_tts_service") as mock_get_service:

            # Mock DB
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Mock Storage
            mock_storage = MagicMock()
            mock_storage.generate_audio_key.return_value = "user-123/job-456/voiceover.mp3"
            mock_storage.upload_file.return_value = "s3://videos/user-123/job-456/voiceover.mp3"
            mock_get_storage.return_value = mock_storage

            # Mock TTS Service
            mock_service = AsyncMock()
            mock_result = TTSResult(
                audio_data=b"fake audio data",
                content_type="audio/mpeg",
                provider_used=TTSProvider.ELEVENLABS,
                character_count=42,
                voice_id="voice-123",
                duration_estimate_seconds=3.36,
            )
            mock_service.generate_speech.return_value = mock_result
            mock_service.close = AsyncMock()
            mock_get_service.return_value = mock_service

            # Execute handler
            result = await handler(event, None)

            # Verify result
            assert result["success"] is True
            assert result["audio_s3_key"] == "user-123/job-456/voiceover.mp3"
            assert result["audio_s3_url"] == "s3://videos/user-123/job-456/voiceover.mp3"
            assert result["provider_used"] == "elevenlabs"
            assert result["character_count"] == 42
            assert result["duration_estimate_seconds"] == 3.36
            assert result["error"] is None

            # Verify DB calls
            mock_db.update_job_status.assert_called_once_with(
                user_id="user-123",
                job_id="job-456",
                status=JobStatus.GENERATING_TTS.value,
            )

            mock_db.update_job_step_output.assert_called_once()
            step_call = mock_db.update_job_step_output.call_args
            assert step_call.kwargs["user_id"] == "user-123"
            assert step_call.kwargs["job_id"] == "job-456"
            assert step_call.kwargs["step_name"] == "tts"
            assert step_call.kwargs["output"]["provider_used"] == "elevenlabs"

            # Verify Storage calls
            mock_storage.generate_audio_key.assert_called_once_with(
                user_id="user-123",
                job_id="job-456",
            )

            mock_storage.upload_file.assert_called_once_with(
                bucket_type="videos",
                key="user-123/job-456/voiceover.mp3",
                body=b"fake audio data",
                content_type="audio/mpeg",
            )

            # Verify TTS Service calls
            mock_service.generate_speech.assert_called_once()
            call_kwargs = mock_service.generate_speech.call_args.kwargs
            assert call_kwargs["text"] == "This is a test script for TTS generation."
            assert call_kwargs["use_ssml"] is False

            mock_service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_handler_success_with_ssml(self) -> None:
        """Test successful handler execution with SSML."""
        event = {
            "user_id": "user-123",
            "job_id": "job-456",
            "tts_script": "Plain text fallback",
            "tts_ssml": "<speak><prosody rate='fast'>Hello world</prosody></speak>",
            "voice_gender": "male",
            "provider": "polly",
        }

        with patch("src.workers.handlers.tts_handler.get_db") as mock_get_db, \
             patch("src.workers.handlers.tts_handler.get_storage") as mock_get_storage, \
             patch("src.workers.handlers.tts_handler.get_tts_service") as mock_get_service:

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_storage = MagicMock()
            mock_storage.generate_audio_key.return_value = "audio.mp3"
            mock_storage.upload_file.return_value = "s3://bucket/audio.mp3"
            mock_get_storage.return_value = mock_storage

            mock_service = AsyncMock()
            mock_result = TTSResult(
                audio_data=b"ssml audio",
                content_type="audio/mpeg",
                provider_used=TTSProvider.POLLY,
                character_count=30,
                voice_id="Matthew",
                duration_estimate_seconds=2.4,
            )
            mock_service.generate_speech.return_value = mock_result
            mock_service.close = AsyncMock()
            mock_get_service.return_value = mock_service

            result = await handler(event, None)

            assert result["success"] is True
            assert result["provider_used"] == "polly"

            # Verify SSML was used
            call_kwargs = mock_service.generate_speech.call_args.kwargs
            assert call_kwargs["text"] == "<speak><prosody rate='fast'>Hello world</prosody></speak>"
            assert call_kwargs["use_ssml"] is True

    @pytest.mark.asyncio
    async def test_handler_success_with_auto_provider(self) -> None:
        """Test handler with AUTO provider (fallback behavior)."""
        event = {
            "user_id": "user-123",
            "job_id": "job-456",
            "tts_script": "Test auto provider",
            "voice_gender": "female",
        }

        with patch("src.workers.handlers.tts_handler.get_db") as mock_get_db, \
             patch("src.workers.handlers.tts_handler.get_storage") as mock_get_storage, \
             patch("src.workers.handlers.tts_handler.get_tts_service") as mock_get_service:

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_storage = MagicMock()
            mock_storage.generate_audio_key.return_value = "audio.mp3"
            mock_storage.upload_file.return_value = "s3://bucket/audio.mp3"
            mock_get_storage.return_value = mock_storage

            # Mock that AUTO fell back to Polly
            mock_service = AsyncMock()
            mock_result = TTSResult(
                audio_data=b"auto fallback audio",
                content_type="audio/mpeg",
                provider_used=TTSProvider.POLLY,  # Fell back to Polly
                character_count=18,
                voice_id="Joanna",
                duration_estimate_seconds=1.44,
            )
            mock_service.generate_speech.return_value = mock_result
            mock_service.close = AsyncMock()
            mock_get_service.return_value = mock_service

            result = await handler(event, None)

            assert result["success"] is True
            assert result["provider_used"] == "polly"  # Used fallback

            # Verify AUTO provider was requested
            mock_get_service.assert_called_once_with(provider=TTSProvider.AUTO)

    @pytest.mark.asyncio
    async def test_handler_failure_invalid_input(self) -> None:
        """Test handler with invalid input."""
        event = {
            "user_id": "user-123",
            "job_id": "job-456",
            # Missing required tts_script and voice_gender
        }

        with patch("src.workers.handlers.tts_handler.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            result = await handler(event, None)

            assert result["success"] is False
            assert result["error"] is not None
            assert "validation" in result["error"].lower() or "required" in result["error"].lower()

            # Verify job was marked as failed
            mock_db.update_job_status.assert_called_once()
            call_kwargs = mock_db.update_job_status.call_args.kwargs
            assert call_kwargs["user_id"] == "user-123"
            assert call_kwargs["job_id"] == "job-456"
            assert call_kwargs["status"] == JobStatus.FAILED.value
            assert "TTS generation failed" in call_kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_handler_failure_tts_generation_error(self) -> None:
        """Test handler when TTS generation fails."""
        event = {
            "user_id": "user-123",
            "job_id": "job-456",
            "tts_script": "Test script",
            "voice_gender": "female",
        }

        with patch("src.workers.handlers.tts_handler.get_db") as mock_get_db, \
             patch("src.workers.handlers.tts_handler.get_storage") as mock_get_storage, \
             patch("src.workers.handlers.tts_handler.get_tts_service") as mock_get_service:

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_storage = MagicMock()
            mock_get_storage.return_value = mock_storage

            # Mock TTS service to raise error
            mock_service = AsyncMock()
            mock_service.generate_speech.side_effect = Exception("TTS API error")
            mock_service.close = AsyncMock()
            mock_get_service.return_value = mock_service

            result = await handler(event, None)

            assert result["success"] is False
            assert "TTS API error" in result["error"]

            # Verify job was updated to GENERATING_TTS then FAILED
            assert mock_db.update_job_status.call_count == 2
            calls = mock_db.update_job_status.call_args_list

            # First call: GENERATING_TTS
            assert calls[0].kwargs["status"] == JobStatus.GENERATING_TTS.value

            # Second call: FAILED
            assert calls[1].kwargs["status"] == JobStatus.FAILED.value
            assert "TTS generation failed" in calls[1].kwargs["error_message"]

            # Verify cleanup was called
            mock_service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_handler_failure_s3_upload_error(self) -> None:
        """Test handler when S3 upload fails."""
        event = {
            "user_id": "user-123",
            "job_id": "job-456",
            "tts_script": "Test script",
            "voice_gender": "male",
        }

        with patch("src.workers.handlers.tts_handler.get_db") as mock_get_db, \
             patch("src.workers.handlers.tts_handler.get_storage") as mock_get_storage, \
             patch("src.workers.handlers.tts_handler.get_tts_service") as mock_get_service:

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            # Mock storage to fail upload
            mock_storage = MagicMock()
            mock_storage.generate_audio_key.return_value = "audio.mp3"
            mock_storage.upload_file.side_effect = Exception("S3 upload failed")
            mock_get_storage.return_value = mock_storage

            mock_service = AsyncMock()
            mock_result = TTSResult(
                audio_data=b"audio",
                content_type="audio/mpeg",
                provider_used=TTSProvider.POLLY,
                character_count=10,
                voice_id="Matthew",
                duration_estimate_seconds=0.8,
            )
            mock_service.generate_speech.return_value = mock_result
            mock_service.close = AsyncMock()
            mock_get_service.return_value = mock_service

            result = await handler(event, None)

            assert result["success"] is False
            assert "S3 upload failed" in result["error"]

    @pytest.mark.asyncio
    async def test_handler_cleanup_on_success(self) -> None:
        """Test that TTS service is cleaned up on success."""
        event = {
            "user_id": "user-123",
            "job_id": "job-456",
            "tts_script": "Test",
            "voice_gender": "female",
        }

        with patch("src.workers.handlers.tts_handler.get_db") as mock_get_db, \
             patch("src.workers.handlers.tts_handler.get_storage") as mock_get_storage, \
             patch("src.workers.handlers.tts_handler.get_tts_service") as mock_get_service:

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_storage = MagicMock()
            mock_storage.generate_audio_key.return_value = "audio.mp3"
            mock_storage.upload_file.return_value = "s3://bucket/audio.mp3"
            mock_get_storage.return_value = mock_storage

            mock_service = AsyncMock()
            mock_result = TTSResult(
                audio_data=b"audio",
                content_type="audio/mpeg",
                provider_used=TTSProvider.ELEVENLABS,
                character_count=4,
                voice_id="Rachel",
                duration_estimate_seconds=0.32,
            )
            mock_service.generate_speech.return_value = mock_result
            mock_service.close = AsyncMock()
            mock_get_service.return_value = mock_service

            await handler(event, None)

            # Verify cleanup was called
            mock_service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_handler_cleanup_failure_is_logged(self) -> None:
        """Test that cleanup failures are logged but don't fail the handler."""
        event = {
            "user_id": "user-123",
            "job_id": "job-456",
            "tts_script": "Test",
            "voice_gender": "female",
        }

        with patch("src.workers.handlers.tts_handler.get_db") as mock_get_db, \
             patch("src.workers.handlers.tts_handler.get_storage") as mock_get_storage, \
             patch("src.workers.handlers.tts_handler.get_tts_service") as mock_get_service:

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_storage = MagicMock()
            mock_storage.generate_audio_key.return_value = "audio.mp3"
            mock_storage.upload_file.return_value = "s3://bucket/audio.mp3"
            mock_get_storage.return_value = mock_storage

            mock_service = AsyncMock()
            mock_result = TTSResult(
                audio_data=b"audio",
                content_type="audio/mpeg",
                provider_used=TTSProvider.POLLY,
                character_count=4,
                voice_id="Joanna",
                duration_estimate_seconds=0.32,
            )
            mock_service.generate_speech.return_value = mock_result
            # Make cleanup fail
            mock_service.close = AsyncMock(side_effect=Exception("Cleanup error"))
            mock_get_service.return_value = mock_service

            result = await handler(event, None)

            # Handler should still succeed
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_handler_with_different_speaking_rates(self) -> None:
        """Test handler with various speaking rates."""
        for rate in [0.5, 0.8, 1.0, 1.5, 2.0]:
            event = {
                "user_id": "user-123",
                "job_id": f"job-{rate}",
                "tts_script": "Test script",
                "voice_gender": "female",
                "speaking_rate": rate,
            }

            with patch("src.workers.handlers.tts_handler.get_db"), \
                 patch("src.workers.handlers.tts_handler.get_storage") as mock_get_storage, \
                 patch("src.workers.handlers.tts_handler.get_tts_service") as mock_get_service:

                mock_storage = MagicMock()
                mock_storage.generate_audio_key.return_value = "audio.mp3"
                mock_storage.upload_file.return_value = "s3://bucket/audio.mp3"
                mock_get_storage.return_value = mock_storage

                mock_service = AsyncMock()
                mock_result = TTSResult(
                    audio_data=b"audio",
                    content_type="audio/mpeg",
                    provider_used=TTSProvider.POLLY,
                    character_count=11,
                    voice_id="Joanna",
                    duration_estimate_seconds=0.88 / rate,
                )
                mock_service.generate_speech.return_value = mock_result
                mock_service.close = AsyncMock()
                mock_get_service.return_value = mock_service

                result = await handler(event, None)

                assert result["success"] is True

                # Verify voice config had correct speaking rate
                call_kwargs = mock_service.generate_speech.call_args.kwargs
                assert call_kwargs["voice_config"].speaking_rate == rate


class TestIntegration:
    """Integration tests for TTS handler."""

    @pytest.mark.asyncio
    async def test_full_workflow_female_elevenlabs(self) -> None:
        """Test complete workflow with female ElevenLabs voice."""
        event = {
            "user_id": "user-789",
            "job_id": "job-abc",
            "tts_script": "Welcome to our amazing product demonstration!",
            "voice_gender": "female",
            "voice_style": "energetic",
            "speaking_rate": 1.1,
            "provider": "elevenlabs",
        }

        with patch("src.workers.handlers.tts_handler.get_db") as mock_get_db, \
             patch("src.workers.handlers.tts_handler.get_storage") as mock_get_storage, \
             patch("src.workers.handlers.tts_handler.get_tts_service") as mock_get_service:

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_storage = MagicMock()
            mock_storage.generate_audio_key.return_value = "user-789/job-abc/voiceover.mp3"
            mock_storage.upload_file.return_value = "s3://ai-video-videos/user-789/job-abc/voiceover.mp3"
            mock_get_storage.return_value = mock_storage

            mock_service = AsyncMock()
            mock_result = TTSResult(
                audio_data=b"high quality female voice audio",
                content_type="audio/mpeg",
                provider_used=TTSProvider.ELEVENLABS,
                character_count=49,
                voice_id="EXAVITQu4vr4xnSDxMaL",  # Bella (energetic)
                duration_estimate_seconds=3.56,
            )
            mock_service.generate_speech.return_value = mock_result
            mock_service.close = AsyncMock()
            mock_get_service.return_value = mock_service

            result = await handler(event, None)

            # Verify complete workflow
            assert result["success"] is True
            assert result["provider_used"] == "elevenlabs"
            assert result["audio_s3_key"] == "user-789/job-abc/voiceover.mp3"
            assert result["character_count"] == 49
            assert result["duration_estimate_seconds"] == 3.56

            # Verify all steps were executed
            mock_db.update_job_status.assert_called_once()
            mock_db.update_job_step_output.assert_called_once()
            mock_storage.upload_file.assert_called_once()
            mock_service.generate_speech.assert_called_once()
            mock_service.close.assert_called_once()
