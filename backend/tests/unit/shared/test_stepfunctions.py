"""Unit tests for StepFunctions helper functions."""
import json
from unittest.mock import MagicMock, patch

import pytest

from src.shared.stepfunctions import get_execution_status, get_sfn_client, start_execution


def test_get_sfn_client_singleton():
    """Test that get_sfn_client returns singleton instance."""
    with patch('src.shared.stepfunctions.get_settings') as mock_settings:
        mock_settings.return_value.aws_region = "us-east-1"
        
        client1 = get_sfn_client()
        client2 = get_sfn_client()
        
        # Both should be the same instance
        assert client1 is client2


def test_start_execution():
    """Test start_execution function."""
    with patch('src.shared.stepfunctions.get_sfn_client') as mock_get_client, \
         patch('src.shared.stepfunctions.get_settings') as mock_settings:
        
        mock_settings.return_value.aws_region = "us-east-1"
        
        # Setup mock client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock the start_execution response
        mock_client.start_execution.return_value = {
            "executionArn": "arn:aws:states:us-east-1:123456789012:execution:test-sfn:exec-123"
        }
        
        # Call the function
        input_data = {"user_id": "user123", "job_id": "job456"}
        execution_arn = start_execution(
            state_machine_arn="arn:aws:states:us-east-1:123456789012:stateMachine:test-sfn",
            name="test-execution",
            input_dict=input_data
        )
        
        # Verify the result
        assert execution_arn == "arn:aws:states:us-east-1:123456789012:execution:test-sfn:exec-123"
        
        # Verify the client was called with correct parameters
        mock_client.start_execution.assert_called_once_with(
            stateMachineArn="arn:aws:states:us-east-1:123456789012:stateMachine:test-sfn",
            name="test-execution",
            input=json.dumps(input_data)
        )


def test_get_execution_status_success():
    """Test get_execution_status function for successful execution."""
    with patch('src.shared.stepfunctions.get_sfn_client') as mock_get_client:
        # Setup mock client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock the describe_execution response for successful execution
        mock_client.describe_execution.return_value = {
            "status": "SUCCEEDED",
            "output": json.dumps({"result": "success", "video_url": "https://example.com/video.mp4"})
        }
        
        # Call the function
        result = get_execution_status("arn:aws:states:us-east-1:123456789012:execution:test-sfn:exec-123")
        
        # Verify the result
        assert result["status"] == "SUCCEEDED"
        assert result["output"] == {"result": "success", "video_url": "https://example.com/video.mp4"}
        assert result["error"] is None


def test_get_execution_status_failed():
    """Test get_execution_status function for failed execution."""
    with patch('src.shared.stepfunctions.get_sfn_client') as mock_get_client:
        # Setup mock client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock the describe_execution response for failed execution
        mock_client.describe_execution.return_value = {
            "status": "FAILED",
            "error": "Task Failed",
            "cause": "Some error occurred"
        }
        
        # Call the function
        result = get_execution_status("arn:aws:states:us-east-1:123456789012:execution:test-sfn:exec-123")
        
        # Verify the result
        assert result["status"] == "FAILED"
        assert result["error"] == "Task Failed"
        assert result["cause"] == "Some error occurred"
        assert result["output"] is None


def test_get_execution_status_running():
    """Test get_execution_status function for running execution."""
    with patch('src.shared.stepfunctions.get_sfn_client') as mock_get_client:
        # Setup mock client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock the describe_execution response for running execution
        mock_client.describe_execution.return_value = {
            "status": "RUNNING"
        }
        
        # Call the function
        result = get_execution_status("arn:aws:states:us-east-1:123456789012:execution:test-sfn:exec-123")
        
        # Verify the result
        assert result["status"] == "RUNNING"
        assert result["output"] is None
        assert result["error"] is None


def test_start_execution_with_complex_input():
    """Test start_execution with complex input data."""
    with patch('src.shared.stepfunctions.get_sfn_client') as mock_get_client, \
         patch('src.shared.stepfunctions.get_settings') as mock_settings:
        
        mock_settings.return_value.aws_region = "us-east-1"
        
        # Setup mock client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock the start_execution response
        mock_client.start_execution.return_value = {
            "executionArn": "arn:aws:states:us-east-1:123456789012:execution:test-sfn:exec-456"
        }
        
        # Call the function with complex input
        input_data = {
            "user_id": "user123",
            "job_id": "job456",
            "product": {
                "id": "prod789",
                "title": "Test Product",
                "description": "A great product",
                "price": 29.99,
                "image_keys": ["image1.jpg", "image2.jpg"]
            },
            "adjustments": {
                "duration": 30,
                "aspect_ratio": "16:9"
            }
        }
        
        execution_arn = start_execution(
            state_machine_arn="arn:aws:states:us-east-1:123456789012:stateMachine:test-sfn",
            name="complex-execution",
            input_dict=input_data
        )
        
        # Verify the result
        assert execution_arn == "arn:aws:states:us-east-1:123456789012:execution:test-sfn:exec-456"
        
        # Verify the client was called with JSON-serialized input
        call_args = mock_client.start_execution.call_args
        assert call_args[1]["input"] == json.dumps(input_data)


def test_get_execution_status_with_empty_output():
    """Test get_execution_status when output is empty for successful execution."""
    with patch('src.shared.stepfunctions.get_sfn_client') as mock_get_client:
        # Setup mock client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock the describe_execution response for successful execution without output
        mock_client.describe_execution.return_value = {
            "status": "SUCCEEDED"
            # No "output" key in response
        }
        
        # Call the function
        result = get_execution_status("arn:aws:states:us-east-1:123456789012:execution:test-sfn:exec-123")
        
        # Verify the result
        assert result["status"] == "SUCCEEDED"
        assert result["output"] is None
        assert result["error"] is None