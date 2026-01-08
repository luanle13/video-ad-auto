"""CrewAI agents for video generation pipeline."""
from src.agents.base import (
    AgentError,
    AgentInput,
    AgentOutput,
    BaseAgent,
    get_anthropic_client,
)
from src.agents.product_analyzer import (
    ProductAnalyzerAgent,
    ProductAnalyzerInput,
    ProductAnalyzerOutput,
)
from src.agents.script_generator import (
    ScriptGeneratorAgent,
    ScriptGeneratorInput,
    ScriptGeneratorOutput,
)
from src.agents.script_optimizer import (
    ScriptOptimizerAgent,
    ScriptOptimizerInput,
    ScriptOptimizerOutput,
)

__all__ = [
    "AgentError",
    "AgentInput",
    "AgentOutput",
    "BaseAgent",
    "get_anthropic_client",
    "ProductAnalyzerAgent",
    "ProductAnalyzerInput",
    "ProductAnalyzerOutput",
    "ScriptGeneratorAgent",
    "ScriptGeneratorInput",
    "ScriptGeneratorOutput",
    "ScriptOptimizerAgent",
    "ScriptOptimizerInput",
    "ScriptOptimizerOutput",
]
