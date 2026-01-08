"""Tests for Script Reviewer Agent."""
import json
from typing import Any
from unittest.mock import Mock, patch

import pytest
from anthropic.types import Message, Usage
from anthropic.types.text_block import TextBlock

from src.agents.script_reviewer import (
    ScriptReviewerAgent,
    ScriptReviewerInput,
    ScriptReviewerOutput,
)


@pytest.fixture
def sample_input() -> ScriptReviewerInput:
    """Sample optimized script for review."""
    return ScriptReviewerInput(
        job_id="test-job-123",
        user_id="test-user-456",
        hook="These $30 earbuds just destroyed my AirPods 🤯",
        scenes=[
            {
                "scene_number": 1,
                "duration_seconds": 3,
                "visual_description": "Dramatic product reveal",
                "voiceover_text": "These $30 earbuds just destroyed my AirPods",
                "text_overlay": "$30 vs $250",
                "engagement_note": "Price comparison hook",
            },
            {
                "scene_number": 2,
                "duration_seconds": 7,
                "visual_description": "Side by side comparison",
                "voiceover_text": "Same active noise cancellation, 40 hour battery",
                "text_overlay": "40HR BATTERY",
                "engagement_note": "Feature showcase",
            },
            {
                "scene_number": 3,
                "duration_seconds": 10,
                "visual_description": "Person using product happily",
                "voiceover_text": "Get yours today",
                "text_overlay": "Link in bio",
                "engagement_note": "CTA scene",
            },
        ],
        call_to_action="Link in bio - selling out fast!",
        full_voiceover_text="These $30 earbuds just destroyed my AirPods. Same active noise cancellation, 40 hour battery. Get yours today. Link in bio - selling out fast!",
        estimated_duration_seconds=20,
        product_title="Wireless Bluetooth Earbuds Pro",
        product_price="799,000 VND",
        key_features=["Active noise cancellation", "40-hour battery life"],
        unique_selling_points=["Best ANC at this price"],
        target_platform="tiktok",
    )


@pytest.fixture
def approved_response() -> dict[str, Any]:
    """Mock approved review response."""
    return {
        "approved": True,
        "overall_score": 8,
        "feedback": [
            {
                "category": "hook",
                "severity": "suggestion",
                "issue": "Consider A/B testing the emoji placement",
                "recommendation": "Try emoji at start vs end",
                "scene_number": None,
            }
        ],
        "critical_issues": [],
        "warnings": [],
        "suggestions": ["Consider A/B testing the emoji placement"],
        "compliance_passed": True,
        "compliance_issues": [],
        "final_hook": "These $30 earbuds just destroyed my AirPods 🤯",
        "final_scenes": [
            {
                "scene_number": 1,
                "duration_seconds": 3,
                "visual_description": "Dramatic product reveal",
                "voiceover_text": "These $30 earbuds just destroyed my AirPods",
                "text_overlay": "$30 vs $250",
            },
            {
                "scene_number": 2,
                "duration_seconds": 7,
                "visual_description": "Side by side comparison",
                "voiceover_text": "Same active noise cancellation, 40 hour battery",
                "text_overlay": "40HR BATTERY",
            },
            {
                "scene_number": 3,
                "duration_seconds": 10,
                "visual_description": "Person using product happily",
                "voiceover_text": "Get yours today",
                "text_overlay": "Link in bio",
            },
        ],
        "final_cta": "Link in bio - selling out fast!",
        "final_voiceover": "These $30 earbuds just destroyed my AirPods. Same active noise cancellation, 40 hour battery. Get yours today. Link in bio - selling out fast!",
        "review_summary": "Strong script with compelling hook and clear value prop",
        "strengths": ["Attention-grabbing hook", "Clear price comparison"],
        "areas_for_improvement": ["Could add more social proof"],
    }


@pytest.fixture
def rejected_response() -> dict[str, Any]:
    """Mock rejected review response."""
    return {
        "approved": False,
        "overall_score": 4,
        "feedback": [
            {
                "category": "compliance",
                "severity": "critical",
                "issue": "Claim 'destroyed AirPods' is unsubstantiated comparison",
                "recommendation": "Use factual comparison or softer language",
                "scene_number": 1,
            },
            {
                "category": "cta",
                "severity": "warning",
                "issue": "'Selling out fast' creates false urgency",
                "recommendation": "Remove or substantiate scarcity claim",
                "scene_number": None,
            },
        ],
        "critical_issues": ["Claim 'destroyed AirPods' is unsubstantiated"],
        "warnings": ["'Selling out fast' creates false urgency"],
        "suggestions": [],
        "compliance_passed": False,
        "compliance_issues": ["Unsubstantiated comparative claim"],
        "final_hook": "",
        "final_scenes": [],
        "final_cta": "",
        "final_voiceover": "",
        "review_summary": "Script contains compliance issues that must be addressed",
        "strengths": ["Good visual concepts"],
        "areas_for_improvement": ["Remove unsubstantiated claims", "Fix false scarcity"],
    }


