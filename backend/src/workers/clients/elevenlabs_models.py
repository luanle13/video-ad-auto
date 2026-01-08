"""ElevenLabs TTS API models and enums."""
from enum import Enum

from pydantic import BaseModel, Field


class ElevenLabsVoice(str, Enum):
    """ElevenLabs voice IDs for TTS.

    Voice characteristics:
    - RACHEL: Female, calm, narrative style
    - DOMI: Female, professional, clear
    - BELLA: Female, energetic, expressive
    - ELLI: Female, young, friendly
    - ADAM: Male, deep, authoritative
    - ANTONI: Male, smooth, professional
    - JOSH: Male, casual, conversational
    - ARNOLD: Male, strong, confident
    """

    RACHEL = "21m00Tcm4TlvDq8ikWAM"
    DOMI = "AZnzlk1XvdvUeBnXmlld"
    BELLA = "EXAVITQu4vr4xnSDxMaL"
    ELLI = "MF3mGyEYCl7XYWbV9V6O"
    ADAM = "pNInz6obpgDQGcFmaJgB"
    ANTONI = "ErXwobaYiN019PkySvjV"
    JOSH = "TxGEqnHWrfWFTfGW9XjX"
    ARNOLD = "VR6AewLTigWG4xSOukaG"

    @staticmethod
    def select_voice(gender: str, style: str | None = None) -> str:
        """Select appropriate voice based on gender and style.

        Args:
            gender: "male" or "female"
            style: Optional style hint ("professional", "energetic", "casual", "narrative")

        Returns:
            Voice ID string

        Raises:
            ValueError: If gender is invalid

        Example:
            >>> ElevenLabsVoice.select_voice("female", "energetic")
            'EXAVITQu4vr4xnSDxMaL'  # BELLA
        """
        gender_lower = gender.lower()
        style_lower = style.lower() if style else None

        if gender_lower == "female":
            if style_lower == "energetic":
                return ElevenLabsVoice.BELLA.value
            elif style_lower == "professional":
                return ElevenLabsVoice.DOMI.value
            elif style_lower == "casual" or style_lower == "friendly":
                return ElevenLabsVoice.ELLI.value
            elif style_lower == "narrative":
                return ElevenLabsVoice.RACHEL.value
            else:
                # Default female voice
                return ElevenLabsVoice.RACHEL.value

        elif gender_lower == "male":
            if style_lower == "professional":
                return ElevenLabsVoice.ANTONI.value
            elif style_lower == "casual":
                return ElevenLabsVoice.JOSH.value
            elif style_lower == "authoritative" or style_lower == "confident":
                return ElevenLabsVoice.ARNOLD.value
            else:
                # Default male voice
                return ElevenLabsVoice.ADAM.value

        else:
            raise ValueError(f"Invalid gender: {gender}. Must be 'male' or 'female'")


class VoiceSettings(BaseModel):
    """Voice settings for ElevenLabs TTS.

    Attributes:
        stability: Voice stability (0.0-1.0). Higher = more consistent, lower = more expressive
        similarity_boost: Voice similarity boost (0.0-1.0). Higher = closer to original voice
        style: Style exaggeration (0.0-1.0). Higher = more stylized
        use_speaker_boost: Enable speaker boost for improved clarity
    """

    stability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Voice stability (0.0-1.0)",
    )
    similarity_boost: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Voice similarity boost (0.0-1.0)",
    )
    style: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Style exaggeration (0.0-1.0)",
    )
    use_speaker_boost: bool = Field(
        default=True,
        description="Enable speaker boost for improved clarity",
    )


class TTSRequest(BaseModel):
    """Request model for ElevenLabs TTS API.

    Attributes:
        text: Text to convert to speech (max 5000 characters for standard)
        voice_id: ElevenLabs voice ID
        model_id: TTS model to use (eleven_monolingual_v1, eleven_multilingual_v2, etc.)
        voice_settings: Optional voice settings for customization
    """

    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text to convert to speech",
    )
    voice_id: str = Field(
        ...,
        description="ElevenLabs voice ID",
    )
    model_id: str = Field(
        default="eleven_multilingual_v2",
        description="TTS model ID",
    )
    voice_settings: VoiceSettings = Field(
        default_factory=VoiceSettings,
        description="Voice settings",
    )


class TTSResponse(BaseModel):
    """Response model for ElevenLabs TTS API.

    Attributes:
        audio_data: Audio data in bytes (MP3 format)
        content_type: MIME type of audio data
        character_count: Number of characters processed
        voice_id: Voice ID used for generation
    """

    audio_data: bytes = Field(
        ...,
        description="Audio data in bytes",
    )
    content_type: str = Field(
        default="audio/mpeg",
        description="MIME type of audio data",
    )
    character_count: int = Field(
        ...,
        ge=0,
        description="Number of characters processed",
    )
    voice_id: str = Field(
        ...,
        description="Voice ID used",
    )
