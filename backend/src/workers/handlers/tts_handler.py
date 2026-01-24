"""TTS Lambda handler for Step Functions workflow."""
import asyncio
from typing import Any

from pydantic import BaseModel, Field

from src.api.models.jobs import JobStatus
from src.shared.db import get_db
from src.shared.logging import get_logger
from src.shared.storage import get_storage
from src.workers.services.tts_models import TTSProvider, TTSVoiceConfig
from src.workers.services.tts_service import get_tts_service

logger = get_logger(__name__)


class TTSHandlerInput(BaseModel):
    """Input model for TTS Lambda handler.

    Attributes:
        user_id: User who owns the job
        job_id: Job ID
        tts_script: Plain text script to convert to speech
        tts_ssml: Optional SSML-formatted script (overrides tts_script if provided)
        voice_gender: Voice gender ("male" or "female")
        voice_style: Optional voice style (e.g., "professional", "energetic")
        speaking_rate: Speaking rate modifier (0.5-2.0, default 1.0)
        provider: TTS provider to use (default: AUTO for fallback)
    """

    user_id: str = Field(..., description="User ID")
    job_id: str = Field(..., description="Job ID")
    tts_script: str = Field(..., min_length=1, description="Text script to convert")
    tts_ssml: str | None = Field(None, description="Optional SSML script")
    voice_gender: str = Field(..., pattern="^(male|female)$", description="Voice gender")
    voice_style: str | None = Field(None, description="Voice style")
    speaking_rate: float = Field(default=1.0, ge=0.5, le=2.0, description="Speaking rate")
    provider: TTSProvider = Field(default=TTSProvider.AUTO, description="TTS provider")


class TTSHandlerOutput(BaseModel):
    """Output model for TTS Lambda handler.

    Attributes:
        success: Whether TTS generation succeeded
        audio_s3_key: S3 key where audio is stored (if success)
        audio_s3_url: S3 URI (s3://bucket/key) for audio (if success)
        provider_used: Which TTS provider was actually used
        character_count: Number of characters processed
        duration_estimate_seconds: Estimated audio duration in seconds
        error: Error message (if failed)
    """

    success: bool = Field(..., description="Whether operation succeeded")
    audio_s3_key: str | None = Field(None, description="S3 key for audio file")
    audio_s3_url: str | None = Field(None, description="S3 URI for audio")
    provider_used: str | None = Field(None, description="TTS provider used")
    character_count: int | None = Field(None, description="Characters processed")
    duration_estimate_seconds: float | None = Field(None, description="Audio duration estimate")
    error: str | None = Field(None, description="Error message if failed")


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Sync wrapper for async TTS handler."""
    return asyncio.run(_async_handler(event, context))


async def _async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler for TTS generation in Step Functions workflow.

    Args:
        event: Step Functions event containing TTSHandlerInput
        context: Lambda context object

    Returns:
        dict with TTSHandlerOutput

    Workflow:
        1. Parse and validate input
        2. Update job status to GENERATING_TTS
        3. Generate speech using TTSService
        4. Upload audio to S3
        5. Update job step_outputs with TTS metadata
        6. Return success output

    On Error:
        - Update job status to FAILED
        - Return error output
    """
    db = get_db()
    storage = get_storage()
    tts_service = None

    try:
        # Parse input
        input_data = TTSHandlerInput(**event)

        logger.info(
            "tts_handler_started",
            user_id=input_data.user_id,
            job_id=input_data.job_id,
            provider=input_data.provider.value,
            text_length=len(input_data.tts_script),
        )

        # Update job status to GENERATING_TTS
        db.update_job_status(
            user_id=input_data.user_id,
            job_id=input_data.job_id,
            status=JobStatus.GENERATING_TTS.value,
        )

        # Create voice configuration
        voice_config = TTSVoiceConfig(
            gender=input_data.voice_gender,
            style=input_data.voice_style,
            speaking_rate=input_data.speaking_rate,
        )

        # Initialize TTS service
        tts_service = get_tts_service(provider=input_data.provider)

        # Determine text to use (SSML takes precedence)
        use_ssml = False
        text_to_convert = input_data.tts_script

        if input_data.tts_ssml:
            text_to_convert = input_data.tts_ssml
            use_ssml = True
            logger.info("using_ssml_input", job_id=input_data.job_id)

        # Generate speech
        logger.info(
            "generating_speech",
            job_id=input_data.job_id,
            use_ssml=use_ssml,
        )

        result = await tts_service.generate_speech(
            text=text_to_convert,
            voice_config=voice_config,
            provider=input_data.provider,
            use_ssml=use_ssml,
        )

        # Generate S3 key for audio
        audio_key = storage.generate_audio_key(
            user_id=input_data.user_id,
            job_id=input_data.job_id,
        )

        # Upload audio to S3
        logger.info(
            "uploading_audio_to_s3",
            job_id=input_data.job_id,
            s3_key=audio_key,
            audio_size=len(result.audio_data),
        )

        audio_s3_url = storage.upload_file(
            bucket_type="videos",  # Audio files go in videos bucket
            key=audio_key,
            body=result.audio_data,
            content_type=result.content_type,
        )

        # Update job step_outputs
        step_output = {
            "provider_used": result.provider_used.value,
            "character_count": result.character_count,
            "duration_estimate_seconds": result.duration_estimate_seconds,
            "voice_id": result.voice_id,
            "audio_s3_key": audio_key,
            "audio_s3_url": audio_s3_url,
        }

        db.update_job_step_output(
            user_id=input_data.user_id,
            job_id=input_data.job_id,
            step_name="tts",
            output=step_output,
        )

        logger.info(
            "tts_handler_success",
            job_id=input_data.job_id,
            provider=result.provider_used.value,
            duration=result.duration_estimate_seconds,
        )

        # Return success output
        return TTSHandlerOutput(
            success=True,
            audio_s3_key=audio_key,
            audio_s3_url=audio_s3_url,
            provider_used=result.provider_used.value,
            character_count=result.character_count,
            duration_estimate_seconds=result.duration_estimate_seconds,
        ).model_dump()

    except Exception as e:
        error_msg = str(e)
        logger.error(
            "tts_handler_failed",
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
                    error_message=f"TTS generation failed: {error_msg}",
                )
        except Exception as db_error:
            logger.error(
                "failed_to_update_job_status",
                error=str(db_error),
                job_id=event.get("job_id"),
            )

        # Return error output
        return TTSHandlerOutput(
            success=False,
            error=error_msg,
        ).model_dump()

    finally:
        # Cleanup TTS service
        if tts_service:
            try:
                await tts_service.close()
            except Exception as cleanup_error:
                logger.warning(
                    "tts_service_cleanup_failed",
                    error=str(cleanup_error),
                )
