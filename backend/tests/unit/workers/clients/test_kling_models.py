"""Tests for Kling AI models."""
import pytest
from pydantic import ValidationError

from src.workers.clients.kling_models import (
    KlingGenerationRequest,
    KlingJobResponse,
    KlingVideoConfig,
    KlingVideoStatus,
)


class TestKlingVideoStatus:
    """Tests for KlingVideoStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """Test that all 4 statuses are defined."""
        assert len(KlingVideoStatus) == 4
        assert KlingVideoStatus.PENDING
        assert KlingVideoStatus.PROCESSING
        assert KlingVideoStatus.COMPLETED
        assert KlingVideoStatus.FAILED

    def test_pending_value(self) -> None:
        """Test PENDING status value."""
        assert KlingVideoStatus.PENDING.value == "pending"

    def test_processing_value(self) -> None:
        """Test PROCESSING status value."""
        assert KlingVideoStatus.PROCESSING.value == "processing"

    def test_completed_value(self) -> None:
        """Test COMPLETED status value."""
        assert KlingVideoStatus.COMPLETED.value == "completed"

    def test_failed_value(self) -> None:
        """Test FAILED status value."""
        assert KlingVideoStatus.FAILED.value == "failed"

    def test_status_enum_is_string(self) -> None:
        """Test that status enum inherits from str."""
        status = KlingVideoStatus.PENDING
        assert isinstance(status, str)
        assert isinstance(status.value, str)


class TestKlingVideoConfig:
    """Tests for KlingVideoConfig model."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = KlingVideoConfig()

        assert config.aspect_ratio == "9:16"
        assert config.duration == 5
        assert config.mode == "standard"

    def test_custom_config_9_16(self) -> None:
        """Test custom 9:16 (vertical) configuration."""
        config = KlingVideoConfig(
            aspect_ratio="9:16",
            duration=8,
            mode="professional",
        )

        assert config.aspect_ratio == "9:16"
        assert config.duration == 8
        assert config.mode == "professional"

    def test_custom_config_16_9(self) -> None:
        """Test custom 16:9 (horizontal) configuration."""
        config = KlingVideoConfig(
            aspect_ratio="16:9",
            duration=10,
            mode="standard",
        )

        assert config.aspect_ratio == "16:9"
        assert config.duration == 10

    def test_custom_config_1_1(self) -> None:
        """Test custom 1:1 (square) configuration."""
        config = KlingVideoConfig(
            aspect_ratio="1:1",
            duration=5,
            mode="professional",
        )

        assert config.aspect_ratio == "1:1"

    def test_duration_minimum(self) -> None:
        """Test minimum duration of 5 seconds."""
        config = KlingVideoConfig(duration=5)
        assert config.duration == 5

    def test_duration_maximum(self) -> None:
        """Test maximum duration of 10 seconds."""
        config = KlingVideoConfig(duration=10)
        assert config.duration == 10

    def test_duration_below_minimum_raises_error(self) -> None:
        """Test that duration below 5 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            KlingVideoConfig(duration=4)

        assert "greater than or equal to 5" in str(exc_info.value).lower()

    def test_duration_above_maximum_raises_error(self) -> None:
        """Test that duration above 10 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            KlingVideoConfig(duration=11)

        assert "less than or equal to 10" in str(exc_info.value).lower()

    def test_invalid_mode_raises_error(self) -> None:
        """Test that invalid mode raises error."""
        with pytest.raises(ValidationError) as exc_info:
            KlingVideoConfig(mode="premium")

        assert "string should match pattern" in str(exc_info.value).lower()

    def test_mode_standard(self) -> None:
        """Test standard mode."""
        config = KlingVideoConfig(mode="standard")
        assert config.mode == "standard"

    def test_mode_professional(self) -> None:
        """Test professional mode."""
        config = KlingVideoConfig(mode="professional")
        assert config.mode == "professional"


