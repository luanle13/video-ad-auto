"""Unit tests for ProductAnalyzerAgent."""
import json
from unittest.mock import MagicMock, patch

import pytest

from src.agents.product_analyzer import (
    ProductAnalyzerAgent,
    ProductAnalyzerInput,
    ProductAnalyzerOutput,
)
from tests.fixtures.mocks import create_mock_openai_client, create_mock_openai_response


class TestProductAnalyzerInput:
    """Tests for ProductAnalyzerInput model."""

    def test_create_input(self):
        """Test creating a ProductAnalyzerInput."""
        input_data = ProductAnalyzerInput(
            job_id="job123",
            user_id="user456",
            title="Test Product",
            description="A great product",
            price="$19.99",
            image_keys=["img1.jpg", "img2.jpg"],
        )
        assert input_data.job_id == "job123"
        assert input_data.title == "Test Product"
        assert len(input_data.image_keys) == 2

    def test_image_keys_validation(self):
        """Test that at least one image key is required."""
        with pytest.raises(ValueError):
            ProductAnalyzerInput(
                job_id="job123",
                user_id="user456",
                title="Test Product",
                description="A great product",
                price="$19.99",
                image_keys=[],
            )


class TestProductAnalyzerOutput:
    """Tests for ProductAnalyzerOutput model."""

    def test_create_output(self):
        """Test creating a ProductAnalyzerOutput."""
        output = ProductAnalyzerOutput(
            success=True,
            key_features=["Feature 1", "Feature 2"],
            unique_selling_points=["USP 1"],
            target_audience="Young professionals",
            visual_elements=["Element 1"],
            product_category="Electronics",
            price_positioning="mid-range",
            suggested_hooks=["Hook 1"],
            raw_analysis="Full analysis text",
        )
        assert output.success is True
        assert len(output.key_features) == 2
        assert output.product_category == "Electronics"


class TestProductAnalyzerAgent:
    """Tests for ProductAnalyzerAgent class."""

    def test_agent_properties(self):
        """Test agent properties."""
        agent = ProductAnalyzerAgent()
        assert agent.name == "ProductAnalyzer"
        assert agent.model == "gpt-4o"
        assert agent.temperature == 0.3

    def test_system_prompt_contains_json_instruction(self):
        """Test system prompt contains JSON instruction."""
        agent = ProductAnalyzerAgent()
        assert "You must respond with valid JSON" in agent.system_prompt

    @patch("src.agents.base.get_openai_client")
    @patch("src.agents.product_analyzer.get_cache_service")
    def test_run_success(self, mock_get_cache_service, mock_get_client):
        """Test successful agent run."""
        # Mock cache service
        mock_cache = MagicMock()
        mock_cache.get_image_base64.return_value = "data:image/jpeg;base64,ZmFrZSBpbWFnZSBkYXRh"
        mock_get_cache_service.return_value = mock_cache

        # Mock OpenAI client
        mock_client = create_mock_openai_client()
        response_content = json.dumps({
            "key_features": ["Wireless", "Fast charging"],
            "unique_selling_points": ["Best in class battery"],
            "target_audience": "Tech enthusiasts",
            "visual_elements": ["Sleek design"],
            "product_category": "Electronics",
            "price_positioning": "premium",
            "suggested_hooks": ["Never charge again!"],
            "raw_analysis": "This product is excellent.",
        })
        mock_response = create_mock_openai_response(response_content)
        mock_client.chat_completion.return_value = mock_response
        mock_get_client.return_value = mock_client

        agent = ProductAnalyzerAgent()
        input_data = ProductAnalyzerInput(
            job_id="job123",
            user_id="user456",
            title="Wireless Earbuds",
            description="Premium wireless earbuds",
            price="$149.99",
            image_keys=["earbuds.jpg"],
        )

        output = agent.run(input_data)

        assert output.success is True
        assert "Wireless" in output.key_features
        assert output.product_category == "Electronics"
        mock_client.chat_completion.assert_called_once()

    @patch("src.agents.base.get_openai_client")
    @patch("src.agents.product_analyzer.get_cache_service")
    def test_build_user_prompt(self, mock_get_cache_service, mock_get_client):
        """Test building user prompt."""
        mock_cache = MagicMock()
        mock_cache.get_image_base64.return_value = "data:image/jpeg;base64,ZmFrZSBpbWFnZSBkYXRh"
        mock_get_cache_service.return_value = mock_cache

        agent = ProductAnalyzerAgent()
        input_data = ProductAnalyzerInput(
            job_id="job123",
            user_id="user456",
            title="Test Product",
            description="Product description",
            price="$99.99",
            image_keys=["img.jpg"],
        )

        prompt = agent.build_user_prompt(input_data, {})

        assert "Test Product" in prompt
        assert "Product description" in prompt
        assert "$99.99" in prompt

    def test_parse_response(self):
        """Test parsing LLM response."""
        agent = ProductAnalyzerAgent()
        input_data = ProductAnalyzerInput(
            job_id="job123",
            user_id="user456",
            title="Test",
            description="Test",
            price="$10",
            image_keys=["img.jpg"],
        )

        response_text = json.dumps({
            "key_features": ["Feature 1"],
            "unique_selling_points": ["USP 1"],
            "target_audience": "Everyone",
            "visual_elements": ["Element 1"],
            "product_category": "General",
            "price_positioning": "budget",
            "suggested_hooks": ["Hook 1"],
            "raw_analysis": "Analysis",
        })

        output = agent.parse_response(response_text, input_data)

        assert output.success is True
        assert output.key_features == ["Feature 1"]
        assert output.product_category == "General"
