"""Tests for AWS Polly TTS client."""
from io import BytesIO
from unittest.mock import MagicMock, Mock, patch

import pytest
from botocore.exceptions import ClientError

from src.shared.exceptions import PollyError
from src.workers.clients.polly import PollyClient, get_polly_client
from src.workers.clients.polly_models import (
    PollyEngine,
    PollyTTSResponse,
    PollyVoice,
)


class TestGetPollyClient:
    """Tests for get_polly_client singleton function."""

    @patch("src.workers.clients.polly.boto3")
    def test_get_polly_client_returns_instance(self, mock_boto3: Mock) -> None:
        """Test that get_polly_client returns PollyClient instance."""
        # Reset singleton
        import src.workers.clients.polly as polly_module

        polly_module._polly_client = None

        mock_boto3.client.return_value = Mock()

        client = get_polly_client()

        assert isinstance(client, PollyClient)
        mock_boto3.client.assert_called_once_with("polly")

    @patch("src.workers.clients.polly.boto3")
    def test_get_polly_client_returns_same_instance(self, mock_boto3: Mock) -> None:
        """Test that get_polly_client returns same instance on multiple calls."""
        import src.workers.clients.polly as polly_module

        polly_module._polly_client = None

        mock_boto3.client.return_value = Mock()

        client1 = get_polly_client()
        client2 = get_polly_client()

        assert client1 is client2
        # Should only create boto3 client once
        assert mock_boto3.client.call_count == 1


