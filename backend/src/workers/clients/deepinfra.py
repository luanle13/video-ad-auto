"""DeepInfra Veo 3.1 Fast video generation API client."""
from typing import Any

import httpx

from src.shared.exceptions import DeepInfraError, ExternalServiceError
from src.workers.clients.base import BaseAPIClient
from src.workers.clients.deepinfra_models import DeepInfraJobResponse


class DeepInfraClient(BaseAPIClient):
    """Client for DeepInfra Veo 3.1 Fast video generation API.

    Provides methods for:
    - Generating videos from text prompts
    - Downloading generated videos

    The DeepInfra API is synchronous - it returns video URLs directly
    in the response without requiring polling.

    Example:
        >>> async with DeepInfraClient(api_key="your-key") as client:
        ...     response = await client.generate_video(
        ...         prompt="A cat playing with a ball",
        ...         config={"resolution": "720p", "aspect_ratio": "9:16"},
        ...     )
        ...     if response.video_url:
        ...         video_bytes = await client.download_video(response.video_url)
    """

    service_name = "DeepInfra"
    base_url = "https://api.deepinfra.com/v1/inference"
    default_timeout = 300.0  # 5 minutes - video generation can take time

    # Model endpoint
    MODEL_ENDPOINT = "/google/veo-3.1-fast"

    @property
    def headers(self) -> dict[str, str]:
        """Return HTTP headers for DeepInfra API requests.

        DeepInfra uses Authorization Bearer token for authentication.

        Returns:
            Dictionary with authorization headers
        """
        return {
            "Authorization": f"bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _wrap_exception(self, exc: Exception) -> ExternalServiceError:
        """Wrap exception as DeepInfraError.

        Args:
            exc: Original exception from API call

        Returns:
            DeepInfraError with error message
        """
        return DeepInfraError(str(exc))

    async def generate_video(
        self,
        prompt: str,
        config: dict[str, Any] | None = None,
        negative_prompt: str | None = None,
    ) -> DeepInfraJobResponse:
        """Generate a video using DeepInfra Veo 3.1 Fast API.

        This is a synchronous API call that returns video URLs directly
        when generation is complete.

        Args:
            prompt: Text prompt describing the video to generate
            config: Configuration dictionary with video parameters:
                - aspect_ratio: "16:9" or "9:16" (default: "9:16")
                - resolution: "720p" or "1080p" (default: "720p")
                - enhance_prompt: Whether to enhance prompt (default: True)
                - generate_audio: Whether to generate audio (default: False)
                - sample_count: Number of videos 1-4 (default: 1)
                - seed: Optional seed for reproducibility
            negative_prompt: Optional negative prompt to avoid certain content

        Returns:
            DeepInfraJobResponse with video URLs and status

        Raises:
            DeepInfraError: If API call fails

        Example:
            >>> response = await client.generate_video(
            ...     prompt="A cat playing with a ball",
            ...     config={
            ...         "resolution": "720p",
            ...         "aspect_ratio": "9:16",
            ...         "enhance_prompt": True,
            ...     },
            ...     negative_prompt="blurry, low quality"
            ... )
            >>> print(f"Video URL: {response.video_url}")
        """
        # Prepare request payload
        payload: dict[str, Any] = {
            "prompt": prompt,
        }

        # Apply config parameters
        if config:
            if "aspect_ratio" in config:
                payload["aspect_ratio"] = config["aspect_ratio"]
            if "resolution" in config:
                payload["resolution"] = config["resolution"]
            if "enhance_prompt" in config:
                payload["enhance_prompt"] = config["enhance_prompt"]
            if "generate_audio" in config:
                payload["generate_audio"] = config["generate_audio"]
            if "sample_count" in config:
                payload["sample_count"] = config["sample_count"]
            if "seed" in config:
                payload["seed"] = config["seed"]

        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        # Make API request
        response = await self.post(
            self.MODEL_ENDPOINT,
            json=payload,
        )

        # Parse response
        data = response.json()

        # Check for errors in response
        if data.get("status") == "error" or "error" in data:
            error_msg = data.get("error", "Unknown error occurred")
            raise DeepInfraError(f"Video generation failed: {error_msg}")

        # Parse and return response
        return DeepInfraJobResponse(
            status=data.get("status", "ok"),
            videos=data.get("videos", []),
            request_id=data.get("request_id", ""),
            inference_status=data.get("inference_status"),
            error=data.get("error"),
        )

    async def download_video(self, video_url: str) -> bytes:
        """Download video content from the provided URL.

        Args:
            video_url: URL of the video to download

        Returns:
            Bytes containing the video file content

        Raises:
            DeepInfraError: If download fails

        Example:
            >>> video_bytes = await client.download_video("https://example.com/video.mp4")
            >>> with open("downloaded_video.mp4", "wb") as f:
            ...     f.write(video_bytes)
        """
        # Create a temporary client to download the video
        # Since video URLs may be on different domains
        temp_client = httpx.AsyncClient(timeout=self._timeout)

        try:
            response = await temp_client.get(video_url)
            response.raise_for_status()

            return response.content
        except httpx.RequestError as e:
            raise self._wrap_exception(e)
        finally:
            await temp_client.aclose()

    async def generate_and_download(
        self,
        prompt: str,
        config: dict[str, Any] | None = None,
        negative_prompt: str | None = None,
    ) -> tuple[DeepInfraJobResponse, bytes]:
        """Generate a video and download it.

        Convenience method that combines generate_video and download_video.

        Args:
            prompt: Text prompt describing the video to generate
            config: Configuration dictionary with video parameters
            negative_prompt: Optional negative prompt to avoid certain content

        Returns:
            Tuple of (DeepInfraJobResponse with details, video bytes)

        Raises:
            DeepInfraError: If generation or download fails

        Example:
            >>> response, video_bytes = await client.generate_and_download(
            ...     prompt="A cat playing with a ball",
            ...     config={"resolution": "720p"}
            ... )
            >>> print(f"Request ID: {response.request_id}")
            >>> with open("output.mp4", "wb") as f:
            ...     f.write(video_bytes)
        """
        # Generate the video
        job_response = await self.generate_video(
            prompt=prompt,
            config=config,
            negative_prompt=negative_prompt,
        )

        # Check if we got a video URL
        if not job_response.video_url:
            raise DeepInfraError("No video URL in response")

        # Download the video
        video_bytes = await self.download_video(job_response.video_url)

        return job_response, video_bytes