class TestKlingGenerationRequest:
    """Tests for KlingGenerationRequest model."""

    def test_minimal_request(self) -> None:
        """Test request with only required fields."""
        request = KlingGenerationRequest(
            prompt="A beautiful sunset over mountains",
        )

        assert request.prompt == "A beautiful sunset over mountains"
        assert request.negative_prompt is None
        assert isinstance(request.config, KlingVideoConfig)
        assert request.config.aspect_ratio == "9:16"
        assert request.image_url is None
        assert request.audio_url is None

    def test_full_request(self) -> None:
        """Test request with all fields."""
        config = KlingVideoConfig(
            aspect_ratio="16:9",
            duration=10,
            mode="professional",
        )

        request = KlingGenerationRequest(
            prompt="Product showcase video",
            negative_prompt="low quality, blurry",
            config=config,
            image_url="https://example.com/image.jpg",
            audio_url="https://example.com/audio.mp3",
        )

        assert request.prompt == "Product showcase video"
        assert request.negative_prompt == "low quality, blurry"
        assert request.config.aspect_ratio == "16:9"
        assert request.config.duration == 10
        assert request.config.mode == "professional"
        assert request.image_url == "https://example.com/image.jpg"
        assert request.audio_url == "https://example.com/audio.mp3"

    def test_request_with_image_url(self) -> None:
        """Test image-to-video request."""
        request = KlingGenerationRequest(
            prompt="Animate this product image",
            image_url="https://cdn.example.com/product.jpg",
        )

        assert request.image_url == "https://cdn.example.com/product.jpg"

    def test_request_with_audio_url(self) -> None:
        """Test request with audio voiceover."""
        request = KlingGenerationRequest(
            prompt="Video with voiceover",
            audio_url="s3://bucket/audio.mp3",
        )

        assert request.audio_url == "s3://bucket/audio.mp3"

    def test_prompt_too_short_raises_error(self) -> None:
        """Test that prompt under 10 characters raises error."""
        with pytest.raises(ValidationError) as exc_info:
            KlingGenerationRequest(prompt="Short")

        assert "at least 10 characters" in str(exc_info.value).lower()

    def test_prompt_too_long_raises_error(self) -> None:
        """Test that prompt over 2000 characters raises error."""
        long_prompt = "A" * 2001

        with pytest.raises(ValidationError) as exc_info:
            KlingGenerationRequest(prompt=long_prompt)

        assert "at most 2000 characters" in str(exc_info.value).lower()

    def test_negative_prompt_too_long_raises_error(self) -> None:
        """Test that negative prompt over 1000 characters raises error."""
        long_negative = "B" * 1001

        with pytest.raises(ValidationError) as exc_info:
            KlingGenerationRequest(
                prompt="Valid prompt here",
                negative_prompt=long_negative,
            )

        assert "at most 1000 characters" in str(exc_info.value).lower()

    def test_prompt_required(self) -> None:
        """Test that prompt is required."""
        with pytest.raises(ValidationError):
            KlingGenerationRequest()  # type: ignore

    def test_prompt_minimum_length(self) -> None:
        """Test prompt with minimum valid length."""
        request = KlingGenerationRequest(prompt="Ten chars!")
        assert len(request.prompt) == 10

    def test_prompt_maximum_length(self) -> None:
        """Test prompt with maximum valid length."""
        max_prompt = "A" * 2000
        request = KlingGenerationRequest(prompt=max_prompt)
        assert len(request.prompt) == 2000

    def test_negative_prompt_maximum_length(self) -> None:
        """Test negative prompt with maximum valid length."""
        max_negative = "B" * 1000
        request = KlingGenerationRequest(
            prompt="Valid prompt",
            negative_prompt=max_negative,
        )
        assert len(request.negative_prompt) == 1000


