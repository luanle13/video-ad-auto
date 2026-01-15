"""Unit tests for BaseAgent."""
import json
from unittest.mock import MagicMock, patch

import pytest
from openai import APIError, RateLimitError

from src.agents.base import AgentInput, AgentOutput, BaseAgent
from src.shared.exceptions import AgentError, OpenAIError, OpenAIRateLimitError
from tests.fixtures.mocks import create_mock_openai_client, create_mock_openai_response


class ConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""

    name = "TestAgent"
    description = "Test agent for unit tests"

    @property
    def system_prompt(self) -> str:
        return "You are a test agent. Respond with valid JSON."

    def build_user_prompt(self, input_data: AgentInput, context: dict) -> str:
        return f"Process job {input_data.job_id}"

    def parse_response(self, response_text: str, input_data: AgentInput) -> AgentOutput:
        data = self._extract_json_from_response(response_text)
        return AgentOutput(success=data.get("success", True))


class TestAgentInput:
    """Tests for AgentInput model."""

    def test_create_input(self):
        """Test creating an AgentInput."""
        input_data = AgentInput(job_id="job123", user_id="user456")
        assert input_data.job_id == "job123"
        assert input_data.user_id == "user456"

    def test_input_validation(self):
        """Test that required fields are validated."""
        with pytest.raises(ValueError):
            AgentInput(job_id="job123")  # Missing user_id


class TestAgentOutput:
    """Tests for AgentOutput model."""

    def test_create_output(self):
        """Test creating an AgentOutput."""
        output = AgentOutput(success=True)
        assert output.success is True
        assert output.error is None

    def test_output_with_error(self):
        """Test creating an AgentOutput with error."""
        output = AgentOutput(success=False, error="Something went wrong")
        assert output.success is False
        assert output.error == "Something went wrong"


class TestBaseAgent:
    """Tests for BaseAgent class."""

    def test_agent_initialization(self):
        """Test agent initializes correctly."""
        agent = ConcreteAgent()
        assert agent.name == "TestAgent"
        assert agent.description == "Test agent for unit tests"
        assert agent.model == "gpt-4o"
        assert agent.max_tokens == 4096
        assert agent.temperature == 0.7
        assert agent._client is None

    @patch("src.agents.base.get_openai_client")
    def test_client_lazy_loading(self, mock_get_client):
        """Test that client is lazy loaded."""
        mock_client = create_mock_openai_client()
        mock_get_client.return_value = mock_client

        agent = ConcreteAgent()
        assert agent._client is None

        # Access client property
        client = agent.client
        assert client is mock_client
        mock_get_client.assert_called_once()

        # Second access should not call get_openai_client again
        client2 = agent.client
        assert client2 is mock_client
        mock_get_client.assert_called_once()

    def test_system_prompt(self):
        """Test system prompt property."""
        agent = ConcreteAgent()
        assert "test agent" in agent.system_prompt.lower()

    def test_build_user_prompt(self):
        """Test building user prompt."""
        agent = ConcreteAgent()
        input_data = AgentInput(job_id="job123", user_id="user456")
        prompt = agent.build_user_prompt(input_data, {})
        assert "job123" in prompt

    def test_build_messages(self):
        """Test _build_messages method."""
        agent = ConcreteAgent()
        input_data = AgentInput(job_id="job123", user_id="user456")
        messages = agent._build_messages(input_data, {})

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "test agent" in messages[0]["content"].lower()
        assert "job123" in messages[1]["content"]

    @patch("src.agents.base.get_openai_client")
    def test_run_success(self, mock_get_client):
        """Test successful agent run."""
        mock_client = create_mock_openai_client()
        mock_response = create_mock_openai_response('{"success": true}')
        mock_client.chat_completion.return_value = mock_response
        mock_get_client.return_value = mock_client

        agent = ConcreteAgent()
        input_data = AgentInput(job_id="job123", user_id="user456")
        output = agent.run(input_data)

        assert output.success is True
        mock_client.chat_completion.assert_called_once()

        # Verify call arguments
        call_kwargs = mock_client.chat_completion.call_args[1]
        assert call_kwargs["model"] == "gpt-4o"
        assert call_kwargs["max_tokens"] == 4096
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["response_format"] == {"type": "json_object"}

    @patch("src.agents.base.get_openai_client")
    def test_run_with_context(self, mock_get_client):
        """Test agent run with context."""
        mock_client = create_mock_openai_client()
        mock_response = create_mock_openai_response('{"success": true}')
        mock_client.chat_completion.return_value = mock_response
        mock_get_client.return_value = mock_client

        agent = ConcreteAgent()
        input_data = AgentInput(job_id="job123", user_id="user456")
        context = {"previous_step": {"output": "data"}}
        output = agent.run(input_data, context)

        assert output.success is True

    @patch("src.agents.base.get_openai_client")
    def test_run_rate_limit_error(self, mock_get_client):
        """Test agent run handles rate limit errors."""
        mock_client = create_mock_openai_client()
        mock_client.chat_completion.side_effect = RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(status_code=429),
            body=None,
        )
        mock_get_client.return_value = mock_client

        agent = ConcreteAgent()
        input_data = AgentInput(job_id="job123", user_id="user456")

        with pytest.raises(OpenAIRateLimitError):
            agent.run(input_data)

    @patch("src.agents.base.get_openai_client")
    def test_run_api_error(self, mock_get_client):
        """Test agent run handles API errors."""
        mock_client = create_mock_openai_client()
        mock_error = APIError(
            message="API error",
            request=MagicMock(),
            body=None,
        )
        mock_error.status_code = 500
        mock_client.chat_completion.side_effect = mock_error
        mock_get_client.return_value = mock_client

        agent = ConcreteAgent()
        input_data = AgentInput(job_id="job123", user_id="user456")

        with pytest.raises(OpenAIError):
            agent.run(input_data)


class TestExtractJsonFromResponse:
    """Tests for _extract_json_from_response method."""

    def test_extract_plain_json(self):
        """Test extracting plain JSON."""
        agent = ConcreteAgent()
        result = agent._extract_json_from_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_extract_json_from_code_block(self):
        """Test extracting JSON from markdown code block."""
        agent = ConcreteAgent()
        text = '```json\n{"key": "value"}\n```'
        result = agent._extract_json_from_response(text)
        assert result == {"key": "value"}

    def test_extract_json_from_code_block_no_language(self):
        """Test extracting JSON from code block without language specifier."""
        agent = ConcreteAgent()
        text = '```\n{"key": "value"}\n```'
        result = agent._extract_json_from_response(text)
        assert result == {"key": "value"}

    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises AgentError."""
        agent = ConcreteAgent()
        with pytest.raises(AgentError):
            agent._extract_json_from_response("not valid json")
