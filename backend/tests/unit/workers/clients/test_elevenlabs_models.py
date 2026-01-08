"""Tests for ElevenLabs models and enums."""
import pytest
from pydantic import ValidationError

from src.workers.clients.elevenlabs_models import (
    ElevenLabsVoice,
    TTSRequest,
    TTSResponse,
    VoiceSettings,
)


class TestElevenLabsVoice:
    """Tests for ElevenLabsVoice enum."""

    def test_all_voices_defined(self) -> None:
        """Test that all 8 voices are defined."""
        assert len(ElevenLabsVoice) == 8

        # Verify all expected voices exist
        assert ElevenLabsVoice.RACHEL
        assert ElevenLabsVoice.DOMI
        assert ElevenLabsVoice.BELLA
        assert ElevenLabsVoice.ELLI
        assert ElevenLabsVoice.ADAM
        assert ElevenLabsVoice.ANTONI
        assert ElevenLabsVoice.JOSH
        assert ElevenLabsVoice.ARNOLD

    def test_voice_ids_are_valid_format(self) -> None:
        """Test that voice IDs are non-empty strings."""
        for voice in ElevenLabsVoice:
            assert isinstance(voice.value, str)
            assert len(voice.value) > 0
            # ElevenLabs voice IDs are typically 20 characters
            assert len(voice.value) == 20

    def test_rachel_voice_id(self) -> None:
        """Test RACHEL voice ID."""
        assert ElevenLabsVoice.RACHEL.value == "21m00Tcm4TlvDq8ikWAM"

    def test_domi_voice_id(self) -> None:
        """Test DOMI voice ID."""
        assert ElevenLabsVoice.DOMI.value == "AZnzlk1XvdvUeBnXmlld"

    def test_bella_voice_id(self) -> None:
        """Test BELLA voice ID."""
        assert ElevenLabsVoice.BELLA.value == "EXAVITQu4vr4xnSDxMaL"

    def test_elli_voice_id(self) -> None:
        """Test ELLI voice ID."""
        assert ElevenLabsVoice.ELLI.value == "MF3mGyEYCl7XYWbV9V6O"

    def test_adam_voice_id(self) -> None:
        """Test ADAM voice ID."""
        assert ElevenLabsVoice.ADAM.value == "pNInz6obpgDQGcFmaJgB"

    def test_antoni_voice_id(self) -> None:
        """Test ANTONI voice ID."""
        assert ElevenLabsVoice.ANTONI.value == "ErXwobaYiN019PkySvjV"

    def test_josh_voice_id(self) -> None:
        """Test JOSH voice ID."""
        assert ElevenLabsVoice.JOSH.value == "TxGEqnHWrfWFTfGW9XjX"

    def test_arnold_voice_id(self) -> None:
        """Test ARNOLD voice ID."""
        assert ElevenLabsVoice.ARNOLD.value == "VR6AewLTigWG4xSOukaG"

    def test_voice_enum_is_string(self) -> None:
        """Test that voice enum inherits from str."""
        voice = ElevenLabsVoice.RACHEL
        assert isinstance(voice, str)
        assert isinstance(voice.value, str)


