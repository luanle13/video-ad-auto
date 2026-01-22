"""DeepInfra Veo 3.1 video generation models."""
from enum import Enum

from pydantic import BaseModel, Field


class DeepInfraVideoStatus(str, Enum):
    """DeepInfra video generation status.

    - OK: Video generation completed successfully
    - ERROR: Video generation failed
    """

    OK = "ok"
    ERROR = "error"


class DeepInfraVideoConfig(BaseModel):
    """Configuration for DeepInfra Veo 3.1 video generation.

    Attributes:
        aspect_ratio: Video aspect ratio (default: "9:16" for vertical mobile)
        resolution: Video resolution ("720p" or "1080p")
        enhance_prompt: Whether to enhance the prompt with additional context
        generate_audio: Whether to generate audio for the video
    """

    aspect_ratio: str = Field(
        default="9:16",
        description="Video aspect ratio (e.g., '9:16', '16:9')",
    )
    resolution: str = Field(
        default="720p",
        pattern="^(720p|1080p)$",
        description="Video resolution (720p or 1080p)",
    )
    enhance_prompt: bool = Field(
        default=True,
        description="Whether to enhance the prompt with additional context",
    )
    generate_audio: bool = Field(
        default=False,
        description="Whether to generate audio for the video",
    )
    sample_count: int = Field(
        default=1,
        ge=1,
        le=4,
        description="Number of videos to generate (1-4)",
    )


class DeepInfraGenerationRequest(BaseModel):
    """Request model for DeepInfra Veo 3.1 video generation.

    Attributes:
        prompt: Text prompt describing desired video content
        negative_prompt: Optional negative prompt (what to avoid)
        aspect_ratio: Video aspect ratio
        resolution: Video resolution
        enhance_prompt: Whether to enhance the prompt
        generate_audio: Whether to generate audio
        seed: Optional seed for reproducibility
        sample_count: Number of videos to generate
    """

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Text prompt for video generation",
    )
    negative_prompt: str | None = Field(
        None,
        max_length=1000,
        description="Negative prompt (what to avoid)",
    )
    aspect_ratio: str = Field(
        default="9:16",
        description="Video aspect ratio",
    )
    resolution: str = Field(
        default="720p",
        description="Video resolution",
    )
    enhance_prompt: bool = Field(
        default=True,
        description="Whether to enhance the prompt",
    )
    generate_audio: bool = Field(
        default=False,
        description="Whether to generate audio",
    )
    seed: int | None = Field(
        None,
        ge=0,
        le=4294967295,
        description="Seed for reproducibility",
    )
    sample_count: int = Field(
        default=1,
        ge=1,
        le=4,
        description="Number of videos to generate",
    )


class DeepInfraInferenceStatus(BaseModel):
    """Inference status from DeepInfra response.

    Attributes:
        status: Status of the inference ("succeeded", "failed", etc.)
        runtime_ms: Runtime in milliseconds
        cost: Cost of the inference
    """

    status: str = Field(
        ...,
        description="Status of the inference",
    )
    runtime_ms: int = Field(
        default=0,
        description="Runtime in milliseconds",
    )
    cost: float = Field(
        default=0.0,
        description="Cost of the inference",
    )


class DeepInfraJobResponse(BaseModel):
    """Response model for DeepInfra Veo 3.1 video generation.

    Attributes:
        status: Response status ("ok" or "error")
        videos: List of video URLs (paths to generated videos)
        request_id: Unique request identifier
        inference_status: Detailed inference status
        error: Error message if failed
    """

    status: str = Field(
        ...,
        description="Response status",
    )
    videos: list[str] = Field(
        default_factory=list,
        description="List of video URLs",
    )
    request_id: str = Field(
        default="",
        description="Unique request identifier",
    )
    inference_status: DeepInfraInferenceStatus | None = Field(
        None,
        description="Detailed inference status",
    )
    error: str | None = Field(
        None,
        description="Error message if failed",
    )

    @property
    def video_url(self) -> str | None:
        """Get the first video URL if available."""
        return self.videos[0] if self.videos else None

    @property
    def job_id(self) -> str:
        """Get the job/request ID."""
        return self.request_id
