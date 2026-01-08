"""Tests for ElevenLabs TTS client."""
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.shared.exceptions import ElevenLabsError
from src.workers.clients.elevenlabs import ElevenLabsClient
from src.workers.clients.elevenlabs_models import (
    ElevenLabsVoice,
    TTSResponse,
    VoiceSettings,
)
from src.workers.clients.retry import RetryConfig


class TestElevenLabsClientInitialization:
    """Tests for ElevenLabsClient initialization."""

    def test_class_attributes(self) -> None:
        """Test that class attributes are set correctly."""
        assert ElevenLabsClient.service_name == "ElevenLabs"
        assert ElevenLabsClient.base_url == "https://api.elevenlabs.io/v1"
        assert ElevenLabsClient.default_timeout == 60.0

    def test_init_with_api_key(self) -> None:
        """Test initialization with API key."""
        client = ElevenLabsClient(api_key="test-api-key-123")

        assert client._api_key == "test-api-key-123"
        assert client._timeout == 60.0
        assert isinstance(client._retry_config, RetryConfig)

    def test_init_with_custom_timeout(self) -> None:
        """Test initialization with custom timeout."""
        client = ElevenLabsClient(api_key="test-key", timeout=120.0)

        assert client._timeout == 120.0

    def test_init_with_custom_retry_config(self) -> None:
        """Test initialization with custom retry config."""
        retry_config = RetryConfig(max_retries=5)
        client = ElevenLabsClient(api_key="test-key", retry_config=retry_config)

        assert client._retry_config.max_retries == 5


class TestHeaders:
    """Tests for headers property."""

    def test_headers_format(self) -> None:
        """Test that headers use xi-api-key instead of Bearer token."""
        client = ElevenLabsClient(api_key="secret-key-456")

        headers = client.headers

        assert "xi-api-key" in headers
        assert headers["xi-api-key"] == "secret-key-456"
        # Should NOT have Authorization header
        assert "Authorization" not in headers

    def test_headers_include_content_type(self) -> None:
        """Test that headers include content-type."""
        client = ElevenLabsClient(api_key="test-key")

        headers = client.headers

        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"

    def test_headers_include_accept(self) -> None:
        """Test that headers include Accept for audio."""
        client = ElevenLabsClient(api_key="test-key")

        headers = client.headers

        assert "Accept" in headers
        assert headers["Accept"] == "audio/mpeg"


class TestWrapException:
    """Tests for _wrap_exception method."""

    def test_wrap_exception_returns_elevenlabs_error(self) -> None:
        """Test that _wrap_exception returns ElevenLabsError."""
        client = ElevenLabsClient(api_key="test-key")

        original = ValueError("API request failed")
        wrapped = client._wrap_exception(original)

        assert isinstance(wrapped, ElevenLabsError)

    def test_wrap_exception_includes_message(self) -> None:
        """Test that wrapped exception includes original message."""
        client = ElevenLabsClient(api_key="test-key")

        original = RuntimeError("Rate limit exceeded")
        wrapped = client._wrap_exception(original)

        assert "Rate limit exceeded" in str(wrapped)


