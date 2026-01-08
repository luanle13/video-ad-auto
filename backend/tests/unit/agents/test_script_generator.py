"""Tests for Script Generator Agent."""
from typing import Any
from unittest.mock import Mock, patch

import pytest
from anthropic.types import Message, Usage
from anthropic.types.text_block import TextBlock

from src.agents.script_generator import (
    ScriptGeneratorAgent,
    ScriptGeneratorInput,
    ScriptGeneratorOutput,
)


@pytest.fixture
def sample_input() -> ScriptGeneratorInput:
    """Sample input for testing."""
    return ScriptGeneratorInput(
        job_id="test-job-123",
        user_id="test-user-456",
        product_title="Wireless Bluetooth Earbuds Pro",
        key_features=[
            "Active noise cancellation",
            "40-hour battery life",
            "IPX5 water resistant",
            "Touch controls",
        ],
        unique_selling_points=[
            "Best-in-class ANC at this price",
            "Longest battery in category",
            "Premium sound quality",
        ],
        target_audience="Young professionals aged 25-35 who commute and exercise regularly",
        visual_elements=[
            "Sleek matte black case",
            "LED indicator lights",
            "Ergonomic ear tips",
        ],
        price="799,000 VND",
        price_positioning="mid-range",
        suggested_hooks=[
            "Tired of hearing your noisy commute?",
            "What if your earbuds lasted a whole week?",
        ],
        content_angles=[
            "Commuter's best friend",
            "Gym-proof audio",
        ],
        trending_formats=["POV", "Before/After", "Day in the life"],
        platform_tips={
            "tiktok": "Use trending sounds",
            "facebook": "Add captions for silent viewing",
        },
        suggested_music_style="upbeat electronic",
        target_duration=45,
        tone="energetic",
    )


@pytest.fixture
def mock_anthropic_response() -> dict[str, Any]:
    """Mock successful Anthropic response."""
    return {
        "hook": "POV: You finally found earbuds that actually block your noisy commute",
        "scenes": [
            {
                "scene_number": 1,
                "duration_seconds": 3,
                "visual_description": "Close-up of crowded, noisy train",
                "voiceover_text": "POV: You finally found earbuds that actually block your noisy commute",
                "text_overlay": "POV: Finding THE earbuds",
                "transition": "cut",
            },
            {
                "scene_number": 2,
                "duration_seconds": 5,
                "visual_description": "Person puts in earbuds, visual noise fades",
                "voiceover_text": "With active noise cancellation that actually works",
                "text_overlay": "ANC that WORKS",
                "transition": "fade",
            },
            {
                "scene_number": 3,
                "duration_seconds": 7,
                "visual_description": "Product showcase with feature callouts",
                "voiceover_text": "40 hours of battery, water resistant, and touch controls",
                "text_overlay": "40HR BATTERY",
                "transition": "zoom",
            },
            {
                "scene_number": 4,
                "duration_seconds": 5,
                "visual_description": "Person using earbuds at gym and commuting",
                "voiceover_text": "Perfect for work, gym, and everything in between",
                "text_overlay": None,
                "transition": "swipe",
            },
            {
                "scene_number": 5,
                "duration_seconds": 5,
                "visual_description": "Price reveal with value comparison",
                "voiceover_text": "And at 799k, you're getting premium quality without the premium price",
                "text_overlay": "799K VND",
                "transition": "cut",
            },
        ],
        "call_to_action": "Link in bio - your ears will thank you",
        "full_voiceover_text": "POV: You finally found earbuds that actually block your noisy commute. With active noise cancellation that actually works. 40 hours of battery, water resistant, and touch controls. Perfect for work, gym, and everything in between. And at 799k, you're getting premium quality without the premium price. Link in bio - your ears will thank you.",
        "full_visual_description": "Opens with noisy train scene. Person puts in earbuds, world goes quiet. Product showcase with feature callouts. Lifestyle montage. Price reveal. End with CTA.",
        "estimated_duration_seconds": 45,
        "scene_count": 5,
        "suggested_hashtags": ["#earbuds", "#techreview", "#commute", "#anc", "#wireless"],
        "suggested_music_mood": "upbeat electronic",
        "text_overlays": ["POV: Finding THE earbuds", "ANC that WORKS", "40HR BATTERY", "799K VND"],
    }


@pytest.fixture
def mock_anthropic_api_response(mock_anthropic_response: dict[str, Any]) -> Message:
    """Mock Anthropic API Message response."""
    import json

    return Message(
        id="msg_script_123",
        type="message",
        role="assistant",
        content=[
            TextBlock(
                type="text",
                text=f"```json\n{json.dumps(mock_anthropic_response, indent=2)}\n```",
            )
        ],
        model="claude-sonnet-4-20250514",
        stop_reason="end_turn",
        usage=Usage(
            input_tokens=800,
            output_tokens=600,
        ),
    )


