"""Tests for Script Optimizer Agent."""
import json
from typing import Any
from unittest.mock import Mock, patch

import pytest
from anthropic.types import Message, Usage
from anthropic.types.text_block import TextBlock

from src.agents.script_optimizer import (
    ScriptOptimizerAgent,
    ScriptOptimizerInput,
    ScriptOptimizerOutput,
)


@pytest.fixture
def sample_input() -> ScriptOptimizerInput:
    """Sample input from script generator."""
    return ScriptOptimizerInput(
        job_id="test-job-123",
        user_id="test-user-456",
        hook="Check out these amazing earbuds",
        scenes=[
            {
                "scene_number": 1,
                "duration_seconds": 5,
                "visual_description": "Product on table",
                "voiceover_text": "Check out these amazing earbuds",
                "text_overlay": None,
                "transition": "cut",
            },
            {
                "scene_number": 2,
                "duration_seconds": 10,
                "visual_description": "Person using earbuds",
                "voiceover_text": "They have great sound quality and noise cancellation",
                "text_overlay": "Great Sound",
                "transition": "cut",
            },
            {
                "scene_number": 3,
                "duration_seconds": 15,
                "visual_description": "Product close-up",
                "voiceover_text": "Get yours today",
                "text_overlay": "Link in bio",
                "transition": "fade",
            },
        ],
        call_to_action="Get yours today, link in bio",
        full_voiceover_text="Check out these amazing earbuds. They have great sound quality and noise cancellation. Get yours today.",
        estimated_duration_seconds=30,
        primary_platform="tiktok",
        trending_formats=["POV", "Before/After"],
        platform_tips={"tiktok": "Use trending sounds and fast cuts"},
        tone="energetic",
        pacing="fast",
    )


@pytest.fixture
def mock_optimized_response() -> dict[str, Any]:
    """Mock optimized response."""
    return {
        "optimized_hook": "Wait... these $30 earbuds have WHAT features? 🤯",
        "optimized_scenes": [
            {
                "scene_number": 1,
                "duration_seconds": 2,
                "visual_description": "Quick zoom into earbuds case opening",
                "voiceover_text": "Wait... these $30 earbuds have WHAT features?",
                "text_overlay": "🤯 $30 ONLY",
                "transition": "zoom",
                "engagement_note": "Curiosity gap + price hook",
                "pattern_interrupt": True,
            },
            {
                "scene_number": 2,
                "duration_seconds": 4,
                "visual_description": "Split screen: noisy train vs silent with earbuds",
                "voiceover_text": "Active noise cancellation that actually blocks your commute",
                "text_overlay": "ANC ✓",
                "transition": "swipe",
                "engagement_note": "Visual before/after",
                "pattern_interrupt": True,
            },
            {
                "scene_number": 3,
                "duration_seconds": 5,
                "visual_description": "Fast montage of features",
                "voiceover_text": "40 hour battery, water resistant, touch controls",
                "text_overlay": "40HR 💪",
                "transition": "cut",
                "engagement_note": "Feature rapid-fire",
                "pattern_interrupt": False,
            },
            {
                "scene_number": 4,
                "duration_seconds": 3,
                "visual_description": "Person looks at camera surprised",
                "voiceover_text": "All for less than dinner out",
                "text_overlay": None,
                "transition": "zoom",
                "engagement_note": "Price comparison",
                "pattern_interrupt": True,
            },
        ],
        "optimized_cta": "Link in bio before they sell out 🏃",
        "optimized_voiceover": "Wait... these $30 earbuds have WHAT features? Active noise cancellation that actually blocks your commute. 40 hour battery, water resistant, touch controls. All for less than dinner out. Link in bio before they sell out.",
        "pacing_notes": ["Reduced scene 1 from 5s to 2s", "Added visual contrast in scene 2"],
        "engagement_hooks": ["Curiosity gap in hook", "Price anchor", "FOMO in CTA"],
        "platform_adjustments": {
            "hook_speed": "Reduced to under 2 seconds for TikTok",
            "text_overlays": "Added emoji for engagement",
        },
        "estimated_duration_seconds": 14,
        "scene_count": 4,
        "pattern_interrupt_count": 3,
        "changes_summary": "Shortened hook, added curiosity gap, increased pacing, added pattern interrupts every 3-4 seconds",
    }


