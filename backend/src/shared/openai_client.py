"""OpenAI client wrapper."""
from openai import OpenAI
from openai.types.chat import ChatCompletion

from src.shared.config import get_settings
from src.shared.secrets import get_secrets
from src.shared.logging import get_logger

logger = get_logger(__name__)


class OpenAIClientWrapper:
    """Wrapper for OpenAI client with logging and convenience methods."""

    def __init__(self, api_key: str) -> None:
        """Initialize OpenAI client with API key.
        
        Args:
            api_key: OpenAI API key.
        """
        self._client = OpenAI(api_key=api_key)
        self.logger = get_logger("openai_client")

    @property
    def client(self) -> OpenAI:
        """Get the underlying OpenAI client."""
        return self._client

    def chat_completion(
        self,
        messages: list[dict],
        model: str = "gpt-4o",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        response_format: dict | None = None,
    ) -> ChatCompletion:
        """Create a chat completion.
        
        Args:
            messages: List of message dicts with role and content.
            model: Model to use (default: gpt-4o).
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature (0-2).
            response_format: Optional response format (e.g., {"type": "json_object"}).
        
        Returns:
            ChatCompletion response from OpenAI.
        """
        kwargs: dict = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = self._client.chat.completions.create(**kwargs)

        # Log token usage for cost tracking
        if response.usage:
            self.logger.info(
                "openai_response",
                model=model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )

        return response


_openai_client: OpenAIClientWrapper | None = None


def get_openai_client() -> OpenAIClientWrapper:
    """Get OpenAI client singleton.
    
    Returns:
        OpenAIClientWrapper instance.
    """
    global _openai_client
    if _openai_client is None:
        settings = get_settings()
        secrets = get_secrets()
        api_key = secrets.get_secret(settings.secrets_openai_key)
        _openai_client = OpenAIClientWrapper(api_key=api_key)
        logger.info("openai_client_initialized")
    return _openai_client


def reset_openai_client() -> None:
    """Reset client singleton for testing."""
    global _openai_client
    _openai_client = None