class TestSelectVoice:
    """Tests for ElevenLabsVoice.select_voice method."""

    def test_select_female_default(self) -> None:
        """Test selecting default female voice."""
        voice_id = ElevenLabsVoice.select_voice("female")
        assert voice_id == ElevenLabsVoice.RACHEL.value

    def test_select_male_default(self) -> None:
        """Test selecting default male voice."""
        voice_id = ElevenLabsVoice.select_voice("male")
        assert voice_id == ElevenLabsVoice.ADAM.value

    def test_select_female_energetic(self) -> None:
        """Test selecting energetic female voice."""
        voice_id = ElevenLabsVoice.select_voice("female", "energetic")
        assert voice_id == ElevenLabsVoice.BELLA.value

    def test_select_female_professional(self) -> None:
        """Test selecting professional female voice."""
        voice_id = ElevenLabsVoice.select_voice("female", "professional")
        assert voice_id == ElevenLabsVoice.DOMI.value

    def test_select_female_casual(self) -> None:
        """Test selecting casual female voice."""
        voice_id = ElevenLabsVoice.select_voice("female", "casual")
        assert voice_id == ElevenLabsVoice.ELLI.value

    def test_select_female_friendly(self) -> None:
        """Test selecting friendly female voice."""
        voice_id = ElevenLabsVoice.select_voice("female", "friendly")
        assert voice_id == ElevenLabsVoice.ELLI.value

    def test_select_female_narrative(self) -> None:
        """Test selecting narrative female voice."""
        voice_id = ElevenLabsVoice.select_voice("female", "narrative")
        assert voice_id == ElevenLabsVoice.RACHEL.value

    def test_select_male_professional(self) -> None:
        """Test selecting professional male voice."""
        voice_id = ElevenLabsVoice.select_voice("male", "professional")
        assert voice_id == ElevenLabsVoice.ANTONI.value

    def test_select_male_casual(self) -> None:
        """Test selecting casual male voice."""
        voice_id = ElevenLabsVoice.select_voice("male", "casual")
        assert voice_id == ElevenLabsVoice.JOSH.value

    def test_select_male_authoritative(self) -> None:
        """Test selecting authoritative male voice."""
        voice_id = ElevenLabsVoice.select_voice("male", "authoritative")
        assert voice_id == ElevenLabsVoice.ARNOLD.value

    def test_select_male_confident(self) -> None:
        """Test selecting confident male voice."""
        voice_id = ElevenLabsVoice.select_voice("male", "confident")
        assert voice_id == ElevenLabsVoice.ARNOLD.value

    def test_select_case_insensitive_gender(self) -> None:
        """Test that gender is case-insensitive."""
        assert ElevenLabsVoice.select_voice("FEMALE") == ElevenLabsVoice.RACHEL.value
        assert ElevenLabsVoice.select_voice("Male") == ElevenLabsVoice.ADAM.value
        assert ElevenLabsVoice.select_voice("FeMaLe") == ElevenLabsVoice.RACHEL.value

    def test_select_case_insensitive_style(self) -> None:
        """Test that style is case-insensitive."""
        assert (
            ElevenLabsVoice.select_voice("female", "ENERGETIC")
            == ElevenLabsVoice.BELLA.value
        )
        assert (
            ElevenLabsVoice.select_voice("male", "Professional")
            == ElevenLabsVoice.ANTONI.value
        )

    def test_select_female_unknown_style(self) -> None:
        """Test selecting female voice with unknown style defaults to RACHEL."""
        voice_id = ElevenLabsVoice.select_voice("female", "unknown_style")
        assert voice_id == ElevenLabsVoice.RACHEL.value

    def test_select_male_unknown_style(self) -> None:
        """Test selecting male voice with unknown style defaults to ADAM."""
        voice_id = ElevenLabsVoice.select_voice("male", "unknown_style")
        assert voice_id == ElevenLabsVoice.ADAM.value

    def test_select_invalid_gender_raises_error(self) -> None:
        """Test that invalid gender raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ElevenLabsVoice.select_voice("other")

        assert "Invalid gender" in str(exc_info.value)
        assert "must be 'male' or 'female'" in str(exc_info.value).lower()

    def test_select_empty_gender_raises_error(self) -> None:
        """Test that empty gender raises ValueError."""
        with pytest.raises(ValueError):
            ElevenLabsVoice.select_voice("")

    def test_select_none_style_uses_default(self) -> None:
        """Test that None style uses default voice."""
        assert ElevenLabsVoice.select_voice("female", None) == ElevenLabsVoice.RACHEL.value
        assert ElevenLabsVoice.select_voice("male", None) == ElevenLabsVoice.ADAM.value


class TestVoiceSettings:
    """Tests for VoiceSettings model."""

    def test_default_values(self) -> None:
        """Test default voice settings values."""
        settings = VoiceSettings()

        assert settings.stability == 0.5
        assert settings.similarity_boost == 0.75
        assert settings.style == 0.0
        assert settings.use_speaker_boost is True

    def test_custom_values(self) -> None:
        """Test creating settings with custom values."""
        settings = VoiceSettings(
            stability=0.8,
            similarity_boost=0.9,
            style=0.5,
            use_speaker_boost=False,
        )

        assert settings.stability == 0.8
        assert settings.similarity_boost == 0.9
        assert settings.style == 0.5
        assert settings.use_speaker_boost is False

    def test_stability_min_value(self) -> None:
        """Test stability minimum value of 0.0."""
        settings = VoiceSettings(stability=0.0)
        assert settings.stability == 0.0

    def test_stability_max_value(self) -> None:
        """Test stability maximum value of 1.0."""
        settings = VoiceSettings(stability=1.0)
        assert settings.stability == 1.0

    def test_stability_below_min_raises_error(self) -> None:
        """Test that stability below 0.0 raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            VoiceSettings(stability=-0.1)

        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_stability_above_max_raises_error(self) -> None:
        """Test that stability above 1.0 raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            VoiceSettings(stability=1.1)

        assert "less than or equal to 1" in str(exc_info.value).lower()

    def test_similarity_boost_min_value(self) -> None:
        """Test similarity_boost minimum value of 0.0."""
        settings = VoiceSettings(similarity_boost=0.0)
        assert settings.similarity_boost == 0.0

    def test_similarity_boost_max_value(self) -> None:
        """Test similarity_boost maximum value of 1.0."""
        settings = VoiceSettings(similarity_boost=1.0)
        assert settings.similarity_boost == 1.0

    def test_similarity_boost_below_min_raises_error(self) -> None:
        """Test that similarity_boost below 0.0 raises error."""
        with pytest.raises(ValidationError):
            VoiceSettings(similarity_boost=-0.1)

    def test_similarity_boost_above_max_raises_error(self) -> None:
        """Test that similarity_boost above 1.0 raises error."""
        with pytest.raises(ValidationError):
            VoiceSettings(similarity_boost=1.1)

    def test_style_min_value(self) -> None:
        """Test style minimum value of 0.0."""
        settings = VoiceSettings(style=0.0)
        assert settings.style == 0.0

    def test_style_max_value(self) -> None:
        """Test style maximum value of 1.0."""
        settings = VoiceSettings(style=1.0)
        assert settings.style == 1.0

    def test_style_below_min_raises_error(self) -> None:
        """Test that style below 0.0 raises error."""
        with pytest.raises(ValidationError):
            VoiceSettings(style=-0.1)

    def test_style_above_max_raises_error(self) -> None:
        """Test that style above 1.0 raises error."""
        with pytest.raises(ValidationError):
            VoiceSettings(style=1.1)

    def test_use_speaker_boost_boolean(self) -> None:
        """Test use_speaker_boost accepts boolean values."""
        settings_true = VoiceSettings(use_speaker_boost=True)
        settings_false = VoiceSettings(use_speaker_boost=False)

        assert settings_true.use_speaker_boost is True
        assert settings_false.use_speaker_boost is False


class TestTTSRequest:
    """Tests for TTSRequest model."""

    def test_valid_request(self) -> None:
        """Test creating valid TTS request."""
        request = TTSRequest(
            text="Hello world",
            voice_id=ElevenLabsVoice.RACHEL.value,
        )

        assert request.text == "Hello world"
        assert request.voice_id == ElevenLabsVoice.RACHEL.value
        assert request.model_id == "eleven_multilingual_v2"
        assert isinstance(request.voice_settings, VoiceSettings)

    def test_custom_model_id(self) -> None:
        """Test request with custom model_id."""
        request = TTSRequest(
            text="Test",
            voice_id=ElevenLabsVoice.ADAM.value,
            model_id="eleven_monolingual_v1",
        )

        assert request.model_id == "eleven_monolingual_v1"

    def test_custom_voice_settings(self) -> None:
        """Test request with custom voice settings."""
        custom_settings = VoiceSettings(
            stability=0.8,
            similarity_boost=0.9,
        )

        request = TTSRequest(
            text="Test",
            voice_id=ElevenLabsVoice.BELLA.value,
            voice_settings=custom_settings,
        )

        assert request.voice_settings.stability == 0.8
        assert request.voice_settings.similarity_boost == 0.9

    def test_text_min_length(self) -> None:
        """Test that text must be at least 1 character."""
        request = TTSRequest(
            text="A",
            voice_id=ElevenLabsVoice.RACHEL.value,
        )

        assert request.text == "A"

    def test_text_empty_raises_error(self) -> None:
        """Test that empty text raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            TTSRequest(
                text="",
                voice_id=ElevenLabsVoice.RACHEL.value,
            )

        assert "at least 1 character" in str(exc_info.value).lower()

    def test_text_max_length(self) -> None:
        """Test text with maximum length."""
        long_text = "A" * 5000

        request = TTSRequest(
            text=long_text,
            voice_id=ElevenLabsVoice.RACHEL.value,
        )

        assert len(request.text) == 5000

    def test_text_exceeds_max_raises_error(self) -> None:
        """Test that text exceeding 5000 characters raises error."""
        too_long_text = "A" * 5001

        with pytest.raises(ValidationError) as exc_info:
            TTSRequest(
                text=too_long_text,
                voice_id=ElevenLabsVoice.RACHEL.value,
            )

        assert "at most 5000 character" in str(exc_info.value).lower()

    def test_text_required(self) -> None:
        """Test that text is required."""
        with pytest.raises(ValidationError):
            TTSRequest(voice_id=ElevenLabsVoice.RACHEL.value)  # type: ignore

    def test_voice_id_required(self) -> None:
        """Test that voice_id is required."""
        with pytest.raises(ValidationError):
            TTSRequest(text="Hello")  # type: ignore

    def test_with_all_voices(self) -> None:
        """Test request works with all voice IDs."""
        for voice in ElevenLabsVoice:
            request = TTSRequest(
                text="Test",
                voice_id=voice.value,
            )

            assert request.voice_id == voice.value


