from unittest.mock import MagicMock, patch
import pytest
from src.agents.script_generator import ScriptGeneratorAgent  # Assuming the agent is in src.agents.script_generator


class TestScriptGeneratorAgent:
    
    def test_build_prompt_with_all_inputs(self):
        """Test that the prompt includes all required inputs."""
        agent = ScriptGeneratorAgent()
        
        product_info = {
            "title": "Wireless Headphones",
            "description": "Premium noise-cancelling headphones",
            "key_features": ["ANC", "30hr battery", "Bluetooth 5.0"]
        }
        tone = "enthusiastic"
        emphasis = "battery life"
        duration = 45
        additional_instructions = "Include call to action"
        
        prompt = agent.build_user_prompt(
            product_info=product_info,
            tone=tone,
            emphasis=emphasis,
            duration=duration,
            additional_instructions=additional_instructions
        )
        
        # Check that all inputs are included in the prompt
        assert product_info["title"] in prompt
        assert product_info["description"] in prompt
        assert tone in prompt
        assert emphasis in prompt
        assert str(duration) in prompt
        assert additional_instructions in prompt
        
        # Check that key features are included
        for feature in product_info["key_features"]:
            assert feature in prompt
    
    def test_parse_scenes_correctly(self):
        """Test that scenes are parsed correctly from response."""
        agent = ScriptGeneratorAgent()
        
        response_data = {
            "scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Show the headphones in the box",
                    "dialogue": "Introducing our premium wireless headphones",
                    "duration_seconds": 10
                },
                {
                    "scene_number": 2,
                    "visual_description": "Demonstrate ANC feature",
                    "dialogue": "Experience total silence with our ANC technology",
                    "duration_seconds": 15
                },
                {
                    "scene_number": 3,
                    "visual_description": "Show long battery life",
                    "dialogue": "30 hours of non-stop music on a single charge",
                    "duration_seconds": 20
                }
            ],
            "overall_tone": "enthusiastic",
            "estimated_duration": 45
        }
        
        parsed = agent.parse_response(response_data)
        
        assert "scenes" in parsed
        assert len(parsed["scenes"]) == 3
        assert parsed["scenes"][0]["scene_number"] == 1
        assert parsed["scenes"][0]["visual_description"] == "Show the headphones in the box"
        assert parsed["scenes"][0]["dialogue"] == "Introducing our premium wireless headphones"
        assert parsed["scenes"][0]["duration_seconds"] == 10
        assert parsed["overall_tone"] == "enthusiastic"
        assert parsed["estimated_duration"] == 45
    
    def test_calculate_duration_from_scenes(self):
        """Test that duration is calculated correctly from scenes."""
        agent = ScriptGeneratorAgent()
        
        response_data = {
            "scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Scene 1",
                    "dialogue": "Dialogue 1",
                    "duration_seconds": 10
                },
                {
                    "scene_number": 2,
                    "visual_description": "Scene 2",
                    "dialogue": "Dialogue 2",
                    "duration_seconds": 15
                },
                {
                    "scene_number": 3,
                    "visual_description": "Scene 3",
                    "dialogue": "Dialogue 3",
                    "duration_seconds": 20
                }
            ],
            "overall_tone": "enthusiastic"
        }
        
        parsed = agent.parse_response(response_data)
        
        # Total duration should be sum of scene durations
        assert parsed["estimated_duration"] == 45  # 10 + 15 + 20
    
    def test_tone_instruction_included(self):
        """Test that tone instruction is included in the prompt."""
        agent = ScriptGeneratorAgent()
        
        product_info = {"title": "Headphones", "description": "Great headphones"}
        tone = "professional"
        
        prompt = agent.build_user_prompt(
            product_info=product_info,
            tone=tone,
            emphasis="quality",
            duration=30
        )
        
        assert tone.lower() in prompt.lower()
        assert "tone" in prompt.lower()
    
    def test_emphasis_instruction_included(self):
        """Test that emphasis instruction is included in the prompt."""
        agent = ScriptGeneratorAgent()
        
        product_info = {"title": "Headphones", "description": "Great headphones"}
        emphasis = "sound quality"
        
        prompt = agent.build_user_prompt(
            product_info=product_info,
            tone="enthusiastic",
            emphasis=emphasis,
            duration=30
        )
        
        assert emphasis.lower() in prompt.lower()
        assert "emphasize" in prompt.lower() or "highlight" in prompt.lower()
    
    def test_run_success(self):
        """Test successful run with mocked client."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Product shot",
                    "dialogue": "Check out our amazing product!",
                    "duration_seconds": 15
                }
            ],
            "overall_tone": "exciting",
            "estimated_duration": 15
        }''')]
        mock_client.messages.create.return_value = mock_response
        
        agent = ScriptGeneratorAgent(client=mock_client)
        
        product_info = {"title": "Amazing Product", "description": "Best product ever"}
        result = agent.run(
            product_info=product_info,
            tone="exciting",
            emphasis="features",
            duration=15
        )
        
        assert "scenes" in result
        assert len(result["scenes"]) == 1
        assert result["scenes"][0]["scene_number"] == 1
        assert result["overall_tone"] == "exciting"
        assert result["estimated_duration"] == 15
    
    def test_empty_scenes_handling(self):
        """Test handling of empty scenes in response."""
        agent = ScriptGeneratorAgent()
        
        response_data = {
            "scenes": [],
            "overall_tone": "neutral"
        }
        
        parsed = agent.parse_response(response_data)
        
        assert "scenes" in parsed
        assert parsed["scenes"] == []
        assert parsed["overall_tone"] == "neutral"
        assert parsed["estimated_duration"] == 0
    
    def test_single_scene_handling(self):
        """Test handling of single scene in response."""
        agent = ScriptGeneratorAgent()
        
        response_data = {
            "scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Product shot",
                    "dialogue": "Check out our amazing product!",
                    "duration_seconds": 30
                }
            ],
            "overall_tone": "exciting"
        }
        
        parsed = agent.parse_response(response_data)
        
        assert "scenes" in parsed
        assert len(parsed["scenes"]) == 1
        assert parsed["scenes"][0]["scene_number"] == 1
        assert parsed["estimated_duration"] == 30
    
    def test_long_duration_handling(self):
        """Test handling of longer durations."""
        agent = ScriptGeneratorAgent()
        
        response_data = {
            "scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Scene 1",
                    "dialogue": "Dialogue 1",
                    "duration_seconds": 60
                },
                {
                    "scene_number": 2,
                    "visual_description": "Scene 2",
                    "dialogue": "Dialogue 2",
                    "duration_seconds": 60
                }
            ],
            "overall_tone": "calm"
        }
        
        parsed = agent.parse_response(response_data)
        
        assert parsed["estimated_duration"] == 120  # 60 + 60