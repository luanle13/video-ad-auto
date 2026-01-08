"""Tests for TTS service models."""
import pytest
from pydantic import ValidationError

from src.workers.services.tts_models import (
    CHARS_PER_SECOND,
    TTSProvider,
    TTSResult,
    TTSVoiceConfig,
)


class TestConstants:
    """Tests for module constants."""

    def test_chars_per_second_constant(self) -> None:
        """Test that CHARS_PER_SECOND is defined correctly."""
        assert CHARS_PER_SECOND == 12.5

    def test_chars_per_second_is_float(self) -> None:
        """Test that CHARS_PER_SECOND is a float."""
        assert isinstance(CHARS_PER_SECOND, float)


class TestTTSProvider:
    """Tests for TTSProvider enum."""

    def test_all_providers_defined(self) -> None:
        """Test that all 3 providers are defined."""
        assert len(TTSProvider) == 3
        assert TTSProvider.ELEVENLABS
        assert TTSProvider.POLLY
        assert TTSProvider.AUTO

    def test_elevenlabs_value(self) -> None:
        """Test ELEVENLABS provider value."""
        assert TTSProvider.ELEVENLABS.value == "elevenlabs"

    def test_polly_value(self) -> None:
        """Test POLLY provider value."""
        assert TTSProvider.POLLY.value == "polly"

    def test_auto_value(self) -> None:
        """Test AUTO provider value."""
        assert TTSProvider.AUTO.value == "auto"

    def test_provider_enum_is_string(self) -> None:
        """Test that provider enum inherits from str."""
        provider = TTSProvider.ELEVENLABS
        assert isinstance(provider, str)
        assert isinstance(provider.value, str)