class TestTextToSpeech:
    """Tests for text_to_speech method."""

    @pytest.mark.asyncio
    async def test_text_to_speech_success(self) -> None:
        """Test successful text-to-speech conversion."""
        client = ElevenLabsClient(api_key="test-key")

        # Mock response
        mock_response = Mock(spec=httpx.Response)
        mock_response.content = b"fake audio data"
        mock_response.headers = {"content-type": "audio/mpeg"}

        # Mock the post method
        with patch.object(client, "post", return_value=mock_response) as mock_post:
            response = await client.text_to_speech(
                text="Hello world",
                voice_id=ElevenLabsVoice.RACHEL.value,
            )

            # Verify API was called correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert f"/text-to-speech/{ElevenLabsVoice.RACHEL.value}" in call_args[0]

            # Verify response
            assert isinstance(response, TTSResponse)
            assert response.audio_data == b"fake audio data"
            assert response.content_type == "audio/mpeg"
            assert response.character_count == 11  # len("Hello world")
            assert response.voice_id == ElevenLabsVoice.RACHEL.value

    @pytest.mark.asyncio
    async def test_text_to_speech_with_custom_voice_settings(self) -> None:
        """Test text-to-speech with custom voice settings."""
        client = ElevenLabsClient(api_key="test-key")

        mock_response = Mock(spec=httpx.Response)
        mock_response.content = b"audio data"
        mock_response.headers = {"content-type": "audio/mpeg"}

        custom_settings = VoiceSettings(
            stability=0.8,
            similarity_boost=0.9,
            style=0.5,
            use_speaker_boost=False,
        )

        with patch.object(client, "post", return_value=mock_response) as mock_post:
            response = await client.text_to_speech(
                text="Test",
                voice_id=ElevenLabsVoice.BELLA.value,
                voice_settings=custom_settings,
            )

            # Verify payload includes custom settings
            call_kwargs = mock_post.call_args.kwargs
            assert "json" in call_kwargs
            payload = call_kwargs["json"]
            assert payload["voice_settings"]["stability"] == 0.8
            assert payload["voice_settings"]["similarity_boost"] == 0.9
            assert payload["voice_settings"]["style"] == 0.5
            assert payload["voice_settings"]["use_speaker_boost"] is False

            assert isinstance(response, TTSResponse)

    @pytest.mark.asyncio
    async def test_text_to_speech_with_custom_model(self) -> None:
        """Test text-to-speech with custom model."""
        client = ElevenLabsClient(api_key="test-key")

        mock_response = Mock(spec=httpx.Response)
        mock_response.content = b"audio"
        mock_response.headers = {"content-type": "audio/mpeg"}

        with patch.object(client, "post", return_value=mock_response) as mock_post:
            await client.text_to_speech(
                text="Test",
                voice_id=ElevenLabsVoice.ADAM.value,
                model_id="eleven_monolingual_v1",
            )

            # Verify model_id in payload
            payload = mock_post.call_args.kwargs["json"]
            assert payload["model_id"] == "eleven_monolingual_v1"

    @pytest.mark.asyncio
    async def test_text_to_speech_default_voice_settings(self) -> None:
        """Test that default voice settings are used when not provided."""
        client = ElevenLabsClient(api_key="test-key")

        mock_response = Mock(spec=httpx.Response)
        mock_response.content = b"audio"
        mock_response.headers = {"content-type": "audio/mpeg"}

        with patch.object(client, "post", return_value=mock_response) as mock_post:
            await client.text_to_speech(
                text="Test",
                voice_id=ElevenLabsVoice.RACHEL.value,
            )

            # Verify default settings
            payload = mock_post.call_args.kwargs["json"]
            assert payload["voice_settings"]["stability"] == 0.5
            assert payload["voice_settings"]["similarity_boost"] == 0.75
            assert payload["voice_settings"]["style"] == 0.0
            assert payload["voice_settings"]["use_speaker_boost"] is True

    @pytest.mark.asyncio
    async def test_text_to_speech_endpoint_format(self) -> None:
        """Test that endpoint includes voice_id in path."""
        client = ElevenLabsClient(api_key="test-key")

        mock_response = Mock(spec=httpx.Response)
        mock_response.content = b"audio"
        mock_response.headers = {"content-type": "audio/mpeg"}

        with patch.object(client, "post", return_value=mock_response) as mock_post:
            await client.text_to_speech(
                text="Test",
                voice_id=ElevenLabsVoice.DOMI.value,
            )

            # Verify endpoint format
            endpoint = mock_post.call_args[0][0]
            assert endpoint == f"/text-to-speech/{ElevenLabsVoice.DOMI.value}"

    @pytest.mark.asyncio
    async def test_text_to_speech_uses_default_model(self) -> None:
        """Test that default model is eleven_multilingual_v2."""
        client = ElevenLabsClient(api_key="test-key")

        mock_response = Mock(spec=httpx.Response)
        mock_response.content = b"audio"
        mock_response.headers = {"content-type": "audio/mpeg"}

        with patch.object(client, "post", return_value=mock_response) as mock_post:
            await client.text_to_speech(
                text="Test",
                voice_id=ElevenLabsVoice.RACHEL.value,
            )

            payload = mock_post.call_args.kwargs["json"]
            assert payload["model_id"] == "eleven_multilingual_v2"

    @pytest.mark.asyncio
    async def test_text_to_speech_content_type_fallback(self) -> None:
        """Test content-type fallback when not in response headers."""
        client = ElevenLabsClient(api_key="test-key")

        mock_response = Mock(spec=httpx.Response)
        mock_response.content = b"audio"
        mock_response.headers = {}  # No content-type header

        with patch.object(client, "post", return_value=mock_response):
            response = await client.text_to_speech(
                text="Test",
                voice_id=ElevenLabsVoice.RACHEL.value,
            )

            # Should default to audio/mpeg
            assert response.content_type == "audio/mpeg"

    @pytest.mark.asyncio
    async def test_text_to_speech_character_count(self) -> None:
        """Test that character_count matches input text length."""
        client = ElevenLabsClient(api_key="test-key")

        mock_response = Mock(spec=httpx.Response)
        mock_response.content = b"audio"
        mock_response.headers = {"content-type": "audio/mpeg"}

        test_text = "This is a longer text for testing character count."

        with patch.object(client, "post", return_value=mock_response):
            response = await client.text_to_speech(
                text=test_text,
                voice_id=ElevenLabsVoice.RACHEL.value,
            )

            assert response.character_count == len(test_text)


