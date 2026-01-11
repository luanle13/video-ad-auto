from unittest.mock import MagicMock, patch
import pytest
from src.agents.base import BaseAgent  # Assuming the base agent is in src.agents.base


class MockAgent(BaseAgent):
    """Mock agent for testing purposes."""
    def __init__(self, client=None, model="test-model", max_retries=3, delay=1):
        super().__init__(client=client, model=model, max_retries=max_retries, delay=delay)


class TestBaseAgent:
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        mock_client = MagicMock()
        agent = MockAgent(client=mock_client, model="test-model", max_retries=5)
        
        assert agent.client == mock_client
        assert agent.model == "test-model"
        assert agent.max_retries == 5
        assert agent.delay == 1
    
    def test_build_messages(self):
        """Test building messages for API call."""
        agent = MockAgent()
        
        system_prompt = "You are a helpful assistant."
        user_input = "Hello, world!"
        
        messages = agent.build_messages(system_prompt, user_input)
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == system_prompt
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == user_input
    
    def test_extract_json_from_response_plain_json(self):
        """Test extracting plain JSON from response."""
        agent = MockAgent()
        
        response_text = '{"key": "value", "number": 42}'
        extracted = agent.extract_json_from_response(response_text)
        
        assert extracted == {"key": "value", "number": 42}
    
    def test_extract_json_from_code_block(self):
        """Test extracting JSON from code block."""
        agent = MockAgent()
        
        response_text = '''Here is the response:
```json
{
    "product": "Test Product",
    "features": ["feature1", "feature2"]
}
```
More text after.'''
        
        extracted = agent.extract_json_from_response(response_text)
        
        expected = {"product": "Test Product", "features": ["feature1", "feature2"]}
        assert extracted == expected
    
    def test_extract_json_from_triple_backtick_block(self):
        """Test extracting JSON from triple backtick block without language identifier."""
        agent = MockAgent()
        
        response_text = '''Here is the response:
```
{
    "test": "value"
}
```
More text after.'''
        
        extracted = agent.extract_json_from_response(response_text)
        
        expected = {"test": "value"}
        assert extracted == expected
    
    def test_extract_json_invalid(self):
        """Test extracting JSON from invalid response raises error."""
        agent = MockAgent()
        
        invalid_responses = [
            "This is not JSON",
            '{"unclosed": "brace"',
            "Just plain text",
            "",
            "{invalid: json}"
        ]
        
        for invalid_response in invalid_responses:
            with pytest.raises(ValueError):
                agent.extract_json_from_response(invalid_response)
    
    def test_run_success(self):
        """Test successful run with mocked anthropic client."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"result": "success"}')]
        mock_client.messages.create.return_value = mock_response
        
        agent = MockAgent(client=mock_client)
        
        system_prompt = "You are a helpful assistant."
        user_input = "Process this data."
        
        result = agent.run(system_prompt, user_input)
        
        assert result == {"result": "success"}
        mock_client.messages.create.assert_called_once()
        
        # Check that the call was made with the right arguments
        call_args = mock_client.messages.create.call_args
        assert call_args[1]['model'] == agent.model
        assert len(call_args[1]['messages']) == 2  # system and user messages
    
    def test_run_api_error(self):
        """Test run with API error."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        
        agent = MockAgent(client=mock_client)
        
        system_prompt = "You are a helpful assistant."
        user_input = "Process this data."
        
        with pytest.raises(Exception, match="API Error"):
            agent.run(system_prompt, user_input)
    
    def test_run_parse_error(self):
        """Test run with JSON parse error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='This is not valid JSON')]
        mock_client.messages.create.return_value = mock_response
        
        agent = MockAgent(client=mock_client)
        
        system_prompt = "You are a helpful assistant."
        user_input = "Process this data."
        
        with pytest.raises(ValueError):
            agent.run(system_prompt, user_input)
    
    def test_retry_on_rate_limit(self):
        """Test that agent retries on rate limit error."""
        mock_client = MagicMock()
        # First two calls raise rate limit error, third succeeds
        mock_client.messages.create.side_effect = [
            Exception("Rate limit exceeded"),
            Exception("Rate limit exceeded"),
            MagicMock(content=[MagicMock(text='{"result": "eventual_success"}')])
        ]
        
        agent = MockAgent(client=mock_client, max_retries=3)
        
        system_prompt = "You are a helpful assistant."
        user_input = "Process this data."
        
        result = agent.run(system_prompt, user_input)
        
        assert result == {"result": "eventual_success"}
        assert mock_client.messages.create.call_count == 3  # Called 3 times
    
    def test_max_retries_exceeded(self):
        """Test that agent stops after max retries."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("Rate limit exceeded")
        
        agent = MockAgent(client=mock_client, max_retries=2)
        
        system_prompt = "You are a helpful assistant."
        user_input = "Process this data."
        
        with pytest.raises(Exception, match="Rate limit exceeded"):
            agent.run(system_prompt, user_input)
        
        # Should be called max_retries + 1 times (initial call + retries)
        assert mock_client.messages.create.call_count == 3
    
    def test_run_with_different_models(self):
        """Test that agent works with different models."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"model_test": "passed"}')]
        mock_client.messages.create.return_value = mock_response
        
        agent = MockAgent(client=mock_client, model="custom-model")
        
        system_prompt = "You are a helpful assistant."
        user_input = "Test with custom model."
        
        result = agent.run(system_prompt, user_input)
        
        assert result == {"model_test": "passed"}
        # Verify the model was passed to the API call
        call_args = mock_client.messages.create.call_args
        assert call_args[1]['model'] == "custom-model"