class TestTTSVoiceConfig:
    """Tests for TTSVoiceConfig model."""

    def test_valid_config_male(self) -> None:
        """Test creating valid male voice config."""
        config = TTSVoiceConfig(gender="male")

        assert config.gender == "male"
        assert config.style is None
        assert config.speaking_rate == 1.0

    def test_valid_config_female(self) -> None:
        """Test creating valid female voice config."""
        config = TTSVoiceConfig(gender="female")

        assert config.gender == "female"
        assert config.style is None
        assert config.speaking_rate == 1.0

    def test_config_with_style(self) -> None:
        """Test config with style parameter."""
        config = TTSVoiceConfig(gender="male", style="professional")

        assert config.style == "professional"

    def test_config_with_speaking_rate(self) -> None:
        """Test config with custom speaking rate."""
        config = TTSVoiceConfig(gender="female", speaking_rate=1.5)

        assert config.speaking_rate == 1.5

    def test_config_with_all_parameters(self) -> None:
        """Test config with all parameters."""
        config = TTSVoiceConfig(
            gender="male",
            style="energetic",
            speaking_rate=0.8,
        )

        assert config.gender == "male"
        assert config.style == "energetic"
        assert config.speaking_rate == 0.8

    def test_speaking_rate_minimum(self) -> None:
        """Test speaking rate minimum value of 0.5."""
        config = TTSVoiceConfig(gender="male", speaking_rate=0.5)
        assert config.speaking_rate == 0.5

    def test_speaking_rate_maximum(self) -> None:
        """Test speaking rate maximum value of 2.0."""
        config = TTSVoiceConfig(gender="female", speaking_rate=2.0)
        assert config.speaking_rate == 2.0

    def test_speaking_rate_below_minimum_raises_error(self) -> None:
        """Test that speaking rate below 0.5 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            TTSVoiceConfig(gender="male", speaking_rate=0.4)

        assert "greater than or equal to 0.5" in str(exc_info.value).lower()

    def test_speaking_rate_above_maximum_raises_error(self) -> None:
        """Test that speaking rate above 2.0 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            TTSVoiceConfig(gender="female", speaking_rate=2.1)

        assert "less than or equal to 2" in str(exc_info.value).lower()

    def test_invalid_gender_raises_error(self) -> None:
        """Test that invalid gender raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            TTSVoiceConfig(gender="other")

        assert "string should match pattern" in str(exc_info.value).lower()

    def test_gender_required(self) -> None:
        """Test that gender is required."""
        with pytest.raises(ValidationError):
            TTSVoiceConfig()  # type: ignore

    def test_gender_case_sensitive(self) -> None:
        """Test that gender is case-sensitive."""
        # Valid lowercase
        config = TTSVoiceConfig(gender="male")
        assert config.gender == "male"

        # Invalid uppercase
        with pytest.raises(ValidationError):
            TTSVoiceConfig(gender="MALE")

    def test_style_optional(self) -> None:
        """Test that style is optional."""
        config = TTSVoiceConfig(gender="female")
        assert config.style is None

    def test_speaking_rate_default(self) -> None:
        """Test default speaking rate is 1.0."""
        config = TTSVoiceConfig(gender="male")
        assert config.speaking_rate == 1.0


class TestTTSResult:
    """Tests for TTSResult model."""

    def test_valid_result(self) -> None:
        """Test creating valid TTS result."""
        audio = b"fake audio data"

        result = TTSResult(
            audio_data=audio,
            provider_used=TTSProvider.ELEVENLABS,
            character_count=100,
            voice_id="voice-123",
            duration_estimate_seconds=8.0,
        )

        assert result.audio_data == audio
        assert result.content_type == "audio/mpeg"
        assert result.provider_used == TTSProvider.ELEVENLABS
        assert result.character_count == 100
        assert result.voice_id == "voice-123"
        assert result.duration_estimate_seconds == 8.0

    def test_result_with_custom_content_type(self) -> None:
        """Test result with custom content type."""
        result = TTSResult(
            audio_data=b"data",
            content_type="audio/ogg",
            provider_used=TTSProvider.POLLY,
            character_count=50,
            voice_id="voice-456",
            duration_estimate_seconds=4.0,
        )

        assert result.content_type == "audio/ogg"

    def test_result_default_content_type(self) -> None:
        """Test default content type is audio/mpeg."""
        result = TTSResult(
            audio_data=b"data",
            provider_used=TTSProvider.AUTO,
            character_count=25,
            voice_id="voice-789",
            duration_estimate_seconds=2.0,
        )

        assert result.content_type == "audio/mpeg"

    def test_character_count_zero(self) -> None:
        """Test character count can be zero."""
        result = TTSResult(
            audio_data=b"",
            provider_used=TTSProvider.POLLY,
            character_count=0,
            voice_id="voice-id",
            duration_estimate_seconds=0.0,
        )

        assert result.character_count == 0

    def test_character_count_negative_raises_error(self) -> None:
        """Test that negative character count raises error."""
        with pytest.raises(ValidationError) as exc_info:
            TTSResult(
                audio_data=b"data",
                provider_used=TTSProvider.ELEVENLABS,
                character_count=-1,
                voice_id="voice-id",
                duration_estimate_seconds=1.0,
            )

        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_duration_zero(self) -> None:
        """Test duration can be zero."""
        result = TTSResult(
            audio_data=b"",
            provider_used=TTSProvider.POLLY,
            character_count=0,
            voice_id="voice-id",
            duration_estimate_seconds=0.0,
        )

        assert result.duration_estimate_seconds == 0.0

    def test_duration_negative_raises_error(self) -> None:
        """Test that negative duration raises error."""
        with pytest.raises(ValidationError) as exc_info:
            TTSResult(
                audio_data=b"data",
                provider_used=TTSProvider.ELEVENLABS,
                character_count=100,
                voice_id="voice-id",
                duration_estimate_seconds=-1.0,
            )

        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_audio_data_required(self) -> None:
        """Test that audio_data is required."""
        with pytest.raises(ValidationError):
            TTSResult(  # type: ignore
                provider_used=TTSProvider.POLLY,
                character_count=100,
                voice_id="voice-id",
                duration_estimate_seconds=8.0,
            )

    def test_provider_used_required(self) -> None:
        """Test that provider_used is required."""
        with pytest.raises(ValidationError):
            TTSResult(  # type: ignore
                audio_data=b"data",
                character_count=100,
                voice_id="voice-id",
                duration_estimate_seconds=8.0,
            )

    def test_character_count_required(self) -> None:
        """Test that character_count is required."""
        with pytest.raises(ValidationError):
            TTSResult(  # type: ignore
                audio_data=b"data",
                provider_used=TTSProvider.POLLY,
                voice_id="voice-id",
                duration_estimate_seconds=8.0,
            )

    def test_voice_id_required(self) -> None:
        """Test that voice_id is required."""
        with pytest.raises(ValidationError):
            TTSResult(  # type: ignore
                audio_data=b"data",
                provider_used=TTSProvider.POLLY,
                character_count=100,
                duration_estimate_seconds=8.0,
            )

    def test_duration_required(self) -> None:
        """Test that duration_estimate_seconds is required."""
        with pytest.raises(ValidationError):
            TTSResult(  # type: ignore
                audio_data=b"data",
                provider_used=TTSProvider.POLLY,
                character_count=100,
                voice_id="voice-id",
            )

    def test_with_all_providers(self) -> None:
        """Test result works with all provider types."""
        for provider in TTSProvider:
            result = TTSResult(
                audio_data=b"test",
                provider_used=provider,
                character_count=10,
                voice_id="voice-id",
                duration_estimate_seconds=0.8,
            )

            assert result.provider_used == provider


class TestEstimateDuration:
    """Tests for TTSResult.estimate_duration static method."""

    def test_estimate_duration_normal_rate(self) -> None:
        """Test duration estimation at normal speaking rate."""
        duration = TTSResult.estimate_duration(125, 1.0)

        # 125 chars / 12.5 chars/sec = 10 seconds
        assert duration == 10.0

    def test_estimate_duration_fast_rate(self) -> None:
        """Test duration estimation at faster speaking rate."""
        duration = TTSResult.estimate_duration(125, 2.0)

        # 125 chars / 12.5 chars/sec / 2.0 = 5 seconds
        assert duration == 5.0

    def test_estimate_duration_slow_rate(self) -> None:
        """Test duration estimation at slower speaking rate."""
        duration = TTSResult.estimate_duration(125, 0.5)

        # 125 chars / 12.5 chars/sec / 0.5 = 20 seconds
        assert duration == 20.0

    def test_estimate_duration_zero_characters(self) -> None:
        """Test duration estimation with zero characters."""
        duration = TTSResult.estimate_duration(0, 1.0)
        assert duration == 0.0

    def test_estimate_duration_negative_characters(self) -> None:
        """Test duration estimation with negative characters."""
        duration = TTSResult.estimate_duration(-10, 1.0)
        assert duration == 0.0

    def test_estimate_duration_zero_rate(self) -> None:
        """Test duration estimation with zero speaking rate."""
        duration = TTSResult.estimate_duration(100, 0.0)
        assert duration == 0.0

    def test_estimate_duration_various_rates(self) -> None:
        """Test duration estimation with various speaking rates."""
        char_count = 100

        # Normal rate
        assert TTSResult.estimate_duration(char_count, 1.0) == 8.0

        # Slightly faster
        assert TTSResult.estimate_duration(char_count, 1.25) == 6.4

        # Slightly slower
        assert TTSResult.estimate_duration(char_count, 0.8) == 10.0

    def test_estimate_duration_short_text(self) -> None:
        """Test duration estimation for short text."""
        duration = TTSResult.estimate_duration(25, 1.0)

        # 25 chars / 12.5 chars/sec = 2 seconds
        assert duration == 2.0

    def test_estimate_duration_long_text(self) -> None:
        """Test duration estimation for long text."""
        duration = TTSResult.estimate_duration(1250, 1.0)

        # 1250 chars / 12.5 chars/sec = 100 seconds
        assert duration == 100.0

    def test_estimate_duration_uses_constant(self) -> None:
        """Test that estimation uses CHARS_PER_SECOND constant."""
        char_count = 50
        expected = char_count / CHARS_PER_SECOND

        duration = TTSResult.estimate_duration(char_count, 1.0)

        assert duration == expected


class TestIntegration:
    """Integration tests for TTS models."""

    def test_voice_config_with_result(self) -> None:
        """Test using voice config with result."""
        # Create config
        config = TTSVoiceConfig(
            gender="female",
            style="professional",
            speaking_rate=1.2,
        )

        # Calculate duration
        char_count = 150
        duration = TTSResult.estimate_duration(char_count, config.speaking_rate)

        # Create result
        result = TTSResult(
            audio_data=b"audio data",
            provider_used=TTSProvider.ELEVENLABS,
            character_count=char_count,
            voice_id="voice-123",
            duration_estimate_seconds=duration,
        )

        # Verify
        assert result.character_count == char_count
        assert result.duration_estimate_seconds == duration
        # 150 / 12.5 / 1.2 = 10.0
        assert result.duration_estimate_seconds == 10.0

    def test_provider_selection_workflow(self) -> None:
        """Test workflow with different providers."""
        configs = [
            (TTSProvider.ELEVENLABS, "Premium voice"),
            (TTSProvider.POLLY, "Fallback voice"),
            (TTSProvider.AUTO, "Auto-selected voice"),
        ]

        for provider, voice_id in configs:
            result = TTSResult(
                audio_data=b"test audio",
                provider_used=provider,
                character_count=50,
                voice_id=voice_id,
                duration_estimate_seconds=4.0,
            )

            assert result.provider_used == provider
            assert result.voice_id == voice_id

    def test_duration_accuracy(self) -> None:
        """Test duration estimation accuracy."""
        # Simulate a 30-second audio clip
        # At 12.5 chars/sec, that's 375 characters
        char_count = 375
        speaking_rate = 1.0

        duration = TTSResult.estimate_duration(char_count, speaking_rate)

        assert duration == 30.0

        # Create result
        result = TTSResult(
            audio_data=b"audio" * 100,
            provider_used=TTSProvider.POLLY,
            character_count=char_count,
            voice_id="Joanna",
            duration_estimate_seconds=duration,
        )

        assert result.duration_estimate_seconds == 30.0

    def test_fast_speech_estimation(self) -> None:
        """Test duration estimation for fast speech."""
        config = TTSVoiceConfig(gender="male", speaking_rate=1.8)

        char_count = 225  # Would be 18 seconds at normal rate
        duration = TTSResult.estimate_duration(char_count, config.speaking_rate)

        # 225 / 12.5 / 1.8 = 10.0 seconds
        assert duration == 10.0

    def test_slow_speech_estimation(self) -> None:
        """Test duration estimation for slow speech."""
        config = TTSVoiceConfig(gender="female", speaking_rate=0.6)

        char_count = 75  # Would be 6 seconds at normal rate
        duration = TTSResult.estimate_duration(char_count, config.speaking_rate)

        # 75 / 12.5 / 0.6 = 10.0 seconds
        assert duration == 10.0
