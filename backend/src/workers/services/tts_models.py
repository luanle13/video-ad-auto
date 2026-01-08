"""TTS service models and enums."""
from enum import Enum

from pydantic import BaseModel, Field

# Average speaking rate in characters per second
# Based on typical speaking rate of 150 words/minute
# Assuming average word length of 5 characters
CHARS_PER_SECOND = 12.5


class TTSProvider(str, Enum):
    """TTS provider options.

    - ELEVENLABS: Premium quality, natural-sounding voices
    - POLLY: AWS Polly, cost-effective fallback
    - AUTO: Automatically select provider (try ElevenLabs, fallback to Polly)
    """

    ELEVENLABS = "elevenlabs"
    POLLY = "polly"
    AUTO = "auto"


class TTSVoiceConfig(BaseModel):
    """Voice configuration for TTS generation.

    Attributes:
        gender: Voice gender ("male" or "female")
        style: Voice style/tone (e.g., "professional", "energetic", "casual")
        speaking_rate: Speech rate modifier (0.5 to 2.0, where 1.0 is normal)
    """

    gender: str = Field(
        ...,
        description="Voice gender (male or female)",
        pattern="^(male|female)$",
    )
    style: str | None = Field(
        default=None,
        description="Voice style or tone",
    )
    speaking_rate: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Speaking rate (0.5-2.0, 1.0 is normal)",
    )


class TTSResult(BaseModel):
    """Result from TTS generation.

    Attributes:
        audio_data: Generated audio in bytes (MP3 format)
        content_type: MIME type of audio
        provider_used: Which TTS provider was used
        character_count: Number of characters processed
        voice_id: Voice ID that was used
        duration_estimate_seconds: Estimated audio duration in seconds
    """

    audio_data: bytes = Field(
        ...,
        description="Audio data in bytes",
    )
    content_type: str = Field(
        default="audio/mpeg",
        description="MIME type of audio",
    )
    provider_used: TTSProvider = Field(
        ...,
        description="TTS provider that was used",
    )
    character_count: int = Field(
        ...,
        ge=0,
        description="Number of characters processed",
    )
    voice_id: str = Field(
        ...,
        description="Voice ID used for generation",
    )
    duration_estimate_seconds: float = Field(
        ...,
        ge=0.0,
        description="Estimated audio duration in seconds",
    )

    @staticmethod
    def estimate_duration(character_count: int, speaking_rate: float = 1.0) -> float:
        """Estimate audio duration based on character count and speaking rate.

        Args:
            character_count: Number of characters in text
            speaking_rate: Speaking rate modifier (1.0 is normal)

        Returns:
            Estimated duration in seconds

        Example:
            >>> TTSResult.estimate_duration(125, 1.0)
            10.0
            >>> TTSResult.estimate_duration(125, 2.0)  # Faster
            5.0
        """
        if character_count <= 0 or speaking_rate <= 0:
            return 0.0

        # Base duration at normal rate
        base_duration = character_count / CHARS_PER_SECOND

        # Adjust for speaking rate
        return base_duration / speaking_rate
