from unittest.mock import MagicMock, AsyncMock


def create_mock_tts_response(audio_data: bytes = b"audio"):
    """Create mock TTS response."""
    mock_response = MagicMock()
    mock_response.audio_data = audio_data
    mock_response.content_type = "audio/mpeg"
    mock_response.character_count = 100
    return mock_response


def create_mock_kling_response(status: str = "completed"):
    """Create mock Kling API response."""
    mock_response = MagicMock()
    mock_job = MagicMock()
    mock_job.id = "test-job-id"
    mock_job.status = status
    mock_job.video_url = "https://example.com/test-video.mp4" if status == "completed" else None
    mock_job.progress = 100 if status == "completed" else 50
    mock_response.job = mock_job
    return mock_response


def create_mock_openai_response(content: str):
    """Create mock OpenAI API response."""
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage.prompt_tokens = 50
    mock_response.usage.completion_tokens = 100
    mock_response.usage.total_tokens = 150
    return mock_response


def create_mock_elevenlabs_response(audio_data: bytes = b"audio"):
    """Create mock ElevenLabs API response."""
    mock_response = MagicMock()
    mock_response.audio = audio_data
    mock_response.status = "completed"
    return mock_response


def create_mock_step_function_response(execution_arn: str = "test-execution-arn"):
    """Create mock Step Functions response."""
    mock_response = MagicMock()
    mock_response.executionArn = execution_arn
    mock_response.startDate = "2023-01-01T00:00:00Z"
    mock_response.status = "RUNNING"
    return mock_response


def create_mock_cognito_response(username: str = "testuser"):
    """Create mock Cognito response."""
    mock_response = MagicMock()
    mock_response.AuthenticationResult.AccessToken = "test-access-token"
    mock_response.AuthenticationResult.RefreshToken = "test-refresh-token"
    mock_response.AuthenticationResult.IdToken = "test-id-token"
    mock_response.AuthenticationResult.TokenType = "Bearer"
    return mock_response