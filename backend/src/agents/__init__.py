"""AI Agents for video content generation."""
from src.agents.base import (
    AgentError,
    AgentInput,
    AgentOutput,
    BaseAgent,
)
from src.agents.handler import handler
from src.agents.market_insight import (
    MarketInsightAgent,
    MarketInsightInput,
    MarketInsightOutput,
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
from src.agents.script_reviewer import (
    ScriptReviewerAgent,
    ScriptReviewerInput,
    ScriptReviewerOutput,
)

# Alias for backward compatibility and consistency
agent_handler = handler

__all__ = [
    # Base classes
    "AgentError",
    "AgentInput",
    "AgentOutput",
    "BaseAgent",
    # Lambda handler
    "handler",
    "agent_handler",
    # Market Insight
    "MarketInsightAgent",
    "MarketInsightInput",
    "MarketInsightOutput",
    # Product Analyzer
    "ProductAnalyzerAgent",
    "ProductAnalyzerInput",
    "ProductAnalyzerOutput",
    # Script Generator
    "ScriptGeneratorAgent",
    "ScriptGeneratorInput",
    "ScriptGeneratorOutput",
    # Script Optimizer
    "ScriptOptimizerAgent",
    "ScriptOptimizerInput",
    "ScriptOptimizerOutput",
    # Script Reviewer
    "ScriptReviewerAgent",
    "ScriptReviewerInput",
    "ScriptReviewerOutput",
]