class TestGetVoices:
    """Tests for get_voices method."""

    @pytest.mark.asyncio
    async def test_get_voices_success(self) -> None:
        """Test successful retrieval of voices."""
        client = ElevenLabsClient(api_key="test-key")

        mock_voices = [
            {"voice_id": "voice1", "name": "Rachel"},
            {"voice_id": "voice2", "name": "Adam"},
        ]

        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {"voices": mock_voices}

        with patch.object(client, "get", return_value=mock_response) as mock_get:
            voices = await client.get_voices()

            # Verify API was called
            mock_get.assert_called_once_with("/voices")

            # Verify response
            assert isinstance(voices, list)
            assert len(voices) == 2
            assert voices[0]["name"] == "Rachel"
            assert voices[1]["name"] == "Adam"

    @pytest.mark.asyncio
    async def test_get_voices_empty_list(self) -> None:
        """Test get_voices with empty voices list."""
        client = ElevenLabsClient(api_key="test-key")

        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {"voices": []}

        with patch.object(client, "get", return_value=mock_response):
            voices = await client.get_voices()

            assert voices == []

    @pytest.mark.asyncio
    async def test_get_voices_missing_voices_key(self) -> None:
        """Test get_voices when response doesn't have 'voices' key."""
        client = ElevenLabsClient(api_key="test-key")

        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {}  # No 'voices' key

        with patch.object(client, "get", return_value=mock_response):
            voices = await client.get_voices()

            # Should return empty list as fallback
            assert voices == []


