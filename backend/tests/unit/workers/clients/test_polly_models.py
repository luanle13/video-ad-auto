"""Tests for AWS Polly models and enums."""
import pytest
from pydantic import ValidationError

from src.workers.clients.polly_models import (
    PollyEngine,
    PollyTTSResponse,
    PollyVoice,
)


class TestPollyVoice:
    """Tests for PollyVoice enum."""

    def test_all_voices_defined(self) -> None:
        """Test that all 6 neural voices are defined."""
        assert len(PollyVoice) == 6

        # Verify all expected voices exist
        assert PollyVoice.JOANNA
        assert PollyVoice.KENDRA
        assert PollyVoice.MATTHEW
        assert PollyVoice.JOEY
        assert PollyVoice.AMY
        assert PollyVoice.BRIAN

    def test_voice_ids_are_strings(self) -> None:
        """Test that voice IDs are non-empty strings."""
        for voice in PollyVoice:
            assert isinstance(voice.value, str)
            assert len(voice.value) > 0

    def test_joanna_voice_id(self) -> None:
        """Test JOANNA voice ID."""
        assert PollyVoice.JOANNA.value == "Joanna"

    def test_kendra_voice_id(self) -> None:
        """Test KENDRA voice ID."""
        assert PollyVoice.KENDRA.value == "Kendra"

    def test_matthew_voice_id(self) -> None:
        """Test MATTHEW voice ID."""
        assert PollyVoice.MATTHEW.value == "Matthew"

    def test_joey_voice_id(self) -> None:
        """Test JOEY voice ID."""
        assert PollyVoice.JOEY.value == "Joey"

    def test_amy_voice_id(self) -> None:
        """Test AMY voice ID."""
        assert PollyVoice.AMY.value == "Amy"

    def test_brian_voice_id(self) -> None:
        """Test BRIAN voice ID."""
        assert PollyVoice.BRIAN.value == "Brian"

    def test_voice_enum_is_string(self) -> None:
        """Test that voice enum inherits from str."""
        voice = PollyVoice.JOANNA
        assert isinstance(voice, str)
        assert isinstance(voice.value, str)


