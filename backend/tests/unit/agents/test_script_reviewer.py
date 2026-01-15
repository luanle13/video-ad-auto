"""Unit tests for ScriptReviewerAgent."""
import json
from unittest.mock import patch

import pytest

from src.agents.script_reviewer import (
    ScriptReviewerAgent,
    ScriptReviewerInput,
    ScriptReviewerOutput,
)
from tests.fixtures.mocks import create_mock_openai_client, create_mock_openai_response


class TestScriptReviewerInput:
    """Tests for ScriptReviewerInput model."""

    def test_create_input(self):
        """Test creating a ScriptReviewerInput."""
        input_data = ScriptReviewerInput(
            job_id="job123",
            user_id="user456",
            hook="Test hook",
            scenes=[{"scene_number": 1}],
            call_to_action="Buy now",
            full_voiceover_text="Full script",
            estimated_duration_seconds=45,
            product_title="Test Product",
            product_price="$19.99",
            key_features=["Feature 1"],
            unique_selling_points=["USP 1"],
        )
        assert input_data.product_title == "Test Product"
        assert input_data.target_platform == "tiktok"  # Default


class TestScriptReviewerOutput:
    """Tests for ScriptReviewerOutput model."""

    def test_create_output(self):
        """Test creating a ScriptReviewerOutput."""
        output = ScriptReviewerOutput(
            success=True,
            approved=True,
            overall_score=8,
            compliance_passed=True,
            final_hook="Approved hook",
            final_scenes=[],
            final_cta="Approved CTA",
            final_voiceover="Approved voiceover",
            review_summary="Script approved",
        )
        assert output.approved is True
        assert output.overall_score == 8


