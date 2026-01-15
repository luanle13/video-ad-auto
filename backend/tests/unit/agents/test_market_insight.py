"""Unit tests for MarketInsightAgent."""
import json
from unittest.mock import patch

import pytest

from src.agents.market_insight import (
    MarketInsightAgent,
    MarketInsightInput,
    MarketInsightOutput,
)
from tests.fixtures.mocks import create_mock_openai_client, create_mock_openai_response


class TestMarketInsightInput:
    """Tests for MarketInsightInput model."""

    def test_create_input(self):
        """Test creating a MarketInsightInput."""
        input_data = MarketInsightInput(
            job_id="job123",
            user_id="user456",
            product_category="Electronics",
            target_audience="Young professionals",
            key_features=["Wireless", "Fast charging"],
            price_positioning="premium",
        )
        assert input_data.job_id == "job123"
        assert input_data.product_category == "Electronics"
        assert len(input_data.key_features) == 2


class TestMarketInsightOutput:
    """Tests for MarketInsightOutput model."""

    def test_create_output(self):
        """Test creating a MarketInsightOutput."""
        output = MarketInsightOutput(
            success=True,
            trending_hashtags=["#tech", "#gadgets"],
            content_angles=["Unboxing", "Review"],
            platform_tips={"tiktok": "Use trending sounds"},
            trending_formats=["POV", "Tutorial"],
            suggested_music_style="Upbeat electronic",
            best_posting_times=["7PM", "9PM"],
            competitor_insights="Market is competitive",
        )
        assert output.success is True
        assert len(output.trending_hashtags) == 2
        assert "tiktok" in output.platform_tips


class TestMarketInsightAgent:
    """Tests for MarketInsightAgent class."""

    def test_agent_properties(self):
        """Test agent properties."""
        agent = MarketInsightAgent()
        assert agent.name == "MarketInsight"
        assert agent.max_tokens == 1536
        assert agent.temperature == 0.5

    def test_system_prompt_contains_json_instruction(self):
        """Test system prompt contains JSON instruction."""
        agent = MarketInsightAgent()
        assert "You must respond with valid JSON" in agent.system_prompt

    def test_trending_formats_constant(self):
        """Test TRENDING_FORMATS constant."""
        agent = MarketInsightAgent()
        assert len(agent.TRENDING_FORMATS) > 0
        assert "Tutorial/How-to" in agent.TRENDING_FORMATS

    @patch("src.agents.base.get_openai_client")
    def test_run_success(self, mock_get_client):
        """Test successful agent run."""
        mock_client = create_mock_openai_client()
        response_content = json.dumps({
            "trending_hashtags": ["#TechReview", "#GadgetVietnam"],
            "content_angles": ["Unboxing experience", "Day in the life"],
            "platform_tips": {
                "tiktok": "Use trending sounds",
                "facebook": "Add captions",
                "shopee": "Show price clearly",
            },
            "trending_formats": ["POV", "Tutorial"],
            "suggested_music_style": "Upbeat pop",
            "best_posting_times": ["7PM GMT+7", "9PM GMT+7"],
            "competitor_insights": "Market is growing",
        })
        mock_response = create_mock_openai_response(response_content)
        mock_client.chat_completion.return_value = mock_response
        mock_get_client.return_value = mock_client

        agent = MarketInsightAgent()
        input_data = MarketInsightInput(
            job_id="job123",
            user_id="user456",
            product_category="Electronics",
            target_audience="Tech enthusiasts",
            key_features=["Wireless", "Bluetooth 5.0"],
            price_positioning="mid-range",
        )

        output = agent.run(input_data)

        assert output.success is True
        assert "#TechReview" in output.trending_hashtags
        assert "tiktok" in output.platform_tips
        mock_client.chat_completion.assert_called_once()

    def test_build_user_prompt(self):
        """Test building user prompt."""
        agent = MarketInsightAgent()
        input_data = MarketInsightInput(
            job_id="job123",
            user_id="user456",
            product_category="Beauty",
            target_audience="Women 18-35",
            key_features=["Organic", "Vegan"],
            price_positioning="premium",
        )

        prompt = agent.build_user_prompt(input_data, {})

        assert "Beauty" in prompt
        assert "Women 18-35" in prompt
        assert "premium" in prompt
        assert "Organic" in prompt

    def test_parse_response(self):
        """Test parsing LLM response."""
        agent = MarketInsightAgent()
        input_data = MarketInsightInput(
            job_id="job123",
            user_id="user456",
            product_category="Electronics",
            target_audience="Gamers",
            key_features=["RGB lighting"],
            price_positioning="budget",
        )

        response_text = json.dumps({
            "trending_hashtags": ["#gaming"] * 20,  # Test limit
            "content_angles": ["Setup tour"],
            "platform_tips": {"tiktok": "Tip"},
            "trending_formats": ["POV"],
            "suggested_music_style": "EDM",
            "best_posting_times": ["8PM"],
            "competitor_insights": "Growing market",
        })

        output = agent.parse_response(response_text, input_data)

        assert output.success is True
        assert len(output.trending_hashtags) <= 15  # Should be limited