class TestScriptGeneratorInput:
    """Tests for ScriptGeneratorInput model."""

    def test_valid_input(self) -> None:
        """Test valid script generator input."""
        input_data = ScriptGeneratorInput(
            job_id="job_123",
            user_id="user_456",
            product_title="Test Product",
            key_features=["feature1"],
            unique_selling_points=["usp1"],
            target_audience="Test audience",
            visual_elements=["element1"],
            price="100 VND",
            price_positioning="budget",
            suggested_hooks=["hook1"],
            content_angles=["angle1"],
            trending_formats=["format1"],
            platform_tips={"tiktok": "tip1"},
            suggested_music_style="upbeat",
        )

        assert input_data.target_duration == 45  # Default
        assert input_data.tone is None
        assert input_data.emphasis is None

    def test_target_duration_validation(self) -> None:
        """Test target duration validation."""
        from pydantic import ValidationError

        base_data = {
            "job_id": "job_123",
            "user_id": "user_456",
            "product_title": "Test",
            "key_features": ["f1"],
            "unique_selling_points": ["u1"],
            "target_audience": "audience",
            "visual_elements": ["v1"],
            "price": "100",
            "price_positioning": "mid-range",
            "suggested_hooks": ["h1"],
            "content_angles": ["a1"],
            "trending_formats": ["f1"],
            "platform_tips": {},
            "suggested_music_style": "upbeat",
        }

        # Too short
        with pytest.raises(ValidationError):
            ScriptGeneratorInput(**{**base_data, "target_duration": 20})

        # Too long
        with pytest.raises(ValidationError):
            ScriptGeneratorInput(**{**base_data, "target_duration": 70})

        # Valid range
        ScriptGeneratorInput(**{**base_data, "target_duration": 30})
        ScriptGeneratorInput(**{**base_data, "target_duration": 60})


class TestScriptGeneratorOutput:
    """Tests for ScriptGeneratorOutput model."""

    def test_default_values(self) -> None:
        """Test default values in output."""
        output = ScriptGeneratorOutput(
            hook="Test hook",
            call_to_action="Buy now",
            full_voiceover_text="Full text",
            full_visual_description="Full visual",
            estimated_duration_seconds=45,
            scene_count=5,
        )

        assert output.success is True
        assert output.scenes == []
        assert output.suggested_hashtags == []
        assert output.suggested_music_mood == ""
        assert output.text_overlays == []

    def test_with_scenes(self, mock_anthropic_response: dict[str, Any]) -> None:
        """Test output with scene data."""
        output = ScriptGeneratorOutput(**mock_anthropic_response)

        assert len(output.scenes) == 5
        assert output.scene_count == 5
        assert output.estimated_duration_seconds == 45
        assert len(output.suggested_hashtags) == 5


