"""Unit tests for base agent."""
import json
from typing import Any
from unittest.mock import Mock, patch

import pytest
from anthropic.types import Message, Usage
from anthropic.types.content_block import ContentBlock
from anthropic.types.text_block import TextBlock

from src.agents.base import (
    AgentError,
    AgentInput,
    AgentOutput,
    BaseAgent,
    get_anthropic_client,
)


class MockAgentInput(AgentInput):
    """Mock agent input for testing."""

    test_data: str = "test"


class MockAgentOutput(AgentOutput):
    """Mock agent output for testing."""

    result: str = "success"


class MockAgent(BaseAgent):
    """Mock agent implementation for testing."""

    name: str = "MockAgent"
    description: str = "Test agent"

    @property
    def system_prompt(self) -> str:
        """System prompt for test agent."""
        return "You are a helpful test agent."

    def build_user_prompt(self, input_data: AgentInput, context: dict[str, Any]) -> str:
        """Build user prompt."""
        return f"Process this: {input_data.job_id}"

    def parse_response(self, response_text: str, input_data: AgentInput) -> AgentOutput:
        """Parse response."""
        data = self._extract_json_from_response(response_text)
        return MockAgentOutput(
            success=data.get("success", True),
            result=data.get("result", "default"),
        )


@pytest.fixture
def mock_anthropic_response() -> Message:
    """Create a mock Anthropic API response."""
    return Message(
        id="msg_123",
        type="message",
        role="assistant",
        content=[
            TextBlock(
                type="text",
                text='{"success": true, "result": "test_output"}',
            )
        ],
        model="claude-sonnet-4-20250514",
        stop_reason="end_turn",
        usage=Usage(
            input_tokens=100,
            output_tokens=50,
        ),
    )


@pytest.fixture
def mock_agent_input() -> MockAgentInput:
    """Create mock agent input."""
    return MockAgentInput(
        job_id="job_123",
        user_id="user_456",
        test_data="test_value",
    )


class TestGetAnthropicClient:
    """Tests for get_anthropic_client function."""

    @patch("src.agents.base.get_settings")
    def test_get_client_from_settings(self, mock_get_settings: Mock) -> None:
        """Test getting client from settings (local dev)."""
        from pydantic import SecretStr

        mock_settings = Mock()
        mock_settings.anthropic_api_key = SecretStr("sk-test-key")
        mock_get_settings.return_value = mock_settings

        with patch("src.agents.base.Anthropic") as mock_anthropic:
            get_anthropic_client()

            mock_anthropic.assert_called_once_with(api_key="sk-test-key")

    @patch("src.agents.base.get_secrets")
    @patch("src.agents.base.get_settings")
    def test_get_client_from_secrets_manager(
        self, mock_get_settings: Mock, mock_get_secrets: Mock
    ) -> None:
        """Test getting client from Secrets Manager (production)."""
        mock_settings = Mock()
        mock_settings.anthropic_api_key = None
        mock_settings.secrets_anthropic_key = "ai-video/anthropic-api-key"
        mock_get_settings.return_value = mock_settings

        mock_secrets = Mock()
        mock_secrets.get_secret.return_value = "sk-prod-key"
        mock_get_secrets.return_value = mock_secrets

        with patch("src.agents.base.Anthropic") as mock_anthropic:
            get_anthropic_client()

            mock_secrets.get_secret.assert_called_once_with("ai-video/anthropic-api-key")
            mock_anthropic.assert_called_once_with(api_key="sk-prod-key")


