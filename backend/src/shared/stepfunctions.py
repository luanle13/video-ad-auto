"""AWS Step Functions client for video generation pipeline."""
from typing import Any

import boto3
from botocore.exceptions import ClientError

from src.shared.config import get_settings
from src.shared.exceptions import NotFoundError, ValidationError
from src.shared.logging import get_logger

logger = get_logger(__name__)


class StepFunctionsClient:
    """AWS Step Functions client wrapper for video pipeline orchestration."""

    def __init__(self, sfn_client=None) -> None:
        """
        Initialize Step Functions client.

        Args:
            sfn_client: Optional boto3 SFN client for testing
        """
        settings = get_settings()
        self._sfn = sfn_client or boto3.client("stepfunctions", region_name=settings.aws_region)
        self._state_machine_arn = settings.stepfunctions_state_machine_arn

    def start_execution(
        self,
        user_id: str,
        job_id: str,
        product: dict[str, Any],
        adjustments: dict[str, Any] | None = None,
    ) -> str:
        """
        Start a Step Functions execution for video generation.

        Args:
            user_id: User ID
            job_id: Job ID
            product: Product data (id, title, description, price, image_keys)
            adjustments: Optional user preferences/adjustments

        Returns:
            Execution ARN

        Raises:
            ValidationError: If state machine ARN is not configured
            ClientError: If execution fails to start
        """
        if not self._state_machine_arn:
            raise ValidationError("Step Functions state machine ARN not configured")

        # Build execution input
        execution_input = {
            "user_id": user_id,
            "job_id": job_id,
            "product": product,
            "adjustments": adjustments or {},
        }

        # Generate execution name (must be unique and <= 80 chars)
        execution_name = f"job-{job_id}"

        try:
            response = self._sfn.start_execution(
                stateMachineArn=self._state_machine_arn,
                name=execution_name,
                input=self._serialize_input(execution_input),
            )

            execution_arn = response["executionArn"]
            logger.info(
                "stepfunctions_execution_started",
                job_id=job_id,
                user_id=user_id,
                execution_arn=execution_arn,
            )

            return execution_arn

        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            # If execution already exists, return existing ARN
            if error_code == "ExecutionAlreadyExists":
                existing_arn = self._build_execution_arn(execution_name)
                logger.warning(
                    "stepfunctions_execution_already_exists",
                    job_id=job_id,
                    execution_arn=existing_arn,
                )
                return existing_arn

            logger.error(
                "stepfunctions_start_execution_failed",
                job_id=job_id,
                error=str(e),
                error_code=error_code,
            )
            raise

    def get_execution_status(self, execution_arn: str) -> dict[str, Any]:
        """
        Get execution status and details.

        Args:
            execution_arn: Execution ARN

        Returns:
            Dictionary with:
                - status: RUNNING, SUCCEEDED, FAILED, TIMED_OUT, ABORTED
                - start_date: ISO timestamp
                - stop_date: ISO timestamp (if completed)
                - output: Execution output (if succeeded)
                - error: Error details (if failed)

        Raises:
            NotFoundError: If execution not found
        """
        try:
            response = self._sfn.describe_execution(executionArn=execution_arn)

            result: dict[str, Any] = {
                "status": response["status"],
                "start_date": response["startDate"].isoformat(),
            }

            # Add stop date if execution is complete
            if "stopDate" in response:
                result["stop_date"] = response["stopDate"].isoformat()

            # Add output if execution succeeded
            if response["status"] == "SUCCEEDED" and "output" in response:
                result["output"] = self._deserialize_output(response["output"])

            # Add error if execution failed
            if response["status"] == "FAILED":
                result["error"] = response.get("error", "Unknown error")
                result["cause"] = response.get("cause", "Unknown cause")

            logger.info(
                "stepfunctions_execution_status_retrieved",
                execution_arn=execution_arn,
                status=result["status"],
            )

            return result

        except ClientError as e:
            if e.response["Error"]["Code"] == "ExecutionDoesNotExist":
                raise NotFoundError("Execution", execution_arn)

            logger.error(
                "stepfunctions_get_status_failed",
                execution_arn=execution_arn,
                error=str(e),
            )
            raise

    def stop_execution(self, execution_arn: str, error: str = "User cancelled", cause: str = "") -> None:
        """
        Stop a running execution.

        Args:
            execution_arn: Execution ARN
            error: Error message
            cause: Detailed cause
        """
        try:
            self._sfn.stop_execution(
                executionArn=execution_arn,
                error=error,
                cause=cause or "Execution stopped by user",
            )

            logger.info(
                "stepfunctions_execution_stopped",
                execution_arn=execution_arn,
                error=error,
            )

        except ClientError as e:
            logger.error(
                "stepfunctions_stop_execution_failed",
                execution_arn=execution_arn,
                error=str(e),
            )
            raise

    def list_executions(
        self,
        status: str | None = None,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """
        List executions for the state machine.

        Args:
            status: Filter by status (RUNNING, SUCCEEDED, FAILED, TIMED_OUT, ABORTED)
            max_results: Maximum number of results to return

        Returns:
            List of execution summaries
        """
        try:
            params: dict[str, Any] = {
                "stateMachineArn": self._state_machine_arn,
                "maxResults": min(max_results, 1000),
            }

            if status:
                params["statusFilter"] = status

            response = self._sfn.list_executions(**params)

            executions = [
                {
                    "execution_arn": exec["executionArn"],
                    "name": exec["name"],
                    "status": exec["status"],
                    "start_date": exec["startDate"].isoformat(),
                    "stop_date": exec.get("stopDate", {}).isoformat() if "stopDate" in exec else None,
                }
                for exec in response.get("executions", [])
            ]

            logger.info(
                "stepfunctions_executions_listed",
                count=len(executions),
                status=status,
            )

            return executions

        except ClientError as e:
            logger.error(
                "stepfunctions_list_executions_failed",
                error=str(e),
            )
            raise

    def _serialize_input(self, input_data: dict[str, Any]) -> str:
        """Serialize execution input to JSON string."""
        import json
        return json.dumps(input_data)

    def _deserialize_output(self, output: str) -> dict[str, Any]:
        """Deserialize execution output from JSON string."""
        import json
        return json.loads(output)

    def _build_execution_arn(self, execution_name: str) -> str:
        """
        Build execution ARN from state machine ARN and execution name.

        Format: arn:aws:states:region:account:execution:state-machine-name:execution-name
        """
        # Parse state machine ARN
        # arn:aws:states:region:account:stateMachine:name
        parts = self._state_machine_arn.split(":")
        region = parts[3]
        account = parts[4]
        sm_name = parts[6]

        return f"arn:aws:states:{region}:{account}:execution:{sm_name}:{execution_name}"


# Singleton instance
_sfn_client: StepFunctionsClient | None = None


def get_stepfunctions_client() -> StepFunctionsClient:
    """Get Step Functions client singleton."""
    global _sfn_client
    if _sfn_client is None:
        _sfn_client = StepFunctionsClient()
    return _sfn_client
