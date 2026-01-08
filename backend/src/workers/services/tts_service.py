"""Unified TTS service with fallback support."""
from typing import Any

from src.shared.config import get_settings
from src.shared.exceptions import ElevenLabsError, PollyError
from src.shared.logging import get_logger
from src.shared.secrets import get_secrets
from src.workers.clients.elevenlabs import ElevenLabsClient
from src.workers.clients.elevenlabs_models import ElevenLabsVoice, VoiceSettings
from src.workers.clients.polly import PollyClient, get_polly_client
from src.workers.clients.polly_models import PollyVoice
from src.workers.services.tts_models import (
    TTSProvider,
    TTSResult,
    TTSVoiceConfig,
)

logger = get_logger(__name__)

# Singleton instance
_tts_service: "TTSService | None" = None


class TTSService:
    """Unified TTS service with provider fallback support.

    Supports both ElevenLabs (premium) and AWS Polly (fallback) providers.
    Can automatically fallback to Polly if ElevenLabs fails.

    Example:
        >>> service = TTSService(preferred_provider=TTSProvider.AUTO)
        >>> config = TTSVoiceConfig(gender="female", speaking_rate=1.2)
        >>> result = await service.generate_speech("Hello world", config)
        >>> print(result.provider_used)
        TTSProvider.ELEVENLABS
    """

    def __init__(self, preferred_provider: TTSProvider = TTSProvider.AUTO) -> None:
        """Initialize TTS service.

        Args:
            preferred_provider: Preferred TTS provider (default: AUTO)
        """
        self.preferred_provider = preferred_provider
        self._elevenlabs_client: ElevenLabsClient | None = None
        self._polly_client: PollyClient | None = None

        logger.info(
            "tts_service_initialized",
            preferred_provider=preferred_provider.value,
        )

    async def _get_elevenlabs_client(self) -> ElevenLabsClient:
        """Get or create ElevenLabs client (lazy initialization).

        Returns:
            ElevenLabsClient instance

        Raises:
            ElevenLabsError: If API key cannot be retrieved
        """
        if self._elevenlabs_client is None:
            try:
                settings = get_settings()
                secrets = get_secrets()

                # Try to get from Secrets Manager first
                api_key = secrets.get_secret(settings.secrets_elevenlabs_key)

                self._elevenlabs_client = ElevenLabsClient(api_key=api_key)
                logger.info("elevenlabs_client_initialized")

            except Exception as e:
                raise ElevenLabsError(f"Failed to initialize ElevenLabs client: {e}")

        return self._elevenlabs_client

    def _get_polly_client(self) -> PollyClient:
        """Get or create Polly client (lazy initialization).

        Returns:
            PollyClient instance
        """
        if self._polly_client is None:
            self._polly_client = get_polly_client()
            logger.info("polly_client_initialized")

        return self._polly_client

    async def generate_speech(
        self,
        text: str,
        voice_config: TTSVoiceConfig,
        provider: TTSProvider | None = None,
        use_ssml: bool = False,
    ) -> TTSResult:
        """Generate speech from text using specified or preferred provider.

        Args:
            text: Text to convert to speech (or SSML if use_ssml=True)
            voice_config: Voice configuration (gender, style, speaking rate)
            provider: Override provider (default: use preferred_provider)
            use_ssml: Whether text is SSML (only for Polly)

        Returns:
            TTSResult with audio data and metadata

        Raises:
            ElevenLabsError: If ElevenLabs generation fails (when not using AUTO)
            PollyError: If Polly generation fails (when not using AUTO)

        Example:
            >>> config = TTSVoiceConfig(gender="male", speaking_rate=1.0)
            >>> result = await service.generate_speech("Hello", config)
        """
        provider = provider or self.preferred_provider

        logger.info(
            "generating_speech",
            provider=provider.value,
            text_length=len(text),
            use_ssml=use_ssml,
        )

        if provider == TTSProvider.ELEVENLABS:
            return await self._generate_elevenlabs(text, voice_config)

        elif provider == TTSProvider.POLLY:
            return await self._generate_polly(text, voice_config, use_ssml)

        else:  # TTSProvider.AUTO
            return await self._generate_with_fallback(text, voice_config, use_ssml)

    async def _generate_elevenlabs(
        self,
        text: str,
        voice_config: TTSVoiceConfig,
    ) -> TTSResult:
        """Generate speech using ElevenLabs.

        Args:
            text: Text to convert to speech
            voice_config: Voice configuration

        Returns:
            TTSResult with ElevenLabs audio

        Raises:
            ElevenLabsError: If generation fails
        """
        client = await self._get_elevenlabs_client()

        # Select voice based on config
        voice_id = ElevenLabsVoice.select_voice(
            gender=voice_config.gender,
            style=voice_config.style,
        )

        # Create voice settings
        voice_settings = VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True,
        )

        # Generate speech
        response = await client.text_to_speech(
            text=text,
            voice_id=voice_id,
            voice_settings=voice_settings,
        )

        # Calculate duration estimate
        duration = TTSResult.estimate_duration(
            character_count=response.character_count,
            speaking_rate=voice_config.speaking_rate,
        )

        logger.info(
            "elevenlabs_generation_complete",
            character_count=response.character_count,
            duration_seconds=duration,
        )

        return TTSResult(
            audio_data=response.audio_data,
            content_type="audio/mpeg",
            provider_used=TTSProvider.ELEVENLABS,
            character_count=response.character_count,
            voice_id=voice_id,
            duration_estimate_seconds=duration,
        )

    async def _generate_polly(
        self,
        text: str,
        voice_config: TTSVoiceConfig,
        use_ssml: bool = False,
    ) -> TTSResult:
        """Generate speech using AWS Polly.

        Args:
            text: Text to convert to speech (or SSML if use_ssml=True)
            voice_config: Voice configuration
            use_ssml: Whether text is SSML

        Returns:
            TTSResult with Polly audio

        Raises:
            PollyError: If generation fails
        """
        client = self._get_polly_client()

        # Select voice based on gender
        if voice_config.gender.lower() == "female":
            voice_id = PollyVoice.JOANNA.value
        else:
            voice_id = PollyVoice.MATTHEW.value

        # Generate speech
        response = await client.text_to_speech(
            text=text,
            voice_id=voice_id,
            use_ssml=use_ssml,
        )

        # Calculate duration estimate
        duration = TTSResult.estimate_duration(
            character_count=response.request_characters,
            speaking_rate=voice_config.speaking_rate,
        )

        logger.info(
            "polly_generation_complete",
            character_count=response.request_characters,
            duration_seconds=duration,
        )

        return TTSResult(
            audio_data=response.audio_data,
            content_type="audio/mpeg",
            provider_used=TTSProvider.POLLY,
            character_count=response.request_characters,
            voice_id=voice_id,
            duration_estimate_seconds=duration,
        )

    async def _generate_with_fallback(
        self,
        text: str,
        voice_config: TTSVoiceConfig,
        use_ssml: bool = False,
    ) -> TTSResult:
        """Generate speech with automatic fallback from ElevenLabs to Polly.

        Tries ElevenLabs first (premium quality). If that fails, falls back
        to AWS Polly (cost-effective).

        Args:
            text: Text to convert to speech (or SSML if use_ssml=True)
            voice_config: Voice configuration
            use_ssml: Whether text is SSML (only used for Polly fallback)

        Returns:
            TTSResult from whichever provider succeeded

        Raises:
            PollyError: If both providers fail
        """
        # Try ElevenLabs first
        try:
            logger.info("attempting_elevenlabs_generation")
            return await self._generate_elevenlabs(text, voice_config)

        except ElevenLabsError as e:
            logger.warning(
                "elevenlabs_failed_falling_back",
                error=str(e),
            )

            # Fallback to Polly
            try:
                logger.info("attempting_polly_fallback")
                return await self._generate_polly(text, voice_config, use_ssml)

            except PollyError as polly_error:
                logger.error(
                    "all_providers_failed",
                    elevenlabs_error=str(e),
                    polly_error=str(polly_error),
                )
                raise

    async def close(self) -> None:
        """Close all client connections and cleanup resources.

        Should be called when service is no longer needed.
        """
        if self._elevenlabs_client is not None:
            await self._elevenlabs_client.close()
            self._elevenlabs_client = None
            logger.info("elevenlabs_client_closed")

        # Polly client doesn't need explicit cleanup
        self._polly_client = None

        logger.info("tts_service_closed")


def get_tts_service(
    provider: TTSProvider = TTSProvider.AUTO,
) -> TTSService:
    """Get TTS service singleton instance.

    Args:
        provider: Preferred TTS provider (default: AUTO)

    Returns:
        TTSService instance

    Example:
        >>> service = get_tts_service(TTSProvider.ELEVENLABS)
        >>> result = await service.generate_speech("Hello", config)
    """
    global _tts_service

    if _tts_service is None:
        _tts_service = TTSService(preferred_provider=provider)

    return _tts_service
