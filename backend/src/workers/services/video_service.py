"""Video generation service using DeepInfra Veo 3.1 Fast."""
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict

from src.shared.config import get_settings
from src.shared.exceptions import DeepInfraError
from src.shared.logging import get_logger
from src.shared.secrets import get_secrets
from src.workers.clients.deepinfra import DeepInfraClient, DeepInfraJobResponse


logger = get_logger(__name__)


class VideoResult(BaseModel):
    """Result of video generation operation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    video_data: bytes
    job_response: DeepInfraJobResponse
    duration_seconds: float


# Singleton instance
_video_service: "VideoService | None" = None


class VideoService:
    """Video generation service using DeepInfra Veo 3.1 Fast.

    Provides methods for generating high-quality videos from text prompts.
    Veo 3.1 Fast generates 8-second videos with optional audio generation.

    Key features:
    - High-fidelity video generation
    - Optional audio generation
    - Prompt enhancement
    - Fast generation times
    """

    def __init__(self) -> None:
        """Initialize video service."""
        self._deepinfra_client: DeepInfraClient | None = None

        logger.info("video_service_initialized")

    async def _get_deepinfra_client(self) -> DeepInfraClient:
        """Get or create DeepInfra client (lazy initialization).

        Returns:
            DeepInfraClient instance

        Raises:
            DeepInfraError: If API key cannot be retrieved
        """
        if self._deepinfra_client is None:
            try:
                settings = get_settings()
                secrets = get_secrets()

                # Get DeepInfra API key from Secrets Manager
                api_key = secrets.get_secret(settings.secrets_deepinfra_key)

                self._deepinfra_client = DeepInfraClient(api_key=api_key)
                logger.info("deepinfra_client_initialized")

            except Exception as e:
                raise DeepInfraError(f"Failed to initialize DeepInfra client: {e}")

        return self._deepinfra_client

    async def generate_video(
        self,
        prompt: str,
        opening_frame_url: str | None = None,
        config: dict[str, Any] | None = None,
        progress_callback: Callable | None = None,
    ) -> VideoResult:
        """Generate a video using DeepInfra Veo 3.1 Fast.

        Args:
            prompt: Text prompt describing the video to generate
            opening_frame_url: Optional URL of opening frame image (note: Veo 3.1 Fast
                is text-to-video only, so this is kept for API compatibility but not used)
            config: Configuration dictionary with video parameters:
                - aspect_ratio: "16:9" or "9:16" (default: "9:16")
                - resolution: "720p" or "1080p" (default: "720p")
                - enhance_prompt: Whether to enhance prompt (default: True)
                - generate_audio: Whether to generate audio (default: False)
                - negative_prompt: What to avoid in generation
            progress_callback: Optional callback function (kept for API compatibility,
                not used since DeepInfra API is synchronous)

        Returns:
            VideoResult with video data, job response, and duration

        Raises:
            DeepInfraError: If video generation fails

        Example:
            >>> result = await service.generate_video(
            ...     prompt="A hand picks up a fresh lemon from a wooden cutting board",
            ...     config={"resolution": "720p", "aspect_ratio": "9:16"},
            ... )
            >>> print(f"Video size: {len(result.video_data)} bytes")
        """
        logger.info(
            "generating_video",
            prompt_length=len(prompt),
            has_opening_frame=bool(opening_frame_url),
            config=config,
        )

        # Get DeepInfra client
        client = await self._get_deepinfra_client()

        # Note: Veo 3.1 Fast is text-to-video only
        if opening_frame_url:
            logger.info(
                "opening_frame_url_provided_but_not_used",
                reason="Veo 3.1 Fast is text-to-video only; image input not supported",
            )

        # Use default config if none provided
        if config is None:
            config = {
                "aspect_ratio": "9:16",
                "resolution": "720p",
                "enhance_prompt": True,
                "generate_audio": False,
            }

        # Map config to DeepInfra format
        deepinfra_config = self._map_config(config)
        negative_prompt = config.get("negative_prompt")

        # Generate and download video
        job_response, video_data = await client.generate_and_download(
            prompt=prompt,
            config=deepinfra_config,
            negative_prompt=negative_prompt,
        )

        # Veo 3.1 generates 8-second videos
        duration_seconds = 8.0

        logger.info(
            "video_generation_complete",
            request_id=job_response.request_id,
            video_size=len(video_data),
            duration_seconds=duration_seconds,
        )

        return VideoResult(
            video_data=video_data,
            job_response=job_response,
            duration_seconds=duration_seconds,
        )

    async def generate_extended_video(
        self,
        prompt: str,
        opening_frame_url: str,
        closing_frame_url: str | None = None,
        target_duration: int = 18,
        progress_callback: Callable | None = None,
    ) -> VideoResult:
        """Generate video (note: Veo 3.1 Fast generates fixed 8-second videos).

        This method is kept for API compatibility. Veo 3.1 Fast generates
        8-second videos regardless of target_duration.

        Args:
            prompt: Text prompt describing the video action
            opening_frame_url: URL of the opening frame image (not used by Veo 3.1)
            closing_frame_url: Optional URL of closing frame (not used)
            target_duration: Target duration in seconds (ignored, Veo generates 8s)
            progress_callback: Optional progress callback (not used)

        Returns:
            VideoResult with the generated 8-second video

        Raises:
            DeepInfraError: If video generation fails
        """
        logger.info(
            "generating_extended_video",
            prompt_length=len(prompt),
            target_duration=target_duration,
            note="Veo 3.1 Fast generates 8-second videos; target_duration ignored",
        )

        # Use standard generate_video - Veo 3.1 always generates 8 seconds
        return await self.generate_video(
            prompt=prompt,
            opening_frame_url=opening_frame_url,
            config={
                "aspect_ratio": "16:9",
                "resolution": "720p",
                "enhance_prompt": True,
                "generate_audio": False,
            },
            progress_callback=progress_callback,
        )

    def _map_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Map configuration to DeepInfra format.

        Handles mapping from various config formats to DeepInfra format.

        Args:
            config: Input configuration dictionary

        Returns:
            Configuration dictionary in DeepInfra format
        """
        deepinfra_config: dict[str, Any] = {}

        # Map aspect_ratio
        if "aspect_ratio" in config:
            aspect_ratio = config["aspect_ratio"]
            # Ensure it's a valid DeepInfra aspect ratio
            if aspect_ratio in ["16:9", "9:16"]:
                deepinfra_config["aspect_ratio"] = aspect_ratio
            else:
                # Default to 9:16 for vertical mobile content
                deepinfra_config["aspect_ratio"] = "9:16"

        # Map resolution
        if "resolution" in config:
            resolution = config["resolution"]
            if resolution in ["720p", "1080p"]:
                deepinfra_config["resolution"] = resolution
            else:
                deepinfra_config["resolution"] = "720p"

        # Map enhance_prompt
        if "enhance_prompt" in config:
            deepinfra_config["enhance_prompt"] = bool(config["enhance_prompt"])

        # Map generate_audio
        if "generate_audio" in config:
            deepinfra_config["generate_audio"] = bool(config["generate_audio"])

        # Map sample_count
        if "sample_count" in config:
            deepinfra_config["sample_count"] = min(max(int(config["sample_count"]), 1), 4)

        # Map seed
        if "seed" in config:
            deepinfra_config["seed"] = int(config["seed"])

        return deepinfra_config

    async def close(self) -> None:
        """Close all client connections and cleanup resources.

        Should be called when service is no longer needed.
        """
        if self._deepinfra_client is not None:
            await self._deepinfra_client.close()
            self._deepinfra_client = None
            logger.info("deepinfra_client_closed")

        logger.info("video_service_closed")


def get_video_service() -> VideoService:
    """Get video service singleton instance.

    Returns:
        VideoService instance

    Example:
        >>> service = get_video_service()
        >>> result = await service.generate_video(
        ...     "A cat playing with a ball",
        ...     config={"resolution": "720p"}
        ... )
    """
    global _video_service

    if _video_service is None:
        _video_service = VideoService()

    return _video_service
