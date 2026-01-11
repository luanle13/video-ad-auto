from unittest.mock import MagicMock, patch
import pytest
from src.agents.prompt_producer import PromptProducerAgent  # Assuming the agent is in src.agents.prompt_producer


@pytest.fixture
def sample_approved_script():
    """Sample approved script for testing."""
    return {
        "scenes": [
            {
                "scene_number": 1,
                "visual_description": "Product shot with bright lighting",
                "dialogue": "Introducing our amazing new product!",
                "duration_seconds": 10
            },
            {
                "scene_number": 2,
                "visual_description": "Close-up of product features",
                "dialogue": "With advanced features and premium quality.",
                "duration_seconds": 15
            },
            {
                "scene_number": 3,
                "visual_description": "Product in use scenario",
                "dialogue": "Try it today and experience the difference!",
                "duration_seconds": 10
            }
        ],
        "overall_tone": "exciting",
        "estimated_duration": 35
    }


@pytest.fixture
def mock_producer_response():
    """Mock producer response with valid JSON."""
    return {
        "video_prompts": [
            {
                "scene_number": 1,
                "prompt": "A stunning product shot with bright studio lighting, high quality, 4k resolution",
                "style_preset": "cinematic",
                "background_style": "bright_studio",
                "color_palette": ["#FFFFFF", "#000000", "#FF6B6B"]
            },
            {
                "scene_number": 2,
                "prompt": "Close-up detail shot of product features, macro lens, premium quality",
                "style_preset": "product_detail",
                "background_style": "clean_white",
                "color_palette": ["#FFFFFF", "#4ECDC4", "#45B7D1"]
            },
            {
                "scene_number": 3,
                "prompt": "Product in action, lifestyle shot, dynamic movement",
                "style_preset": "lifestyle",
                "background_style": "natural_outdoor",
                "color_palette": ["#F7DC6F", "#BB8FCE", "#85C1E9"]
            }
        ],
        "tts_script": "Introducing our amazing new product! With advanced features and premium quality. Try it today and experience the difference!",
        "ssml_output": "<speak><prosody rate='medium'>Introducing our amazing new product! With advanced features and premium quality. Try it today and experience the difference!</prosody></speak>",
        "scene_timings": [
            {"scene_number": 1, "start_time": 0, "end_time": 10},
            {"scene_number": 2, "start_time": 10, "end_time": 25},
            {"scene_number": 3, "start_time": 25, "end_time": 35}
        ],
        "color_palette": ["#FFFFFF", "#000000", "#FF6B6B", "#4ECDC4", "#45B7D1"],
        "additional_instructions": "Use vibrant colors and dynamic camera movements"
    }