class TestBaseAgent:
    """Tests for BaseAgent class."""

    @patch("src.agents.base.get_anthropic_client")
    def test_agent_initialization(self, mock_get_client: Mock) -> None:
        """Test agent initialization."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        agent = MockAgent()

        assert agent.name == "MockAgent"
        assert agent.description == "Test agent"
        assert agent._client == mock_client
        assert agent.logger is not None

    @patch("src.agents.base.get_anthropic_client")
    def test_successful_agent_run(
        self,
        mock_get_client: Mock,
        mock_anthropic_response: Message,
        mock_agent_input: MockAgentInput,
    ) -> None:
        """Test successful agent execution."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_get_client.return_value = mock_client

        agent = MockAgent()
        result = agent.run(mock_agent_input)

        assert isinstance(result, MockAgentOutput)
        assert result.success is True
        assert result.result == "test_output"

        # Verify API call
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-sonnet-4-20250514"
        assert call_args.kwargs["system"] == "You are a helpful test agent."
        assert len(call_args.kwargs["messages"]) == 1
        assert "job_123" in call_args.kwargs["messages"][0]["content"]

    @patch("src.agents.base.get_anthropic_client")
    def test_agent_run_with_context(
        self,
        mock_get_client: Mock,
        mock_anthropic_response: Message,
        mock_agent_input: MockAgentInput,
    ) -> None:
        """Test agent execution with context from previous agents."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_get_client.return_value = mock_client

        agent = MockAgent()
        context = {"previous_output": "some_data"}
        result = agent.run(mock_agent_input, context)

        assert result.success is True

    @patch("src.agents.base.get_anthropic_client")
    def test_agent_run_logs_token_usage(
        self,
        mock_get_client: Mock,
        mock_anthropic_response: Message,
        mock_agent_input: MockAgentInput,
    ) -> None:
        """Test that token usage is logged for cost monitoring."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_get_client.return_value = mock_client

        agent = MockAgent()

        with patch.object(agent.logger, "info") as mock_log:
            agent.run(mock_agent_input)

            # Check for token usage log
            calls = [call[0][0] for call in mock_log.call_args_list]
            assert "agent_llm_call" in calls

            # Verify token counts in log
            llm_call = [
                call for call in mock_log.call_args_list if call[0][0] == "agent_llm_call"
            ][0]
            assert llm_call.kwargs["input_tokens"] == 100
            assert llm_call.kwargs["output_tokens"] == 50

    @patch("src.agents.base.get_anthropic_client")
    def test_agent_run_error_handling(
        self, mock_get_client: Mock, mock_agent_input: MockAgentInput
    ) -> None:
        """Test agent error handling."""
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API error")
        mock_get_client.return_value = mock_client

        agent = MockAgent()

        with pytest.raises(AgentError) as exc_info:
            agent.run(mock_agent_input)

        assert "MockAgent" in str(exc_info.value)
        assert "API error" in str(exc_info.value)

    @patch("src.agents.base.get_anthropic_client")
    def test_extract_json_from_code_block(self, mock_get_client: Mock) -> None:
        """Test JSON extraction from markdown code blocks."""
        agent = MockAgent()

        # Test with ```json code block
        response = """Here's the result:
```json
{"success": true, "value": 42}
```
"""
        data = agent._extract_json_from_response(response)
        assert data == {"success": True, "value": 42}

        # Test with ``` code block (no language)
        response = """
```
{"success": false, "error": "test"}
```
"""
        data = agent._extract_json_from_response(response)
        assert data == {"success": False, "error": "test"}

    @patch("src.agents.base.get_anthropic_client")
    def test_extract_json_from_plain_text(self, mock_get_client: Mock) -> None:
        """Test JSON extraction from plain text."""
        agent = MockAgent()

        response = '{"result": "plain", "count": 10}'
        data = agent._extract_json_from_response(response)
        assert data == {"result": "plain", "count": 10}

    @patch("src.agents.base.get_anthropic_client")
    def test_extract_json_invalid(self, mock_get_client: Mock) -> None:
        """Test JSON extraction with invalid JSON."""
        agent = MockAgent()

        with pytest.raises(AgentError) as exc_info:
            agent._extract_json_from_response("not valid json {")

        assert "Failed to parse JSON response" in str(exc_info.value)

    @patch("src.agents.base.get_anthropic_client")
    def test_agent_logs_lifecycle_events(
        self,
        mock_get_client: Mock,
        mock_anthropic_response: Message,
        mock_agent_input: MockAgentInput,
    ) -> None:
        """Test that agent logs starting and completion events."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_get_client.return_value = mock_client

        agent = MockAgent()

        with patch.object(agent.logger, "info") as mock_log:
            agent.run(mock_agent_input)

            calls = [call[0][0] for call in mock_log.call_args_list]
            assert "agent_starting" in calls
            assert "agent_completed" in calls

            # Verify job_id is in logs
            for call in mock_log.call_args_list:
                if "job_id" in call.kwargs:
                    assert call.kwargs["job_id"] == "job_123"


class TestAgentInputOutput:
    """Tests for AgentInput and AgentOutput base classes."""

    def test_agent_input_validation(self) -> None:
        """Test AgentInput validation."""
        input_data = AgentInput(job_id="job_123", user_id="user_456")
        assert input_data.job_id == "job_123"
        assert input_data.user_id == "user_456"

    def test_agent_output_defaults(self) -> None:
        """Test AgentOutput default values."""
        output = AgentOutput()
        assert output.success is True
        assert output.error is None

    def test_agent_output_with_error(self) -> None:
        """Test AgentOutput with error."""
        output = AgentOutput(success=False, error="Something went wrong")
        assert output.success is False
        assert output.error == "Something went wrong"

    def test_custom_agent_input_extension(self) -> None:
        """Test extending AgentInput with custom fields."""
        input_data = MockAgentInput(
            job_id="job_123",
            user_id="user_456",
            test_data="custom_value",
        )
        assert input_data.test_data == "custom_value"

    def test_custom_agent_output_extension(self) -> None:
        """Test extending AgentOutput with custom fields."""
        output = MockAgentOutput(success=True, result="custom_result")
        assert output.result == "custom_result"
