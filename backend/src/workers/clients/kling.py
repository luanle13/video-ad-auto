"""Kling AI video generation API client."""
import asyncio
from typing import Any, Callable

import httpx

from src.shared.exceptions import ExternalServiceError, KlingError, JobTimeoutError
from src.workers.clients.base import BaseAPIClient
from src.workers.clients.retry import RetryConfig


class KlingJobResponse:
    """Response model for Kling AI job status."""
    
    def __init__(self, data: dict[str, Any]) -> None:
        self.job_id = data.get("id", "")
        self.status = data.get("status", "")
        self.video_url = data.get("video_url", "")
        self.prompt = data.get("prompt", "")
        self.negative_prompt = data.get("negative_prompt", "")
        self.created_at = data.get("created_at", "")
        self.updated_at = data.get("updated_at", "")
        self.data = data


class KlingClient(BaseAPIClient):
    """Client for Kling AI video generation API.

    Provides methods for:
    - Generating videos from text prompts and images
    - Checking job status
    - Downloading generated videos

    Example:
        >>> async with KlingClient(api_key="your-key") as client:
        ...     job_id = await client.generate_video(
        ...         prompt="A cat playing with a ball",
        ...         config={"duration": 5, "resolution": "1080x720"},
        ...     )
        ...     status = await client.get_job_status(job_id)
        ...     if status.status == "completed":
        ...         video_bytes = await client.download_video(status.video_url)
    """

    service_name = "KlingAI"
    base_url = "https://api.klingai.com/v1"
    default_timeout = 120.0
    
    # Configuration constants
    POLL_INTERVAL_SECONDS = 10
    MAX_POLL_ATTEMPTS = 60

    @property
    def headers(self) -> dict[str, str]:
        """Return HTTP headers for Kling AI API requests.

        Kling AI uses Authorization Bearer token for authentication and
        requires X-API-Version header.

        Returns:
            Dictionary with authorization and version headers
        """
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Version": "v1",
        }

    def _wrap_exception(self, exc: Exception) -> ExternalServiceError:
        """Wrap exception as KlingError.

        Args:
            exc: Original exception from API call

        Returns:
            KlingError with error message
        """
        return KlingError(str(exc))

    async def generate_video(
        self,
        prompt: str,
        config: dict[str, Any],
        negative_prompt: str | None = None,
        image_url: str | None = None,
        audio_url: str | None = None,
    ) -> str:
        """Generate a video using Kling AI API.

        Args:
            prompt: Text prompt describing the video to generate
            config: Configuration dictionary with video parameters
            negative_prompt: Optional negative prompt to avoid certain content
            image_url: Optional URL of an image to use as base for video
            audio_url: Optional URL of audio to accompany the video

        Returns:
            Job ID for the video generation task

        Raises:
            KlingError: If API call fails

        Example:
            >>> job_id = await client.generate_video(
            ...     prompt="A cat playing with a ball",
            ...     config={
            ...         "duration": 5,
            ...         "resolution": "1080x720",
            ...         "motion_strength": 1.0
            ...     },
            ...     negative_prompt="blurry, low quality"
            ... )
        """
        # Prepare request payload
        payload = {
            "prompt": prompt,
            "config": config,
        }

        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if image_url:
            payload["image_url"] = image_url
        if audio_url:
            payload["audio_url"] = audio_url

        # Make API request to create video generation job
        response = await self.post(
            "/video-generation",
            json=payload,
        )

        # Parse response to extract job ID
        data = response.json()
        job_id = data.get("id", "")

        if not job_id:
            raise KlingError("Failed to get job ID from response")

        return job_id

    async def get_job_status(self, job_id: str) -> KlingJobResponse:
        """Get the status of a video generation job.

        Args:
            job_id: ID of the video generation job

        Returns:
            KlingJobResponse with job status and details

        Raises:
            KlingError: If API call fails

        Example:
            >>> status = await client.get_job_status("job-12345")
            >>> print(f"Status: {status.status}")
            >>> if status.status == "completed":
            ...     print(f"Video URL: {status.video_url}")
        """
        # Make API request to get job status
        response = await self.get(f"/video-generation/{job_id}")

        # Parse response and create KlingJobResponse
        data = response.json()
        return KlingJobResponse(data)

    async def download_video(self, video_url: str) -> bytes:
        """Download video content from the provided URL.

        Args:
            video_url: URL of the video to download

        Returns:
            Bytes containing the video file content

        Raises:
            KlingError: If download fails

        Example:
            >>> video_bytes = await client.download_video("https://example.com/video.mp4")
            >>> with open("downloaded_video.mp4", "wb") as f:
            ...     f.write(video_bytes)
        """
        # Create a temporary client to download the video
        # Since this might be a direct URL not using our base_url
        temp_client = httpx.AsyncClient(timeout=self._timeout)

        try:
            response = await temp_client.get(video_url)
            response.raise_for_status()

            return response.content
        except httpx.RequestError as e:
            raise self._wrap_exception(e)
        finally:
            await temp_client.aclose()

    async def wait_for_completion(
        self,
        job_id: str,
        poll_interval: float | None = None,
        max_attempts: int | None = None,
        progress_callback: Callable | None = None,
    ) -> KlingJobResponse:
        """Wait for a video generation job to complete by polling its status.

        Args:
            job_id: ID of the video generation job to wait for
            poll_interval: Seconds between status checks (uses default if None)
            max_attempts: Maximum number of polling attempts (uses default if None)
            progress_callback: Optional async callback function called with each status update

        Returns:
            KlingJobResponse with completed job details

        Raises:
            KlingError: If job fails
            JobTimeoutError: If max_attempts exceeded

        Example:
            >>> status = await client.wait_for_completion("job-12345")
            >>> print(f"Job completed: {status.status}")
            >>> print(f"Video URL: {status.video_url}")
        """
        poll_interval = poll_interval or self.POLL_INTERVAL_SECONDS
        max_attempts = max_attempts or self.MAX_POLL_ATTEMPTS

        for attempt in range(max_attempts):
            # Get current job status
            job_response = await self.get_job_status(job_id)

            # Call progress callback if provided
            if progress_callback:
                await progress_callback(job_response) if asyncio.iscoroutinefunction(progress_callback) else progress_callback(job_response)

            # Check job status
            if job_response.status.lower() in ["completed", "success", "done"]:
                return job_response
            elif job_response.status.lower() in ["failed", "error"]:
                raise KlingError(f"Video generation failed: {job_response.status}")

            # Wait before next poll (except on last attempt)
            if attempt < max_attempts - 1:
                await asyncio.sleep(poll_interval)

        # If we've reached max attempts without completion
        raise JobTimeoutError(job_id, f"Video generation timed out after {max_attempts} attempts with {poll_interval}s intervals")

    async def generate_and_wait(
        self,
        prompt: str,
        config: dict[str, Any],
        negative_prompt: str | None = None,
        image_url: str | None = None,
        audio_url: str | None = None,
        poll_interval: float | None = None,
        max_attempts: int | None = None,
        progress_callback: Callable | None = None,
    ) -> tuple[KlingJobResponse, bytes]:
        """Generate a video and wait for completion, then download it.

        Convenience method that combines generate_video, wait_for_completion,
        and download_video in a single call.

        Args:
            prompt: Text prompt describing the video to generate
            config: Configuration dictionary with video parameters
            negative_prompt: Optional negative prompt to avoid certain content
            image_url: Optional URL of an image to use as base for video
            audio_url: Optional URL of audio to accompany the video
            poll_interval: Seconds between status checks (uses default if None)
            max_attempts: Maximum number of polling attempts (uses default if None)
            progress_callback: Optional async callback function called with each status update

        Returns:
            Tuple of (KlingJobResponse with completed job details, video bytes)

        Raises:
            KlingError: If generation fails or times out

        Example:
            >>> status, video_bytes = await client.generate_and_wait(
            ...     prompt="A cat playing with a ball",
            ...     config={"duration": 5, "resolution": "1080x720"}
            ... )
            >>> print(f"Video generated: {status.video_url}")
            >>> with open("output.mp4", "wb") as f:
            ...     f.write(video_bytes)
        """
        # Generate the video and get job ID
        job_id = await self.generate_video(
            prompt=prompt,
            config=config,
            negative_prompt=negative_prompt,
            image_url=image_url,
            audio_url=audio_url,
        )

        # Wait for completion
        job_response = await self.wait_for_completion(
            job_id=job_id,
            poll_interval=poll_interval,
            max_attempts=max_attempts,
            progress_callback=progress_callback,
        )

        # Download the completed video
        video_bytes = await self.download_video(job_response.video_url)

        return job_response, video_bytes