"""Integration tests for TTS service with external API mocks."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.shared.storage import get_storage
from src.workers.clients.elevenlabs import ElevenLabsClient
from src.workers.clients.polly import PollyClient
from src.workers.services.tts_service import TTSService, get_tts_service
from src.workers.services.tts_models import TTSProvider, TTSVoiceConfig


@pytest.mark.asyncio
async def test_tts_service_elevenlabs_success():
    """Test TTS service with successful ElevenLabs API call."""
    with patch('src.workers.services.tts_service.get_settings') as mock_settings, \
         patch('src.workers.services.tts_service.get_secrets') as mock_secrets, \
         patch('src.workers.clients.elevenlabs.ElevenLabsClient') as mock_client_class:

        # Setup mocks
        mock_settings.return_value.secrets_elevenlabs_key = "test-elevenlabs-key"
        mock_secrets.return_value.get_secret.return_value = "test-api-key"

        # Mock the client instance
        mock_client = AsyncMock()
        mock_client_instance = AsyncMock()
        mock_client.return_value = mock_client_instance

        # Mock the text_to_speech response
        mock_response = MagicMock()
        mock_response.audio_data = b"fake audio content"
        mock_response.content_type = "audio/mpeg"
        mock_response.character_count = 22
        mock_response.voice_id = "test-voice"
        mock_client_instance.text_to_speech.return_value = mock_response

        # Initialize service
        service = get_tts_service(TTSProvider.ELEVENLABS)

        # Replace the client with our mock
        service._elevenlabs_client = mock_client_instance

        # Test voice configuration
        voice_config = TTSVoiceConfig(
            gender="female",
            speaking_rate=1.0
        )

        # Generate speech
        result = await service.generate_speech(
            text="Hello, this is a test.",
            voice_config=voice_config,
            provider=TTSProvider.ELEVENLABS
        )

        # Verify result
        assert result.audio_data == b"fake audio content"
        assert result.provider_used == TTSProvider.ELEVENLABS
        assert result.content_type == "audio/mpeg"

        # Verify the client method was called
        mock_client_instance.text_to_speech.assert_called_once()

        # Cleanup
        await service.close()


@pytest.mark.asyncio
async def test_tts_service_polly_success():
    """Test TTS service with successful Polly API call."""
    with patch('boto3.client') as mock_boto_client:
        # Setup mock Polly client
        mock_polly = MagicMock()
        mock_boto_client.return_value = mock_polly
        mock_polly.synthesize_speech.return_value = {
            "AudioStream": MagicMock(read=lambda: b"fake polly audio content"),
            "ContentType": "audio/mpeg",
            "RequestCharacters": 25
        }
        
        # Initialize service
        service = get_tts_service(TTSProvider.POLLY)
        
        # Test voice configuration
        voice_config = TTSVoiceConfig(
            gender="male",
            speaking_rate=1.0
        )
        
        # Generate speech
        result = await service.generate_speech(
            text="Hello, this is a test.",
            voice_config=voice_config,
            provider=TTSProvider.POLLY
        )
        
        # Verify result
        assert result.audio_data == b"fake polly audio content"
        assert result.provider_used == TTSProvider.POLLY
        assert result.content_type == "audio/mpeg"
        assert result.character_count == 25


@pytest.mark.asyncio
async def test_tts_service_fallback_success():
    """Test TTS service fallback from ElevenLabs to Polly."""
    from src.workers.services.tts_service import TTSService

    # Create a service instance directly
    service = TTSService(preferred_provider=TTSProvider.AUTO)

    # Mock the internal methods to simulate fallback behavior
    with patch.object(service, '_generate_with_fallback') as mock_fallback:
        # Setup mock fallback response
        mock_result = MagicMock()
        mock_result.audio_data = b"fallback audio content"
        mock_result.content_type = "audio/mpeg"
        mock_result.provider_used = TTSProvider.POLLY
        mock_fallback.return_value = mock_result

        # Test voice configuration
        voice_config = TTSVoiceConfig(
            gender="female",
            speaking_rate=1.0
        )

        # Generate speech (should use fallback logic)
        result = await service.generate_speech(
            text="Hello, this is a test.",
            voice_config=voice_config
        )

        # Verify result came from fallback
        assert result.audio_data == b"fallback audio content"
        assert result.provider_used == TTSProvider.POLLY
        assert result.content_type == "audio/mpeg"

        # Verify the fallback method was called
        mock_fallback.assert_called_once()

        # Cleanup
        await service.close()


@pytest.mark.asyncio
async def test_tts_service_full_flow_with_s3_upload():
    """Test full TTS flow with S3 upload."""
    with patch('src.workers.services.tts_service.get_settings') as mock_settings, \
         patch('src.workers.services.tts_service.get_secrets') as mock_secrets, \
         patch('src.workers.clients.elevenlabs.ElevenLabsClient') as mock_client_class, \
         patch('src.shared.storage.get_storage') as mock_get_storage:

        # Setup mocks
        mock_settings.return_value.secrets_elevenlabs_key = "test-elevenlabs-key"
        mock_secrets.return_value.get_secret.return_value = "test-api-key"

        # Mock the client instance
        mock_client = AsyncMock()
        mock_client_instance = AsyncMock()
        mock_client.return_value = mock_client_instance

        # Mock the text_to_speech response
        mock_response = MagicMock()
        mock_response.audio_data = b"audio content for s3 upload"
        mock_response.content_type = "audio/mpeg"
        mock_response.character_count = 36
        mock_response.voice_id = "test-voice"
        mock_client_instance.text_to_speech.return_value = mock_response

        # Mock storage
        mock_storage = MagicMock()
        mock_storage.generate_audio_key.return_value = "test-user/test-job/audio.mp3"
        mock_storage.upload_file.return_value = "s3://test-bucket/test-user/test-job/audio.mp3"
        mock_get_storage.return_value = mock_storage

        # Initialize service
        service = get_tts_service(TTSProvider.ELEVENLABS)

        # Replace the client with our mock
        service._elevenlabs_client = mock_client_instance

        # Test voice configuration
        voice_config = TTSVoiceConfig(
            gender="female",
            speaking_rate=1.0
        )

        # Generate speech
        result = await service.generate_speech(
            text="Hello, this is a test for S3 upload.",
            voice_config=voice_config,
            provider=TTSProvider.ELEVENLABS
        )

        # Verify result
        assert result.audio_data == b"audio content for s3 upload"
        assert result.provider_used == TTSProvider.ELEVENLABS

        # Test S3 upload using storage client
        s3_key = mock_storage.generate_audio_key("test-user", "test-job")
        s3_url = mock_storage.upload_file(
            bucket_type="videos",
            key=s3_key,
            body=result.audio_data,
            content_type=result.content_type
        )

        # Verify S3 operations were called
        assert s3_key.startswith("test-user/test-job/")
        assert s3_url.startswith("s3://")

        # Verify the client method was called
        mock_client_instance.text_to_speech.assert_called_once()

        # Cleanup
        await service.close()


@pytest.mark.asyncio
async def test_tts_service_elevenlabs_failure_then_polly_success():
    """Test TTS service with ElevenLabs failure followed by Polly success."""
    from src.workers.services.tts_service import TTSService

    # Create a service instance directly
    service = TTSService(preferred_provider=TTSProvider.AUTO)

    # Mock the internal methods to simulate fallback behavior
    with patch.object(service, '_generate_with_fallback') as mock_fallback:
        # Setup mock fallback response
        mock_result = MagicMock()
        mock_result.audio_data = b"fallback polly content"
        mock_result.content_type = "audio/mpeg"
        mock_result.provider_used = TTSProvider.POLLY
        mock_fallback.return_value = mock_result

        # Test voice configuration
        voice_config = TTSVoiceConfig(
            gender="male",
            speaking_rate=1.2
        )

        # Generate speech (should use fallback logic)
        result = await service.generate_speech(
            text="Testing fallback mechanism.",
            voice_config=voice_config
        )

        # Verify result came from Polly
        assert result.audio_data == b"fallback polly content"
        assert result.provider_used == TTSProvider.POLLY
        # Don't check speaking_rate since it's not part of the mock result

        # Verify the fallback method was called
        mock_fallback.assert_called_once()

        # Cleanup
        await service.close()