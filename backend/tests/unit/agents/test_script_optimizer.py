"""Unit tests for ScriptOptimizerAgent."""
import json
from unittest.mock import patch

import pytest

from src.agents.script_optimizer import (
    ScriptOptimizerAgent,
    ScriptOptimizerInput,
    ScriptOptimizerOutput,
)
from tests.fixtures.mocks import create_mock_openai_client, create_mock_openai_response


class TestScriptOptimizerInput:
    """Tests for ScriptOptimizerInput model."""

    def test_create_input(self):
        """Test creating a ScriptOptimizerInput."""
        input_data = ScriptOptimizerInput(
            job_id="job123",
            user_id="user456",
            hook="Original hook",
            scenes=[{"scene_number": 1, "duration_seconds": 5}],
            call_to_action="Shop now",
            full_voiceover_text="Full script",
            estimated_duration_seconds=45,
        )
        assert input_data.hook == "Original hook"
        assert input_data.primary_platform == "tiktok"  # Default


class TestScriptOptimizerOutput:
    """Tests for ScriptOptimizerOutput model."""

    def test_create_output(self):
        """Test creating a ScriptOptimizerOutput."""
        output = ScriptOptimizerOutput(
            success=True,
            optimized_hook="Better hook!",
            optimized_scenes=[{"scene_number": 1}],
            optimized_cta="Buy now!",
            optimized_voiceover="Improved script",
            estimated_duration_seconds=45,
            scene_count=5,
            pattern_interrupt_count=3,
            changes_summary="Improved pacing",
        )
        assert output.optimized_hook == "Better hook!"
        assert output.pattern_interrupt_count == 3


class TestScriptOptimizerAgent:
    """Tests for ScriptOptimizerAgent class."""

    def test_agent_properties(self):
        """Test agent properties."""
        agent = ScriptOptimizerAgent()
        assert agent.name == "ScriptOptimizer"
        assert agent.max_tokens == 3000
        assert agent.temperature == 0.5

    def test_system_prompt_contains_json_instruction(self):
        """Test system prompt contains JSON instruction."""
        agent = ScriptOptimizerAgent()
        assert "You must respond with valid JSON" in agent.system_prompt

    def test_platform_requirements_constant(self):
        """Test PLATFORM_REQUIREMENTS constant."""
        agent = ScriptOptimizerAgent()
        assert "tiktok" in agent.PLATFORM_REQUIREMENTS
        assert "facebook" in agent.PLATFORM_REQUIREMENTS
        assert "shopee" in agent.PLATFORM_REQUIREMENTS
        assert agent.PLATFORM_REQUIREMENTS["tiktok"]["hook_time"] == 1.5

    @patch("src.agents.base.get_openai_client")
    def test_run_success(self, mock_get_client):
        """Test successful agent run."""
        mock_client = create_mock_openai_client()
        response_content = json.dumps({
            "optimized_hook": "Wait - you NEED to see this!",
            "optimized_scenes": [
                {
                    "scene_number": 1,
                    "duration_seconds": 2,
                    "visual_description": "Quick product reveal",
                    "voiceover_text": "This changes everything",
                    "text_overlay": "GAME CHANGER",
                    "transition": "zoom",
                    "engagement_note": "Creates curiosity",
                    "pattern_interrupt": True,
                },
            ],
            "optimized_cta": "Link in bio - don't miss out!",
            "optimized_voiceover": "Wait. You need to see this...",
            "pacing_notes": ["Added zoom for energy", "Shortened intro"],
            "engagement_hooks": ["Curiosity gap in opening"],
            "platform_adjustments": {"hook_speed": "Faster to match TikTok"},
            "estimated_duration_seconds": 42,
            "scene_count": 7,
            "pattern_interrupt_count": 5,
            "changes_summary": "Optimized for TikTok engagement",
        })
        mock_response = create_mock_openai_response(response_content)
        mock_client.chat_completion.return_value = mock_response
        mock_get_client.return_value = mock_client

        agent = ScriptOptimizerAgent()
        input_data = ScriptOptimizerInput(
            job_id="job123",
            user_id="user456",
            hook="Check out this product",
            scenes=[{"scene_number": 1, "duration_seconds": 10}],
            call_to_action="Buy now",
            full_voiceover_text="Check out this product...",
            estimated_duration_seconds=45,
            primary_platform="tiktok",
        )

        output = agent.run(input_data)

        assert output.success is True
        assert "NEED" in output.optimized_hook or "need" in output.optimized_hook.lower()
        assert output.pattern_interrupt_count > 0
        mock_client.chat_completion.assert_called_once()

    def test_build_user_prompt(self):
        """Test building user prompt."""
        agent = ScriptOptimizerAgent()
        input_data = ScriptOptimizerInput(
            job_id="job123",
            user_id="user456",
            hook="Original hook",
            scenes=[
                {"scene_number": 1, "duration_seconds": 5, "visual_description": "Scene 1", "voiceover_text": "Text 1"},
            ],
            call_to_action="Shop now",
            full_voiceover_text="Full script",
            estimated_duration_seconds=45,
            primary_platform="facebook",
            tone="professional",
            pacing="medium",
        )

        prompt = agent.build_user_prompt(input_data, {})

        assert "FACEBOOK" in prompt
        assert "Original hook" in prompt
        assert "professional" in prompt.lower()

    def test_parse_response(self):
        """Test parsing LLM response."""
        agent = ScriptOptimizerAgent()
        input_data = ScriptOptimizerInput(
            job_id="job123",
            user_id="user456",
            hook="Hook",
            scenes=[{"scene_number": 1}],
            call_to_action="CTA",
            full_voiceover_text="Script",
            estimated_duration_seconds=45,
        )

        response_text = json.dumps({
            "optimized_hook": "Better hook",
            "optimized_scenes": [
                {"scene_number": 1, "pattern_interrupt": True},
                {"scene_number": 2, "pattern_interrupt": False},
            ],
            "optimized_cta": "Better CTA",
            "optimized_voiceover": "Better script",
            "pacing_notes": ["Note 1"],
            "engagement_hooks": ["Hook 1"],
            "platform_adjustments": {"change": "value"},
            "estimated_duration_seconds": 40,
            "scene_count": 2,
            "pattern_interrupt_count": 1,
            "changes_summary": "Summary",
        })

        output = agent.parse_response(response_text, input_data)

        assert output.success is True
        assert output.optimized_hook == "Better hook"
        assert output.pattern_interrupt_count == 1