@pytest.fixture
def mock_anthropic_api_response(mock_optimized_response: dict[str, Any]) -> Message:
    """Mock Anthropic API Message response."""
    return Message(
        id="msg_optimizer_123",
        type="message",
        role="assistant",
        content=[
            TextBlock(
                type="text",
                text=f"```json\n{json.dumps(mock_optimized_response, indent=2)}\n```",
            )
        ],
        model="claude-sonnet-4-20250514",
        stop_reason="end_turn",
        usage=Usage(
            input_tokens=900,
            output_tokens=700,
        ),
    )


class TestScriptOptimizerInput:
    """Tests for ScriptOptimizerInput model."""

    def test_valid_input(self) -> None:
        """Test valid optimizer input."""
        input_data = ScriptOptimizerInput(
            job_id="job_123",
            user_id="user_456",
            hook="Test hook",
            scenes=[{"scene_number": 1, "duration_seconds": 5, "visual_description": "test", "voiceover_text": "test"}],
            call_to_action="Buy now",
            full_voiceover_text="Test",
            estimated_duration_seconds=30,
        )

        assert input_data.primary_platform == "tiktok"  # Default
        assert input_data.tone is None
        assert input_data.pacing is None


class TestScriptOptimizerOutput:
    """Tests for ScriptOptimizerOutput model."""

    def test_default_values(self) -> None:
        """Test default values in output."""
        output = ScriptOptimizerOutput(
            optimized_hook="Test",
            optimized_scenes=[],
            optimized_cta="Buy",
            optimized_voiceover="Text",
            estimated_duration_seconds=30,
            scene_count=0,
            changes_summary="Test summary",
        )

        assert output.success is True
        assert output.pacing_notes == []
        assert output.engagement_hooks == []
        assert output.platform_adjustments == {}
        assert output.pattern_interrupt_count == 0