class TestTTSResponse:
    """Tests for TTSResponse model."""

    def test_valid_response(self) -> None:
        """Test creating valid TTS response."""
        audio_data = b"fake audio data"

        response = TTSResponse(
            audio_data=audio_data,
            character_count=100,
            voice_id=ElevenLabsVoice.RACHEL.value,
        )

        assert response.audio_data == audio_data
        assert response.content_type == "audio/mpeg"
        assert response.character_count == 100
        assert response.voice_id == ElevenLabsVoice.RACHEL.value

    def test_custom_content_type(self) -> None:
        """Test response with custom content type."""
        response = TTSResponse(
            audio_data=b"data",
            content_type="audio/wav",
            character_count=50,
            voice_id=ElevenLabsVoice.ADAM.value,
        )

        assert response.content_type == "audio/wav"

    def test_default_content_type(self) -> None:
        """Test default content type is audio/mpeg."""
        response = TTSResponse(
            audio_data=b"data",
            character_count=50,
            voice_id=ElevenLabsVoice.ADAM.value,
        )

        assert response.content_type == "audio/mpeg"

    def test_character_count_zero(self) -> None:
        """Test character_count can be zero."""
        response = TTSResponse(
            audio_data=b"",
            character_count=0,
            voice_id=ElevenLabsVoice.RACHEL.value,
        )

        assert response.character_count == 0

    def test_character_count_negative_raises_error(self) -> None:
        """Test that negative character_count raises error."""
        with pytest.raises(ValidationError) as exc_info:
            TTSResponse(
                audio_data=b"data",
                character_count=-1,
                voice_id=ElevenLabsVoice.RACHEL.value,
            )

        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_audio_data_required(self) -> None:
        """Test that audio_data is required."""
        with pytest.raises(ValidationError):
            TTSResponse(  # type: ignore
                character_count=100,
                voice_id=ElevenLabsVoice.RACHEL.value,
            )

    def test_character_count_required(self) -> None:
        """Test that character_count is required."""
        with pytest.raises(ValidationError):
            TTSResponse(  # type: ignore
                audio_data=b"data",
                voice_id=ElevenLabsVoice.RACHEL.value,
            )

    def test_voice_id_required(self) -> None:
        """Test that voice_id is required."""
        with pytest.raises(ValidationError):
            TTSResponse(  # type: ignore
                audio_data=b"data",
                character_count=100,
            )

    def test_empty_audio_data(self) -> None:
        """Test response with empty audio data."""
        response = TTSResponse(
            audio_data=b"",
            character_count=0,
            voice_id=ElevenLabsVoice.RACHEL.value,
        )

        assert response.audio_data == b""

    def test_large_audio_data(self) -> None:
        """Test response with large audio data."""
        large_audio = b"x" * 1000000  # 1MB of data

        response = TTSResponse(
            audio_data=large_audio,
            character_count=5000,
            voice_id=ElevenLabsVoice.RACHEL.value,
        )

        assert len(response.audio_data) == 1000000


