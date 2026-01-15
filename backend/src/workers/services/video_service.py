"""Video generation service using Kling AI."""
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict

from src.shared.config import get_settings
from src.shared.exceptions import KlingError
from src.shared.logging import get_logger
from src.shared.secrets import get_secrets
from src.workers.clients.kling import KlingClient, KlingJobResponse


logger = get_logger(__name__)


class VideoResult(BaseModel):
    """Result of video generation operation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    video_data: bytes
    job_response: KlingJobResponse
    duration_seconds: float


# Singleton instance
_video_service: "VideoService | None" = None


class VideoService:
    """Video generation service using Kling AI API.

    Provides methods for generating videos from text prompts.
    """

    def __init__(self) -> None:
        """Initialize video service."""
        self._kling_client: KlingClient | None = None

        logger.info("video_service_initialized")

    async def _get_kling_client(self) -> KlingClient:
        """Get or create Kling client (lazy initialization).

        Returns:
            KlingClient instance

        Raises:
            KlingError: If API key cannot be retrieved
        """
        if self._kling_client is None:
            try:
                settings = get_settings()
                secrets = get_secrets()

                # Get Kling API key from Secrets Manager
                api_key = secrets.get_secret(settings.secrets_kling_key)

                self._kling_client = KlingClient(api_key=api_key)
                logger.info("kling_client_initialized")

            except Exception as e:
                raise KlingError(f"Failed to initialize Kling client: {e}")

        return self._kling_client

    async def generate_video(
        self,
        prompt: str,
        audio_s3_key: str | None = None,
        config: dict[str, Any] | None = None,
        progress_callback: Callable | None = None,
    ) -> VideoResult:
        """Generate a video using Kling AI API.

        Args:
            prompt: Text prompt describing the video to generate
            audio_s3_key: Optional S3 key for audio file to accompany the video
            config: Configuration dictionary with video parameters (defaults to basic config)
            progress_callback: Optional callback function called with each status update

        Returns:
            VideoResult with video data, job response, and duration

        Raises:
            KlingError: If video generation fails

        Example:
            >>> result = await service.generate_video(
            ...     prompt="A cat playing with a ball",
            ...     config={"duration": 5, "resolution": "1080x720"},
            ...     audio_s3_key="user123/job456/voiceover.mp3"
            ... )
            >>> print(f"Video duration: {result.duration_seconds}s")
        """
        logger.info(
            "generating_video",
            prompt_length=len(prompt),
            has_audio=bool(audio_s3_key),
            config=config,
        )

        # Get Kling client
        client = await self._get_kling_client()

        # Note: Audio URL support removed with S3 migration
        # Audio is now cached and not passed to video generation
        audio_url = None
        if audio_s3_key:
            logger.info("audio_s3_key_ignored", key=audio_s3_key)

        # Use default config if none provided
        if config is None:
            config = {
                "duration": 5,
                "resolution": "1080x720",
                "aspect_ratio": "16:9"
            }

        # Generate and wait for video completion
        job_response, video_data = await client.generate_and_wait(
            prompt=prompt,
            config=config,
            audio_url=audio_url,
            progress_callback=progress_callback,
        )

        # Calculate duration from job response or config
        duration_seconds = config.get("duration", 5.0)

        logger.info(
            "video_generation_complete",
            job_id=job_response.job_id,
            video_size=len(video_data),
            duration_seconds=duration_seconds,
        )

        return VideoResult(
            video_data=video_data,
            job_response=job_response,
            duration_seconds=duration_seconds,
        )

    async def close(self) -> None:
        """Close all client connections and cleanup resources.

        Should be called when service is no longer needed.
        """
        if self._kling_client is not None:
            await self._kling_client.close()
            self._kling_client = None
            logger.info("kling_client_closed")

        logger.info("video_service_closed")


def get_video_service() -> VideoService:
    """Get video service singleton instance.

    Returns:
        VideoService instance

    Example:
        >>> service = get_video_service()
        >>> result = await service.generate_video("A cat playing", config={"duration": 5})
    """
    global _video_service

    if _video_service is None:
        _video_service = VideoService()

    return _video_service