class TestKlingJobResponse:
    """Tests for KlingJobResponse model."""

    def test_pending_job(self) -> None:
        """Test pending job response."""
        response = KlingJobResponse(
            job_id="job-123",
            status=KlingVideoStatus.PENDING,
            progress=0,
            created_at="2025-01-09T10:00:00Z",
        )

        assert response.job_id == "job-123"
        assert response.status == KlingVideoStatus.PENDING
        assert response.progress == 0
        assert response.video_url is None
        assert response.thumbnail_url is None
        assert response.error_message is None
        assert response.created_at == "2025-01-09T10:00:00Z"
        assert response.completed_at is None

    def test_processing_job(self) -> None:
        """Test processing job with progress."""
        response = KlingJobResponse(
            job_id="job-456",
            status=KlingVideoStatus.PROCESSING,
            progress=45,
            created_at="2025-01-09T10:00:00Z",
        )

        assert response.status == KlingVideoStatus.PROCESSING
        assert response.progress == 45

    def test_completed_job(self) -> None:
        """Test completed job with video URL."""
        response = KlingJobResponse(
            job_id="job-789",
            status=KlingVideoStatus.COMPLETED,
            progress=100,
            video_url="https://cdn.kling.ai/videos/job-789.mp4",
            thumbnail_url="https://cdn.kling.ai/thumbnails/job-789.jpg",
            created_at="2025-01-09T10:00:00Z",
            completed_at="2025-01-09T10:05:00Z",
        )

        assert response.status == KlingVideoStatus.COMPLETED
        assert response.progress == 100
        assert response.video_url == "https://cdn.kling.ai/videos/job-789.mp4"
        assert response.thumbnail_url == "https://cdn.kling.ai/thumbnails/job-789.jpg"
        assert response.completed_at == "2025-01-09T10:05:00Z"

    def test_failed_job(self) -> None:
        """Test failed job with error message."""
        response = KlingJobResponse(
            job_id="job-error",
            status=KlingVideoStatus.FAILED,
            progress=30,
            error_message="Generation failed: Invalid prompt",
            created_at="2025-01-09T10:00:00Z",
            completed_at="2025-01-09T10:01:00Z",
        )

        assert response.status == KlingVideoStatus.FAILED
        assert response.progress == 30
        assert response.error_message == "Generation failed: Invalid prompt"
        assert response.video_url is None

    def test_progress_minimum(self) -> None:
        """Test minimum progress of 0."""
        response = KlingJobResponse(
            job_id="job-123",
            status=KlingVideoStatus.PENDING,
            progress=0,
            created_at="2025-01-09T10:00:00Z",
        )
        assert response.progress == 0

    def test_progress_maximum(self) -> None:
        """Test maximum progress of 100."""
        response = KlingJobResponse(
            job_id="job-123",
            status=KlingVideoStatus.COMPLETED,
            progress=100,
            created_at="2025-01-09T10:00:00Z",
        )
        assert response.progress == 100

    def test_progress_below_minimum_raises_error(self) -> None:
        """Test that progress below 0 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            KlingJobResponse(
                job_id="job-123",
                status=KlingVideoStatus.PENDING,
                progress=-1,
                created_at="2025-01-09T10:00:00Z",
            )

        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_progress_above_maximum_raises_error(self) -> None:
        """Test that progress above 100 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            KlingJobResponse(
                job_id="job-123",
                status=KlingVideoStatus.COMPLETED,
                progress=101,
                created_at="2025-01-09T10:00:00Z",
            )

        assert "less than or equal to 100" in str(exc_info.value).lower()

    def test_job_id_required(self) -> None:
        """Test that job_id is required."""
        with pytest.raises(ValidationError):
            KlingJobResponse(  # type: ignore
                status=KlingVideoStatus.PENDING,
                created_at="2025-01-09T10:00:00Z",
            )

    def test_status_required(self) -> None:
        """Test that status is required."""
        with pytest.raises(ValidationError):
            KlingJobResponse(  # type: ignore
                job_id="job-123",
                created_at="2025-01-09T10:00:00Z",
            )

    def test_created_at_required(self) -> None:
        """Test that created_at is required."""
        with pytest.raises(ValidationError):
            KlingJobResponse(  # type: ignore
                job_id="job-123",
                status=KlingVideoStatus.PENDING,
            )

    def test_default_progress_is_zero(self) -> None:
        """Test that progress defaults to 0."""
        response = KlingJobResponse(
            job_id="job-123",
            status=KlingVideoStatus.PENDING,
            created_at="2025-01-09T10:00:00Z",
        )
        assert response.progress == 0

    def test_with_all_statuses(self) -> None:
        """Test response works with all status types."""
        for status in KlingVideoStatus:
            response = KlingJobResponse(
                job_id=f"job-{status.value}",
                status=status,
                created_at="2025-01-09T10:00:00Z",
            )
            assert response.status == status


