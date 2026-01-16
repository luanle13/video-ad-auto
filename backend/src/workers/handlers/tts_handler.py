"""TTS Lambda handler for Step Functions workflow."""
from typing import Any

from pydantic import BaseModel, Field

from src.api.models.jobs import JobStatus
from src.shared.cache_service import get_cache_service
from src.shared.db import get_db
from src.shared.logging import get_logger
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
        audio_cached: Whether audio was stored in cache (if success)
        provider_used: Which TTS provider was actually used
        character_count: Number of characters processed
        duration_estimate_seconds: Estimated audio duration in seconds
        error: Error message (if failed)
    """

    success: bool = Field(..., description="Whether operation succeeded")
    audio_cached: bool = Field(default=False, description="Whether audio is stored in cache")
    provider_used: str | None = Field(None, description="TTS provider used")
    character_count: int | None = Field(None, description="Characters processed")
    duration_estimate_seconds: float | None = Field(None, description="Audio duration estimate")
    error: str | None = Field(None, description="Error message if failed")


async def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
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
        4. Store audio in cache
        5. Update job step_outputs with TTS metadata
        6. Return success output

    On Error:
        - Update job status to FAILED
        - Return error output
    """
    db = get_db()
    cache_service = get_cache_service()
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

        # Store audio in cache
        logger.info(
            "storing_audio_in_cache",
            job_id=input_data.job_id,
            audio_size=len(result.audio_data),
        )

        cache_service.store_audio(
            user_id=input_data.user_id,
            job_id=input_data.job_id,
            data=result.audio_data,
        )

        # Update job step_outputs
        step_output = {
            "provider_used": result.provider_used.value,
            "character_count": result.character_count,
            "duration_estimate_seconds": result.duration_estimate_seconds,
            "voice_id": result.voice_id,
            "audio_cached": True,
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
            audio_cached=True,
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
