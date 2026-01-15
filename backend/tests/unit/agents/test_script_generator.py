"""Unit tests for ScriptGeneratorAgent."""
import json
from unittest.mock import patch

import pytest

from src.agents.script_generator import (
    ScriptGeneratorAgent,
    ScriptGeneratorInput,
    ScriptGeneratorOutput,
)
from tests.fixtures.mocks import create_mock_openai_client, create_mock_openai_response


class TestScriptGeneratorInput:
    """Tests for ScriptGeneratorInput model."""

    def test_create_input(self):
        """Test creating a ScriptGeneratorInput."""
        input_data = ScriptGeneratorInput(
            job_id="job123",
            user_id="user456",
            product_title="Wireless Earbuds",
            key_features=["Wireless", "Noise canceling"],
            unique_selling_points=["Best battery life"],
            target_audience="Music lovers",
            visual_elements=["Sleek design"],
            price="$149.99",
            price_positioning="premium",
            suggested_hooks=["Never miss a beat!"],
            content_angles=["Lifestyle"],
            trending_formats=["POV"],
            platform_tips={"tiktok": "Use trending sounds"},
            suggested_music_style="Upbeat",
        )
        assert input_data.product_title == "Wireless Earbuds"
        assert input_data.target_duration == 45  # Default value

    def test_target_duration_validation(self):
        """Test target duration validation."""
        with pytest.raises(ValueError):
            ScriptGeneratorInput(
                job_id="job123",
                user_id="user456",
                product_title="Test",
                key_features=["Feature"],
                unique_selling_points=["USP"],
                target_audience="Everyone",
                visual_elements=["Element"],
                price="$10",
                price_positioning="budget",
                suggested_hooks=["Hook"],
                content_angles=["Angle"],
                trending_formats=["Format"],
                platform_tips={},
                suggested_music_style="Pop",
                target_duration=120,  # Too long
            )


class TestScriptGeneratorOutput:
    """Tests for ScriptGeneratorOutput model."""

    def test_create_output(self):
        """Test creating a ScriptGeneratorOutput."""
        output = ScriptGeneratorOutput(
            success=True,
            hook="Stop scrolling!",
            scenes=[{"scene_number": 1, "duration_seconds": 5}],
            call_to_action="Shop now!",
            full_voiceover_text="Complete script here",
            full_visual_description="Visual directions",
            estimated_duration_seconds=45,
            scene_count=5,
        )
        assert output.hook == "Stop scrolling!"
        assert output.scene_count == 5


