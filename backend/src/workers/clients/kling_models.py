"""Kling AI video generation models."""
from enum import Enum

from pydantic import BaseModel, Field


class KlingVideoStatus(str, Enum):
    """Kling AI video generation job status.

    - PENDING: Job created, waiting to be processed
    - PROCESSING: Video generation in progress
    - COMPLETED: Video generation completed successfully
    - FAILED: Video generation failed
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class KlingVideoConfig(BaseModel):
    """Configuration for Kling AI video generation.

    Attributes:
        aspect_ratio: Video aspect ratio (default: "9:16" for vertical mobile)
        duration: Video duration in seconds (5-10 seconds)
        mode: Generation mode ("standard" or "professional")
    """

    aspect_ratio: str = Field(
        default="9:16",
        description="Video aspect ratio (e.g., '9:16', '16:9', '1:1')",
    )
    duration: int = Field(
        default=5,
        ge=5,
        le=10,
        description="Video duration in seconds (5-10)",
    )
    mode: str = Field(
        default="standard",
        pattern="^(standard|professional)$",
        description="Generation mode (standard or professional)",
    )


class KlingGenerationRequest(BaseModel):
    """Request model for Kling AI video generation.

    Attributes:
        prompt: Text prompt describing desired video content
        negative_prompt: Optional negative prompt (what to avoid)
        config: Video configuration (aspect ratio, duration, mode)
        image_url: Optional input image URL (for image-to-video)
        audio_url: Optional audio URL for voiceover
    """

    prompt: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Text prompt for video generation",
    )
    negative_prompt: str | None = Field(
        None,
        max_length=1000,
        description="Negative prompt (what to avoid)",
    )
    config: KlingVideoConfig = Field(
        default_factory=KlingVideoConfig,
        description="Video generation configuration",
    )
    image_url: str | None = Field(
        None,
        description="Optional input image URL for image-to-video",
    )
    audio_url: str | None = Field(
        None,
        description="Optional audio URL for voiceover",
    )


class KlingJobResponse(BaseModel):
    """Response model for Kling AI video generation job.

    Attributes:
        job_id: Unique job identifier
        status: Current job status
        progress: Generation progress percentage (0-100)
        video_url: URL to generated video (if completed)
        thumbnail_url: URL to video thumbnail (if available)
        error_message: Error message (if failed)
        created_at: Job creation timestamp (ISO 8601)
        completed_at: Job completion timestamp (ISO 8601, if completed)
    """

    job_id: str = Field(
        ...,
        description="Unique job identifier",
    )
    status: KlingVideoStatus = Field(
        ...,
        description="Current job status",
    )
    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Generation progress (0-100)",
    )
    video_url: str | None = Field(
        None,
        description="URL to generated video",
    )
    thumbnail_url: str | None = Field(
        None,
        description="URL to video thumbnail",
    )
    error_message: str | None = Field(
        None,
        description="Error message if failed",
    )
    created_at: str = Field(
        ...,
        description="Job creation timestamp (ISO 8601)",
    )
    completed_at: str | None = Field(
        None,
        description="Job completion timestamp (ISO 8601)",
    )