class TestIntegration:
    """Integration tests for Kling models."""

    def test_full_workflow_request_to_response(self) -> None:
        """Test complete workflow from request to completed response."""
        # Create generation request
        config = KlingVideoConfig(
            aspect_ratio="9:16",
            duration=8,
            mode="professional",
        )

        request = KlingGenerationRequest(
            prompt="Showcase this amazing product with smooth camera movements",
            negative_prompt="low quality, blurry, distorted",
            config=config,
            image_url="https://s3.amazonaws.com/products/image-123.jpg",
            audio_url="https://s3.amazonaws.com/audio/voiceover-123.mp3",
        )

        # Verify request
        assert request.prompt.startswith("Showcase this amazing")
        assert request.config.duration == 8
        assert request.config.mode == "professional"

        # Simulate completed job response
        response = KlingJobResponse(
            job_id="kling-job-abc123",
            status=KlingVideoStatus.COMPLETED,
            progress=100,
            video_url="https://cdn.kling.ai/videos/kling-job-abc123.mp4",
            thumbnail_url="https://cdn.kling.ai/thumbnails/kling-job-abc123.jpg",
            created_at="2025-01-09T10:00:00Z",
            completed_at="2025-01-09T10:08:00Z",
        )

        # Verify response
        assert response.status == KlingVideoStatus.COMPLETED
        assert response.progress == 100
        assert response.video_url is not None
        assert ".mp4" in response.video_url

    def test_progressive_status_updates(self) -> None:
        """Test job progression through different statuses."""
        job_id = "job-progressive"
        created_at = "2025-01-09T10:00:00Z"

        # Start: Pending
        pending = KlingJobResponse(
            job_id=job_id,
            status=KlingVideoStatus.PENDING,
            progress=0,
            created_at=created_at,
        )
        assert pending.status == KlingVideoStatus.PENDING
        assert pending.progress == 0

        # Middle: Processing
        processing = KlingJobResponse(
            job_id=job_id,
            status=KlingVideoStatus.PROCESSING,
            progress=50,
            created_at=created_at,
        )
        assert processing.status == KlingVideoStatus.PROCESSING
        assert processing.progress == 50

        # End: Completed
        completed = KlingJobResponse(
            job_id=job_id,
            status=KlingVideoStatus.COMPLETED,
            progress=100,
            video_url="https://example.com/video.mp4",
            created_at=created_at,
            completed_at="2025-01-09T10:05:00Z",
        )
        assert completed.status == KlingVideoStatus.COMPLETED
        assert completed.progress == 100
        assert completed.video_url is not None

    def test_failure_scenario(self) -> None:
        """Test failure scenario with error message."""
        request = KlingGenerationRequest(
            prompt="Invalid content that violates policies",
            negative_prompt="inappropriate content",
        )

        response = KlingJobResponse(
            job_id="job-failed",
            status=KlingVideoStatus.FAILED,
            progress=0,
            error_message="Content policy violation: Inappropriate prompt detected",
            created_at="2025-01-09T10:00:00Z",
            completed_at="2025-01-09T10:00:10Z",
        )

        assert response.status == KlingVideoStatus.FAILED
        assert response.error_message is not None
        assert "policy violation" in response.error_message.lower()

    def test_different_aspect_ratios(self) -> None:
        """Test requests with different aspect ratios."""
        aspect_ratios = ["9:16", "16:9", "1:1", "4:3", "21:9"]

        for ratio in aspect_ratios:
            config = KlingVideoConfig(aspect_ratio=ratio)
            request = KlingGenerationRequest(
                prompt=f"Video with {ratio} aspect ratio",
                config=config,
            )
            assert request.config.aspect_ratio == ratio

    def test_different_durations(self) -> None:
        """Test requests with different valid durations."""
        for duration in [5, 6, 7, 8, 9, 10]:
            config = KlingVideoConfig(duration=duration)
            request = KlingGenerationRequest(
                prompt=f"Video with {duration} second duration",
                config=config,
            )
            assert request.config.duration == duration

    def test_image_to_video_workflow(self) -> None:
        """Test image-to-video generation workflow."""
        request = KlingGenerationRequest(
            prompt="Animate this product image with zoom and rotation effects",
            config=KlingVideoConfig(duration=5, mode="professional"),
            image_url="https://s3.amazonaws.com/products/product-001.jpg",
            audio_url="https://s3.amazonaws.com/audio/music-001.mp3",
        )

        assert request.image_url is not None
        assert request.audio_url is not None
        assert "product" in request.image_url
        assert "audio" in request.audio_url

        # Simulate successful generation
        response = KlingJobResponse(
            job_id="img2vid-123",
            status=KlingVideoStatus.COMPLETED,
            progress=100,
            video_url="https://cdn.kling.ai/videos/img2vid-123.mp4",
            created_at="2025-01-09T10:00:00Z",
            completed_at="2025-01-09T10:05:00Z",
        )

        assert response.status == KlingVideoStatus.COMPLETED
        assert response.video_url is not None