class TestScriptReviewerAgent:
    """Tests for ScriptReviewerAgent class."""

    def test_agent_properties(self):
        """Test agent properties."""
        agent = ScriptReviewerAgent()
        assert agent.name == "ScriptReviewer"
        assert agent.max_tokens == 2500
        assert agent.temperature == 0.3

    def test_system_prompt_contains_json_instruction(self):
        """Test system prompt contains JSON instruction."""
        agent = ScriptReviewerAgent()
        assert "You must respond with valid JSON" in agent.system_prompt

    def test_compliance_rules_constant(self):
        """Test COMPLIANCE_RULES constant."""
        agent = ScriptReviewerAgent()
        assert len(agent.COMPLIANCE_RULES) > 0
        assert any("false" in rule.lower() or "misleading" in rule.lower() for rule in agent.COMPLIANCE_RULES)

    def test_quality_criteria_constant(self):
        """Test QUALITY_CRITERIA constant."""
        agent = ScriptReviewerAgent()
        assert len(agent.QUALITY_CRITERIA) > 0
        assert any("hook" in criterion.lower() for criterion in agent.QUALITY_CRITERIA)

    @patch("src.agents.base.get_openai_client")
    def test_run_success_approved(self, mock_get_client):
        """Test successful agent run with approval."""
        mock_client = create_mock_openai_client()
        response_content = json.dumps({
            "approved": True,
            "overall_score": 9,
            "feedback": [
                {
                    "category": "hook",
                    "severity": "suggestion",
                    "issue": "Could be slightly stronger",
                    "recommendation": "Add urgency",
                    "scene_number": None,
                }
            ],
            "critical_issues": [],
            "warnings": [],
            "suggestions": ["Consider adding urgency to hook"],
            "compliance_passed": True,
            "compliance_issues": [],
            "final_hook": "Don't miss this - limited time!",
            "final_scenes": [{"scene_number": 1}],
            "final_cta": "Shop now!",
            "final_voiceover": "Complete voiceover",
            "review_summary": "Excellent script, ready for production",
            "strengths": ["Strong value proposition", "Good pacing"],
            "areas_for_improvement": ["Hook could be stronger"],
        })
        mock_response = create_mock_openai_response(response_content)
        mock_client.chat_completion.return_value = mock_response
        mock_get_client.return_value = mock_client

        agent = ScriptReviewerAgent()
        input_data = ScriptReviewerInput(
            job_id="job123",
            user_id="user456",
            hook="Check this out",
            scenes=[{"scene_number": 1, "duration_seconds": 5}],
            call_to_action="Shop now",
            full_voiceover_text="Check this out...",
            estimated_duration_seconds=45,
            product_title="Smart Watch",
            product_price="$299.99",
            key_features=["Health tracking"],
            unique_selling_points=["7-day battery"],
        )

        output = agent.run(input_data)

        assert output.success is True
        assert output.approved is True
        assert output.overall_score == 9
        assert output.compliance_passed is True
        mock_client.chat_completion.assert_called_once()

    @patch("src.agents.base.get_openai_client")
    def test_run_compliance_failure(self, mock_get_client):
        """Test agent run with compliance failure."""
        mock_client = create_mock_openai_client()
        response_content = json.dumps({
            "approved": False,
            "overall_score": 4,
            "feedback": [
                {
                    "category": "compliance",
                    "severity": "critical",
                    "issue": "Misleading claim about effectiveness",
                    "recommendation": "Remove unsubstantiated claims",
                    "scene_number": 2,
                }
            ],
            "critical_issues": ["Misleading effectiveness claim"],
            "warnings": [],
            "suggestions": [],
            "compliance_passed": False,
            "compliance_issues": ["Unsubstantiated '100% effective' claim"],
            "final_hook": "",
            "final_scenes": [],
            "final_cta": "",
            "final_voiceover": "",
            "review_summary": "Script rejected due to compliance issues",
            "strengths": ["Good visual direction"],
            "areas_for_improvement": ["Remove misleading claims"],
        })
        mock_response = create_mock_openai_response(response_content)
        mock_client.chat_completion.return_value = mock_response
        mock_get_client.return_value = mock_client

        agent = ScriptReviewerAgent()
        input_data = ScriptReviewerInput(
            job_id="job123",
            user_id="user456",
            hook="This is 100% effective!",
            scenes=[{"scene_number": 1}],
            call_to_action="Buy now",
            full_voiceover_text="100% effective...",
            estimated_duration_seconds=45,
            product_title="Health Product",
            product_price="$49.99",
            key_features=["Natural"],
            unique_selling_points=["Fast results"],
        )

        output = agent.run(input_data)

        assert output.success is True  # Agent ran successfully
        assert output.approved is False  # But script not approved
        assert output.compliance_passed is False

    def test_build_user_prompt(self):
        """Test building user prompt."""
        agent = ScriptReviewerAgent()
        input_data = ScriptReviewerInput(
            job_id="job123",
            user_id="user456",
            hook="Test hook",
            scenes=[{"scene_number": 1, "duration_seconds": 5}],
            call_to_action="Shop now",
            full_voiceover_text="Test voiceover",
            estimated_duration_seconds=45,
            product_title="Test Product",
            product_price="$99.99",
            key_features=["Feature 1", "Feature 2"],
            unique_selling_points=["USP 1"],
            brand_voice="Professional and trustworthy",
        )

        prompt = agent.build_user_prompt(input_data, {})

        assert "Test Product" in prompt
        assert "$99.99" in prompt
        assert "Feature 1" in prompt
        assert "Professional and trustworthy" in prompt

    def test_parse_response(self):
        """Test parsing LLM response."""
        agent = ScriptReviewerAgent()
        input_data = ScriptReviewerInput(
            job_id="job123",
            user_id="user456",
            hook="Hook",
            scenes=[{"scene_number": 1}],
            call_to_action="CTA",
            full_voiceover_text="Script",
            estimated_duration_seconds=45,
            product_title="Product",
            product_price="$10",
            key_features=["Feature"],
            unique_selling_points=["USP"],
        )

        response_text = json.dumps({
            "approved": True,
            "overall_score": 7,
            "feedback": [],
            "critical_issues": [],
            "warnings": ["Minor pacing issue"],
            "suggestions": ["Add more energy"],
            "compliance_passed": True,
            "compliance_issues": [],
            "final_hook": "Final hook",
            "final_scenes": [{"scene_number": 1}],
            "final_cta": "Final CTA",
            "final_voiceover": "Final voiceover",
            "review_summary": "Good script",
            "strengths": ["Strong hook"],
            "areas_for_improvement": ["Pacing"],
        })

        output = agent.parse_response(response_text, input_data)

        assert output.success is True
        assert output.approved is True
        assert output.overall_score == 7
        assert "Minor pacing issue" in output.warnings
