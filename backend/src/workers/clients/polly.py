"""AWS Polly TTS client using boto3."""
from typing import Any

import boto3
from botocore.exceptions import ClientError

from src.shared.exceptions import PollyError
from src.shared.logging import get_logger
from src.workers.clients.polly_models import PollyEngine, PollyTTSResponse, PollyVoice

logger = get_logger(__name__)

# Singleton instance
_polly_client: "PollyClient | None" = None


def get_polly_client() -> "PollyClient":
    """Get singleton Polly client instance.

    Returns:
        PollyClient singleton instance

    Example:
        >>> client = get_polly_client()
        >>> response = await client.text_to_speech("Hello", PollyVoice.JOANNA.value)
    """
    global _polly_client
    if _polly_client is None:
        _polly_client = PollyClient()
    return _polly_client


class PollyClient:
    """Client for AWS Polly Text-to-Speech.

    Uses boto3 to interact with AWS Polly for text-to-speech synthesis.
    Supports both real-time synthesis and asynchronous long-form synthesis.

    Example:
        >>> client = PollyClient()
        >>> # Short text (< 3000 characters)
        >>> response = await client.text_to_speech(
        ...     text="Hello world",
        ...     voice_id=PollyVoice.JOANNA.value,
        ...     engine=PollyEngine.NEURAL,
        ... )
        >>> # Save audio
        >>> with open("output.mp3", "wb") as f:
        ...     f.write(response.audio_data)
    """

    def __init__(self) -> None:
        """Initialize Polly client with boto3."""
        try:
            self._client = boto3.client("polly")
            logger.info("polly_client_initialized")
        except Exception as e:
            logger.error("polly_client_init_failed", error=str(e))
            raise PollyError(f"Failed to initialize Polly client: {e}")

    async def text_to_speech(
        self,
        text: str,
        voice_id: str,
        engine: str = PollyEngine.NEURAL.value,
        use_ssml: bool = False,
    ) -> PollyTTSResponse:
        """Convert text to speech using AWS Polly.

        For text under 3000 characters. Returns audio data immediately.

        Args:
            text: Text or SSML to convert (max 3000 characters for neural)
            voice_id: Polly voice ID (use PollyVoice enum)
            engine: TTS engine ("neural" or "standard")
            use_ssml: Whether text is SSML format

        Returns:
            PollyTTSResponse with audio data and metadata

        Raises:
            PollyError: If synthesis fails

        Example:
            >>> from src.workers.clients.polly_models import PollyVoice
            >>> response = await client.text_to_speech(
            ...     text="<speak>Hello!</speak>",
            ...     voice_id=PollyVoice.JOANNA.value,
            ...     use_ssml=True,
            ... )
        """
        try:
            # Determine text type
            text_type = "ssml" if use_ssml else "text"

            logger.info(
                "polly_synthesize_speech",
                voice_id=voice_id,
                engine=engine,
                text_type=text_type,
                text_length=len(text),
            )

            # Call Polly synthesize_speech
            response = self._client.synthesize_speech(
                Text=text,
                TextType=text_type,
                VoiceId=voice_id,
                OutputFormat="mp3",
                Engine=engine,
            )

            # Read audio stream
            audio_data = response["AudioStream"].read()

            logger.info(
                "polly_synthesis_success",
                voice_id=voice_id,
                audio_size=len(audio_data),
                request_characters=response.get("RequestCharacters", len(text)),
            )

            return PollyTTSResponse(
                audio_data=audio_data,
                content_type="audio/mpeg",
                request_characters=response.get("RequestCharacters", len(text)),
                voice_id=voice_id,
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            logger.error(
                "polly_synthesis_failed",
                error_code=error_code,
                error_message=error_message,
                voice_id=voice_id,
            )

            raise PollyError(f"{error_code}: {error_message}")

        except Exception as e:
            logger.error(
                "polly_synthesis_unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise PollyError(f"Unexpected error: {e}")

    async def text_to_speech_long(
        self,
        text: str,
        voice_id: str,
        s3_bucket: str,
        s3_key: str,
        engine: str = PollyEngine.NEURAL.value,
        use_ssml: bool = False,
    ) -> str:
        """Start asynchronous TTS synthesis for long text (> 3000 characters).

        Uses Polly's StartSpeechSynthesisTask for texts up to 100,000 characters.
        Audio is saved to S3.

        Args:
            text: Text or SSML to convert (max 100,000 characters)
            voice_id: Polly voice ID
            s3_bucket: S3 bucket name for output
            s3_key: S3 key (path) for output file
            engine: TTS engine ("neural" or "standard")
            use_ssml: Whether text is SSML format

        Returns:
            Task ID for tracking synthesis progress

        Raises:
            PollyError: If task creation fails

        Example:
            >>> task_id = await client.text_to_speech_long(
            ...     text=long_text,
            ...     voice_id=PollyVoice.MATTHEW.value,
            ...     s3_bucket="my-bucket",
            ...     s3_key="audio/output.mp3",
            ... )
            >>> # Check status later
            >>> status = await client.get_task_status(task_id)
        """
        try:
            text_type = "ssml" if use_ssml else "text"

            logger.info(
                "polly_start_synthesis_task",
                voice_id=voice_id,
                engine=engine,
                text_type=text_type,
                text_length=len(text),
                s3_bucket=s3_bucket,
                s3_key=s3_key,
            )

            response = self._client.start_speech_synthesis_task(
                Text=text,
                TextType=text_type,
                VoiceId=voice_id,
                OutputFormat="mp3",
                Engine=engine,
                OutputS3BucketName=s3_bucket,
                OutputS3KeyPrefix=s3_key,
            )

            task = response.get("SynthesisTask", {})
            task_id = task.get("TaskId", "")

            logger.info(
                "polly_task_started",
                task_id=task_id,
                task_status=task.get("TaskStatus", "unknown"),
            )

            return task_id

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            logger.error(
                "polly_start_task_failed",
                error_code=error_code,
                error_message=error_message,
            )

            raise PollyError(f"{error_code}: {error_message}")

        except Exception as e:
            logger.error(
                "polly_start_task_unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise PollyError(f"Unexpected error: {e}")

    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """Get status of asynchronous synthesis task.

        Args:
            task_id: Task ID from text_to_speech_long()

        Returns:
            Dictionary with task status information:
            - TaskId: Task identifier
            - TaskStatus: "scheduled", "inProgress", "completed", "failed"
            - OutputUri: S3 URI when completed
            - CreationTime: Task creation timestamp
            - RequestCharacters: Number of characters processed

        Raises:
            PollyError: If status check fails

        Example:
            >>> status = await client.get_task_status(task_id)
            >>> if status["TaskStatus"] == "completed":
            ...     print(f"Audio at: {status['OutputUri']}")
        """
        try:
            logger.info("polly_get_task_status", task_id=task_id)

            response = self._client.get_speech_synthesis_task(TaskId=task_id)

            task = response.get("SynthesisTask", {})

            logger.info(
                "polly_task_status_retrieved",
                task_id=task_id,
                status=task.get("TaskStatus", "unknown"),
            )

            return task

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            logger.error(
                "polly_get_task_status_failed",
                error_code=error_code,
                error_message=error_message,
                task_id=task_id,
            )

            raise PollyError(f"{error_code}: {error_message}")

        except Exception as e:
            logger.error(
                "polly_get_task_status_unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise PollyError(f"Unexpected error: {e}")
