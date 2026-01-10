"""Integration tests for agent pipeline."""

import os

import pytest
from dotenv import load_dotenv

from src.agents.product_analyzer import ProductAnalyzerAgent, ProductAnalyzerInput


load_dotenv()


@pytest.fixture
def sample_product_input() -> ProductAnalyzerInput:
    """Create sample product input for testing."""
    return ProductAnalyzerInput(
        job_id="test-job-001",
        user_id="test-user-001",
        title="Test Product",
        description="A sample product for testing.",
        price="19.99",
        image_keys=["dummy-image-key"],
    )


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)
def test_product_analyzer_agent(sample_product_input: ProductAnalyzerInput) -> None:
    """Test ProductAnalyzerAgent with sample input."""
    agent = ProductAnalyzerAgent()
    output = agent.run(sample_product_input)

    assert output is not None
