"""Tests for Step Functions client."""
import json
from datetime import datetime, timezone
from typing import Any
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from src.shared.exceptions import NotFoundError, ValidationError
from src.shared.stepfunctions import StepFunctionsClient


@pytest.fixture
def mock_sfn_client() -> Mock:
    """Mock boto3 Step Functions client."""
    return Mock()


@pytest.fixture
def sfn_client(mock_sfn_client: Mock) -> StepFunctionsClient:
    """Step Functions client with mock boto3 client."""
    with patch("src.shared.stepfunctions.get_settings") as mock_settings:
        mock_settings.return_value.aws_region = "ap-southeast-1"
        mock_settings.return_value.stepfunctions_state_machine_arn = (
            "arn:aws:states:ap-southeast-1:123456789012:stateMachine:ai-video-pipeline-dev"
        )
        return StepFunctionsClient(sfn_client=mock_sfn_client)


@pytest.fixture
def sample_product() -> dict[str, Any]:
    """Sample product data."""
    return {
        "id": "prod_123",
        "title": "Wireless Earbuds Pro",
        "description": "High-quality earbuds",
        "price": "799,000 VND",
        "image_keys": ["images/prod_123/img1.jpg", "images/prod_123/img2.jpg"],
    }


@pytest.fixture
def sample_adjustments() -> dict[str, Any]:
    """Sample user adjustments."""
    return {
        "tone": "energetic",
        "target_duration": 45,
        "primary_platform": "tiktok",
    }


