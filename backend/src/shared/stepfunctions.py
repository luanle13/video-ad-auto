"""AWS Step Functions integration helper."""
import json
from typing import Any

import boto3

from src.shared.config import get_settings
from src.shared.logging import get_logger


logger = get_logger(__name__)


# Singleton instance
_sfn_client = None


def get_sfn_client():
    """Get Step Functions client singleton."""
    global _sfn_client
    if _sfn_client is None:
        settings = get_settings()
        _sfn_client = boto3.client("stepfunctions", region_name=settings.aws_region)
    return _sfn_client


def start_execution(state_machine_arn: str, name: str, input_dict: dict[str, Any]) -> str:
    """Start a Step Functions execution.
    
    Args:
        state_machine_arn: ARN of the state machine to execute
        name: Unique name for the execution
        input_dict: Input data for the execution
        
    Returns:
        Execution ARN
    """
    client = get_sfn_client()
    
    # JSON serialize input
    input_json = json.dumps(input_dict)
    
    response = client.start_execution(
        stateMachineArn=state_machine_arn,
        name=name,
        input=input_json
    )
    
    execution_arn = response["executionArn"]
    
    logger.info(
        "stepfunctions_execution_started",
        execution_arn=execution_arn,
        state_machine_arn=state_machine_arn,
        execution_name=name
    )
    
    return execution_arn


def get_execution_status(execution_arn: str) -> dict[str, Any]:
    """Get the status of a Step Functions execution.
    
    Args:
        execution_arn: ARN of the execution to check
        
    Returns:
        Dictionary with status, output, error
    """
    client = get_sfn_client()
    
    response = client.describe_execution(executionArn=execution_arn)
    
    result = {
        "status": response["status"],
        "output": None,
        "error": None
    }
    
    # Add output if execution succeeded
    if response["status"] == "SUCCEEDED" and "output" in response:
        result["output"] = json.loads(response["output"])
    
    # Add error if execution failed
    if response["status"] == "FAILED":
        result["error"] = response.get("error", "Unknown error")
        result["cause"] = response.get("cause", "Unknown cause")
    
    logger.info(
        "stepfunctions_execution_status_retrieved",
        execution_arn=execution_arn,
        status=result["status"]
    )
    
    return result