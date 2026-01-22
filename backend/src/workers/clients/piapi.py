"""PiAPI video generation API client for Wan 2.6 model."""
import asyncio
from typing import Any, Callable

import httpx

from src.shared.exceptions import ExternalServiceError, PiAPIError, JobTimeoutError
from src.shared.logging import get_logger
from src.workers.clients.base import BaseAPIClient
from src.workers.clients.retry import RetryConfig


logger = get_logger(__name__)


class PiAPIJobResponse:
    """Response model for PiAPI job status."""
    
    def __init__(self, data: dict[str, Any]) -> None:
        self.task_id = data.get("task_id", data.get("id", ""))
        self.status = data.get("status", "")
        self.video_url = data.get("video_url", data.get("output", {}).get("video_url", ""))
        self.progress = data.get("progress", 0)
        self.created_at = data.get("created_at", "")
        self.completed_at = data.get("completed_at", "")
        self.error_message = data.get("error", data.get("message", ""))
        self.data = data


class PiAPIClient(BaseAPIClient):
    """Client for PiAPI video generation API using Wan 2.6 model.

    PiAPI provides access to various AI video generation models including Wan 2.6,
    which supports text-to-video and image-to-video generation up to 20 seconds.

    Features:
    - Text-to-video generation
    - Image-to-video generation (for style consistency)
    - Video extension capabilities
    - Realistic animation style

    Example:
        >>> async with PiAPIClient(api_key="your-key") as client:
        ...     task_id = await client.generate_video(
        ...         prompt="Kitchen blender mixing smoothie ingredients",
        ...         duration=10,
        ...         aspect_ratio="16:9"
        ...     )
        ...     result = await client.wait_for_completion(task_id)
        ...     video_bytes = await client.download_video(result.video_url)
    """

    service_name = "PiAPI"
    base_url = "https://api.piapi.ai/api/v1"
    default_timeout = 180.0
    
    # Configuration constants
    POLL_INTERVAL_SECONDS = 5
    MAX_POLL_ATTEMPTS = 120  # 10 minutes max wait
    
    # Wan 2.6 model identifier
    MODEL_WAN_26 = "wan-2.6"
    
    # Supported durations for Wan 2.6 (seconds)
    SUPPORTED_DURATIONS = [5, 10, 15, 20]

    @property
    def headers(self) -> dict[str, str]:
        """Return HTTP headers for PiAPI requests.

        PiAPI uses X-API-Key header for authentication.

        Returns:
            Dictionary with authentication headers
        """
        return {
            "X-API-Key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _wrap_exception(self, exc: Exception) -> ExternalServiceError:
        """Wrap exception as PiAPIError.

        Args:
            exc: Original exception from API call

        Returns:
            PiAPIError with error message
        """
        return PiAPIError(str(exc))

    async def generate_video(
        self,
        prompt: str,
        duration: int = 10,
        aspect_ratio: str = "16:9",
        negative_prompt: str | None = None,
        seed: int | None = None,
    ) -> str:
        """Generate video from text prompt using Wan 2.6 model.

        Args:
            prompt: Text prompt describing the video to generate
            duration: Video duration in seconds (5, 10, 15, or 20)
            aspect_ratio: Video aspect ratio ("16:9", "9:16", "1:1")
            negative_prompt: What to avoid in the video
            seed: Random seed for reproducibility

        Returns:
            Task ID for the video generation job

        Raises:
            PiAPIError: If API call fails or invalid parameters

        Example:
            >>> task_id = await client.generate_video(
            ...     prompt="Stainless steel blender on marble countertop",
            ...     duration=15,
            ...     aspect_ratio="16:9"
            ... )
        """
        # Validate duration
        if duration not in self.SUPPORTED_DURATIONS:
            closest = min(self.SUPPORTED_DURATIONS, key=lambda x: abs(x - duration))
            logger.warning(
                "duration_adjusted",
                requested=duration,
                adjusted=closest,
            )
            duration = closest

        payload = {
            "model": self.MODEL_WAN_26,
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "style": "realistic",  # Kitchen product ads need realistic style
            "motion_strength": 0.7,  # Moderate motion for product showcase
        }

        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["seed"] = seed

        # Default negative prompt for kitchen product videos
        if not negative_prompt:
            payload["negative_prompt"] = (
                "human face, person's face, facial features, eyes, mouth, "
                "blurry, low quality, distorted, deformed, watermark, text overlay, "
                "cartoon, anime, unrealistic"
            )

        logger.info(
            "generating_video_text2video",
            prompt_length=len(prompt),
            duration=duration,
            aspect_ratio=aspect_ratio,
            model=self.MODEL_WAN_26,
        )

        response = await self.post(
            "/video/generate",
            json=payload,
        )

        data = response.json()
        task_id = data.get("task_id", data.get("id", ""))

        if not task_id:
            raise PiAPIError("Failed to get task ID from response")

        logger.info("video_generation_started", task_id=task_id)
        return task_id

    async def generate_video_from_image(
        self,
        prompt: str,
        image_url: str,
        duration: int = 10,
        aspect_ratio: str = "16:9",
        negative_prompt: str | None = None,
        motion_strength: float = 0.6,
        seed: int | None = None,
    ) -> str:
        """Generate video from image using Wan 2.6 model (image-to-video).

        This is ideal for extending videos while maintaining style consistency.
        Use generated base/last screen images to ensure visual continuity.

        Args:
            prompt: Text prompt describing the motion/action in the video
            image_url: URL of the starting image
            duration: Video duration in seconds (5, 10, 15, or 20)
            aspect_ratio: Video aspect ratio
            negative_prompt: What to avoid in the video
            motion_strength: How much motion to apply (0.0-1.0)
            seed: Random seed for reproducibility

        Returns:
            Task ID for the video generation job

        Raises:
            PiAPIError: If API call fails

        Example:
            >>> task_id = await client.generate_video_from_image(
            ...     prompt="Camera slowly pans around the kitchen appliance",
            ...     image_url="https://example.com/base_frame.jpg",
            ...     duration=10,
            ... )
        """
        if duration not in self.SUPPORTED_DURATIONS:
            closest = min(self.SUPPORTED_DURATIONS, key=lambda x: abs(x - duration))
            duration = closest

        payload = {
            "model": self.MODEL_WAN_26,
            "mode": "image_to_video",
            "prompt": prompt,
            "image_url": image_url,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "style": "realistic",
            "motion_strength": motion_strength,
        }

        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        else:
            payload["negative_prompt"] = (
                "human face, person's face, facial features, eyes, mouth, "
                "blurry, low quality, distorted, deformed, watermark, text overlay"
            )
        
        if seed is not None:
            payload["seed"] = seed

        logger.info(
            "generating_video_image2video",
            prompt_length=len(prompt),
            duration=duration,
            motion_strength=motion_strength,
            model=self.MODEL_WAN_26,
        )

        response = await self.post(
            "/video/generate",
            json=payload,
        )

        data = response.json()
        task_id = data.get("task_id", data.get("id", ""))

        if not task_id:
            raise PiAPIError("Failed to get task ID from response")

        logger.info("image_to_video_started", task_id=task_id)
        return task_id

    async def extend_video(
        self,
        video_url: str,
        prompt: str,
        extension_duration: int = 10,
        direction: str = "forward",  # "forward" or "backward"
    ) -> str:
        """Extend an existing video using Wan 2.6.

        Args:
            video_url: URL of the video to extend
            prompt: Prompt describing the extension content
            extension_duration: Duration to add in seconds
            direction: Direction to extend ("forward" or "backward")

        Returns:
            Task ID for the extension job

        Raises:
            PiAPIError: If API call fails
        """
        payload = {
            "model": self.MODEL_WAN_26,
            "mode": "extend",
            "video_url": video_url,
            "prompt": prompt,
            "extension_duration": extension_duration,
            "direction": direction,
            "style": "realistic",
        }

        logger.info(
            "extending_video",
            extension_duration=extension_duration,
            direction=direction,
        )

        response = await self.post(
            "/video/extend",
            json=payload,
        )

        data = response.json()
        task_id = data.get("task_id", data.get("id", ""))

        if not task_id:
            raise PiAPIError("Failed to get task ID from extension response")

        return task_id

    async def get_task_status(self, task_id: str) -> PiAPIJobResponse:
        """Get the status of a video generation task.

        Args:
            task_id: ID of the video generation task

        Returns:
            PiAPIJobResponse with task status and details

        Raises:
            PiAPIError: If API call fails
        """
        response = await self.get(f"/task/{task_id}")
        data = response.json()
        return PiAPIJobResponse(data)

    async def wait_for_completion(
        self,
        task_id: str,
        progress_callback: Callable[[int, str], None] | None = None,
        timeout_seconds: int | None = None,
    ) -> PiAPIJobResponse:
        """Wait for video generation task to complete.

        Args:
            task_id: ID of the task to wait for
            progress_callback: Optional callback(progress_pct, status)
            timeout_seconds: Maximum time to wait

        Returns:
            PiAPIJobResponse with completed task details

        Raises:
            PiAPIError: If task fails
            JobTimeoutError: If task exceeds timeout
        """
        max_attempts = self.MAX_POLL_ATTEMPTS
        if timeout_seconds:
            max_attempts = timeout_seconds // self.POLL_INTERVAL_SECONDS

        for attempt in range(max_attempts):
            status = await self.get_task_status(task_id)

            if progress_callback:
                progress_callback(status.progress, status.status)

            if status.status in ["completed", "success", "finished"]:
                logger.info(
                    "video_generation_complete",
                    task_id=task_id,
                    video_url=status.video_url,
                )
                return status

            if status.status in ["failed", "error", "cancelled"]:
                raise PiAPIError(
                    f"Video generation failed: {status.error_message or status.status}"
                )

            logger.debug(
                "waiting_for_video",
                task_id=task_id,
                status=status.status,
                progress=status.progress,
                attempt=attempt + 1,
            )

            await asyncio.sleep(self.POLL_INTERVAL_SECONDS)

        raise JobTimeoutError(
            task_id,
            timeout_seconds or (max_attempts * self.POLL_INTERVAL_SECONDS),
        )

    async def generate_and_wait(
        self,
        prompt: str,
        duration: int = 10,
        aspect_ratio: str = "16:9",
        image_url: str | None = None,
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> tuple[PiAPIJobResponse, bytes]:
        """Generate video and wait for completion, returning video bytes.

        Convenience method that combines generation, waiting, and download.

        Args:
            prompt: Video generation prompt
            duration: Duration in seconds
            aspect_ratio: Video aspect ratio
            image_url: Optional starting image for image-to-video
            progress_callback: Optional progress callback

        Returns:
            Tuple of (PiAPIJobResponse, video_bytes)

        Raises:
            PiAPIError: If generation fails
        """
        if image_url:
            task_id = await self.generate_video_from_image(
                prompt=prompt,
                image_url=image_url,
                duration=duration,
                aspect_ratio=aspect_ratio,
            )
        else:
            task_id = await self.generate_video(
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
            )

        job_response = await self.wait_for_completion(
            task_id,
            progress_callback=progress_callback,
        )

        video_bytes = await self.download_video(job_response.video_url)

        return job_response, video_bytes

    async def download_video(self, video_url: str) -> bytes:
        """Download video content from URL.

        Args:
            video_url: URL of the video to download

        Returns:
            Bytes containing the video file

        Raises:
            PiAPIError: If download fails
        """
        temp_client = httpx.AsyncClient(timeout=self._timeout)

        try:
            response = await temp_client.get(video_url)
            response.raise_for_status()
            return response.content
        except httpx.RequestError as e:
            raise self._wrap_exception(e)
        finally:
            await temp_client.aclose()


# Singleton instance
_piapi_client: PiAPIClient | None = None


async def get_piapi_client() -> PiAPIClient:
    """Get PiAPI client singleton instance.

    Returns:
        PiAPIClient instance

    Raises:
        PiAPIError: If client cannot be initialized
    """
    global _piapi_client

    if _piapi_client is None:
        from src.shared.config import get_settings
        from src.shared.secrets import get_secrets

        settings = get_settings()
        secrets = get_secrets()

        try:
            api_key = secrets.get_secret(settings.secrets_piapi_key)
            _piapi_client = PiAPIClient(api_key=api_key)
        except Exception as e:
            raise PiAPIError(f"Failed to initialize PiAPI client: {e}")

    return _piapi_client
