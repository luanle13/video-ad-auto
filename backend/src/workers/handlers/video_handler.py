"""Video Lambda handler for Step Functions workflow."""
from typing import Any

from pydantic import BaseModel, Field

from src.api.models.jobs import JobStatus
from src.shared.cache_service import get_cache_service
from src.shared.db import get_db
from src.shared.logging import get_logger
from src.workers.services.video_service import get_video_service


logger = get_logger(__name__)


class VideoHandlerInput(BaseModel):
    """Input model for Video Lambda handler.

    Attributes:
        user_id: User who owns the job
        job_id: Job ID
        video_prompt: Text prompt describing the video to generate
        aspect_ratio: Aspect ratio for the video (e.g., "16:9", "9:16", "1:1")
        duration: Duration of the video in seconds
    """

    user_id: str = Field(..., description="User ID")
    job_id: str = Field(..., description="Job ID")
    video_prompt: str = Field(..., min_length=1, description="Text prompt for video generation")
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio for video (e.g., '16:9', '9:16')")
    duration: int = Field(default=5, ge=1, le=60, description="Duration of video in seconds")


class VideoHandlerOutput(BaseModel):
    """Output model for Video Lambda handler.

    Attributes:
        success: Whether video generation succeeded
        video_cached: Whether video was stored in cache (if success)
        duration_seconds: Actual duration of the generated video in seconds
        error: Error message (if failed)
    """

    success: bool = Field(..., description="Whether operation succeeded")
    video_cached: bool = Field(default=False, description="Whether video is stored in cache")
    duration_seconds: float | None = Field(None, description="Actual video duration in seconds")
    error: str | None = Field(None, description="Error message if failed")


async def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler for video generation in Step Functions workflow.

    Args:
        event: Step Functions event containing VideoHandlerInput
        context: Lambda context object

    Returns:
        dict with VideoHandlerOutput

    Workflow:
        1. Parse and validate input
        2. Update job status to GENERATING_VIDEO
        3. Generate video using VideoService
        4. Store video in cache
        5. Update job with status=COMPLETE
        6. Return success output

    On Error:
        - Update job status to FAILED
        - Return error output
    """
    db = get_db()
    cache_service = get_cache_service()
    video_service = None

    try:
        # Parse input
        input_data = VideoHandlerInput(**event)

        logger.info(
            "video_handler_started",
            user_id=input_data.user_id,
            job_id=input_data.job_id,
            prompt_length=len(input_data.video_prompt),
        )

        # Update job status to GENERATING_VIDEO
        db.update_job_status(
            user_id=input_data.user_id,
            job_id=input_data.job_id,
            status=JobStatus.GENERATING_VIDEO.value,
        )

        # Initialize video service
        video_service = get_video_service()

        # Prepare config for video generation
        config = {
            "duration": input_data.duration,
            "aspect_ratio": input_data.aspect_ratio,
            "resolution": "1080x720"  # Default resolution
        }

        # Generate video
        logger.info(
            "generating_video",
            job_id=input_data.job_id,
            duration=input_data.duration,
            aspect_ratio=input_data.aspect_ratio,
        )

        result = await video_service.generate_video(
            prompt=input_data.video_prompt,
            config=config,
        )

        # Store video in cache
        logger.info(
            "storing_video_in_cache",
            job_id=input_data.job_id,
            video_size=len(result.video_data),
        )

        cache_service.store_video(
            user_id=input_data.user_id,
            job_id=input_data.job_id,
            data=result.video_data,
        )

        # Update job step output
        step_output = {
            "video_cached": True,
            "duration_seconds": result.duration_seconds,
            "job_response": result.job_response.data,  # Store job response data
        }

        db.update_job_step_output(
            user_id=input_data.user_id,
            job_id=input_data.job_id,
            step_name="video",
            output=step_output,
        )

        # Update job status to COMPLETE
        db.update_job_status(
            user_id=input_data.user_id,
            job_id=input_data.job_id,
            status=JobStatus.COMPLETE.value,
        )

        logger.info(
            "video_handler_success",
            job_id=input_data.job_id,
            duration=result.duration_seconds,
            video_size=len(result.video_data),
        )

        # Return success output
        return VideoHandlerOutput(
            success=True,
            video_cached=True,
            duration_seconds=result.duration_seconds,
        ).model_dump()

    except Exception as e:
        error_msg = str(e)
        logger.error(
            "video_handler_failed",
            error=error_msg,
            error_type=type(e).__name__,
            user_id=event.get("user_id"),
            job_id=event.get("job_id"),
        )

        # Update job status to FAILED
        try:
            if "user_id" in event and "job_id" in event:
                db.update_job_status(
                    user_id=event["user_id"],
                    job_id=event["job_id"],
                    status=JobStatus.FAILED.value,
                    error_message=f"Video generation failed: {error_msg}",
                )
        except Exception as db_error:
            logger.error(
                "failed_to_update_job_status",
                error=str(db_error),
                job_id=event.get("job_id"),
            )

        # Return error output
        return VideoHandlerOutput(
            success=False,
            error=error_msg,
        ).model_dump()

    finally:
        # Cleanup video service
        if video_service:
            try:
                await video_service.close()
            except Exception as cleanup_error:
                logger.warning(
                    "video_service_cleanup_failed",
                    error=str(cleanup_error),
                )