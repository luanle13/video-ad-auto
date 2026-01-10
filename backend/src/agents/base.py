"""Base agent and CrewAI configuration."""
from abc import ABC, abstractmethod
from typing import Any

from openai import OpenAI
from pydantic import BaseModel

from src.shared.config import get_settings
from src.shared.exceptions import AgentError
from src.shared.logging import get_logger
from src.shared.secrets import get_secrets

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
    model: str = "gpt-4.1"
    max_tokens: int = 4096
    temperature: float = 0.7

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.azure_openai_api_key.get_secret_value() if settings.azure_openai_api_key else None
        self.endpoint = settings.azure_openai_endpoint

        if not self.api_key or not self.endpoint:
            raise ValueError("Azure OpenAI API key and endpoint must be set in environment variables.")

        # Configure OpenAI client (v1.x)
        self._client = OpenAI(
            base_url=self.endpoint,
            api_key=self.api_key
        )

        self.logger = get_logger(f"agents.{self.name}")

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

            response = self._client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
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
