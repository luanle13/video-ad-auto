"""Unit tests for PromptProducerAgent."""
import json
from unittest.mock import patch

import pytest

from src.agents.prompt_producer import (
    PromptProducerAgent,
    PromptProducerInput,
    PromptProducerOutput,
)
from tests.fixtures.mocks import create_mock_openai_client, create_mock_openai_response


class TestPromptProducerInput:
    """Tests for PromptProducerInput model."""

    def test_create_input(self):
        """Test creating a PromptProducerInput."""
        input_data = PromptProducerInput(
            job_id="job123",
            user_id="user456",
            hook="Stop scrolling!",
            scenes=[{"scene_number": 1, "visual_description": "Product closeup"}],
            call_to_action="Shop now!",
            full_voiceover_text="Complete script here",
            product_title="Wireless Earbuds",
        )
        assert input_data.product_title == "Wireless Earbuds"
        assert input_data.target_duration == 45  # Default


class TestPromptProducerOutput:
    """Tests for PromptProducerOutput model."""

    def test_create_output(self):
        """Test creating a PromptProducerOutput."""
        output = PromptProducerOutput(
            success=True,
            video_prompts=[{"scene_number": 1, "prompt": "Test prompt"}],
            master_prompt="Overall style prompt",
            negative_prompt="No faces",
            style_keywords=["cinematic", "modern"],
            camera_movements=["pan", "zoom"],
            transition_effects=["cut", "fade"],
            audio_sync_notes="Sync with beat drops",
        )
        assert output.success is True
        assert len(output.video_prompts) == 1
        assert "cinematic" in output.style_keywords


class TestPromptProducerAgent:
    """Tests for PromptProducerAgent class."""

    def test_agent_properties(self):
        """Test agent properties."""
        agent = PromptProducerAgent()
        assert agent.name == "PromptProducer"
        assert agent.model == "gpt-4o"
        assert agent.max_tokens == 2500
        assert agent.temperature == 0.4

    def test_system_prompt_contains_json_instruction(self):
        """Test system prompt contains JSON instruction."""
        agent = PromptProducerAgent()
        assert "You must respond with valid JSON" in agent.system_prompt

    def test_system_prompt_contains_no_face_constraint(self):
        """Test system prompt emphasizes no faces."""
        agent = PromptProducerAgent()
        prompt = agent.system_prompt.lower()
        assert "no face" in prompt or "no faces" in prompt

    @patch("src.agents.base.get_openai_client")
    def test_run_success(self, mock_get_client):
        """Test successful agent run."""
        mock_client = create_mock_openai_client()
        response_content = json.dumps({
            "video_prompts": [
                {
                    "scene_number": 1,
                    "duration_seconds": 3,
                    "prompt": "Cinematic close-up of wireless earbuds on marble surface, soft studio lighting, shallow depth of field, product photography style",
                    "camera_movement": "slow zoom in",
                    "style_notes": "Clean, minimalist aesthetic",
                },
                {
                    "scene_number": 2,
                    "duration_seconds": 5,
                    "prompt": "Hands placing earbuds into charging case, soft natural lighting, lifestyle shot, no face visible",
                    "camera_movement": "static",
                    "style_notes": "Focus on tactile interaction",
                },
            ],
            "master_prompt": "Modern, cinematic product video with soft lighting, clean backgrounds, focus on product details and hands-only human interaction",
            "negative_prompt": "face, facial features, eyes, portrait, blurry, low quality, distorted, cartoon, anime",
            "style_keywords": ["cinematic", "modern", "clean", "minimalist", "professional"],
            "camera_movements": ["slow zoom", "pan", "static", "dolly"],
            "transition_effects": ["cut", "fade", "zoom transition"],
            "audio_sync_notes": "Match cuts to music beats, emphasize product reveals on drops",
        })
        mock_response = create_mock_openai_response(response_content)
        mock_client.chat_completion.return_value = mock_response
        mock_get_client.return_value = mock_client

        agent = PromptProducerAgent()
        input_data = PromptProducerInput(
            job_id="job123",
            user_id="user456",
            hook="Stop scrolling!",
            scenes=[
                {"scene_number": 1, "duration_seconds": 3, "visual_description": "Product closeup"},
                {"scene_number": 2, "duration_seconds": 5, "visual_description": "Hands using product"},
            ],
            call_to_action="Shop now!",
            full_voiceover_text="Stop scrolling. These earbuds will change your life...",
            product_title="Premium Wireless Earbuds",
            visual_elements=["Sleek design", "LED indicator", "Charging case"],
        )

        output = agent.run(input_data)

        assert output.success is True
        assert len(output.video_prompts) == 2
        assert "cinematic" in output.master_prompt.lower()
        assert "face" in output.negative_prompt.lower()
        mock_client.chat_completion.assert_called_once()

    def test_build_user_prompt(self):
        """Test building user prompt."""
        agent = PromptProducerAgent()
        input_data = PromptProducerInput(
            job_id="job123",
            user_id="user456",
            hook="Amazing product!",
            scenes=[
                {"scene_number": 1, "duration_seconds": 3, "visual_description": "Closeup", "transition": "cut"},
            ],
            call_to_action="Buy now",
            full_voiceover_text="This is amazing...",
            product_title="Smart Watch",
            visual_elements=["Digital display", "Leather strap"],
            target_duration=30,
        )

        prompt = agent.build_user_prompt(input_data, {})

        assert "Smart Watch" in prompt
        assert "30" in prompt
        assert "Amazing product!" in prompt
        assert "Digital display" in prompt
        assert "NO FACES" in prompt

    def test_parse_response(self):
        """Test parsing LLM response."""
        agent = PromptProducerAgent()
        input_data = PromptProducerInput(
            job_id="job123",
            user_id="user456",
            hook="Hook",
            scenes=[{"scene_number": 1}],
            call_to_action="CTA",
            full_voiceover_text="Script",
            product_title="Product",
        )

        response_text = json.dumps({
            "video_prompts": [
                {
                    "scene_number": 1,
                    "duration_seconds": 5,
                    "prompt": "Test prompt",
                    "camera_movement": "pan",
                    "style_notes": "Clean",
                }
            ],
            "master_prompt": "Master style",
            "negative_prompt": "No faces",
            "style_keywords": ["modern"],
            "camera_movements": ["pan"],
            "transition_effects": ["cut"],
            "audio_sync_notes": "Sync notes",
        })

        output = agent.parse_response(response_text, input_data)

        assert output.success is True
        assert len(output.video_prompts) == 1
        assert output.video_prompts[0]["prompt"] == "Test prompt"
        assert output.master_prompt == "Master style"

    def test_parse_response_default_negative_prompt(self):
        """Test that parse_response provides default negative prompt."""
        agent = PromptProducerAgent()
        input_data = PromptProducerInput(
            job_id="job123",
            user_id="user456",
            hook="Hook",
            scenes=[],
            call_to_action="CTA",
            full_voiceover_text="Script",
            product_title="Product",
        )

        response_text = json.dumps({
            "video_prompts": [],
            "master_prompt": "",
            "style_keywords": [],
            "camera_movements": [],
            "transition_effects": [],
            "audio_sync_notes": "",
        })

        output = agent.parse_response(response_text, input_data)

        assert "face" in output.negative_prompt.lower()