class TestSelectVoiceByGenderAccent:
    """Tests for PollyVoice.select_voice method."""

    def test_select_voice_female_us(self) -> None:
        """Test selecting female US voice returns JOANNA."""
        voice_id = PollyVoice.select_voice("female", "us")

        assert voice_id == PollyVoice.JOANNA.value

    def test_select_voice_female_british(self) -> None:
        """Test selecting female British voice returns AMY."""
        voice_id = PollyVoice.select_voice("female", "british")

        assert voice_id == PollyVoice.AMY.value

    def test_select_voice_female_uk(self) -> None:
        """Test selecting female UK voice returns AMY."""
        voice_id = PollyVoice.select_voice("female", "uk")

        assert voice_id == PollyVoice.AMY.value

    def test_select_voice_female_default(self) -> None:
        """Test selecting female with no accent returns JOANNA (US default)."""
        voice_id = PollyVoice.select_voice("female")

        assert voice_id == PollyVoice.JOANNA.value

    def test_select_voice_female_unknown_accent(self) -> None:
        """Test selecting female with unknown accent returns JOANNA (US default)."""
        voice_id = PollyVoice.select_voice("female", "australian")

        assert voice_id == PollyVoice.JOANNA.value

    def test_select_voice_male_us(self) -> None:
        """Test selecting male US voice returns MATTHEW."""
        voice_id = PollyVoice.select_voice("male", "us")

        assert voice_id == PollyVoice.MATTHEW.value

    def test_select_voice_male_british(self) -> None:
        """Test selecting male British voice returns BRIAN."""
        voice_id = PollyVoice.select_voice("male", "british")

        assert voice_id == PollyVoice.BRIAN.value

    def test_select_voice_male_uk(self) -> None:
        """Test selecting male UK voice returns BRIAN."""
        voice_id = PollyVoice.select_voice("male", "uk")

        assert voice_id == PollyVoice.BRIAN.value

    def test_select_voice_male_default(self) -> None:
        """Test selecting male with no accent returns MATTHEW (US default)."""
        voice_id = PollyVoice.select_voice("male")

        assert voice_id == PollyVoice.MATTHEW.value

    def test_select_voice_male_unknown_accent(self) -> None:
        """Test selecting male with unknown accent returns MATTHEW (US default)."""
        voice_id = PollyVoice.select_voice("male", "indian")

        assert voice_id == PollyVoice.MATTHEW.value

    def test_select_voice_case_insensitive_gender(self) -> None:
        """Test that gender selection is case-insensitive."""
        voice_id_upper = PollyVoice.select_voice("MALE", "british")
        voice_id_lower = PollyVoice.select_voice("male", "british")
        voice_id_mixed = PollyVoice.select_voice("Male", "british")

        assert voice_id_upper == voice_id_lower == voice_id_mixed
        assert voice_id_upper == PollyVoice.BRIAN.value

    def test_select_voice_case_insensitive_accent(self) -> None:
        """Test that accent selection is case-insensitive."""
        voice_id_upper = PollyVoice.select_voice("female", "BRITISH")
        voice_id_lower = PollyVoice.select_voice("female", "british")
        voice_id_mixed = PollyVoice.select_voice("female", "British")

        assert voice_id_upper == voice_id_lower == voice_id_mixed
        assert voice_id_upper == PollyVoice.AMY.value

    def test_select_voice_invalid_gender_raises_error(self) -> None:
        """Test that invalid gender raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            PollyVoice.select_voice("invalid", "us")

        assert "Invalid gender" in str(exc_info.value)
        assert "male" in str(exc_info.value)
        assert "female" in str(exc_info.value)


class TestTextToSSMLConversion:
    """Tests for PollyVoice.text_to_ssml method."""

    def test_text_to_ssml_plain_text(self) -> None:
        """Test SSML conversion without prosody attributes."""
        ssml = PollyVoice.text_to_ssml("Hello world")

        assert ssml == "<speak>Hello world</speak>"

    def test_text_to_ssml_with_rate(self) -> None:
        """Test SSML conversion with rate attribute."""
        ssml = PollyVoice.text_to_ssml("Hello", rate="fast")

        assert ssml == '<speak><prosody rate="fast">Hello</prosody></speak>'

    def test_text_to_ssml_with_pitch(self) -> None:
        """Test SSML conversion with pitch attribute."""
        ssml = PollyVoice.text_to_ssml("Hello", pitch="high")

        assert ssml == '<speak><prosody pitch="high">Hello</prosody></speak>'

    def test_text_to_ssml_with_volume(self) -> None:
        """Test SSML conversion with volume attribute."""
        ssml = PollyVoice.text_to_ssml("Hello", volume="loud")

        assert ssml == '<speak><prosody volume="loud">Hello</prosody></speak>'

    def test_text_to_ssml_with_all_prosody(self) -> None:
        """Test SSML conversion with rate, pitch, and volume."""
        ssml = PollyVoice.text_to_ssml("Hello!", rate="fast", pitch="high", volume="loud")

        assert "<speak><prosody" in ssml
        assert 'rate="fast"' in ssml
        assert 'pitch="high"' in ssml
        assert 'volume="loud"' in ssml
        assert ">Hello!</prosody></speak>" in ssml

    def test_text_to_ssml_with_rate_and_pitch(self) -> None:
        """Test SSML conversion with rate and pitch."""
        ssml = PollyVoice.text_to_ssml("Test", rate="slow", pitch="low")

        assert 'rate="slow"' in ssml
        assert 'pitch="low"' in ssml

    def test_text_to_ssml_escapes_ampersand(self) -> None:
        """Test SSML conversion escapes ampersand character."""
        ssml = PollyVoice.text_to_ssml("Tom & Jerry")

        assert "Tom &amp; Jerry" in ssml
        assert "<speak>Tom &amp; Jerry</speak>" == ssml

    def test_text_to_ssml_escapes_less_than(self) -> None:
        """Test SSML conversion escapes less-than character."""
        ssml = PollyVoice.text_to_ssml("5 < 10")

        assert "5 &lt; 10" in ssml

    def test_text_to_ssml_escapes_greater_than(self) -> None:
        """Test SSML conversion escapes greater-than character."""
        ssml = PollyVoice.text_to_ssml("10 > 5")

        assert "10 &gt; 5" in ssml

    def test_text_to_ssml_escapes_double_quotes(self) -> None:
        """Test SSML conversion escapes double quote character."""
        ssml = PollyVoice.text_to_ssml('Say "hello"')

        assert "Say &quot;hello&quot;" in ssml

    def test_text_to_ssml_escapes_single_quotes(self) -> None:
        """Test SSML conversion escapes single quote character."""
        ssml = PollyVoice.text_to_ssml("It's great")

        assert "It&apos;s great" in ssml

    def test_text_to_ssml_escapes_multiple_special_chars(self) -> None:
        """Test SSML conversion escapes all special characters."""
        text = "Tom & Jerry say: \"Hi!\" It's <fun>"
        ssml = PollyVoice.text_to_ssml(text)

        assert "&amp;" in ssml
        assert "&quot;" in ssml
        assert "&apos;" in ssml
        assert "&lt;" in ssml
        assert "&gt;" in ssml

    def test_text_to_ssml_rate_values(self) -> None:
        """Test SSML with various rate values."""
        for rate in ["x-slow", "slow", "medium", "fast", "x-fast"]:
            ssml = PollyVoice.text_to_ssml("Test", rate=rate)
            assert f'rate="{rate}"' in ssml

    def test_text_to_ssml_pitch_values(self) -> None:
        """Test SSML with various pitch values."""
        for pitch in ["x-low", "low", "medium", "high", "x-high"]:
            ssml = PollyVoice.text_to_ssml("Test", pitch=pitch)
            assert f'pitch="{pitch}"' in ssml

    def test_text_to_ssml_volume_values(self) -> None:
        """Test SSML with various volume values."""
        for volume in ["silent", "x-soft", "soft", "medium", "loud", "x-loud"]:
            ssml = PollyVoice.text_to_ssml("Test", volume=volume)
            assert f'volume="{volume}"' in ssml


class TestPollyClientInitialization:
    """Tests for PollyClient initialization."""

    @patch("src.workers.clients.polly.boto3")
    def test_init_creates_boto3_client(self, mock_boto3: Mock) -> None:
        """Test that initialization creates boto3 polly client."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        client = PollyClient()

        mock_boto3.client.assert_called_once_with("polly")
        assert client._client is mock_client

    @patch("src.workers.clients.polly.boto3")
    def test_init_failure_raises_polly_error(self, mock_boto3: Mock) -> None:
        """Test that initialization failure raises PollyError."""
        mock_boto3.client.side_effect = Exception("AWS credentials not found")

        with pytest.raises(PollyError) as exc_info:
            PollyClient()

        assert "Failed to initialize" in str(exc_info.value)
        assert "AWS credentials not found" in str(exc_info.value)