@pytest.fixture
def mock_anthropic_api_response(approved_response: dict[str, Any]) -> Message:
    """Mock Anthropic API Message response."""
    return Message(
        id="msg_reviewer_123",
        type="message",
        role="assistant",
        content=[
            TextBlock(
                type="text",
                text=f"```json\n{json.dumps(approved_response, indent=2)}\n```",
            )
        ],
        model="claude-sonnet-4-20250514",
        stop_reason="end_turn",
        usage=Usage(
            input_tokens=1000,
            output_tokens=800,
        ),
    )


class TestScriptReviewerInput:
    """Tests for ScriptReviewerInput model."""

    def test_valid_input(self) -> None:
        """Test valid reviewer input."""
        input_data = ScriptReviewerInput(
            job_id="job_123",
            user_id="user_456",
            hook="Test hook",
            scenes=[],
            call_to_action="Buy now",
            full_voiceover_text="Test",
            estimated_duration_seconds=30,
            product_title="Product",
            product_price="100",
            key_features=["feature1"],
            unique_selling_points=["usp1"],
        )

        assert input_data.target_platform == "tiktok"  # Default
        assert input_data.brand_voice is None


class TestScriptReviewerOutput:
    """Tests for ScriptReviewerOutput model."""

    def test_default_values(self) -> None:
        """Test default values in output."""
        output = ScriptReviewerOutput(
            approved=True,
            overall_score=8,
            review_summary="Good script",
        )

        assert output.success is True
        assert output.feedback == []
        assert output.critical_issues == []
        assert output.compliance_passed is True