class TestScriptOptimizerAgent:
    """Tests for ScriptOptimizerAgent."""

    @patch("src.agents.base.get_anthropic_client")
    def test_agent_initialization(self, mock_get_client: Mock) -> None:
        """Test agent initialization."""
        agent = ScriptOptimizerAgent()

        assert agent.name == "ScriptOptimizer"
        assert agent.temperature == 0.5
        assert agent.max_tokens == 3000

    @patch("src.agents.base.get_anthropic_client")
    def test_platform_requirements_loaded(self, mock_get_client: Mock) -> None:
        """Test platform requirements are defined."""
        agent = ScriptOptimizerAgent()

        assert "tiktok" in agent.PLATFORM_REQUIREMENTS
        assert "facebook" in agent.PLATFORM_REQUIREMENTS
        assert "shopee" in agent.PLATFORM_REQUIREMENTS

        tiktok = agent.PLATFORM_REQUIREMENTS["tiktok"]
        assert tiktok["hook_time"] == 1.5
        assert tiktok["pattern_interrupt_interval"] == 5

        facebook = agent.PLATFORM_REQUIREMENTS["facebook"]
        assert facebook["hook_time"] == 3
        assert facebook["pattern_interrupt_interval"] == 7

    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_includes_platform(
        self, mock_get_client: Mock, sample_input: ScriptOptimizerInput
    ) -> None:
        """Test platform-specific content in prompt."""
        agent = ScriptOptimizerAgent()

        prompt = agent.build_user_prompt(sample_input, {})

        assert "TIKTOK" in prompt
        assert "1.5s" in prompt  # Hook time
        assert "5s" in prompt  # Pattern interrupt interval
        assert "energetic" in prompt  # Tone
        assert "fast" in prompt.lower()  # Pacing
        assert sample_input.hook in prompt

    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_facebook(self, mock_get_client: Mock) -> None:
        """Test Facebook-specific optimization."""
        input_data = ScriptOptimizerInput(
            job_id="job_123",
            user_id="user_456",
            hook="Test",
            scenes=[],
            call_to_action="Buy",
            full_voiceover_text="Test",
            estimated_duration_seconds=30,
            primary_platform="facebook",
        )

        agent = ScriptOptimizerAgent()
        prompt = agent.build_user_prompt(input_data, {})

        assert "FACEBOOK" in prompt
        assert "3s" in prompt  # Hook time for Facebook
        assert "caption-friendly" in prompt.lower()

    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_shopee(self, mock_get_client: Mock) -> None:
        """Test Shopee-specific optimization."""
        input_data = ScriptOptimizerInput(
            job_id="job_123",
            user_id="user_456",
            hook="Test",
            scenes=[],
            call_to_action="Buy",
            full_voiceover_text="Test",
            estimated_duration_seconds=30,
            primary_platform="shopee",
        )

        agent = ScriptOptimizerAgent()
        prompt = agent.build_user_prompt(input_data, {})

        assert "SHOPEE" in prompt
        assert "2s" in prompt  # Hook time for Shopee
        assert "price callout" in prompt.lower()

    @patch("src.agents.base.get_anthropic_client")
    def test_parse_response_counts_pattern_interrupts(
        self, mock_get_client: Mock, sample_input: ScriptOptimizerInput, mock_optimized_response: dict[str, Any]
    ) -> None:
        """Test pattern interrupt counting."""
        agent = ScriptOptimizerAgent()

        output = agent.parse_response(json.dumps(mock_optimized_response), sample_input)

        assert output.pattern_interrupt_count == 3

    @patch("src.agents.base.get_anthropic_client")
    def test_parse_response_preserves_original_on_missing(
        self, mock_get_client: Mock, sample_input: ScriptOptimizerInput
    ) -> None:
        """Test fallback to original values."""
        agent = ScriptOptimizerAgent()
        minimal_response = {
            "optimized_scenes": [
                {"scene_number": 1, "duration_seconds": 10, "visual_description": "s1", "voiceover_text": "t1"},
                {"scene_number": 2, "duration_seconds": 10, "visual_description": "s2", "voiceover_text": "t2"},
                {"scene_number": 3, "duration_seconds": 10, "visual_description": "s3", "voiceover_text": "t3"},
            ],
            "changes_summary": "Minor tweaks",
        }

        output = agent.parse_response(json.dumps(minimal_response), sample_input)

        # Should fall back to original hook and CTA
        assert output.optimized_hook == sample_input.hook
        assert output.optimized_cta == sample_input.call_to_action

    @patch("src.agents.base.get_anthropic_client")
    def test_run_success(
        self,
        mock_get_client: Mock,
        sample_input: ScriptOptimizerInput,
        mock_anthropic_api_response: Message,
    ) -> None:
        """Test full optimization run."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_api_response
        mock_get_client.return_value = mock_client

        agent = ScriptOptimizerAgent()
        output = agent.run(sample_input, {})

        assert output.success is True
        assert output.pattern_interrupt_count >= 0
        assert len(output.pacing_notes) > 0
        assert output.changes_summary != ""
        mock_client.messages.create.assert_called_once()

    @patch("src.agents.base.get_anthropic_client")
    def test_scene_duration_calculation(
        self, mock_get_client: Mock, sample_input: ScriptOptimizerInput
    ) -> None:
        """Test total duration calculated from scenes."""
        agent = ScriptOptimizerAgent()
        response = {
            "optimized_hook": "Test",
            "optimized_scenes": [
                {"scene_number": 1, "duration_seconds": 10, "visual_description": "s1", "voiceover_text": "t1"},
                {"scene_number": 2, "duration_seconds": 15, "visual_description": "s2", "voiceover_text": "t2"},
                {"scene_number": 3, "duration_seconds": 20, "visual_description": "s3", "voiceover_text": "t3"},
            ],
            "optimized_cta": "Buy now",
            "optimized_voiceover": "Test voiceover",
            "changes_summary": "Optimized",
        }

        output = agent.parse_response(json.dumps(response), sample_input)

        # Should calculate duration from scenes (10 + 15 + 20 = 45)
        assert output.estimated_duration_seconds == 45
        assert output.scene_count == 3

    @patch("src.agents.base.get_anthropic_client")
    def test_parse_response_with_code_block(
        self, mock_get_client: Mock, sample_input: ScriptOptimizerInput, mock_optimized_response: dict[str, Any]
    ) -> None:
        """Test parsing JSON wrapped in markdown code block."""
        agent = ScriptOptimizerAgent()
        response_text = f"```json\n{json.dumps(mock_optimized_response)}\n```"

        output = agent.parse_response(response_text, sample_input)

        assert output.success is True
        assert output.optimized_hook == mock_optimized_response["optimized_hook"]

    @patch("src.agents.base.get_anthropic_client")
    def test_system_prompt_content(self, mock_get_client: Mock) -> None:
        """Test system prompt contains required instructions."""
        agent = ScriptOptimizerAgent()

        assert "optimizer" in agent.system_prompt.lower()
        assert "engagement" in agent.system_prompt.lower()
        assert "pattern interrupt" in agent.system_prompt.lower()
        assert "tiktok" in agent.system_prompt.lower()
        assert "facebook" in agent.system_prompt.lower()

    @patch("src.agents.base.get_anthropic_client")
    def test_run_logs_token_usage(
        self,
        mock_get_client: Mock,
        sample_input: ScriptOptimizerInput,
        mock_anthropic_api_response: Message,
    ) -> None:
        """Test that token usage is logged."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_api_response
        mock_get_client.return_value = mock_client

        agent = ScriptOptimizerAgent()

        with patch.object(agent.logger, "info") as mock_log:
            agent.run(sample_input)

            # Find the LLM call log
            llm_call = [call for call in mock_log.call_args_list if call[0][0] == "agent_llm_call"][0]

            assert llm_call.kwargs["input_tokens"] == 900
            assert llm_call.kwargs["output_tokens"] == 700

    @patch("src.agents.base.get_anthropic_client")
    def test_scene_defaults_applied(
        self, mock_get_client: Mock, sample_input: ScriptOptimizerInput
    ) -> None:
        """Test that scene defaults are applied when missing."""
        agent = ScriptOptimizerAgent()
        response = {
            "optimized_hook": "Test",
            "optimized_scenes": [
                {"visual_description": "s1", "voiceover_text": "t1"},
                {"visual_description": "s2", "voiceover_text": "t2"},
                {"visual_description": "s3", "voiceover_text": "t3"},
            ],
            "optimized_cta": "Buy",
            "optimized_voiceover": "Test",
            "changes_summary": "Test",
            "estimated_duration_seconds": 30,
        }

        output = agent.parse_response(json.dumps(response), sample_input)

        # Check defaults
        scene = output.optimized_scenes[0]
        assert scene["duration_seconds"] == 5  # Default
        assert scene["transition"] == "cut"  # Default
        assert scene["pattern_interrupt"] is False  # Default

    @patch("src.agents.base.get_anthropic_client")
    def test_optimization_metadata_preserved(
        self, mock_get_client: Mock, sample_input: ScriptOptimizerInput, mock_optimized_response: dict[str, Any]
    ) -> None:
        """Test that optimization metadata is preserved."""
        agent = ScriptOptimizerAgent()

        output = agent.parse_response(json.dumps(mock_optimized_response), sample_input)

        assert len(output.pacing_notes) == 2
        assert len(output.engagement_hooks) == 3
        assert len(output.platform_adjustments) == 2
        assert output.changes_summary != ""
