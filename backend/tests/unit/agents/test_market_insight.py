"""Tests for Market Insight Agent."""
import json
from typing import Any
from unittest.mock import Mock, patch

import pytest
from anthropic.types import Message, Usage
from anthropic.types.text_block import TextBlock

from src.agents.market_insight import (
    MarketInsightAgent,
    MarketInsightInput,
    MarketInsightOutput,
)


@pytest.fixture
def sample_input() -> MarketInsightInput:
    """Sample input for market insight."""
    return MarketInsightInput(
        job_id="test-job-123",
        user_id="test-user-456",
        product_category="Electronics",
        target_audience="Tech-savvy millennials in Vietnam",
        key_features=[
            "Wireless charging",
            "40-hour battery life",
            "Active noise cancellation",
            "Water resistant",
            "Touch controls",
        ],
        price_positioning="mid-range",
    )


@pytest.fixture
def sample_response() -> dict[str, Any]:
    """Sample LLM response."""
    return {
        "trending_hashtags": [
            "#TechReview",
            "#GadgetVietnam",
            "#WirelessEarbuds",
            "#TechTok",
            "#SảnPhẩmCôngNghệ",
        ],
        "content_angles": [
            "Day in the life with noise cancellation for busy professionals",
            "Comparison with premium brands at fraction of cost",
            "How it changed my daily commute experience",
            "Unboxing and first impressions",
        ],
        "platform_tips": {
            "tiktok": "Use trending sounds and quick cuts, focus on first 3 seconds",
            "facebook": "Add captions for sound-off viewing, longer engagement works",
            "shopee": "Show product features clearly, include price prominently",
        },
        "trending_formats": [
            "POV: Finding budget tech that works",
            "Before/After commute experience",
            "Product comparison",
        ],
        "suggested_music_style": "Upbeat electronic or trending Vietnamese pop",
        "best_posting_times": ["7-9 AM", "12-1 PM", "7-9 PM"],
        "competitor_insights": "Market shows strong demand for affordable wireless audio with premium features",
    }


@pytest.fixture
def mock_anthropic_response(sample_response: dict[str, Any]) -> Message:
    """Mock Anthropic API response."""
    return Message(
        id="msg_insight_123",
        type="message",
        role="assistant",
        content=[
            TextBlock(
                type="text",
                text=f"```json\n{json.dumps(sample_response, indent=2)}\n```",
            )
        ],
        model="claude-sonnet-4-20250514",
        stop_reason="end_turn",
        usage=Usage(
            input_tokens=500,
            output_tokens=400,
        ),
    )


class TestMarketInsightInput:
    """Tests for MarketInsightInput model."""

    def test_valid_input(self) -> None:
        """Test valid input creation."""
        input_data = MarketInsightInput(
            job_id="job_123",
            user_id="user_456",
            product_category="Beauty",
            target_audience="Women 25-35",
            key_features=["Natural ingredients", "Cruelty-free"],
            price_positioning="premium",
        )

        assert input_data.product_category == "Beauty"
        assert input_data.target_audience == "Women 25-35"
        assert len(input_data.key_features) == 2
        assert input_data.price_positioning == "premium"


class TestMarketInsightOutput:
    """Tests for MarketInsightOutput model."""

    def test_default_values(self) -> None:
        """Test default output values."""
        output = MarketInsightOutput()

        assert output.success is True
        assert output.trending_hashtags == []
        assert output.content_angles == []
        assert output.platform_tips == {}
        assert output.trending_formats == []
        assert output.suggested_music_style == ""
        assert output.best_posting_times == []
        assert output.competitor_insights == ""

    def test_with_data(self, sample_response: dict[str, Any]) -> None:
        """Test output with populated data."""
        output = MarketInsightOutput(**sample_response)

        assert len(output.trending_hashtags) > 0
        assert len(output.content_angles) > 0
        assert "tiktok" in output.platform_tips
        assert len(output.trending_formats) > 0
        assert output.suggested_music_style != ""