class TestPromptProducerAgent:
    
    def test_style_presets_applied(self, sample_approved_script, mock_producer_response):
        """Test that style presets are applied correctly."""
        agent = PromptProducerAgent()
        
        # Mock the client response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=str(mock_producer_response))]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        result = agent.run(
            script=sample_approved_script,
            background_style="cinematic",
            tone="exciting"
        )
        
        # Verify that style presets are in the result
        assert "video_prompts" in result
        for prompt_data in result["video_prompts"]:
            assert "style_preset" in prompt_data
            assert prompt_data["style_preset"] in ["cinematic", "product_detail", "lifestyle"]
    
    def test_background_presets_applied(self, sample_approved_script, mock_producer_response):
        """Test that background presets are applied correctly."""
        agent = PromptProducerAgent()
        
        # Mock the client response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=str(mock_producer_response))]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        result = agent.run(
            script=sample_approved_script,
            background_style="minimal_white",
            tone="professional"
        )
        
        # Verify that background styles are in the result
        assert "video_prompts" in result
        for prompt_data in result["video_prompts"]:
            assert "background_style" in prompt_data
            # The background style should be reflected in the prompts
            assert isinstance(prompt_data["background_style"], str)
    
    def test_video_prompt_generated(self, sample_approved_script, mock_producer_response):
        """Test that video prompts are generated."""
        agent = PromptProducerAgent()
        
        # Mock the client response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=str(mock_producer_response))]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        result = agent.run(
            script=sample_approved_script,
            background_style="cinematic",
            tone="exciting"
        )
        
        # Verify that video prompts are generated
        assert "video_prompts" in result
        assert len(result["video_prompts"]) == len(sample_approved_script["scenes"])
        for prompt_data in result["video_prompts"]:
            assert "prompt" in prompt_data
            assert "scene_number" in prompt_data
            assert isinstance(prompt_data["prompt"], str)
            assert len(prompt_data["prompt"]) > 0
    
    def test_tts_script_extracted(self, sample_approved_script, mock_producer_response):
        """Test that TTS script is extracted from the script."""
        agent = PromptProducerAgent()
        
        # Mock the client response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=str(mock_producer_response))]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        result = agent.run(
            script=sample_approved_script,
            background_style="cinematic",
            tone="exciting"
        )
        
        # Verify that TTS script is extracted
        assert "tts_script" in result
        assert isinstance(result["tts_script"], str)
        # The TTS script should contain the dialogue from the scenes
        for scene in sample_approved_script["scenes"]:
            assert scene["dialogue"] in result["tts_script"]
    
    def test_ssml_generated(self, sample_approved_script, mock_producer_response):
        """Test that SSML is generated."""
        agent = PromptProducerAgent()
        
        # Mock the client response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=str(mock_producer_response))]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        result = agent.run(
            script=sample_approved_script,
            background_style="cinematic",
            tone="exciting"
        )
        
        # Verify that SSML is generated
        assert "ssml_output" in result
        assert isinstance(result["ssml_output"], str)
        # Should contain SSML tags
        assert "<speak>" in result["ssml_output"]
        assert "</speak>" in result["ssml_output"]
    
    def test_scene_timings_sequential(self, sample_approved_script, mock_producer_response):
        """Test that scene timings are sequential."""
        agent = PromptProducerAgent()
        
        # Mock the client response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=str(mock_producer_response))]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        result = agent.run(
            script=sample_approved_script,
            background_style="cinematic",
            tone="exciting"
        )
        
        # Verify that scene timings are sequential
        assert "scene_timings" in result
        timings = result["scene_timings"]
        
        # Timings should be sequential (each end time equals next start time)
        for i in range(len(timings) - 1):
            assert timings[i]["end_time"] == timings[i + 1]["start_time"]
        
        # First timing should start at 0
        assert timings[0]["start_time"] == 0
    
    def test_duration_calculated_from_scenes(self, sample_approved_script, mock_producer_response):
        """Test that duration is calculated from scenes."""
        agent = PromptProducerAgent()
        
        # Mock the client response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=str(mock_producer_response))]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        result = agent.run(
            script=sample_approved_script,
            background_style="cinematic",
            tone="exciting"
        )
        
        # Verify that duration calculation is consistent
        assert "scene_timings" in result
        if "scene_timings" in result and result["scene_timings"]:
            total_duration = result["scene_timings"][-1]["end_time"]  # Last scene's end time
            # The total duration should match the original script's estimated duration
            assert total_duration == sample_approved_script["estimated_duration"]
    
    def test_color_palette_extracted(self, sample_approved_script, mock_producer_response):
        """Test that color palette is extracted."""
        agent = PromptProducerAgent()
        
        # Mock the client response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=str(mock_producer_response))]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        result = agent.run(
            script=sample_approved_script,
            background_style="cinematic",
            tone="exciting"
        )
        
        # Verify that color palette is extracted
        assert "color_palette" in result
        assert isinstance(result["color_palette"], list)
        for color in result["color_palette"]:
            assert isinstance(color, str)
            # Verify it's a hex color code
            assert color.startswith("#")
            assert len(color) == 7  # Format: #RRGGBB
    
    def test_additional_instructions_included(self, sample_approved_script, mock_producer_response):
        """Test that additional instructions are included."""
        agent = PromptProducerAgent()
        
        # Mock the client response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=str(mock_producer_response))]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        additional_instructions = "Use vibrant colors and dynamic camera movements"
        result = agent.run(
            script=sample_approved_script,
            background_style="cinematic",
            tone="exciting",
            additional_instructions=additional_instructions
        )
        
        # Verify that additional instructions are included in the result
        assert "additional_instructions" in result
        assert result["additional_instructions"] == additional_instructions
    
    def test_run_success(self, sample_approved_script):
        """Test successful run with mocked client."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "video_prompts": [
                {
                    "scene_number": 1,
                    "prompt": "A stunning product shot with bright studio lighting",
                    "style_preset": "cinematic",
                    "background_style": "bright_studio",
                    "color_palette": ["#FFFFFF", "#000000"]
                }
            ],
            "tts_script": "Introducing our amazing new product!",
            "ssml_output": "<speak>Introducing our amazing new product!</speak>",
            "scene_timings": [
                {"scene_number": 1, "start_time": 0, "end_time": 10}
            ],
            "color_palette": ["#FFFFFF", "#000000"],
            "additional_instructions": "Use vibrant colors"
        }''')]
        mock_client.messages.create.return_value = mock_response
        
        agent = PromptProducerAgent(client=mock_client)
        
        result = agent.run(
            script=sample_approved_script,
            background_style="cinematic",
            tone="exciting"
        )
        
        # Verify the result structure
        assert "video_prompts" in result
        assert "tts_script" in result
        assert "ssml_output" in result
        assert "scene_timings" in result
        assert "color_palette" in result
        assert len(result["video_prompts"]) >= 1
        assert len(result["scene_timings"]) >= 1
    
    def test_empty_script_handling(self):
        """Test handling of empty script."""
        agent = PromptProducerAgent()
        
        empty_script = {
            "scenes": [],
            "overall_tone": "neutral",
            "estimated_duration": 0
        }
        
        # Mock the client response for empty script
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "video_prompts": [],
            "tts_script": "",
            "ssml_output": "<speak></speak>",
            "scene_timings": [],
            "color_palette": [],
            "additional_instructions": "No content to process"
        }''')]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        result = agent.run(
            script=empty_script,
            background_style="cinematic",
            tone="neutral"
        )
        
        # Verify that empty script is handled gracefully
        assert "video_prompts" in result
        assert "tts_script" in result
        assert "ssml_output" in result
        assert result["video_prompts"] == []
        assert result["scene_timings"] == []
        assert result["tts_script"] == ""
    
    def test_prompt_building_includes_all_elements(self, sample_approved_script):
        """Test that the prompt includes all necessary elements."""
        agent = PromptProducerAgent()
        
        prompt = agent.build_user_prompt(
            script=sample_approved_script,
            background_style="cinematic",
            tone="exciting",
            additional_instructions="Use dynamic movements"
        )
        
        # Verify that script elements are included in the prompt
        for scene in sample_approved_script["scenes"]:
            assert scene["visual_description"] in prompt
            assert scene["dialogue"] in prompt
        
        # Verify that style and tone are mentioned
        assert "cinematic" in prompt.lower()
        assert "exciting" in prompt.lower()
        assert "dynamic movements" in prompt.lower()