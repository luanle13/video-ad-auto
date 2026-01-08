"""AWS Polly TTS models and enums."""
from enum import Enum

from pydantic import BaseModel, Field


class PollyVoice(str, Enum):
    """AWS Polly neural voice IDs for TTS.

    Voice characteristics (neural voices):
    - JOANNA: Female, US English, professional
    - KENDRA: Female, US English, conversational
    - MATTHEW: Male, US English, authoritative
    - JOEY: Male, US English, casual
    - AMY: Female, British English, clear
    - BRIAN: Male, British English, professional
    """

    JOANNA = "Joanna"
    KENDRA = "Kendra"
    MATTHEW = "Matthew"
    JOEY = "Joey"
    AMY = "Amy"
    BRIAN = "Brian"

    @staticmethod
    def select_voice(gender: str, accent: str | None = None) -> str:
        """Select appropriate Polly voice based on gender and accent.

        Args:
            gender: "male" or "female"
            accent: Optional accent ("us", "british", "uk")

        Returns:
            Voice ID string

        Raises:
            ValueError: If gender is invalid

        Example:
            >>> PollyVoice.select_voice("female", "british")
            'Amy'
        """
        gender_lower = gender.lower()
        accent_lower = accent.lower() if accent else None

        if gender_lower == "female":
            # Check for British/UK accent
            if accent_lower in ("british", "uk"):
                return PollyVoice.AMY.value
            else:
                # Default to US female - use Joanna as default
                return PollyVoice.JOANNA.value

        elif gender_lower == "male":
            # Check for British/UK accent
            if accent_lower in ("british", "uk"):
                return PollyVoice.BRIAN.value
            else:
                # Default to US male - use Matthew as default
                return PollyVoice.MATTHEW.value

        else:
            raise ValueError(f"Invalid gender: {gender}. Must be 'male' or 'female'")

    @staticmethod
    def text_to_ssml(
        text: str,
        rate: str | None = None,
        pitch: str | None = None,
        volume: str | None = None,
    ) -> str:
        """Convert plain text to SSML for enhanced speech control.

        SSML (Speech Synthesis Markup Language) allows fine control over
        prosody (rate, pitch, volume) and pronunciation.

        Args:
            text: Plain text to convert
            rate: Speech rate ("x-slow", "slow", "medium", "fast", "x-fast")
            pitch: Voice pitch ("x-low", "low", "medium", "high", "x-high")
            volume: Speech volume ("silent", "x-soft", "soft", "medium", "loud", "x-loud")

        Returns:
            SSML-formatted string

        Example:
            >>> PollyVoice.text_to_ssml("Hello!", rate="fast", pitch="high")
            '<speak><prosody rate="fast" pitch="high">Hello!</prosody></speak>'
        """
        # Escape XML special characters in text
        escaped_text = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

        # If no prosody attributes, return simple SSML
        if not any([rate, pitch, volume]):
            return f"<speak>{escaped_text}</speak>"

        # Build prosody attributes
        prosody_attrs = []
        if rate:
            prosody_attrs.append(f'rate="{rate}"')
        if pitch:
            prosody_attrs.append(f'pitch="{pitch}"')
        if volume:
            prosody_attrs.append(f'volume="{volume}"')

        prosody_tag = " ".join(prosody_attrs)

        return f"<speak><prosody {prosody_tag}>{escaped_text}</prosody></speak>"


class PollyEngine(str, Enum):
    """AWS Polly TTS engine types.

    - NEURAL: High-quality neural TTS (requires neural-compatible voices)
    - STANDARD: Standard concatenative TTS (lower quality, lower cost)
    """

    NEURAL = "neural"
    STANDARD = "standard"


class PollyTTSResponse(BaseModel):
    """Response model for AWS Polly TTS.

    Attributes:
        audio_data: Audio data in bytes (MP3 format)
        content_type: MIME type of audio data
        request_characters: Number of characters in the request
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
    request_characters: int = Field(
        ...,
        ge=0,
        description="Number of characters in request",
    )
    voice_id: str = Field(
        ...,
        description="Voice ID used",
    )