class TestMarketInsightAgent:
    """Tests for MarketInsightAgent."""

    @patch("src.agents.base.get_anthropic_client")
    def test_agent_initialization(self, mock_get_client: Mock) -> None:
        """Test agent initialization."""
        agent = MarketInsightAgent()

        assert agent.name == "MarketInsight"
        assert agent.temperature == 0.5
        assert agent.max_tokens == 1536
        assert len(agent.TRENDING_FORMATS) > 0

    @patch("src.agents.base.get_anthropic_client")
    def test_trending_formats_defined(self, mock_get_client: Mock) -> None:
        """Test that trending formats are defined."""
        agent = MarketInsightAgent()

        assert "POV (Point of View)" in agent.TRENDING_FORMATS
        assert "Unboxing experience" in agent.TRENDING_FORMATS
        assert "Tutorial/How-to" in agent.TRENDING_FORMATS

    @patch("src.agents.base.get_anthropic_client")
    def test_system_prompt_content(self, mock_get_client: Mock) -> None:
        """Test system prompt includes key elements."""
        agent = MarketInsightAgent()

        prompt = agent.system_prompt

        assert "Vietnam" in prompt or "SEA" in prompt
        assert "hashtag" in prompt.lower()
        assert "tiktok" in prompt.lower()
        assert "JSON" in prompt

    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_includes_category(
        self, mock_get_client: Mock, sample_input: MarketInsightInput
    ) -> None:
        """Test user prompt includes product category."""
        agent = MarketInsightAgent()

        prompt = agent.build_user_prompt(sample_input, {})

        assert sample_input.product_category in prompt

    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_includes_audience(
        self, mock_get_client: Mock, sample_input: MarketInsightInput
    ) -> None:
        """Test user prompt includes target audience."""
        agent = MarketInsightAgent()

        prompt = agent.build_user_prompt(sample_input, {})

        assert sample_input.target_audience in prompt

    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_includes_features(
        self, mock_get_client: Mock, sample_input: MarketInsightInput
    ) -> None:
        """Test user prompt includes key features."""
        agent = MarketInsightAgent()

        prompt = agent.build_user_prompt(sample_input, {})

        # Should include at least first feature
        assert sample_input.key_features[0] in prompt

    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_limits_features(
        self, mock_get_client: Mock
    ) -> None:
        """Test that features are limited to 5."""
        input_data = MarketInsightInput(
            job_id="job_123",
            user_id="user_456",
            product_category="Test",
            target_audience="Test audience",
            key_features=[f"Feature {i}" for i in range(10)],  # 10 features
            price_positioning="mid-range",
        )

        agent = MarketInsightAgent()
        prompt = agent.build_user_prompt(input_data, {})

        # Should have first 5 features
        assert "Feature 0" in prompt
        assert "Feature 4" in prompt
        # Should not have 6th+ features
        assert "Feature 5" not in prompt

    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_includes_trending_formats(
        self, mock_get_client: Mock, sample_input: MarketInsightInput
    ) -> None:
        """Test user prompt mentions trending formats."""
        agent = MarketInsightAgent()

        prompt = agent.build_user_prompt(sample_input, {})

        # Should mention at least one trending format
        assert any(fmt in prompt for fmt in agent.TRENDING_FORMATS)

    @patch("src.agents.base.get_anthropic_client")
    def test_parse_response_success(
        self, mock_get_client: Mock, sample_input: MarketInsightInput, sample_response: dict[str, Any]
    ) -> None:
        """Test parsing successful response."""
        agent = MarketInsightAgent()

        output = agent.parse_response(json.dumps(sample_response), sample_input)

        assert output.success is True
        assert len(output.trending_hashtags) > 0
        assert len(output.content_angles) > 0
        assert "tiktok" in output.platform_tips

    @patch("src.agents.base.get_anthropic_client")
    def test_parse_response_limits_hashtags(
        self, mock_get_client: Mock, sample_input: MarketInsightInput
    ) -> None:
        """Test that hashtags are limited to 15."""
        agent = MarketInsightAgent()

        # Create response with 20 hashtags
        response = {
            "trending_hashtags": [f"#hashtag{i}" for i in range(20)],
            "content_angles": [],
            "platform_tips": {},
            "trending_formats": [],
            "suggested_music_style": "",
            "best_posting_times": [],
            "competitor_insights": "",
        }

        output = agent.parse_response(json.dumps(response), sample_input)

        assert len(output.trending_hashtags) == 15

    @patch("src.agents.base.get_anthropic_client")
    def test_parse_response_with_code_block(
        self, mock_get_client: Mock, sample_input: MarketInsightInput, sample_response: dict[str, Any]
    ) -> None:
        """Test parsing JSON wrapped in markdown code block."""
        agent = MarketInsightAgent()

        response_text = f"```json\n{json.dumps(sample_response)}\n```"
        output = agent.parse_response(response_text, sample_input)

        assert output.success is True
        assert len(output.trending_hashtags) > 0

    @patch("src.agents.base.get_anthropic_client")
    def test_parse_response_handles_missing_fields(
        self, mock_get_client: Mock, sample_input: MarketInsightInput
    ) -> None:
        """Test parsing with missing optional fields."""
        agent = MarketInsightAgent()

        # Minimal response
        response = {
            "trending_hashtags": ["#test"],
        }

        output = agent.parse_response(json.dumps(response), sample_input)

        assert output.success is True
        assert output.trending_hashtags == ["#test"]
        assert output.content_angles == []
        assert output.platform_tips == {}

    @patch("src.agents.base.get_anthropic_client")
    def test_run_success(
        self,
        mock_get_client: Mock,
        sample_input: MarketInsightInput,
        mock_anthropic_response: Message,
    ) -> None:
        """Test full agent run."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_get_client.return_value = mock_client

        agent = MarketInsightAgent()
        output = agent.run(sample_input, {})

        assert output.success is True
        assert len(output.trending_hashtags) > 0
        assert len(output.content_angles) > 0
        mock_client.messages.create.assert_called_once()

    @patch("src.agents.base.get_anthropic_client")
    def test_output_includes_vietnam_focus(
        self, mock_get_client: Mock, sample_input: MarketInsightInput, sample_response: dict[str, Any]
    ) -> None:
        """Test that output reflects Vietnam market focus."""
        agent = MarketInsightAgent()

        output = agent.parse_response(json.dumps(sample_response), sample_input)

        # Check for Vietnam-specific content
        all_text = " ".join(
            output.trending_hashtags
            + output.content_angles
            + list(output.platform_tips.values())
        )

        # Should have some Vietnam or Vietnamese content
        assert "Vietnam" in all_text or "Vietnamese" in all_text or "Việt" in all_text

    @patch("src.agents.base.get_anthropic_client")
    def test_platform_tips_for_all_platforms(
        self, mock_get_client: Mock, sample_input: MarketInsightInput, sample_response: dict[str, Any]
    ) -> None:
        """Test that platform tips include all major platforms."""
        agent = MarketInsightAgent()

        output = agent.parse_response(json.dumps(sample_response), sample_input)

        assert "tiktok" in output.platform_tips
        assert "facebook" in output.platform_tips
        assert "shopee" in output.platform_tips

    @patch("src.agents.base.get_anthropic_client")
    def test_content_angles_are_actionable(
        self, mock_get_client: Mock, sample_input: MarketInsightInput, sample_response: dict[str, Any]
    ) -> None:
        """Test that content angles are provided."""
        agent = MarketInsightAgent()

        output = agent.parse_response(json.dumps(sample_response), sample_input)

        assert len(output.content_angles) > 0
        # Content angles should be strings
        assert all(isinstance(angle, str) for angle in output.content_angles)
        # Should have some content
        assert all(len(angle) > 10 for angle in output.content_angles)

    @patch("src.agents.base.get_anthropic_client")
    def test_best_posting_times_provided(
        self, mock_get_client: Mock, sample_input: MarketInsightInput, sample_response: dict[str, Any]
    ) -> None:
        """Test that posting times are provided."""
        agent = MarketInsightAgent()

        output = agent.parse_response(json.dumps(sample_response), sample_input)

        assert len(output.best_posting_times) > 0
        # Times should be strings
        assert all(isinstance(time, str) for time in output.best_posting_times)

    @patch("src.agents.base.get_anthropic_client")
    def test_run_logs_token_usage(
        self,
        mock_get_client: Mock,
        sample_input: MarketInsightInput,
        mock_anthropic_response: Message,
    ) -> None:
        """Test that token usage is logged."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_get_client.return_value = mock_client

        agent = MarketInsightAgent()

        with patch.object(agent.logger, "info") as mock_log:
            agent.run(sample_input, {})

            # Find LLM call log
            llm_call = [call for call in mock_log.call_args_list if call[0][0] == "agent_llm_call"][0]

            assert llm_call.kwargs["input_tokens"] == 500
            assert llm_call.kwargs["output_tokens"] == 400