class TestTextToSpeech:
    """Tests for text_to_speech method."""

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_text_to_speech_success(self, mock_boto3: Mock) -> None:
        """Test successful text-to-speech synthesis."""
        # Setup mock
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        audio_bytes = b"fake audio data"
        mock_stream = BytesIO(audio_bytes)

        mock_client.synthesize_speech.return_value = {
            "AudioStream": mock_stream,
            "RequestCharacters": 11,
        }

        client = PollyClient()

        # Call method
        response = await client.text_to_speech(
            text="Hello world",
            voice_id=PollyVoice.JOANNA.value,
        )

        # Verify boto3 call
        mock_client.synthesize_speech.assert_called_once_with(
            Text="Hello world",
            TextType="text",
            VoiceId="Joanna",
            OutputFormat="mp3",
            Engine="neural",
        )

        # Verify response
        assert isinstance(response, PollyTTSResponse)
        assert response.audio_data == audio_bytes
        assert response.content_type == "audio/mpeg"
        assert response.request_characters == 11
        assert response.voice_id == "Joanna"

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_text_to_speech_with_ssml(self, mock_boto3: Mock) -> None:
        """Test text-to-speech with SSML input."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        mock_stream = BytesIO(b"audio")
        mock_client.synthesize_speech.return_value = {
            "AudioStream": mock_stream,
            "RequestCharacters": 20,
        }

        client = PollyClient()

        ssml_text = "<speak>Hello!</speak>"
        await client.text_to_speech(
            text=ssml_text,
            voice_id=PollyVoice.MATTHEW.value,
            use_ssml=True,
        )

        # Verify SSML text type
        call_kwargs = mock_client.synthesize_speech.call_args.kwargs
        assert call_kwargs["Text"] == ssml_text
        assert call_kwargs["TextType"] == "ssml"

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_text_to_speech_with_standard_engine(self, mock_boto3: Mock) -> None:
        """Test text-to-speech with standard engine."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        mock_stream = BytesIO(b"audio")
        mock_client.synthesize_speech.return_value = {
            "AudioStream": mock_stream,
            "RequestCharacters": 5,
        }

        client = PollyClient()

        await client.text_to_speech(
            text="Test",
            voice_id=PollyVoice.AMY.value,
            engine=PollyEngine.STANDARD.value,
        )

        call_kwargs = mock_client.synthesize_speech.call_args.kwargs
        assert call_kwargs["Engine"] == "standard"

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_text_to_speech_default_engine_is_neural(
        self, mock_boto3: Mock
    ) -> None:
        """Test that default engine is neural."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        mock_stream = BytesIO(b"audio")
        mock_client.synthesize_speech.return_value = {
            "AudioStream": mock_stream,
            "RequestCharacters": 4,
        }

        client = PollyClient()

        await client.text_to_speech(
            text="Test",
            voice_id=PollyVoice.JOANNA.value,
        )

        call_kwargs = mock_client.synthesize_speech.call_args.kwargs
        assert call_kwargs["Engine"] == "neural"

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_text_to_speech_output_format_is_mp3(
        self, mock_boto3: Mock
    ) -> None:
        """Test that output format is MP3."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        mock_stream = BytesIO(b"audio")
        mock_client.synthesize_speech.return_value = {
            "AudioStream": mock_stream,
            "RequestCharacters": 4,
        }

        client = PollyClient()

        await client.text_to_speech(
            text="Test",
            voice_id=PollyVoice.JOEY.value,
        )

        call_kwargs = mock_client.synthesize_speech.call_args.kwargs
        assert call_kwargs["OutputFormat"] == "mp3"

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_text_to_speech_client_error_raises_polly_error(
        self, mock_boto3: Mock
    ) -> None:
        """Test that ClientError is wrapped as PollyError."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        # Simulate ClientError
        error_response = {
            "Error": {"Code": "InvalidSsml", "Message": "Invalid SSML syntax"}
        }
        mock_client.synthesize_speech.side_effect = ClientError(
            error_response, "SynthesizeSpeech"
        )

        client = PollyClient()

        with pytest.raises(PollyError) as exc_info:
            await client.text_to_speech(
                text="<speak>Bad SSML",
                voice_id=PollyVoice.JOANNA.value,
                use_ssml=True,
            )

        assert "InvalidSsml" in str(exc_info.value)
        assert "Invalid SSML syntax" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_text_to_speech_unexpected_error_raises_polly_error(
        self, mock_boto3: Mock
    ) -> None:
        """Test that unexpected errors are wrapped as PollyError."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        mock_client.synthesize_speech.side_effect = RuntimeError("Unexpected failure")

        client = PollyClient()

        with pytest.raises(PollyError) as exc_info:
            await client.text_to_speech(
                text="Test",
                voice_id=PollyVoice.BRIAN.value,
            )

        assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_text_to_speech_request_characters_fallback(
        self, mock_boto3: Mock
    ) -> None:
        """Test fallback to text length when RequestCharacters not in response."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        mock_stream = BytesIO(b"audio")
        # Response without RequestCharacters
        mock_client.synthesize_speech.return_value = {"AudioStream": mock_stream}

        client = PollyClient()

        text = "Test text"
        response = await client.text_to_speech(
            text=text,
            voice_id=PollyVoice.KENDRA.value,
        )

        # Should use text length as fallback
        assert response.request_characters == len(text)


class TestTextToSpeechLong:
    """Tests for text_to_speech_long method."""

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_text_to_speech_long_success(self, mock_boto3: Mock) -> None:
        """Test successful long-form synthesis task."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        mock_client.start_speech_synthesis_task.return_value = {
            "SynthesisTask": {
                "TaskId": "task-123",
                "TaskStatus": "scheduled",
            }
        }

        client = PollyClient()

        task_id = await client.text_to_speech_long(
            text="Long text content here" * 200,
            voice_id=PollyVoice.MATTHEW.value,
            s3_bucket="my-bucket",
            s3_key="audio/output.mp3",
        )

        # Verify boto3 call
        mock_client.start_speech_synthesis_task.assert_called_once()
        call_kwargs = mock_client.start_speech_synthesis_task.call_args.kwargs

        assert call_kwargs["VoiceId"] == "Matthew"
        assert call_kwargs["OutputS3BucketName"] == "my-bucket"
        assert call_kwargs["OutputS3KeyPrefix"] == "audio/output.mp3"
        assert call_kwargs["Engine"] == "neural"
        assert call_kwargs["OutputFormat"] == "mp3"
        assert call_kwargs["TextType"] == "text"

        # Verify response
        assert task_id == "task-123"

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_text_to_speech_long_with_ssml(self, mock_boto3: Mock) -> None:
        """Test long-form synthesis with SSML."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        mock_client.start_speech_synthesis_task.return_value = {
            "SynthesisTask": {"TaskId": "task-456", "TaskStatus": "scheduled"}
        }

        client = PollyClient()

        await client.text_to_speech_long(
            text="<speak>Long SSML text</speak>",
            voice_id=PollyVoice.AMY.value,
            s3_bucket="bucket",
            s3_key="key",
            use_ssml=True,
        )

        call_kwargs = mock_client.start_speech_synthesis_task.call_args.kwargs
        assert call_kwargs["TextType"] == "ssml"

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_text_to_speech_long_client_error(self, mock_boto3: Mock) -> None:
        """Test that ClientError in long synthesis is wrapped."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        error_response = {
            "Error": {
                "Code": "TextLengthExceededException",
                "Message": "Text too long",
            }
        }
        mock_client.start_speech_synthesis_task.side_effect = ClientError(
            error_response, "StartSpeechSynthesisTask"
        )

        client = PollyClient()

        with pytest.raises(PollyError) as exc_info:
            await client.text_to_speech_long(
                text="Too long text",
                voice_id=PollyVoice.JOEY.value,
                s3_bucket="bucket",
                s3_key="key",
            )

        assert "TextLengthExceededException" in str(exc_info.value)