class TestStepFunctionsClient:
    """Tests for StepFunctionsClient."""

    def test_initialization(self, mock_sfn_client: Mock) -> None:
        """Test client initialization."""
        with patch("src.shared.stepfunctions.get_settings") as mock_settings:
            mock_settings.return_value.aws_region = "ap-southeast-1"
            mock_settings.return_value.stepfunctions_state_machine_arn = "arn:aws:states:..."

            client = StepFunctionsClient(sfn_client=mock_sfn_client)

            assert client._sfn == mock_sfn_client
            assert client._state_machine_arn == "arn:aws:states:..."

    def test_start_execution_success(
        self,
        sfn_client: StepFunctionsClient,
        mock_sfn_client: Mock,
        sample_product: dict[str, Any],
        sample_adjustments: dict[str, Any],
    ) -> None:
        """Test successful execution start."""
        mock_sfn_client.start_execution.return_value = {
            "executionArn": "arn:aws:states:ap-southeast-1:123456789012:execution:ai-video-pipeline-dev:job-job_456",
            "startDate": datetime.now(timezone.utc),
        }

        execution_arn = sfn_client.start_execution(
            user_id="usr_123",
            job_id="job_456",
            product=sample_product,
            adjustments=sample_adjustments,
        )

        assert execution_arn.startswith("arn:aws:states:")
        mock_sfn_client.start_execution.assert_called_once()

        # Verify the call arguments
        call_args = mock_sfn_client.start_execution.call_args
        assert call_args.kwargs["name"] == "job-job_456"
        assert "user_id" in json.loads(call_args.kwargs["input"])

    def test_start_execution_without_adjustments(
        self,
        sfn_client: StepFunctionsClient,
        mock_sfn_client: Mock,
        sample_product: dict[str, Any],
    ) -> None:
        """Test execution start without adjustments."""
        mock_sfn_client.start_execution.return_value = {
            "executionArn": "arn:aws:states:...",
            "startDate": datetime.now(timezone.utc),
        }

        execution_arn = sfn_client.start_execution(
            user_id="usr_123",
            job_id="job_456",
            product=sample_product,
        )

        assert execution_arn.startswith("arn:aws:states:")

        # Verify adjustments defaults to empty dict
        call_args = mock_sfn_client.start_execution.call_args
        input_data = json.loads(call_args.kwargs["input"])
        assert input_data["adjustments"] == {}

    def test_start_execution_already_exists(
        self,
        sfn_client: StepFunctionsClient,
        mock_sfn_client: Mock,
        sample_product: dict[str, Any],
    ) -> None:
        """Test execution already exists scenario."""
        error_response = {"Error": {"Code": "ExecutionAlreadyExists"}}
        mock_sfn_client.start_execution.side_effect = ClientError(error_response, "StartExecution")

        execution_arn = sfn_client.start_execution(
            user_id="usr_123",
            job_id="job_456",
            product=sample_product,
        )

        # Should return constructed ARN
        assert "job-job_456" in execution_arn

    def test_start_execution_no_state_machine_arn(
        self,
        mock_sfn_client: Mock,
        sample_product: dict[str, Any],
    ) -> None:
        """Test execution start without configured state machine ARN."""
        with patch("src.shared.stepfunctions.get_settings") as mock_settings:
            mock_settings.return_value.aws_region = "ap-southeast-1"
            mock_settings.return_value.stepfunctions_state_machine_arn = ""

            client = StepFunctionsClient(sfn_client=mock_sfn_client)

            with pytest.raises(ValidationError) as exc_info:
                client.start_execution(
                    user_id="usr_123",
                    job_id="job_456",
                    product=sample_product,
                )

            assert "state machine ARN not configured" in str(exc_info.value)

    def test_start_execution_client_error(
        self,
        sfn_client: StepFunctionsClient,
        mock_sfn_client: Mock,
        sample_product: dict[str, Any],
    ) -> None:
        """Test execution start with client error."""
        error_response = {"Error": {"Code": "InvalidArn"}}
        mock_sfn_client.start_execution.side_effect = ClientError(error_response, "StartExecution")

        with pytest.raises(ClientError):
            sfn_client.start_execution(
                user_id="usr_123",
                job_id="job_456",
                product=sample_product,
            )

    def test_get_execution_status_running(
        self,
        sfn_client: StepFunctionsClient,
        mock_sfn_client: Mock,
    ) -> None:
        """Test get status for running execution."""
        mock_sfn_client.describe_execution.return_value = {
            "executionArn": "arn:aws:states:...",
            "status": "RUNNING",
            "startDate": datetime(2025, 1, 8, 12, 0, 0, tzinfo=timezone.utc),
        }

        status = sfn_client.get_execution_status("arn:aws:states:...")

        assert status["status"] == "RUNNING"
        assert status["start_date"] == "2025-01-08T12:00:00+00:00"
        assert "stop_date" not in status

    def test_get_execution_status_succeeded(
        self,
        sfn_client: StepFunctionsClient,
        mock_sfn_client: Mock,
    ) -> None:
        """Test get status for succeeded execution."""
        mock_sfn_client.describe_execution.return_value = {
            "executionArn": "arn:aws:states:...",
            "status": "SUCCEEDED",
            "startDate": datetime(2025, 1, 8, 12, 0, 0, tzinfo=timezone.utc),
            "stopDate": datetime(2025, 1, 8, 12, 10, 0, tzinfo=timezone.utc),
            "output": '{"video_key": "videos/job_456/output.mp4"}',
        }

        status = sfn_client.get_execution_status("arn:aws:states:...")

        assert status["status"] == "SUCCEEDED"
        assert status["stop_date"] == "2025-01-08T12:10:00+00:00"
        assert status["output"]["video_key"] == "videos/job_456/output.mp4"

    def test_get_execution_status_failed(
        self,
        sfn_client: StepFunctionsClient,
        mock_sfn_client: Mock,
    ) -> None:
        """Test get status for failed execution."""
        mock_sfn_client.describe_execution.return_value = {
            "executionArn": "arn:aws:states:...",
            "status": "FAILED",
            "startDate": datetime(2025, 1, 8, 12, 0, 0, tzinfo=timezone.utc),
            "stopDate": datetime(2025, 1, 8, 12, 5, 0, tzinfo=timezone.utc),
            "error": "States.TaskFailed",
            "cause": "Lambda function failed",
        }

        status = sfn_client.get_execution_status("arn:aws:states:...")

        assert status["status"] == "FAILED"
        assert status["error"] == "States.TaskFailed"
        assert status["cause"] == "Lambda function failed"

    def test_get_execution_status_not_found(
        self,
        sfn_client: StepFunctionsClient,
        mock_sfn_client: Mock,
    ) -> None:
        """Test get status for non-existent execution."""
        error_response = {"Error": {"Code": "ExecutionDoesNotExist"}}
        mock_sfn_client.describe_execution.side_effect = ClientError(error_response, "DescribeExecution")

        with pytest.raises(NotFoundError):
            sfn_client.get_execution_status("arn:aws:states:...")

    def test_stop_execution(
        self,
        sfn_client: StepFunctionsClient,
        mock_sfn_client: Mock,
    ) -> None:
        """Test stopping an execution."""
        mock_sfn_client.stop_execution.return_value = {
            "stopDate": datetime.now(timezone.utc)
        }

        sfn_client.stop_execution(
            execution_arn="arn:aws:states:...",
            error="User cancelled",
            cause="User requested cancellation",
        )

        mock_sfn_client.stop_execution.assert_called_once_with(
            executionArn="arn:aws:states:...",
            error="User cancelled",
            cause="User requested cancellation",
        )

    def test_stop_execution_default_cause(
        self,
        sfn_client: StepFunctionsClient,
        mock_sfn_client: Mock,
    ) -> None:
        """Test stopping execution with default cause."""
        mock_sfn_client.stop_execution.return_value = {}

        sfn_client.stop_execution(
            execution_arn="arn:aws:states:...",
            error="Cancelled",
        )

        call_args = mock_sfn_client.stop_execution.call_args
        assert call_args.kwargs["cause"] == "Execution stopped by user"

    def test_list_executions(
        self,
        sfn_client: StepFunctionsClient,
        mock_sfn_client: Mock,
    ) -> None:
        """Test listing executions."""
        mock_sfn_client.list_executions.return_value = {
            "executions": [
                {
                    "executionArn": "arn:aws:states:...:execution1",
                    "name": "job-job_1",
                    "status": "RUNNING",
                    "startDate": datetime(2025, 1, 8, 12, 0, 0, tzinfo=timezone.utc),
                },
                {
                    "executionArn": "arn:aws:states:...:execution2",
                    "name": "job-job_2",
                    "status": "SUCCEEDED",
                    "startDate": datetime(2025, 1, 8, 11, 0, 0, tzinfo=timezone.utc),
                    "stopDate": datetime(2025, 1, 8, 11, 10, 0, tzinfo=timezone.utc),
                },
            ]
        }

        executions = sfn_client.list_executions()

        assert len(executions) == 2
        assert executions[0]["name"] == "job-job_1"
        assert executions[0]["status"] == "RUNNING"
        assert executions[1]["stop_date"] == "2025-01-08T11:10:00+00:00"

    def test_list_executions_with_status_filter(
        self,
        sfn_client: StepFunctionsClient,
        mock_sfn_client: Mock,
    ) -> None:
        """Test listing executions with status filter."""
        mock_sfn_client.list_executions.return_value = {"executions": []}

        sfn_client.list_executions(status="RUNNING", max_results=10)

        call_args = mock_sfn_client.list_executions.call_args
        assert call_args.kwargs["statusFilter"] == "RUNNING"
        assert call_args.kwargs["maxResults"] == 10

    def test_list_executions_max_results_capped(
        self,
        sfn_client: StepFunctionsClient,
        mock_sfn_client: Mock,
    ) -> None:
        """Test max results is capped at 1000."""
        mock_sfn_client.list_executions.return_value = {"executions": []}

        sfn_client.list_executions(max_results=5000)

        call_args = mock_sfn_client.list_executions.call_args
        assert call_args.kwargs["maxResults"] == 1000

    def test_build_execution_arn(self, sfn_client: StepFunctionsClient) -> None:
        """Test building execution ARN from execution name."""
        execution_arn = sfn_client._build_execution_arn("job-job_456")

        assert "execution:ai-video-pipeline-dev:job-job_456" in execution_arn
        assert execution_arn.startswith("arn:aws:states:ap-southeast-1:")

    def test_serialize_input(self, sfn_client: StepFunctionsClient) -> None:
        """Test input serialization."""
        input_data = {
            "user_id": "usr_123",
            "job_id": "job_456",
            "product": {"title": "Test Product"},
        }

        serialized = sfn_client._serialize_input(input_data)

        assert isinstance(serialized, str)
        assert "usr_123" in serialized
        assert json.loads(serialized) == input_data

    def test_deserialize_output(self, sfn_client: StepFunctionsClient) -> None:
        """Test output deserialization."""
        output_json = '{"video_key": "videos/output.mp4", "status": "complete"}'

        deserialized = sfn_client._deserialize_output(output_json)

        assert isinstance(deserialized, dict)
        assert deserialized["video_key"] == "videos/output.mp4"
        assert deserialized["status"] == "complete"


class TestGetStepFunctionsClient:
    """Tests for get_stepfunctions_client singleton."""

    def test_singleton_returns_same_instance(self) -> None:
        """Test singleton returns same instance."""
        with patch("src.shared.stepfunctions.StepFunctionsClient"):
            from src.shared.stepfunctions import get_stepfunctions_client

            client1 = get_stepfunctions_client()
            client2 = get_stepfunctions_client()

            assert client1 is client2
