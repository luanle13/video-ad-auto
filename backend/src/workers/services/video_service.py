"""Video generation service using PiAPI Wan 2.6 model."""
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict

from src.shared.config import get_settings
from src.shared.exceptions import PiAPIError
from src.shared.logging import get_logger
from src.shared.secrets import get_secrets
from src.shared.storage import get_storage
from src.workers.clients.piapi import PiAPIClient, PiAPIJobResponse


logger = get_logger(__name__)


class VideoResult(BaseModel):
    """Result of video generation operation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    video_data: bytes
    job_response: PiAPIJobResponse
    duration_seconds: float


# Singleton instance
_video_service: "VideoService | None" = None


class VideoService:
    """Video generation service using PiAPI Wan 2.6 model.

    Provides methods for generating 15-20 second kitchen product advertisement videos.
    Supports:
    - Text-to-video generation
    - Image-to-video generation (for style consistency)
    - Video extension for reaching 15-20 second duration
    
    Key features:
    - Realistic animation style
    - No human faces (hands-only)
    - Silent video (no voiceover)
    """

    def __init__(self) -> None:
        """Initialize video service."""
        self._piapi_client: PiAPIClient | None = None

        logger.info("video_service_initialized")

    async def _get_piapi_client(self) -> PiAPIClient:
        """Get or create PiAPI client (lazy initialization).

        Returns:
            PiAPIClient instance

        Raises:
            PiAPIError: If API key cannot be retrieved
        """
        if self._piapi_client is None:
            try:
                settings = get_settings()
                secrets = get_secrets()

                # Get PiAPI API key from Secrets Manager
                api_key = secrets.get_secret(settings.secrets_piapi_key)

                self._piapi_client = PiAPIClient(api_key=api_key)
                logger.info("piapi_client_initialized")

            except Exception as e:
                raise PiAPIError(f"Failed to initialize PiAPI client: {e}")

        return self._piapi_client

    async def generate_video(
        self,
        prompt: str,
        opening_frame_url: str | None = None,
        config: dict[str, Any] | None = None,
        progress_callback: Callable | None = None,
    ) -> VideoResult:
        """Generate a video using PiAPI Wan 2.6 model.

        Args:
            prompt: Text prompt describing the video to generate
            opening_frame_url: Optional URL of opening frame image for image-to-video
            config: Configuration dictionary with video parameters
            progress_callback: Optional callback function called with each status update

        Returns:
            VideoResult with video data, job response, and duration

        Raises:
            PiAPIError: If video generation fails

        Example:
            >>> result = await service.generate_video(
            ...     prompt="Kitchen blender mixing fresh smoothie ingredients",
            ...     config={"duration": 15, "aspect_ratio": "16:9"},
            ...     opening_frame_url="https://example.com/frame.jpg"
            ... )
            >>> print(f"Video duration: {result.duration_seconds}s")
        """
        logger.info(
            "generating_video",
            prompt_length=len(prompt),
            has_opening_frame=bool(opening_frame_url),
            config=config,
        )

        # Get PiAPI client
        client = await self._get_piapi_client()

        # Use default config if none provided
        if config is None:
            config = {
                "duration": 15,
                "aspect_ratio": "16:9"
            }

        duration = config.get("duration", 15)
        aspect_ratio = config.get("aspect_ratio", "16:9")

        # Generate video using image-to-video if opening frame provided
        if opening_frame_url:
            job_response, video_data = await client.generate_and_wait(
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                image_url=opening_frame_url,
                progress_callback=progress_callback,
            )
        else:
            job_response, video_data = await client.generate_and_wait(
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                progress_callback=progress_callback,
            )

        logger.info(
            "video_generation_complete",
            task_id=job_response.task_id,
            video_size=len(video_data),
            duration_seconds=duration,
        )

        return VideoResult(
            video_data=video_data,
            job_response=job_response,
            duration_seconds=duration,
        )

    async def generate_extended_video(
        self,
        prompt: str,
        opening_frame_url: str,
        closing_frame_url: str | None = None,
        target_duration: int = 18,
        progress_callback: Callable | None = None,
    ) -> VideoResult:
        """Generate an extended video using multiple segments for style consistency.

        This method generates a video starting from the opening frame image,
        which helps maintain visual consistency throughout the video.
        For videos longer than 10 seconds, it may generate multiple segments.

        Args:
            prompt: Text prompt describing the video action
            opening_frame_url: URL of the opening frame image (required)
            closing_frame_url: Optional URL of closing frame for end matching
            target_duration: Target duration in seconds (15-20)
            progress_callback: Optional progress callback

        Returns:
            VideoResult with the generated video

        Raises:
            PiAPIError: If video generation fails
        """
        logger.info(
            "generating_extended_video",
            prompt_length=len(prompt),
            target_duration=target_duration,
        )

        client = await self._get_piapi_client()

        # For Wan 2.6, we can generate up to 20 seconds directly
        # If supported duration is less, we'd need to extend
        actual_duration = min(target_duration, 20)
        
        # Generate video from opening frame
        job_response, video_data = await client.generate_and_wait(
            prompt=prompt,
            duration=actual_duration,
            aspect_ratio="16:9",
            image_url=opening_frame_url,
            progress_callback=progress_callback,
        )

        logger.info(
            "extended_video_complete",
            task_id=job_response.task_id,
            video_size=len(video_data),
            duration_seconds=actual_duration,
        )

        return VideoResult(
            video_data=video_data,
            job_response=job_response,
            duration_seconds=actual_duration,
        )

    async def close(self) -> None:
        """Close all client connections and cleanup resources.

        Should be called when service is no longer needed.
        """
        if self._piapi_client is not None:
            await self._piapi_client.close()
            self._piapi_client = None
            logger.info("piapi_client_closed")

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