class TestScriptGeneratorAgent:
    """Tests for ScriptGeneratorAgent."""

    @patch("src.agents.base.get_anthropic_client")
    def test_agent_initialization(self, mock_get_client: Mock) -> None:
        """Test agent initialization."""
        agent = ScriptGeneratorAgent()

        assert agent.name == "ScriptGenerator"
        assert agent.temperature == 0.7
        assert agent.max_tokens == 3000

    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_includes_all_inputs(
        self, mock_get_client: Mock, sample_input: ScriptGeneratorInput
    ) -> None:
        """Test that user prompt includes all relevant input data."""
        agent = ScriptGeneratorAgent()

        prompt = agent.build_user_prompt(sample_input, {})

        assert sample_input.product_title in prompt
        assert sample_input.price in prompt
        assert sample_input.target_audience in prompt
        assert "45-second" in prompt
        assert "energetic" in prompt
        assert "Active noise cancellation" in prompt
        assert "upbeat electronic" in prompt

    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_with_emphasis(self, mock_get_client: Mock) -> None:
        """Test emphasis instruction is included."""
        input_data = ScriptGeneratorInput(
            job_id="job_123",
            user_id="user_456",
            product_title="Test",
            key_features=["battery life"],
            unique_selling_points=["long battery"],
            target_audience="users",
            visual_elements=["sleek"],
            price="100",
            price_positioning="mid-range",
            suggested_hooks=["hook"],
            content_angles=["angle"],
            trending_formats=["format"],
            platform_tips={},
            suggested_music_style="upbeat",
            emphasis="battery life",
        )

        agent = ScriptGeneratorAgent()
        prompt = agent.build_user_prompt(input_data, {})

        assert "battery life" in prompt
        assert "EMPHASIS" in prompt

    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_with_platform_tips(self, mock_get_client: Mock) -> None:
        """Test platform tips are included."""
        input_data = ScriptGeneratorInput(
            job_id="job_123",
            user_id="user_456",
            product_title="Test",
            key_features=["f1"],
            unique_selling_points=["u1"],
            target_audience="users",
            visual_elements=["v1"],
            price="100",
            price_positioning="mid-range",
            suggested_hooks=["h1"],
            content_angles=["a1"],
            trending_formats=["f1"],
            platform_tips={"tiktok": "Use trending sounds", "facebook": "Add captions"},
            suggested_music_style="upbeat",
        )

        agent = ScriptGeneratorAgent()
        prompt = agent.build_user_prompt(input_data, {})

        assert "tiktok" in prompt.lower()
        assert "trending sounds" in prompt
        assert "facebook" in prompt.lower()
        assert "PLATFORM TIPS" in prompt

    @patch("src.agents.base.get_anthropic_client")
    def test_parse_response_valid_json(
        self, mock_get_client: Mock, sample_input: ScriptGeneratorInput, mock_anthropic_response: dict[str, Any]
    ) -> None:
        """Test parsing valid JSON response."""
        import json

        agent = ScriptGeneratorAgent()
        response_text = json.dumps(mock_anthropic_response)

        output = agent.parse_response(response_text, sample_input)

        assert output.success is True
        assert output.hook == mock_anthropic_response["hook"]
        assert len(output.scenes) == 5
        assert output.scene_count == 5
        assert output.estimated_duration_seconds == 45
        assert output.call_to_action == mock_anthropic_response["call_to_action"]

    @patch("src.agents.base.get_anthropic_client")
    def test_parse_response_with_code_block(
        self, mock_get_client: Mock, sample_input: ScriptGeneratorInput, mock_anthropic_response: dict[str, Any]
    ) -> None:
        """Test parsing JSON wrapped in markdown code block."""
        import json

        agent = ScriptGeneratorAgent()
        response_text = f"```json\n{json.dumps(mock_anthropic_response)}\n```"

        output = agent.parse_response(response_text, sample_input)

        assert output.success is True
        assert output.hook == mock_anthropic_response["hook"]

    @patch("src.agents.base.get_anthropic_client")
    def test_run_success(
        self,
        mock_get_client: Mock,
        sample_input: ScriptGeneratorInput,
        mock_anthropic_api_response: Message,
    ) -> None:
        """Test full agent run."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_api_response
        mock_get_client.return_value = mock_client

        agent = ScriptGeneratorAgent()
        output = agent.run(sample_input, {})

        assert output.success is True
        assert len(output.scenes) > 0
        mock_client.messages.create.assert_called_once()

    @patch("src.agents.base.get_anthropic_client")
    def test_scenes_duration_calculation(
        self, mock_get_client: Mock, sample_input: ScriptGeneratorInput
    ) -> None:
        """Test that total duration is calculated from scenes."""
        agent = ScriptGeneratorAgent()
        response_text = """{
            "hook": "Test hook",
            "scenes": [
                {"scene_number": 1, "duration_seconds": 10, "visual_description": "scene 1", "voiceover_text": "text 1"},
                {"scene_number": 2, "duration_seconds": 15, "visual_description": "scene 2", "voiceover_text": "text 2"},
                {"scene_number": 3, "duration_seconds": 20, "visual_description": "scene 3", "voiceover_text": "text 3"}
            ],
            "call_to_action": "Buy now",
            "full_voiceover_text": "Complete text",
            "full_visual_description": "Complete visual"
        }"""

        output = agent.parse_response(response_text, sample_input)

        # Should calculate duration from scenes (10 + 15 + 20 = 45)
        assert output.estimated_duration_seconds == 45
        assert output.scene_count == 3

    @patch("src.agents.base.get_anthropic_client")
    def test_scenes_use_provided_duration_if_available(
        self, mock_get_client: Mock, sample_input: ScriptGeneratorInput
    ) -> None:
        """Test that provided duration is used over calculated."""
        agent = ScriptGeneratorAgent()
        response_text = """{
            "hook": "Test hook",
            "scenes": [
                {"scene_number": 1, "duration_seconds": 10, "visual_description": "scene 1", "voiceover_text": "text 1"},
                {"scene_number": 2, "duration_seconds": 8, "visual_description": "scene 2", "voiceover_text": "text 2"},
                {"scene_number": 3, "duration_seconds": 12, "visual_description": "scene 3", "voiceover_text": "text 3"}
            ],
            "call_to_action": "Buy now",
            "full_voiceover_text": "Complete text",
            "full_visual_description": "Complete visual",
            "estimated_duration_seconds": 50
        }"""

        output = agent.parse_response(response_text, sample_input)

        # Should use provided duration instead of calculated (10 + 8 + 12 = 30)
        assert output.estimated_duration_seconds == 50

    @patch("src.agents.base.get_anthropic_client")
    def test_hashtag_limit(self, mock_get_client: Mock, sample_input: ScriptGeneratorInput) -> None:
        """Test that hashtags are limited to 10."""
        import json

        agent = ScriptGeneratorAgent()
        many_hashtags = [f"#tag{i}" for i in range(20)]
        response_data = {
            "hook": "Test",
            "scenes": [
                {"scene_number": 1, "duration_seconds": 15, "visual_description": "s1", "voiceover_text": "t1"},
                {"scene_number": 2, "duration_seconds": 15, "visual_description": "s2", "voiceover_text": "t2"},
                {"scene_number": 3, "duration_seconds": 15, "visual_description": "s3", "voiceover_text": "t3"},
            ],
            "call_to_action": "Buy",
            "full_voiceover_text": "text",
            "full_visual_description": "visual",
            "estimated_duration_seconds": 45,
            "suggested_hashtags": many_hashtags,
        }
        response_text = json.dumps(response_data)

        output = agent.parse_response(response_text, sample_input)

        assert len(output.suggested_hashtags) <= 10

    @patch("src.agents.base.get_anthropic_client")
    def test_scene_defaults(self, mock_get_client: Mock, sample_input: ScriptGeneratorInput) -> None:
        """Test that scene defaults are applied."""
        agent = ScriptGeneratorAgent()
        response_text = """{
            "hook": "Test",
            "scenes": [
                {"visual_description": "scene 1", "voiceover_text": "text 1"},
                {"visual_description": "scene 2", "voiceover_text": "text 2"},
                {"visual_description": "scene 3", "voiceover_text": "text 3"}
            ],
            "call_to_action": "Buy",
            "full_voiceover_text": "text",
            "full_visual_description": "visual",
            "estimated_duration_seconds": 30
        }"""

        output = agent.parse_response(response_text, sample_input)

        scene = output.scenes[0]
        assert scene["scene_number"] == 1
        assert scene["duration_seconds"] == 5  # Default
        assert scene["transition"] == "cut"  # Default
        assert scene["text_overlay"] is None

    @patch("src.agents.base.get_anthropic_client")
    def test_system_prompt_content(self, mock_get_client: Mock) -> None:
        """Test system prompt contains required instructions."""
        agent = ScriptGeneratorAgent()

        assert "scriptwriter" in agent.system_prompt.lower()
        assert "tiktok" in agent.system_prompt.lower()
        assert "hook" in agent.system_prompt.lower()
        assert "json" in agent.system_prompt.lower()
        assert "scenes" in agent.system_prompt
        assert "call_to_action" in agent.system_prompt

    @patch("src.agents.base.get_anthropic_client")
    def test_run_logs_token_usage(
        self,
        mock_get_client: Mock,
        sample_input: ScriptGeneratorInput,
        mock_anthropic_api_response: Message,
    ) -> None:
        """Test that token usage is logged."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_api_response
        mock_get_client.return_value = mock_client

        agent = ScriptGeneratorAgent()

        with patch.object(agent.logger, "info") as mock_log:
            agent.run(sample_input)

            # Find the LLM call log
            llm_call = [call for call in mock_log.call_args_list if call[0][0] == "agent_llm_call"][0]

            assert llm_call.kwargs["input_tokens"] == 800
            assert llm_call.kwargs["output_tokens"] == 600

    @patch("src.agents.base.get_anthropic_client")
    def test_parse_response_handles_missing_optional_fields(
        self, mock_get_client: Mock, sample_input: ScriptGeneratorInput
    ) -> None:
        """Test parsing with missing optional fields."""
        agent = ScriptGeneratorAgent()
        response_text = """{
            "hook": "Test hook",
            "scenes": [
                {"scene_number": 1, "duration_seconds": 15, "visual_description": "s1", "voiceover_text": "t1"},
                {"scene_number": 2, "duration_seconds": 15, "visual_description": "s2", "voiceover_text": "t2"},
                {"scene_number": 3, "duration_seconds": 15, "visual_description": "s3", "voiceover_text": "t3"}
            ],
            "call_to_action": "Buy now",
            "full_voiceover_text": "text",
            "full_visual_description": "visual",
            "estimated_duration_seconds": 45
        }"""

        output = agent.parse_response(response_text, sample_input)

        assert output.success is True
        assert output.suggested_hashtags == []
        assert output.suggested_music_mood == ""
        assert output.text_overlays == []
        assert output.scene_count == 3