class TestScriptReviewerAgent:
    """Tests for ScriptReviewerAgent."""

    @patch("src.agents.base.get_anthropic_client")
    def test_agent_initialization(self, mock_get_client: Mock) -> None:
        """Test agent initialization."""
        agent = ScriptReviewerAgent()

        assert agent.name == "ScriptReviewer"
        assert agent.temperature == 0.3
        assert agent.max_tokens == 2500

    @patch("src.agents.base.get_anthropic_client")
    def test_compliance_rules_defined(self, mock_get_client: Mock) -> None:
        """Test compliance rules are defined."""
        agent = ScriptReviewerAgent()

        assert len(agent.COMPLIANCE_RULES) > 0
        assert any("false" in rule.lower() or "misleading" in rule.lower() for rule in agent.COMPLIANCE_RULES)

    @patch("src.agents.base.get_anthropic_client")
    def test_quality_criteria_defined(self, mock_get_client: Mock) -> None:
        """Test quality criteria are defined."""
        agent = ScriptReviewerAgent()

        assert len(agent.QUALITY_CRITERIA) > 0
        assert any("hook" in criterion.lower() for criterion in agent.QUALITY_CRITERIA)

    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_includes_product_info(
        self, mock_get_client: Mock, sample_input: ScriptReviewerInput
    ) -> None:
        """Test product info included for fact-checking."""
        agent = ScriptReviewerAgent()

        prompt = agent.build_user_prompt(sample_input, {})

        assert sample_input.product_title in prompt
        assert sample_input.product_price in prompt
        assert "Active noise cancellation" in prompt
        assert "40-hour battery" in prompt

    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_with_brand_voice(self, mock_get_client: Mock) -> None:
        """Test brand voice instruction included."""
        input_data = ScriptReviewerInput(
            job_id="job_123",
            user_id="user_456",
            hook="Test",
            scenes=[],
            call_to_action="Buy",
            full_voiceover_text="Test",
            estimated_duration_seconds=30,
            product_title="Product",
            product_price="100",
            key_features=["f1"],
            unique_selling_points=["u1"],
            brand_voice="Professional and trustworthy",
        )

        agent = ScriptReviewerAgent()
        prompt = agent.build_user_prompt(input_data, {})

        assert "Professional and trustworthy" in prompt
        assert "BRAND VOICE" in prompt

    @patch("src.agents.base.get_anthropic_client")
    def test_parse_approved_response(
        self, mock_get_client: Mock, sample_input: ScriptReviewerInput, approved_response: dict[str, Any]
    ) -> None:
        """Test parsing approved review."""
        agent = ScriptReviewerAgent()

        output = agent.parse_response(json.dumps(approved_response), sample_input)

        assert output.approved is True
        assert output.overall_score == 8
        assert output.compliance_passed is True
        assert len(output.compliance_issues) == 0
        assert len(output.strengths) > 0
        assert output.final_hook != ""

    @patch("src.agents.base.get_anthropic_client")
    def test_parse_rejected_response(
        self, mock_get_client: Mock, sample_input: ScriptReviewerInput, rejected_response: dict[str, Any]
    ) -> None:
        """Test parsing rejected review."""
        agent = ScriptReviewerAgent()

        output = agent.parse_response(json.dumps(rejected_response), sample_input)

        assert output.approved is False
        assert output.overall_score < 7
        assert output.compliance_passed is False
        assert len(output.critical_issues) > 0
        assert len(output.compliance_issues) > 0

    @patch("src.agents.base.get_anthropic_client")
    def test_compliance_failure_forces_rejection(
        self, mock_get_client: Mock, sample_input: ScriptReviewerInput
    ) -> None:
        """Test that compliance failure always results in rejection."""
        agent = ScriptReviewerAgent()

        # Response says approved but compliance failed
        response = {
            "approved": True,  # Incorrectly marked as approved
            "overall_score": 9,
            "compliance_passed": False,  # But compliance failed
            "compliance_issues": ["Serious violation"],
            "feedback": [],
            "review_summary": "Test",
        }

        output = agent.parse_response(json.dumps(response), sample_input)

        # Should be rejected regardless of approved flag
        assert output.approved is False

    @patch("src.agents.base.get_anthropic_client")
    def test_feedback_categorization(
        self, mock_get_client: Mock, sample_input: ScriptReviewerInput
    ) -> None:
        """Test feedback items are categorized by severity."""
        agent = ScriptReviewerAgent()
        response = {
            "approved": True,
            "overall_score": 7,
            "feedback": [
                {"category": "hook", "severity": "critical", "issue": "Critical issue", "recommendation": "Fix it"},
                {"category": "cta", "severity": "warning", "issue": "Warning issue", "recommendation": "Consider"},
                {"category": "pacing", "severity": "suggestion", "issue": "Suggestion", "recommendation": "Maybe"},
            ],
            "compliance_passed": True,
            "review_summary": "Test",
        }

        output = agent.parse_response(json.dumps(response), sample_input)

        assert "Critical issue" in output.critical_issues
        assert "Warning issue" in output.warnings
        assert "Suggestion" in output.suggestions

    @patch("src.agents.base.get_anthropic_client")
    def test_run_success(
        self,
        mock_get_client: Mock,
        sample_input: ScriptReviewerInput,
        mock_anthropic_api_response: Message,
    ) -> None:
        """Test full review run."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_api_response
        mock_get_client.return_value = mock_client

        agent = ScriptReviewerAgent()
        output = agent.run(sample_input, {})

        assert output.success is True
        assert output.overall_score >= 1
        assert output.review_summary != ""
        mock_client.messages.create.assert_called_once()

    @patch("src.agents.base.get_anthropic_client")
    def test_fallback_to_original_if_not_provided(
        self, mock_get_client: Mock, sample_input: ScriptReviewerInput
    ) -> None:
        """Test fallback to original values when final not provided."""
        agent = ScriptReviewerAgent()
        response = {
            "approved": True,
            "overall_score": 8,
            "compliance_passed": True,
            "feedback": [],
            "review_summary": "Good",
            # No final_* fields provided
        }

        output = agent.parse_response(json.dumps(response), sample_input)

        assert output.final_hook == sample_input.hook
        assert output.final_cta == sample_input.call_to_action

    @patch("src.agents.base.get_anthropic_client")
    def test_system_prompt_content(self, mock_get_client: Mock) -> None:
        """Test system prompt contains required instructions."""
        agent = ScriptReviewerAgent()

        assert "reviewer" in agent.system_prompt.lower()
        assert "compliance" in agent.system_prompt.lower()
        assert "quality" in agent.system_prompt.lower()
        assert "scoring" in agent.system_prompt.lower()

    @patch("src.agents.base.get_anthropic_client")
    def test_run_logs_token_usage(
        self,
        mock_get_client: Mock,
        sample_input: ScriptReviewerInput,
        mock_anthropic_api_response: Message,
    ) -> None:
        """Test that token usage is logged."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_api_response
        mock_get_client.return_value = mock_client

        agent = ScriptReviewerAgent()

        with patch.object(agent.logger, "info") as mock_log:
            agent.run(sample_input)

            # Find the LLM call log
            llm_call = [call for call in mock_log.call_args_list if call[0][0] == "agent_llm_call"][0]

            assert llm_call.kwargs["input_tokens"] == 1000
            assert llm_call.kwargs["output_tokens"] == 800

    @patch("src.agents.base.get_anthropic_client")
    def test_parse_response_with_code_block(
        self, mock_get_client: Mock, sample_input: ScriptReviewerInput, approved_response: dict[str, Any]
    ) -> None:
        """Test parsing JSON wrapped in markdown code block."""
        agent = ScriptReviewerAgent()
        response_text = f"```json\n{json.dumps(approved_response)}\n```"

        output = agent.parse_response(response_text, sample_input)

        assert output.success is True
        assert output.approved is True