class TestGetTaskStatus:
    """Tests for get_task_status method."""

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_get_task_status_success(self, mock_boto3: Mock) -> None:
        """Test successful task status retrieval."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        mock_task = {
            "TaskId": "task-123",
            "TaskStatus": "completed",
            "OutputUri": "s3://my-bucket/audio/output.mp3",
            "CreationTime": "2024-01-01T00:00:00Z",
            "RequestCharacters": 5000,
        }

        mock_client.get_speech_synthesis_task.return_value = {
            "SynthesisTask": mock_task
        }

        client = PollyClient()

        status = await client.get_task_status("task-123")

        # Verify boto3 call
        mock_client.get_speech_synthesis_task.assert_called_once_with(
            TaskId="task-123"
        )

        # Verify response
        assert status == mock_task
        assert status["TaskId"] == "task-123"
        assert status["TaskStatus"] == "completed"
        assert status["OutputUri"] == "s3://my-bucket/audio/output.mp3"

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_get_task_status_in_progress(self, mock_boto3: Mock) -> None:
        """Test task status for in-progress task."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        mock_client.get_speech_synthesis_task.return_value = {
            "SynthesisTask": {
                "TaskId": "task-456",
                "TaskStatus": "inProgress",
            }
        }

        client = PollyClient()

        status = await client.get_task_status("task-456")

        assert status["TaskStatus"] == "inProgress"

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_get_task_status_failed(self, mock_boto3: Mock) -> None:
        """Test task status for failed task."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        mock_client.get_speech_synthesis_task.return_value = {
            "SynthesisTask": {
                "TaskId": "task-789",
                "TaskStatus": "failed",
                "TaskStatusReason": "Invalid voice ID",
            }
        }

        client = PollyClient()

        status = await client.get_task_status("task-789")

        assert status["TaskStatus"] == "failed"
        assert "TaskStatusReason" in status

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_get_task_status_not_found_error(self, mock_boto3: Mock) -> None:
        """Test task status when task not found."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        error_response = {
            "Error": {"Code": "SynthesisTaskNotFoundException", "Message": "Task not found"}
        }
        mock_client.get_speech_synthesis_task.side_effect = ClientError(
            error_response, "GetSpeechSynthesisTask"
        )

        client = PollyClient()

        with pytest.raises(PollyError) as exc_info:
            await client.get_task_status("invalid-task-id")

        assert "SynthesisTaskNotFoundException" in str(exc_info.value)