class TestMarketInsightIntegration:
    """Integration tests for market insight workflow."""

    @patch("src.agents.base.get_anthropic_client")
    def test_electronics_category(self, mock_get_client: Mock) -> None:
        """Test with electronics category."""
        input_data = MarketInsightInput(
            job_id="job_123",
            user_id="user_456",
            product_category="Electronics",
            target_audience="Tech enthusiasts",
            key_features=["Latest tech", "Great value"],
            price_positioning="mid-range",
        )

        agent = MarketInsightAgent()
        prompt = agent.build_user_prompt(input_data, {})

        assert "Electronics" in prompt
        assert "Tech enthusiasts" in prompt

    @patch("src.agents.base.get_anthropic_client")
    def test_beauty_category(self, mock_get_client: Mock) -> None:
        """Test with beauty category."""
        input_data = MarketInsightInput(
            job_id="job_123",
            user_id="user_456",
            product_category="Beauty",
            target_audience="Women 25-40",
            key_features=["Natural", "Organic"],
            price_positioning="premium",
        )

        agent = MarketInsightAgent()
        prompt = agent.build_user_prompt(input_data, {})

        assert "Beauty" in prompt
        assert "Women 25-40" in prompt

    @patch("src.agents.base.get_anthropic_client")
    def test_budget_positioning(self, mock_get_client: Mock) -> None:
        """Test with budget price positioning."""
        input_data = MarketInsightInput(
            job_id="job_123",
            user_id="user_456",
            product_category="Fashion",
            target_audience="Students",
            key_features=["Affordable", "Trendy"],
            price_positioning="budget",
        )

        agent = MarketInsightAgent()
        prompt = agent.build_user_prompt(input_data, {})

        assert "budget" in prompt
