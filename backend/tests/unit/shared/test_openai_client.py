"""Tests for OpenAI client wrapper."""
from unittest.mock import MagicMock, patch

import pytest

from src.shared.openai_client import (
    OpenAIClientWrapper,
    get_openai_client,
    reset_openai_client,
)


class TestOpenAIClientWrapper:
    """Tests for OpenAIClientWrapper class."""

    def test_init_creates_client(self) -> None:
        """Test that initialization creates OpenAI client."""
        with patch("src.shared.openai_client.OpenAI") as mock_openai:
            wrapper = OpenAIClientWrapper(api_key="test-key")
            mock_openai.assert_called_once_with(api_key="test-key")
            assert wrapper._client == mock_openai.return_value

    def test_client_property(self) -> None:
        """Test client property returns underlying client."""
        with patch("src.shared.openai_client.OpenAI") as mock_openai:
            wrapper = OpenAIClientWrapper(api_key="test-key")
            assert wrapper.client == mock_openai.return_value

    def test_chat_completion_basic(self) -> None:
        """Test basic chat completion call."""
        with patch("src.shared.openai_client.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            mock_response.usage.total_tokens = 150
            mock_client.chat.completions.create.return_value = mock_response
            
            wrapper = OpenAIClientWrapper(api_key="test-key")
            messages = [{"role": "user", "content": "Hello"}]
            
            response = wrapper.chat_completion(messages=messages)
            
            mock_client.chat.completions.create.assert_called_once_with(
                model="gpt-4o",
                messages=messages,
                max_tokens=4096,
                temperature=0.7,
            )
            assert response == mock_response

    def test_chat_completion_with_custom_params(self) -> None:
        """Test chat completion with custom parameters."""
        with patch("src.shared.openai_client.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.usage.prompt_tokens = 200
            mock_response.usage.completion_tokens = 100
            mock_response.usage.total_tokens = 300
            mock_client.chat.completions.create.return_value = mock_response
            
            wrapper = OpenAIClientWrapper(api_key="test-key")
            messages = [{"role": "user", "content": "Generate JSON"}]
            
            response = wrapper.chat_completion(
                messages=messages,
                model="gpt-4-turbo",
                max_tokens=2048,
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            
            mock_client.chat.completions.create.assert_called_once_with(
                model="gpt-4-turbo",
                messages=messages,
                max_tokens=2048,
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            assert response == mock_response

    def test_chat_completion_logs_token_usage(self) -> None:
        """Test that chat completion logs token usage."""
        with patch("src.shared.openai_client.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            mock_response.usage.total_tokens = 150
            mock_client.chat.completions.create.return_value = mock_response
            
            wrapper = OpenAIClientWrapper(api_key="test-key")
            
            with patch.object(wrapper.logger, "info") as mock_log:
                wrapper.chat_completion(messages=[{"role": "user", "content": "Hi"}])
                
                mock_log.assert_called_once_with(
                    "openai_response",
                    model="gpt-4o",
                    prompt_tokens=100,
                    completion_tokens=50,
                    total_tokens=150,
                )

    def test_chat_completion_no_usage(self) -> None:
        """Test chat completion handles missing usage data."""
        with patch("src.shared.openai_client.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.usage = None
            mock_client.chat.completions.create.return_value = mock_response
            
            wrapper = OpenAIClientWrapper(api_key="test-key")
            
            # Should not raise even without usage data
            response = wrapper.chat_completion(messages=[{"role": "user", "content": "Hi"}])
            assert response == mock_response


class TestGetOpenAIClient:
    """Tests for get_openai_client singleton function."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        reset_openai_client()

    def teardown_method(self) -> None:
        """Reset singleton after each test."""
        reset_openai_client()

    def test_get_openai_client_creates_singleton(self) -> None:
        """Test that get_openai_client creates and returns singleton."""
        with patch("src.shared.openai_client.get_settings") as mock_settings, \
             patch("src.shared.openai_client.get_secrets") as mock_secrets, \
             patch("src.shared.openai_client.OpenAI"):
            
            mock_settings.return_value.secrets_openai_key = "ai-video/openai-api-key"
            mock_secrets.return_value.get_secret.return_value = "test-api-key"
            
            client1 = get_openai_client()
            client2 = get_openai_client()
            
            assert client1 is client2
            mock_secrets.return_value.get_secret.assert_called_once_with("ai-video/openai-api-key")

    def test_get_openai_client_uses_settings(self) -> None:
        """Test that get_openai_client uses settings for secret name."""
        with patch("src.shared.openai_client.get_settings") as mock_settings, \
             patch("src.shared.openai_client.get_secrets") as mock_secrets, \
             patch("src.shared.openai_client.OpenAI") as mock_openai:
            
            mock_settings.return_value.secrets_openai_key = "custom/secret/name"
            mock_secrets.return_value.get_secret.return_value = "custom-api-key"
            
            get_openai_client()
            
            mock_secrets.return_value.get_secret.assert_called_once_with("custom/secret/name")
            mock_openai.assert_called_once_with(api_key="custom-api-key")


class TestResetOpenAIClient:
    """Tests for reset_openai_client function."""

    def test_reset_clears_singleton(self) -> None:
        """Test that reset_openai_client clears the singleton."""
        with patch("src.shared.openai_client.get_settings") as mock_settings, \
             patch("src.shared.openai_client.get_secrets") as mock_secrets, \
             patch("src.shared.openai_client.OpenAI"):
            
            mock_settings.return_value.secrets_openai_key = "test-key"
            mock_secrets.return_value.get_secret.return_value = "api-key"
            
            client1 = get_openai_client()
            reset_openai_client()
            client2 = get_openai_client()
            
            # Should be different instances after reset
            assert client1 is not client2
            # Should have called get_secret twice
            assert mock_secrets.return_value.get_secret.call_count == 2
