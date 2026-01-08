"""ElevenLabs TTS API client."""
from typing import Any

import httpx

from src.shared.exceptions import ElevenLabsError, ExternalServiceError
from src.workers.clients.base import BaseAPIClient
from src.workers.clients.elevenlabs_models import (
    TTSRequest,
    TTSResponse,
    VoiceSettings,
)
from src.workers.clients.retry import RetryConfig


class ElevenLabsClient(BaseAPIClient):
    """Client for ElevenLabs Text-to-Speech API.

    Provides methods for:
    - Converting text to speech with customizable voices
    - Retrieving available voices
    - Getting user account information

    Example:
        >>> async with ElevenLabsClient(api_key="your-key") as client:
        ...     response = await client.text_to_speech(
        ...         text="Hello world",
        ...         voice_id=ElevenLabsVoice.RACHEL.value,
        ...     )
        ...     # Save audio_data to file
        ...     with open("output.mp3", "wb") as f:
        ...         f.write(response.audio_data)
    """

    service_name = "ElevenLabs"
    base_url = "https://api.elevenlabs.io/v1"
    default_timeout = 60.0

    @property
    def headers(self) -> dict[str, str]:
        """Return HTTP headers for ElevenLabs API requests.

        ElevenLabs uses "xi-api-key" header for authentication instead of
        the standard Authorization Bearer token.

        Returns:
            Dictionary with xi-api-key and content-type headers
        """
        return {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

    def _wrap_exception(self, exc: Exception) -> ExternalServiceError:
        """Wrap exception as ElevenLabsError.

        Args:
            exc: Original exception from API call

        Returns:
            ElevenLabsError with error message
        """
        return ElevenLabsError(str(exc))

    async def text_to_speech(
        self,
        text: str,
        voice_id: str,
        voice_settings: VoiceSettings | None = None,
        model_id: str = "eleven_multilingual_v2",
    ) -> TTSResponse:
        """Convert text to speech using ElevenLabs API.

        Args:
            text: Text to convert to speech (max 5000 characters)
            voice_id: ElevenLabs voice ID (use ElevenLabsVoice enum)
            voice_settings: Optional voice settings for customization
            model_id: TTS model to use (default: eleven_multilingual_v2)

        Returns:
            TTSResponse with audio data and metadata

        Raises:
            ElevenLabsError: If API call fails

        Example:
            >>> from src.workers.clients.elevenlabs_models import ElevenLabsVoice
            >>> response = await client.text_to_speech(
            ...     text="Welcome to our platform",
            ...     voice_id=ElevenLabsVoice.RACHEL.value,
            ...     voice_settings=VoiceSettings(stability=0.7),
            ... )
        """
        # Create request model for validation
        request = TTSRequest(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            voice_settings=voice_settings or VoiceSettings(),
        )

        # Prepare request payload
        payload = {
            "text": request.text,
            "model_id": request.model_id,
            "voice_settings": {
                "stability": request.voice_settings.stability,
                "similarity_boost": request.voice_settings.similarity_boost,
                "style": request.voice_settings.style,
                "use_speaker_boost": request.voice_settings.use_speaker_boost,
            },
        }

        # Make API request
        response = await self.post(
            f"/text-to-speech/{request.voice_id}",
            json=payload,
        )

        # ElevenLabs returns audio directly as bytes
        audio_data = response.content

        # Return structured response
        return TTSResponse(
            audio_data=audio_data,
            content_type=response.headers.get("content-type", "audio/mpeg"),
            character_count=len(text),
            voice_id=voice_id,
        )

    async def get_voices(self) -> list[dict[str, Any]]:
        """Retrieve list of available voices from ElevenLabs.

        Returns:
            List of voice dictionaries with metadata

        Raises:
            ElevenLabsError: If API call fails

        Example:
            >>> voices = await client.get_voices()
            >>> for voice in voices:
            ...     print(f"{voice['name']}: {voice['voice_id']}")
        """
        response = await self.get("/voices")

        data = response.json()

        # ElevenLabs returns {"voices": [...]}
        return data.get("voices", [])

    async def get_user_info(self) -> dict[str, Any]:
        """Get user account information and quota usage.

        Returns:
            Dictionary with user info including character count and limits

        Raises:
            ElevenLabsError: If API call fails

        Example:
            >>> info = await client.get_user_info()
            >>> print(f"Characters used: {info['character_count']}")
            >>> print(f"Characters limit: {info['character_limit']}")
        """
        response = await self.get("/user")

        return response.json()
