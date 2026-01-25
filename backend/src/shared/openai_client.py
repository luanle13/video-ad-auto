"""OpenAI client wrapper for Azure OpenAI."""
from openai import OpenAI
from openai.types.chat import ChatCompletion

from src.shared.config import get_settings
from src.shared.logging import get_logger

logger = get_logger(__name__)


class OpenAIClientWrapper:
    """Wrapper for Azure OpenAI client with logging and convenience methods."""

    def __init__(self, api_key: str, endpoint: str, deployment_name: str) -> None:
        """Initialize Azure OpenAI client.
        
        Args:
            api_key: Azure OpenAI API key.
            endpoint: Azure OpenAI endpoint (e.g., https://xxx.openai.azure.com/openai/v1/).
            deployment_name: GPT model deployment name.
        """
        # Azure OpenAI client using base_url approach
        self._client = OpenAI(
            base_url=endpoint,
            api_key=api_key,
        )
        self._deployment_name = deployment_name
        self.logger = get_logger("azure_openai_client")

    @property
    def client(self) -> OpenAI:
        """Get the underlying OpenAI client."""
        return self._client

    def chat_completion(
        self,
        messages: list[dict],
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        response_format: dict | None = None,
    ) -> ChatCompletion:
        """Create a chat completion.
        
        Args:
            messages: List of message dicts with role and content.
            model: Model to use (uses deployment_name if None).
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature (0-2).
            response_format: Optional response format (e.g., {"type": "json_object"}).
        
        Returns:
            ChatCompletion response from Azure OpenAI.
        """
        # Use deployment name for Azure
        model_name = model or self._deployment_name
        
        kwargs: dict = {
            "model": model_name,
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
                "azure_openai_response",
                model=model_name,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )

        return response


_openai_client: OpenAIClientWrapper | None = None


def get_openai_client() -> OpenAIClientWrapper:
    """Get Azure OpenAI client singleton.

    Returns:
        OpenAIClientWrapper instance.
    """
    global _openai_client
    if _openai_client is None:
        from src.shared.secrets import get_secrets

        settings = get_settings()
        endpoint = settings.azure_openai_endpoint

        if not endpoint:
            raise ValueError(
                "Azure OpenAI not configured. Set AZURE_OPENAI_ENDPOINT"
            )

        # Try to get API key from Secrets Manager first, then fall back to env var
        api_key = None
        if settings.secrets_azure_openai_key:
            try:
                secrets = get_secrets()
                secret_data = secrets.get_secret_json(settings.secrets_azure_openai_key)
                api_key = secret_data.get("api_key")
                logger.info("azure_openai_key_from_secrets_manager")
            except Exception as e:
                logger.warning("failed_to_get_azure_key_from_secrets", error=str(e))

        # Fall back to environment variable
        if not api_key and settings.azure_openai_api_key:
            api_key = settings.azure_openai_api_key.get_secret_value() if hasattr(settings.azure_openai_api_key, 'get_secret_value') else str(settings.azure_openai_api_key)
            logger.info("azure_openai_key_from_env")

        if not api_key:
            raise ValueError(
                "Azure OpenAI API key not found. Set it in Secrets Manager or AZURE_OPENAI_API_KEY env var"
            )

        _openai_client = OpenAIClientWrapper(
            api_key=api_key,
            endpoint=endpoint,
            deployment_name=settings.azure_gpt_deployment_name,
        )
        logger.info("azure_openai_client_initialized", deployment=settings.azure_gpt_deployment_name)
    return _openai_client


def reset_openai_client() -> None:
    """Reset client singleton for testing."""
    global _openai_client
    _openai_client = None