class TestSelectVoice:
    """Tests for PollyVoice.select_voice method."""

    def test_select_female_default(self) -> None:
        """Test selecting default female voice (US)."""
        voice_id = PollyVoice.select_voice("female")
        assert voice_id == PollyVoice.JOANNA.value

    def test_select_male_default(self) -> None:
        """Test selecting default male voice (US)."""
        voice_id = PollyVoice.select_voice("male")
        assert voice_id == PollyVoice.MATTHEW.value

    def test_select_female_us(self) -> None:
        """Test selecting US female voice."""
        voice_id = PollyVoice.select_voice("female", "us")
        assert voice_id == PollyVoice.JOANNA.value

    def test_select_male_us(self) -> None:
        """Test selecting US male voice."""
        voice_id = PollyVoice.select_voice("male", "us")
        assert voice_id == PollyVoice.MATTHEW.value

    def test_select_female_british(self) -> None:
        """Test selecting British female voice."""
        voice_id = PollyVoice.select_voice("female", "british")
        assert voice_id == PollyVoice.AMY.value

    def test_select_male_british(self) -> None:
        """Test selecting British male voice."""
        voice_id = PollyVoice.select_voice("male", "british")
        assert voice_id == PollyVoice.BRIAN.value

    def test_select_female_uk(self) -> None:
        """Test selecting UK female voice (alias for british)."""
        voice_id = PollyVoice.select_voice("female", "uk")
        assert voice_id == PollyVoice.AMY.value

    def test_select_male_uk(self) -> None:
        """Test selecting UK male voice (alias for british)."""
        voice_id = PollyVoice.select_voice("male", "uk")
        assert voice_id == PollyVoice.BRIAN.value

    def test_select_case_insensitive_gender(self) -> None:
        """Test that gender is case-insensitive."""
        assert PollyVoice.select_voice("FEMALE") == PollyVoice.JOANNA.value
        assert PollyVoice.select_voice("Male") == PollyVoice.MATTHEW.value
        assert PollyVoice.select_voice("FeMaLe") == PollyVoice.JOANNA.value

    def test_select_case_insensitive_accent(self) -> None:
        """Test that accent is case-insensitive."""
        assert PollyVoice.select_voice("female", "BRITISH") == PollyVoice.AMY.value
        assert PollyVoice.select_voice("male", "British") == PollyVoice.BRIAN.value
        assert PollyVoice.select_voice("female", "UK") == PollyVoice.AMY.value

    def test_select_unknown_accent_defaults_to_us(self) -> None:
        """Test that unknown accent defaults to US."""
        assert PollyVoice.select_voice("female", "australian") == PollyVoice.JOANNA.value
        assert PollyVoice.select_voice("male", "canadian") == PollyVoice.MATTHEW.value

    def test_select_none_accent_defaults_to_us(self) -> None:
        """Test that None accent defaults to US."""
        assert PollyVoice.select_voice("female", None) == PollyVoice.JOANNA.value
        assert PollyVoice.select_voice("male", None) == PollyVoice.MATTHEW.value

    def test_select_invalid_gender_raises_error(self) -> None:
        """Test that invalid gender raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            PollyVoice.select_voice("other")

        assert "Invalid gender" in str(exc_info.value)
        assert "must be 'male' or 'female'" in str(exc_info.value).lower()

    def test_select_empty_gender_raises_error(self) -> None:
        """Test that empty gender raises ValueError."""
        with pytest.raises(ValueError):
            PollyVoice.select_voice("")


class TestTextToSSML:
    """Tests for PollyVoice.text_to_ssml method."""

    def test_text_to_ssml_plain_text(self) -> None:
        """Test converting plain text without prosody."""
        ssml = PollyVoice.text_to_ssml("Hello world")
        assert ssml == "<speak>Hello world</speak>"

    def test_text_to_ssml_with_rate(self) -> None:
        """Test SSML with rate attribute."""
        ssml = PollyVoice.text_to_ssml("Fast speech", rate="fast")
        assert ssml == '<speak><prosody rate="fast">Fast speech</prosody></speak>'

    def test_text_to_ssml_with_pitch(self) -> None:
        """Test SSML with pitch attribute."""
        ssml = PollyVoice.text_to_ssml("High pitch", pitch="high")
        assert ssml == '<speak><prosody pitch="high">High pitch</prosody></speak>'

    def test_text_to_ssml_with_volume(self) -> None:
        """Test SSML with volume attribute."""
        ssml = PollyVoice.text_to_ssml("Loud voice", volume="loud")
        assert ssml == '<speak><prosody volume="loud">Loud voice</prosody></speak>'

    def test_text_to_ssml_with_all_attributes(self) -> None:
        """Test SSML with all prosody attributes."""
        ssml = PollyVoice.text_to_ssml(
            "Complete control",
            rate="fast",
            pitch="high",
            volume="loud",
        )
        assert ssml == '<speak><prosody rate="fast" pitch="high" volume="loud">Complete control</prosody></speak>'

    def test_text_to_ssml_with_rate_and_pitch(self) -> None:
        """Test SSML with rate and pitch."""
        ssml = PollyVoice.text_to_ssml("Test", rate="slow", pitch="low")
        assert ssml == '<speak><prosody rate="slow" pitch="low">Test</prosody></speak>'

    def test_text_to_ssml_escapes_ampersand(self) -> None:
        """Test that & is escaped in SSML."""
        ssml = PollyVoice.text_to_ssml("Tom & Jerry")
        assert ssml == "<speak>Tom &amp; Jerry</speak>"

    def test_text_to_ssml_escapes_less_than(self) -> None:
        """Test that < is escaped in SSML."""
        ssml = PollyVoice.text_to_ssml("5 < 10")
        assert ssml == "<speak>5 &lt; 10</speak>"

    def test_text_to_ssml_escapes_greater_than(self) -> None:
        """Test that > is escaped in SSML."""
        ssml = PollyVoice.text_to_ssml("10 > 5")
        assert ssml == "<speak>10 &gt; 5</speak>"

    def test_text_to_ssml_escapes_quotes(self) -> None:
        """Test that quotes are escaped in SSML."""
        ssml = PollyVoice.text_to_ssml('Say "hello"')
        assert ssml == "<speak>Say &quot;hello&quot;</speak>"

    def test_text_to_ssml_escapes_apostrophe(self) -> None:
        """Test that apostrophe is escaped in SSML."""
        ssml = PollyVoice.text_to_ssml("It's great")
        assert ssml == "<speak>It&apos;s great</speak>"

    def test_text_to_ssml_escapes_all_special_chars(self) -> None:
        """Test escaping all special XML characters."""
        ssml = PollyVoice.text_to_ssml("A&B < C > D \"E\" 'F'")
        assert ssml == "<speak>A&amp;B &lt; C &gt; D &quot;E&quot; &apos;F&apos;</speak>"

    def test_text_to_ssml_escapes_with_prosody(self) -> None:
        """Test that escaping works with prosody attributes."""
        ssml = PollyVoice.text_to_ssml("Tom & Jerry", rate="fast")
        assert ssml == '<speak><prosody rate="fast">Tom &amp; Jerry</prosody></speak>'

    def test_text_to_ssml_rate_values(self) -> None:
        """Test various rate values."""
        rates = ["x-slow", "slow", "medium", "fast", "x-fast"]
        for rate in rates:
            ssml = PollyVoice.text_to_ssml("Test", rate=rate)
            assert f'rate="{rate}"' in ssml

    def test_text_to_ssml_pitch_values(self) -> None:
        """Test various pitch values."""
        pitches = ["x-low", "low", "medium", "high", "x-high"]
        for pitch in pitches:
            ssml = PollyVoice.text_to_ssml("Test", pitch=pitch)
            assert f'pitch="{pitch}"' in ssml

    def test_text_to_ssml_volume_values(self) -> None:
        """Test various volume values."""
        volumes = ["silent", "x-soft", "soft", "medium", "loud", "x-loud"]
        for volume in volumes:
            ssml = PollyVoice.text_to_ssml("Test", volume=volume)
            assert f'volume="{volume}"' in ssml

    def test_text_to_ssml_empty_string(self) -> None:
        """Test SSML with empty string."""
        ssml = PollyVoice.text_to_ssml("")
        assert ssml == "<speak></speak>"

    def test_text_to_ssml_multiline_text(self) -> None:
        """Test SSML with multiline text."""
        text = "Line 1\nLine 2\nLine 3"
        ssml = PollyVoice.text_to_ssml(text)
        assert ssml == "<speak>Line 1\nLine 2\nLine 3</speak>"


class TestPollyEngine:
    """Tests for PollyEngine enum."""

    def test_all_engines_defined(self) -> None:
        """Test that both engines are defined."""
        assert len(PollyEngine) == 2
        assert PollyEngine.NEURAL
        assert PollyEngine.STANDARD

    def test_neural_engine_value(self) -> None:
        """Test NEURAL engine value."""
        assert PollyEngine.NEURAL.value == "neural"

    def test_standard_engine_value(self) -> None:
        """Test STANDARD engine value."""
        assert PollyEngine.STANDARD.value == "standard"

    def test_engine_enum_is_string(self) -> None:
        """Test that engine enum inherits from str."""
        engine = PollyEngine.NEURAL
        assert isinstance(engine, str)
        assert isinstance(engine.value, str)


class TestPollyTTSResponse:
    """Tests for PollyTTSResponse model."""

    def test_valid_response(self) -> None:
        """Test creating valid Polly TTS response."""
        audio_data = b"fake audio data"

        response = PollyTTSResponse(
            audio_data=audio_data,
            request_characters=100,
            voice_id=PollyVoice.JOANNA.value,
        )

        assert response.audio_data == audio_data
        assert response.content_type == "audio/mpeg"
        assert response.request_characters == 100
        assert response.voice_id == PollyVoice.JOANNA.value

    def test_custom_content_type(self) -> None:
        """Test response with custom content type."""
        response = PollyTTSResponse(
            audio_data=b"data",
            content_type="audio/ogg",
            request_characters=50,
            voice_id=PollyVoice.MATTHEW.value,
        )

        assert response.content_type == "audio/ogg"

    def test_default_content_type(self) -> None:
        """Test default content type is audio/mpeg."""
        response = PollyTTSResponse(
            audio_data=b"data",
            request_characters=50,
            voice_id=PollyVoice.AMY.value,
        )

        assert response.content_type == "audio/mpeg"

    def test_request_characters_zero(self) -> None:
        """Test request_characters can be zero."""
        response = PollyTTSResponse(
            audio_data=b"",
            request_characters=0,
            voice_id=PollyVoice.JOANNA.value,
        )

        assert response.request_characters == 0

    def test_request_characters_negative_raises_error(self) -> None:
        """Test that negative request_characters raises error."""
        with pytest.raises(ValidationError) as exc_info:
            PollyTTSResponse(
                audio_data=b"data",
                request_characters=-1,
                voice_id=PollyVoice.JOANNA.value,
            )

        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_audio_data_required(self) -> None:
        """Test that audio_data is required."""
        with pytest.raises(ValidationError):
            PollyTTSResponse(  # type: ignore
                request_characters=100,
                voice_id=PollyVoice.JOANNA.value,
            )

    def test_request_characters_required(self) -> None:
        """Test that request_characters is required."""
        with pytest.raises(ValidationError):
            PollyTTSResponse(  # type: ignore
                audio_data=b"data",
                voice_id=PollyVoice.JOANNA.value,
            )

    def test_voice_id_required(self) -> None:
        """Test that voice_id is required."""
        with pytest.raises(ValidationError):
            PollyTTSResponse(  # type: ignore
                audio_data=b"data",
                request_characters=100,
            )

    def test_empty_audio_data(self) -> None:
        """Test response with empty audio data."""
        response = PollyTTSResponse(
            audio_data=b"",
            request_characters=0,
            voice_id=PollyVoice.JOANNA.value,
        )

        assert response.audio_data == b""

    def test_large_audio_data(self) -> None:
        """Test response with large audio data."""
        large_audio = b"x" * 1000000  # 1MB of data

        response = PollyTTSResponse(
            audio_data=large_audio,
            request_characters=3000,
            voice_id=PollyVoice.MATTHEW.value,
        )

        assert len(response.audio_data) == 1000000

    def test_with_all_voices(self) -> None:
        """Test response works with all voice IDs."""
        for voice in PollyVoice:
            response = PollyTTSResponse(
                audio_data=b"test",
                request_characters=10,
                voice_id=voice.value,
            )

            assert response.voice_id == voice.value


class TestIntegration:
    """Integration tests for Polly models."""

    def test_voice_selection_and_response(self) -> None:
        """Test full workflow: select voice and create response."""
        # Select voice
        voice_id = PollyVoice.select_voice("female", "british")

        # Create response
        response = PollyTTSResponse(
            audio_data=b"audio data",
            request_characters=50,
            voice_id=voice_id,
        )

        assert response.voice_id == PollyVoice.AMY.value

    def test_ssml_generation_workflow(self) -> None:
        """Test SSML generation with different parameters."""
        # Plain text
        ssml1 = PollyVoice.text_to_ssml("Hello")
        assert "<speak>" in ssml1
        assert "Hello" in ssml1

        # With prosody
        ssml2 = PollyVoice.text_to_ssml("Fast speech", rate="x-fast")
        assert "x-fast" in ssml2
        assert "prosody" in ssml2

    def test_default_us_voices(self) -> None:
        """Test default voice selection uses US voices."""
        female = PollyVoice.select_voice("female")
        male = PollyVoice.select_voice("male")

        # Should be US voices (Joanna and Matthew)
        assert female == PollyVoice.JOANNA.value
        assert male == PollyVoice.MATTHEW.value

    def test_british_voice_selection(self) -> None:
        """Test British voice selection."""
        female_british = PollyVoice.select_voice("female", "british")
        male_british = PollyVoice.select_voice("male", "british")

        assert female_british == PollyVoice.AMY.value
        assert male_british == PollyVoice.BRIAN.value

    def test_neural_engine_with_voices(self) -> None:
        """Test using neural engine with voices."""
        engine = PollyEngine.NEURAL

        for voice in PollyVoice:
            response = PollyTTSResponse(
                audio_data=b"neural audio",
                request_characters=20,
                voice_id=voice.value,
            )

            # All defined voices are neural-compatible
            assert response.voice_id == voice.value
            assert engine.value == "neural"