class TestScriptGeneratorAgent:
    """Tests for ScriptGeneratorAgent class."""

    def test_agent_properties(self):
        """Test agent properties."""
        agent = ScriptGeneratorAgent()
        assert agent.name == "ScriptGenerator"
        assert agent.max_tokens == 3000
        assert agent.temperature == 0.7

    def test_system_prompt_contains_json_instruction(self):
        """Test system prompt contains JSON instruction."""
        agent = ScriptGeneratorAgent()
        assert "You must respond with valid JSON" in agent.system_prompt

    def test_system_prompt_contains_no_face_constraint(self):
        """Test system prompt contains no-face visual constraint."""
        agent = ScriptGeneratorAgent()
        assert "NO faces" in agent.system_prompt or "no face" in agent.system_prompt.lower()

    @patch("src.agents.base.get_openai_client")
    def test_run_success(self, mock_get_client):
        """Test successful agent run."""
        mock_client = create_mock_openai_client()
        response_content = json.dumps({
            "hook": "Stop scrolling - this changes everything!",
            "scenes": [
                {
                    "scene_number": 1,
                    "duration_seconds": 3,
                    "visual_description": "Product closeup",
                    "voiceover_text": "Introducing the future",
                    "text_overlay": "NEW!",
                    "transition": "cut",
                },
                {
                    "scene_number": 2,
                    "duration_seconds": 5,
                    "visual_description": "Hands using product",
                    "voiceover_text": "Experience premium quality",
                    "text_overlay": None,
                    "transition": "fade",
                },
            ],
            "call_to_action": "Shop now - link in bio!",
            "full_voiceover_text": "Stop scrolling. Introducing the future...",
            "full_visual_description": "Product showcase with hands-on demo",
            "estimated_duration_seconds": 45,
            "scene_count": 6,
            "suggested_hashtags": ["#NewProduct", "#MustHave"],
            "suggested_music_mood": "Upbeat electronic",
            "text_overlays": ["NEW!", "Premium Quality"],
        })
        # Add more scenes to meet minimum scene_count requirement
        response_data = json.loads(response_content)
        while len(response_data["scenes"]) < 3:
            response_data["scenes"].append({
                "scene_number": len(response_data["scenes"]) + 1,
                "duration_seconds": 5,
                "visual_description": "Additional scene",
                "voiceover_text": "More content",
            })
        response_content = json.dumps(response_data)
        mock_response = create_mock_openai_response(response_content)
        mock_client.chat_completion.return_value = mock_response
        mock_get_client.return_value = mock_client

        agent = ScriptGeneratorAgent()
        input_data = ScriptGeneratorInput(
            job_id="job123",
            user_id="user456",
            product_title="Smart Watch",
            key_features=["Health tracking", "GPS"],
            unique_selling_points=["7-day battery"],
            target_audience="Fitness enthusiasts",
            visual_elements=["Modern design"],
            price="$299.99",
            price_positioning="premium",
            suggested_hooks=["Track your life!"],
            content_angles=["Fitness journey"],
            trending_formats=["Day in the life"],
            platform_tips={"tiktok": "Show results"},
            suggested_music_style="Motivational",
        )

        output = agent.run(input_data)

        assert output.success is True
        assert "scrolling" in output.hook.lower()
        assert len(output.scenes) >= 2
        mock_client.chat_completion.assert_called_once()

    def test_build_user_prompt(self):
        """Test building user prompt."""
        agent = ScriptGeneratorAgent()
        input_data = ScriptGeneratorInput(
            job_id="job123",
            user_id="user456",
            product_title="Coffee Maker",
            key_features=["Auto brew", "Timer"],
            unique_selling_points=["Perfect coffee every time"],
            target_audience="Coffee lovers",
            visual_elements=["Stainless steel"],
            price="$79.99",
            price_positioning="mid-range",
            suggested_hooks=["Wake up to perfection!"],
            content_angles=["Morning routine"],
            trending_formats=["ASMR"],
            platform_tips={"tiktok": "Coffee sounds"},
            suggested_music_style="Calm",
            target_duration=30,
            tone="cozy",
        )

        prompt = agent.build_user_prompt(input_data, {})

        assert "Coffee Maker" in prompt
        assert "30-second" in prompt or "30" in prompt
        assert "cozy" in prompt.lower()

    def test_parse_response(self):
        """Test parsing LLM response."""
        agent = ScriptGeneratorAgent()
        input_data = ScriptGeneratorInput(
            job_id="job123",
            user_id="user456",
            product_title="Test",
            key_features=["Feature"],
            unique_selling_points=["USP"],
            target_audience="Everyone",
            visual_elements=["Element"],
            price="$10",
            price_positioning="budget",
            suggested_hooks=["Hook"],
            content_angles=["Angle"],
            trending_formats=["Format"],
            platform_tips={},
            suggested_music_style="Pop",
        )

        response_text = json.dumps({
            "hook": "Test hook",
            "scenes": [
                {"scene_number": 1, "duration_seconds": 5, "visual_description": "V1", "voiceover_text": "T1"},
                {"scene_number": 2, "duration_seconds": 5, "visual_description": "V2", "voiceover_text": "T2"},
                {"scene_number": 3, "duration_seconds": 5, "visual_description": "V3", "voiceover_text": "T3"},
            ],
            "call_to_action": "Buy now",
            "full_voiceover_text": "Full script",
            "full_visual_description": "Full visuals",
            "estimated_duration_seconds": 30,
            "scene_count": 3,
            "suggested_hashtags": ["#test"],
            "suggested_music_mood": "Happy",
            "text_overlays": ["Text"],
        })

        output = agent.parse_response(response_text, input_data)

        assert output.success is True
        assert output.hook == "Test hook"
        assert output.scene_count == 3