class TestIntegration:
    """Integration tests for ElevenLabs models."""

    def test_full_workflow_female_energetic(self) -> None:
        """Test full workflow with female energetic voice."""
        # Select voice
        voice_id = ElevenLabsVoice.select_voice("female", "energetic")

        # Create request
        request = TTSRequest(
            text="Check out this amazing product!",
            voice_id=voice_id,
        )

        assert request.voice_id == ElevenLabsVoice.BELLA.value
        assert request.text == "Check out this amazing product!"

        # Simulate response
        response = TTSResponse(
            audio_data=b"fake audio bytes",
            character_count=len(request.text),
            voice_id=request.voice_id,
        )

        assert response.voice_id == ElevenLabsVoice.BELLA.value
        assert response.character_count == 31

    def test_full_workflow_male_professional(self) -> None:
        """Test full workflow with male professional voice."""
        voice_id = ElevenLabsVoice.select_voice("male", "professional")

        request = TTSRequest(
            text="Welcome to our premium service.",
            voice_id=voice_id,
            voice_settings=VoiceSettings(
                stability=0.7,
                similarity_boost=0.8,
            ),
        )

        assert request.voice_id == ElevenLabsVoice.ANTONI.value
        assert request.voice_settings.stability == 0.7

        response = TTSResponse(
            audio_data=b"professional audio",
            character_count=len(request.text),
            voice_id=request.voice_id,
        )

        assert response.voice_id == ElevenLabsVoice.ANTONI.value

    def test_default_workflow(self) -> None:
        """Test workflow with default settings."""
        voice_id = ElevenLabsVoice.select_voice("female")

        request = TTSRequest(
            text="Default settings test",
            voice_id=voice_id,
        )

        # Should use defaults
        assert request.voice_id == ElevenLabsVoice.RACHEL.value
        assert request.model_id == "eleven_multilingual_v2"
        assert request.voice_settings.stability == 0.5
        assert request.voice_settings.use_speaker_boost is True
