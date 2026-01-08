"""Tests for TTS service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.shared.exceptions import ElevenLabsError, PollyError
from src.workers.clients.elevenlabs_models import ElevenLabsVoice, TTSResponse
from src.workers.clients.polly_models import PollyTTSResponse, PollyVoice
from src.workers.services.tts_models import TTSProvider, TTSVoiceConfig
from src.workers.services.tts_service import TTSService, get_tts_service


class TestTTSServiceInit:
    """Tests for TTSService initialization."""

    def test_init_with_default_provider(self) -> None:
        """Test initialization with default AUTO provider."""
        service = TTSService()

        assert service.preferred_provider == TTSProvider.AUTO
        assert service._elevenlabs_client is None
        assert service._polly_client is None

    def test_init_with_elevenlabs_provider(self) -> None:
        """Test initialization with ElevenLabs provider."""
        service = TTSService(preferred_provider=TTSProvider.ELEVENLABS)

        assert service.preferred_provider == TTSProvider.ELEVENLABS

    def test_init_with_polly_provider(self) -> None:
        """Test initialization with Polly provider."""
        service = TTSService(preferred_provider=TTSProvider.POLLY)

        assert service.preferred_provider == TTSProvider.POLLY


class TestGetElevenLabsClient:
    """Tests for _get_elevenlabs_client method."""

    @pytest.mark.asyncio
    async def test_get_elevenlabs_client_success(self) -> None:
        """Test successful ElevenLabs client initialization."""
        service = TTSService()

        with patch("src.workers.services.tts_service.get_secrets") as mock_secrets, \
             patch("src.workers.services.tts_service.ElevenLabsClient") as mock_client_class:

            # Mock secrets retrieval
            mock_secrets_instance = MagicMock()
            mock_secrets_instance.get_secret.return_value = "test-api-key"
            mock_secrets.return_value = mock_secrets_instance

            # Mock client creation
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Get client
            client = await service._get_elevenlabs_client()

            # Verify
            assert client == mock_client
            assert service._elevenlabs_client == mock_client
            mock_secrets_instance.get_secret.assert_called_once()
            mock_client_class.assert_called_once_with(api_key="test-api-key")

    @pytest.mark.asyncio
    async def test_get_elevenlabs_client_caches_instance(self) -> None:
        """Test that ElevenLabs client is cached after first initialization."""
        service = TTSService()

        with patch("src.workers.services.tts_service.get_secrets") as mock_secrets, \
             patch("src.workers.services.tts_service.ElevenLabsClient") as mock_client_class:

            mock_secrets_instance = MagicMock()
            mock_secrets_instance.get_secret.return_value = "test-api-key"
            mock_secrets.return_value = mock_secrets_instance

            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Get client twice
            client1 = await service._get_elevenlabs_client()
            client2 = await service._get_elevenlabs_client()

            # Should return same instance
            assert client1 is client2
            # Client should only be created once
            mock_client_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_elevenlabs_client_failure(self) -> None:
        """Test ElevenLabs client initialization failure."""
        service = TTSService()

        with patch("src.workers.services.tts_service.get_secrets") as mock_secrets:
            mock_secrets_instance = MagicMock()
            mock_secrets_instance.get_secret.side_effect = Exception("Secret not found")
            mock_secrets.return_value = mock_secrets_instance

            with pytest.raises(ElevenLabsError) as exc_info:
                await service._get_elevenlabs_client()

            assert "Failed to initialize ElevenLabs client" in str(exc_info.value)


class TestGetPollyClient:
    """Tests for _get_polly_client method."""

    def test_get_polly_client_success(self) -> None:
        """Test successful Polly client retrieval."""
        service = TTSService()

        with patch("src.workers.services.tts_service.get_polly_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            client = service._get_polly_client()

            assert client == mock_client
            assert service._polly_client == mock_client
            mock_get_client.assert_called_once()

    def test_get_polly_client_caches_instance(self) -> None:
        """Test that Polly client is cached after first retrieval."""
        service = TTSService()

        with patch("src.workers.services.tts_service.get_polly_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            # Get client twice
            client1 = service._get_polly_client()
            client2 = service._get_polly_client()

            # Should return same instance
            assert client1 is client2
            # get_polly_client should only be called once
            mock_get_client.assert_called_once()


class TestGenerateElevenLabs:
    """Tests for _generate_elevenlabs method."""

    @pytest.mark.asyncio
    async def test_generate_elevenlabs_success_female(self) -> None:
        """Test successful ElevenLabs generation with female voice."""
        service = TTSService()
        config = TTSVoiceConfig(gender="female", style="professional")

        with patch.object(service, "_get_elevenlabs_client") as mock_get_client:
            # Mock client
            mock_client = AsyncMock()
            mock_response = TTSResponse(
                audio_data=b"fake audio",
                character_count=100,
                voice_id=ElevenLabsVoice.DOMI.value,
            )
            mock_client.text_to_speech.return_value = mock_response
            mock_get_client.return_value = mock_client

            # Generate speech
            result = await service._generate_elevenlabs("Hello world", config)

            # Verify result
            assert result.audio_data == b"fake audio"
            assert result.provider_used == TTSProvider.ELEVENLABS
            assert result.character_count == 100
            assert result.voice_id == ElevenLabsVoice.DOMI.value
            assert result.content_type == "audio/mpeg"
            assert result.duration_estimate_seconds == 8.0  # 100 / 12.5

    @pytest.mark.asyncio
    async def test_generate_elevenlabs_success_male(self) -> None:
        """Test successful ElevenLabs generation with male voice."""
        service = TTSService()
        config = TTSVoiceConfig(gender="male")

        with patch.object(service, "_get_elevenlabs_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = TTSResponse(
                audio_data=b"audio data",
                character_count=50,
                voice_id=ElevenLabsVoice.ADAM.value,
            )
            mock_client.text_to_speech.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await service._generate_elevenlabs("Test", config)

            assert result.provider_used == TTSProvider.ELEVENLABS
            assert result.character_count == 50
            assert result.duration_estimate_seconds == 4.0  # 50 / 12.5

    @pytest.mark.asyncio
    async def test_generate_elevenlabs_with_speaking_rate(self) -> None:
        """Test ElevenLabs generation with custom speaking rate."""
        service = TTSService()
        config = TTSVoiceConfig(gender="female", speaking_rate=2.0)

        with patch.object(service, "_get_elevenlabs_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = TTSResponse(
                audio_data=b"audio",
                character_count=100,
                voice_id=ElevenLabsVoice.RACHEL.value,
            )
            mock_client.text_to_speech.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await service._generate_elevenlabs("Text", config)

            # Duration should be adjusted for speaking rate
            assert result.duration_estimate_seconds == 4.0  # 100 / 12.5 / 2.0

    @pytest.mark.asyncio
    async def test_generate_elevenlabs_failure(self) -> None:
        """Test ElevenLabs generation failure."""
        service = TTSService()
        config = TTSVoiceConfig(gender="male")

        with patch.object(service, "_get_elevenlabs_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.text_to_speech.side_effect = ElevenLabsError("API error")
            mock_get_client.return_value = mock_client

            with pytest.raises(ElevenLabsError):
                await service._generate_elevenlabs("Text", config)


class TestGeneratePolly:
    """Tests for _generate_polly method."""

    @pytest.mark.asyncio
    async def test_generate_polly_success_female(self) -> None:
        """Test successful Polly generation with female voice."""
        service = TTSService()
        config = TTSVoiceConfig(gender="female")

        with patch.object(service, "_get_polly_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = PollyTTSResponse(
                audio_data=b"polly audio",
                request_characters=75,
                voice_id=PollyVoice.JOANNA.value,
            )
            mock_client.text_to_speech.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await service._generate_polly("Hello", config)

            assert result.audio_data == b"polly audio"
            assert result.provider_used == TTSProvider.POLLY
            assert result.character_count == 75
            assert result.voice_id == PollyVoice.JOANNA.value
            assert result.duration_estimate_seconds == 6.0  # 75 / 12.5

    @pytest.mark.asyncio
    async def test_generate_polly_success_male(self) -> None:
        """Test successful Polly generation with male voice."""
        service = TTSService()
        config = TTSVoiceConfig(gender="male")

        with patch.object(service, "_get_polly_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = PollyTTSResponse(
                audio_data=b"audio",
                request_characters=50,
                voice_id=PollyVoice.MATTHEW.value,
            )
            mock_client.text_to_speech.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await service._generate_polly("Test", config)

            assert result.voice_id == PollyVoice.MATTHEW.value
            assert result.character_count == 50

    @pytest.mark.asyncio
    async def test_generate_polly_with_ssml(self) -> None:
        """Test Polly generation with SSML."""
        service = TTSService()
        config = TTSVoiceConfig(gender="female")
        ssml_text = "<speak>Hello world</speak>"

        with patch.object(service, "_get_polly_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = PollyTTSResponse(
                audio_data=b"ssml audio",
                request_characters=30,
                voice_id=PollyVoice.JOANNA.value,
            )
            mock_client.text_to_speech.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await service._generate_polly(ssml_text, config, use_ssml=True)

            assert result.audio_data == b"ssml audio"
            mock_client.text_to_speech.assert_called_once_with(
                text=ssml_text,
                voice_id=PollyVoice.JOANNA.value,
                use_ssml=True,
            )

    @pytest.mark.asyncio
    async def test_generate_polly_with_speaking_rate(self) -> None:
        """Test Polly generation with custom speaking rate."""
        service = TTSService()
        config = TTSVoiceConfig(gender="male", speaking_rate=0.5)

        with patch.object(service, "_get_polly_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = PollyTTSResponse(
                audio_data=b"audio",
                request_characters=100,
                voice_id=PollyVoice.MATTHEW.value,
            )
            mock_client.text_to_speech.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await service._generate_polly("Text", config)

            # Duration should be adjusted for speaking rate
            assert result.duration_estimate_seconds == 16.0  # 100 / 12.5 / 0.5

    @pytest.mark.asyncio
    async def test_generate_polly_failure(self) -> None:
        """Test Polly generation failure."""
        service = TTSService()
        config = TTSVoiceConfig(gender="female")

        with patch.object(service, "_get_polly_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.text_to_speech.side_effect = PollyError("Polly error")
            mock_get_client.return_value = mock_client

            with pytest.raises(PollyError):
                await service._generate_polly("Text", config)


class TestGenerateWithFallback:
    """Tests for _generate_with_fallback method."""

    @pytest.mark.asyncio
    async def test_fallback_elevenlabs_success(self) -> None:
        """Test fallback when ElevenLabs succeeds."""
        service = TTSService()
        config = TTSVoiceConfig(gender="female")

        with patch.object(service, "_generate_elevenlabs") as mock_elevenlabs:
            mock_result = MagicMock()
            mock_result.provider_used = TTSProvider.ELEVENLABS
            mock_elevenlabs.return_value = mock_result

            result = await service._generate_with_fallback("Test", config)

            assert result.provider_used == TTSProvider.ELEVENLABS
            mock_elevenlabs.assert_called_once_with("Test", config)

    @pytest.mark.asyncio
    async def test_fallback_to_polly_on_elevenlabs_failure(self) -> None:
        """Test fallback to Polly when ElevenLabs fails."""
        service = TTSService()
        config = TTSVoiceConfig(gender="male")

        with patch.object(service, "_generate_elevenlabs") as mock_elevenlabs, \
             patch.object(service, "_generate_polly") as mock_polly:

            # ElevenLabs fails
            mock_elevenlabs.side_effect = ElevenLabsError("API error")

            # Polly succeeds
            mock_polly_result = MagicMock()
            mock_polly_result.provider_used = TTSProvider.POLLY
            mock_polly.return_value = mock_polly_result

            result = await service._generate_with_fallback("Test", config)

            assert result.provider_used == TTSProvider.POLLY
            mock_elevenlabs.assert_called_once()
            mock_polly.assert_called_once_with("Test", config, False)

    @pytest.mark.asyncio
    async def test_fallback_both_providers_fail(self) -> None:
        """Test fallback when both providers fail."""
        service = TTSService()
        config = TTSVoiceConfig(gender="female")

        with patch.object(service, "_generate_elevenlabs") as mock_elevenlabs, \
             patch.object(service, "_generate_polly") as mock_polly:

            # Both fail
            mock_elevenlabs.side_effect = ElevenLabsError("ElevenLabs error")
            mock_polly.side_effect = PollyError("Polly error")

            with pytest.raises(PollyError) as exc_info:
                await service._generate_with_fallback("Test", config)

            assert "Polly error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fallback_with_ssml(self) -> None:
        """Test fallback passes SSML flag to Polly."""
        service = TTSService()
        config = TTSVoiceConfig(gender="female")

        with patch.object(service, "_generate_elevenlabs") as mock_elevenlabs, \
             patch.object(service, "_generate_polly") as mock_polly:

            mock_elevenlabs.side_effect = ElevenLabsError("Error")
            mock_polly_result = MagicMock()
            mock_polly.return_value = mock_polly_result

            await service._generate_with_fallback("Text", config, use_ssml=True)

            mock_polly.assert_called_once_with("Text", config, True)


class TestGenerateSpeech:
    """Tests for generate_speech method."""

    @pytest.mark.asyncio
    async def test_generate_speech_elevenlabs_provider(self) -> None:
        """Test generate_speech with ELEVENLABS provider."""
        service = TTSService()
        config = TTSVoiceConfig(gender="female")

        with patch.object(service, "_generate_elevenlabs") as mock_generate:
            mock_result = MagicMock()
            mock_generate.return_value = mock_result

            result = await service.generate_speech(
                "Test",
                config,
                provider=TTSProvider.ELEVENLABS,
            )

            assert result == mock_result
            mock_generate.assert_called_once_with("Test", config)

    @pytest.mark.asyncio
    async def test_generate_speech_polly_provider(self) -> None:
        """Test generate_speech with POLLY provider."""
        service = TTSService()
        config = TTSVoiceConfig(gender="male")

        with patch.object(service, "_generate_polly") as mock_generate:
            mock_result = MagicMock()
            mock_generate.return_value = mock_result

            result = await service.generate_speech(
                "Test",
                config,
                provider=TTSProvider.POLLY,
            )

            assert result == mock_result
            mock_generate.assert_called_once_with("Test", config, False)

    @pytest.mark.asyncio
    async def test_generate_speech_auto_provider(self) -> None:
        """Test generate_speech with AUTO provider."""
        service = TTSService()
        config = TTSVoiceConfig(gender="female")

        with patch.object(service, "_generate_with_fallback") as mock_fallback:
            mock_result = MagicMock()
            mock_fallback.return_value = mock_result

            result = await service.generate_speech(
                "Test",
                config,
                provider=TTSProvider.AUTO,
            )

            assert result == mock_result
            mock_fallback.assert_called_once_with("Test", config, False)

    @pytest.mark.asyncio
    async def test_generate_speech_uses_preferred_provider(self) -> None:
        """Test generate_speech uses preferred provider when not specified."""
        service = TTSService(preferred_provider=TTSProvider.POLLY)
        config = TTSVoiceConfig(gender="female")

        with patch.object(service, "_generate_polly") as mock_generate:
            mock_result = MagicMock()
            mock_generate.return_value = mock_result

            result = await service.generate_speech("Test", config)

            assert result == mock_result
            mock_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_speech_with_ssml(self) -> None:
        """Test generate_speech with SSML flag."""
        service = TTSService()
        config = TTSVoiceConfig(gender="female")

        with patch.object(service, "_generate_polly") as mock_generate:
            mock_result = MagicMock()
            mock_generate.return_value = mock_result

            await service.generate_speech(
                "<speak>Test</speak>",
                config,
                provider=TTSProvider.POLLY,
                use_ssml=True,
            )

            mock_generate.assert_called_once_with("<speak>Test</speak>", config, True)


class TestClose:
    """Tests for close method."""

    @pytest.mark.asyncio
    async def test_close_with_elevenlabs_client(self) -> None:
        """Test close when ElevenLabs client exists."""
        service = TTSService()

        # Set up mock client
        mock_client = AsyncMock()
        service._elevenlabs_client = mock_client

        await service.close()

        mock_client.close.assert_called_once()
        assert service._elevenlabs_client is None
        assert service._polly_client is None

    @pytest.mark.asyncio
    async def test_close_without_clients(self) -> None:
        """Test close when no clients initialized."""
        service = TTSService()

        # Should not raise any errors
        await service.close()

        assert service._elevenlabs_client is None
        assert service._polly_client is None

    @pytest.mark.asyncio
    async def test_close_with_both_clients(self) -> None:
        """Test close with both clients initialized."""
        service = TTSService()

        mock_elevenlabs = AsyncMock()
        mock_polly = MagicMock()

        service._elevenlabs_client = mock_elevenlabs
        service._polly_client = mock_polly

        await service.close()

        mock_elevenlabs.close.assert_called_once()
        assert service._elevenlabs_client is None
        assert service._polly_client is None


class TestGetTTSService:
    """Tests for get_tts_service factory function."""

    def test_get_tts_service_default(self) -> None:
        """Test get_tts_service with default provider."""
        # Reset global singleton
        import src.workers.services.tts_service as tts_module
        tts_module._tts_service = None

        service = get_tts_service()

        assert isinstance(service, TTSService)
        assert service.preferred_provider == TTSProvider.AUTO

    def test_get_tts_service_with_provider(self) -> None:
        """Test get_tts_service with specific provider."""
        import src.workers.services.tts_service as tts_module
        tts_module._tts_service = None

        service = get_tts_service(TTSProvider.ELEVENLABS)

        assert isinstance(service, TTSService)
        assert service.preferred_provider == TTSProvider.ELEVENLABS

    def test_get_tts_service_singleton(self) -> None:
        """Test get_tts_service returns singleton."""
        import src.workers.services.tts_service as tts_module
        tts_module._tts_service = None

        service1 = get_tts_service()
        service2 = get_tts_service()

        assert service1 is service2


class TestIntegration:
    """Integration tests for TTS service."""

    @pytest.mark.asyncio
    async def test_full_workflow_elevenlabs(self) -> None:
        """Test complete workflow with ElevenLabs."""
        service = TTSService(preferred_provider=TTSProvider.ELEVENLABS)
        config = TTSVoiceConfig(
            gender="female",
            style="professional",
            speaking_rate=1.2,
        )

        with patch.object(service, "_get_elevenlabs_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = TTSResponse(
                audio_data=b"high quality audio",
                character_count=150,
                voice_id=ElevenLabsVoice.DOMI.value,
            )
            mock_client.text_to_speech.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await service.generate_speech("Professional voice test", config)

            assert result.provider_used == TTSProvider.ELEVENLABS
            assert result.character_count == 150
            assert result.audio_data == b"high quality audio"
            # 150 / 12.5 / 1.2 = 10.0
            assert result.duration_estimate_seconds == 10.0

    @pytest.mark.asyncio
    async def test_full_workflow_polly(self) -> None:
        """Test complete workflow with Polly."""
        service = TTSService(preferred_provider=TTSProvider.POLLY)
        config = TTSVoiceConfig(gender="male", speaking_rate=1.0)

        with patch.object(service, "_get_polly_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = PollyTTSResponse(
                audio_data=b"polly audio data",
                request_characters=125,
                voice_id=PollyVoice.MATTHEW.value,
            )
            mock_client.text_to_speech.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await service.generate_speech("Test text", config)

            assert result.provider_used == TTSProvider.POLLY
            assert result.character_count == 125
            # 125 / 12.5 = 10.0
            assert result.duration_estimate_seconds == 10.0

    @pytest.mark.asyncio
    async def test_full_workflow_auto_with_fallback(self) -> None:
        """Test complete workflow with AUTO and fallback."""
        service = TTSService(preferred_provider=TTSProvider.AUTO)
        config = TTSVoiceConfig(gender="female")

        with patch.object(service, "_get_elevenlabs_client") as mock_el_client, \
             patch.object(service, "_get_polly_client") as mock_polly_client:

            # ElevenLabs fails
            mock_el = AsyncMock()
            mock_el.text_to_speech.side_effect = ElevenLabsError("Rate limit")
            mock_el_client.return_value = mock_el

            # Polly succeeds
            mock_polly = AsyncMock()
            mock_polly_response = PollyTTSResponse(
                audio_data=b"fallback audio",
                request_characters=100,
                voice_id=PollyVoice.JOANNA.value,
            )
            mock_polly.text_to_speech.return_value = mock_polly_response
            mock_polly_client.return_value = mock_polly

            result = await service.generate_speech("Fallback test", config)

            # Should use Polly as fallback
            assert result.provider_used == TTSProvider.POLLY
            assert result.audio_data == b"fallback audio"
