"""Base agent and CrewAI configuration."""
from abc import ABC, abstractmethod
from typing import Any

from openai import APIError, RateLimitError
from pydantic import BaseModel

from src.shared.config import get_settings
from src.shared.exceptions import AgentError, OpenAIError, OpenAIRateLimitError
from src.shared.logging import get_logger
from src.shared.openai_client import OpenAIClientWrapper, get_openai_client

logger = get_logger(__name__)


class AgentInput(BaseModel):
    """Base class for agent inputs."""

    job_id: str
    user_id: str


class AgentOutput(BaseModel):
    """Base class for agent outputs."""

    success: bool = True
    error: str | None = None


class BaseAgent(ABC):
    """Base class for all CrewAI agents."""

    name: str = "BaseAgent"
    description: str = ""
    model: str = "gpt-4o"
    max_tokens: int = 4096
    temperature: float = 0.7

    def __init__(self) -> None:
        """Initialize agent with lazy-loaded OpenAI client."""
        self._client: OpenAIClientWrapper | None = None
        self.logger = get_logger(f"agents.{self.name}")

    @property
    def client(self) -> OpenAIClientWrapper:
        """Get OpenAI client (lazy loaded)."""
        if self._client is None:
            self._client = get_openai_client()
        return self._client

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt for this agent."""
        pass

    @abstractmethod
    def build_user_prompt(self, input_data: AgentInput, context: dict[str, Any]) -> str:
        """Build user prompt from input data and context."""
        pass

    @abstractmethod
    def parse_response(self, response_text: str, input_data: AgentInput) -> AgentOutput:
        """Parse LLM response into structured output."""
        pass

    def run(self, input_data: AgentInput, context: dict[str, Any] | None = None) -> AgentOutput:
        """
        Execute the agent.

        Args:
            input_data: Agent-specific input
            context: Outputs from previous agents in the pipeline

        Returns:
            Agent-specific output
        """
        context = context or {}

        self.logger.info(
            "agent_starting",
            agent=self.name,
            job_id=input_data.job_id,
        )

        try:
            user_prompt = self.build_user_prompt(input_data, context)

            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            response = self.client.chat_completion(
                messages=messages,
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            response_text = response.choices[0].message.content

            # Log token usage for cost monitoring
            self.logger.info(
                "agent_llm_call",
                agent=self.name,
                job_id=input_data.job_id,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
            )

            output = self.parse_response(response_text, input_data)

            self.logger.info(
                "agent_completed",
                agent=self.name,
                job_id=input_data.job_id,
                success=output.success,
            )

            return output

        except RateLimitError as e:
            self.logger.error(
                "agent_rate_limit",
                agent=self.name,
                job_id=input_data.job_id,
                error=str(e),
            )
            raise OpenAIRateLimitError(str(e))

        except APIError as e:
            self.logger.error(
                "agent_api_error",
                agent=self.name,
                job_id=input_data.job_id,
                error=str(e),
            )
            raise OpenAIError(str(e), status_code=e.status_code if hasattr(e, "status_code") else None)

        except Exception as e:
            self.logger.exception(
                "agent_error",
                agent=self.name,
                job_id=input_data.job_id,
                error=str(e),
            )
            raise AgentError(self.name, str(e))

    def _extract_json_from_response(self, text: str) -> dict[str, Any]:
        """Extract JSON from LLM response, handling markdown code blocks."""
        import json
        import re

        # Try to find JSON in code blocks first
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Assume the whole response is JSON
            json_str = text.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise AgentError(self.name, f"Failed to parse JSON response: {e}")