class TestIntegration:
    """Integration tests for Polly client."""

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_full_workflow_short_text(self, mock_boto3: Mock) -> None:
        """Test full workflow for short text synthesis."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        # Mock synthesis response
        mock_stream = BytesIO(b"audio data")
        mock_client.synthesize_speech.return_value = {
            "AudioStream": mock_stream,
            "RequestCharacters": 50,
        }

        client = PollyClient()

        # Generate speech
        response = await client.text_to_speech(
            text="Welcome to our platform!",
            voice_id=PollyVoice.JOANNA.value,
            engine=PollyEngine.NEURAL.value,
        )

        assert response.audio_data == b"audio data"
        assert response.voice_id == "Joanna"

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_full_workflow_long_text(self, mock_boto3: Mock) -> None:
        """Test full workflow for long text synthesis."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        # Mock task start
        mock_client.start_speech_synthesis_task.return_value = {
            "SynthesisTask": {"TaskId": "task-999", "TaskStatus": "scheduled"}
        }

        # Mock task status check
        mock_client.get_speech_synthesis_task.return_value = {
            "SynthesisTask": {
                "TaskId": "task-999",
                "TaskStatus": "completed",
                "OutputUri": "s3://bucket/output.mp3",
            }
        }

        client = PollyClient()

        # Start task
        task_id = await client.text_to_speech_long(
            text="Very long text content here",
            voice_id=PollyVoice.MATTHEW.value,
            s3_bucket="my-bucket",
            s3_key="audio/long.mp3",
        )

        assert task_id == "task-999"

        # Check status
        status = await client.get_task_status(task_id)

        assert status["TaskStatus"] == "completed"
        assert "OutputUri" in status

    @pytest.mark.asyncio
    @patch("src.workers.clients.polly.boto3")
    async def test_with_ssml_generation(self, mock_boto3: Mock) -> None:
        """Test integration with SSML generation from polly_models."""
        from src.workers.clients.polly_models import PollyVoice as PV

        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        mock_stream = BytesIO(b"audio")
        mock_client.synthesize_speech.return_value = {
            "AudioStream": mock_stream,
            "RequestCharacters": 30,
        }

        client = PollyClient()

        # Generate SSML
        ssml = PV.text_to_ssml("Hello!", rate="fast", pitch="high")

        # Synthesize with SSML
        response = await client.text_to_speech(
            text=ssml,
            voice_id=PV.JOANNA.value,
            use_ssml=True,
        )

        assert response.audio_data == b"audio"

        # Verify SSML was passed
        call_kwargs = mock_client.synthesize_speech.call_args.kwargs
        assert "<prosody" in call_kwargs["Text"]
        assert call_kwargs["TextType"] == "ssml"