class TestGetUserInfo:
    """Tests for get_user_info method."""

    @pytest.mark.asyncio
    async def test_get_user_info_success(self) -> None:
        """Test successful retrieval of user info."""
        client = ElevenLabsClient(api_key="test-key")

        mock_user_data = {
            "user_id": "user123",
            "character_count": 5000,
            "character_limit": 10000,
            "can_use_instant_voice_cloning": True,
        }

        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = mock_user_data

        with patch.object(client, "get", return_value=mock_response) as mock_get:
            user_info = await client.get_user_info()

            # Verify API was called
            mock_get.assert_called_once_with("/user")

            # Verify response
            assert isinstance(user_info, dict)
            assert user_info["user_id"] == "user123"
            assert user_info["character_count"] == 5000
            assert user_info["character_limit"] == 10000

    @pytest.mark.asyncio
    async def test_get_user_info_returns_dict(self) -> None:
        """Test that get_user_info returns dictionary."""
        client = ElevenLabsClient(api_key="test-key")

        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {"user_id": "test"}

        with patch.object(client, "get", return_value=mock_response):
            user_info = await client.get_user_info()

            assert isinstance(user_info, dict)


class TestContextManager:
    """Tests for async context manager usage."""

    @pytest.mark.asyncio
    async def test_context_manager_usage(self) -> None:
        """Test using ElevenLabsClient as context manager."""
        async with ElevenLabsClient(api_key="test-key") as client:
            assert client._api_key == "test-key"
            assert isinstance(client, ElevenLabsClient)

        # Client should be closed after context
        assert client._client is None


class TestIntegration:
    """Integration tests for ElevenLabs client."""

    @pytest.mark.asyncio
    async def test_full_workflow(self) -> None:
        """Test full workflow: init, TTS, get voices, get user info."""
        client = ElevenLabsClient(api_key="test-key")

        # Mock TTS
        mock_tts_response = Mock(spec=httpx.Response)
        mock_tts_response.content = b"audio data"
        mock_tts_response.headers = {"content-type": "audio/mpeg"}

        # Mock voices
        mock_voices_response = Mock(spec=httpx.Response)
        mock_voices_response.json.return_value = {
            "voices": [{"voice_id": "v1", "name": "Test Voice"}]
        }

        # Mock user info
        mock_user_response = Mock(spec=httpx.Response)
        mock_user_response.json.return_value = {
            "character_count": 100,
            "character_limit": 10000,
        }

        with patch.object(client, "post", return_value=mock_tts_response):
            with patch.object(client, "get") as mock_get:
                # Setup get to return different responses
                mock_get.side_effect = [mock_voices_response, mock_user_response]

                # Generate TTS
                tts_response = await client.text_to_speech(
                    text="Hello",
                    voice_id=ElevenLabsVoice.RACHEL.value,
                )
                assert tts_response.audio_data == b"audio data"

                # Get voices
                voices = await client.get_voices()
                assert len(voices) == 1

                # Get user info
                user_info = await client.get_user_info()
                assert user_info["character_count"] == 100

    @pytest.mark.asyncio
    async def test_with_all_voices(self) -> None:
        """Test TTS works with all voice enum values."""
        client = ElevenLabsClient(api_key="test-key")

        mock_response = Mock(spec=httpx.Response)
        mock_response.content = b"audio"
        mock_response.headers = {"content-type": "audio/mpeg"}

        with patch.object(client, "post", return_value=mock_response):
            for voice in ElevenLabsVoice:
                response = await client.text_to_speech(
                    text="Test",
                    voice_id=voice.value,
                )

                assert response.voice_id == voice.value
                assert isinstance(response, TTSResponse)

    @pytest.mark.asyncio
    async def test_voice_selection_integration(self) -> None:
        """Test integration with voice selection."""
        client = ElevenLabsClient(api_key="test-key")

        mock_response = Mock(spec=httpx.Response)
        mock_response.content = b"audio"
        mock_response.headers = {"content-type": "audio/mpeg"}

        # Use voice selection to pick a voice
        voice_id = ElevenLabsVoice.select_voice("female", "energetic")

        with patch.object(client, "post", return_value=mock_response):
            response = await client.text_to_speech(
                text="Check this out!",
                voice_id=voice_id,
            )

            # Should use BELLA for energetic female
            assert response.voice_id == ElevenLabsVoice.BELLA.value
