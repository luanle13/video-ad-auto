"""Job models."""
from enum import Enum
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, Field

from src.shared.validators import sanitize_for_prompt, validate_uuid_format

# Custom types with validation
UUIDStr = Annotated[str, AfterValidator(validate_uuid_format)]
PromptSafeStr = Annotated[str, AfterValidator(sanitize_for_prompt)]


class JobStatus(str, Enum):
    """Job status enum."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    ANALYZING = "ANALYZING"
    SCRIPTING = "SCRIPTING"
    PROMPTING = "PROMPTING"
    GENERATING_TTS = "GENERATING_TTS"
    GENERATING_VIDEO = "GENERATING_VIDEO"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class JobAdjustments(BaseModel):
    """Video generation adjustments."""

    background_style: str | None = Field(
        None,
        max_length=50,
        description="e.g., 'minimal', 'vibrant', 'professional'",
    )
    tone: str | None = Field(
        None,
        max_length=50,
        description="e.g., 'energetic', 'calm', 'humorous'",
    )
    emphasis: str | None = Field(
        None,
        max_length=100,
        description="Feature to emphasize",
    )
    duration_preference: int | None = Field(
        None,
        ge=10,
        le=60,
        description="Target duration in seconds",
    )
    additional_instructions: PromptSafeStr | None = Field(
        None,
        max_length=500,
        description="Additional instructions for video generation",
    )


class CreateJobRequest(BaseModel):
    """Create video generation job request."""

    product_id: UUIDStr = Field(..., description="Product UUID")
    adjustments: JobAdjustments | None = None


class RegenerateJobRequest(BaseModel):
    """Regenerate video with adjustments."""

    adjustments: JobAdjustments


class JobResponse(BaseModel):
    """Job response."""
    
    job_id: str
    user_id: str
    product_id: str
    status: JobStatus
    adjustments: dict[str, Any]
    step_outputs: dict[str, Any] = Field(default_factory=dict)
    video_url: str | None = None
    audio_url: str | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str


class JobListResponse(BaseModel):
    """Job list response."""
    
    jobs: list[JobResponse]
    count: int