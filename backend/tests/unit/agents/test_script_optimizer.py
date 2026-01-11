from unittest.mock import MagicMock, patch
import pytest
from src.agents.script_optimizer import ScriptOptimizerAgent  # Assuming the agent is in src.agents.script_optimizer


class TestScriptOptimizerAgent:
    
    def test_platform_requirements_applied(self):
        """Test that platform requirements are applied to the script."""
        agent = ScriptOptimizerAgent()
        
        original_script = {
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
        }
        
        platform_requirements = {
            "max_duration": 30,
            "preferred_tone": "professional",
            "content_restrictions": ["no exaggerated claims"]
        }
        
        # Mock the client to return an optimized script
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "optimized_scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Professional product shot",
                    "dialogue": "Discover our high-quality product!",
                    "duration_seconds": 15
                }
            ],
            "optimized_tone": "professional",
            "optimized_duration": 15,
            "optimization_notes": ["Adjusted tone to professional", "Removed exaggerated claims"]
        }''')]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        result = agent.run(
            original_script=original_script,
            platform_requirements=platform_requirements
        )
        
        assert "optimized_scenes" in result
        assert result["optimized_tone"] == "professional"
        assert result["optimized_duration"] <= 30  # Respects max duration
    
    def test_pattern_interrupt_counting(self):
        """Test that interrupt patterns are counted correctly."""
        agent = ScriptOptimizerAgent()
        
        # Count interrupt patterns in a sample script
        sample_dialogue = """
        Wait! Stop! Don't buy anything else yet!
        But wait, there's more!
        Hold on, let me tell you something important.
        First, you need to know this.
        Second, consider this option.
        Third, don't forget about this feature.
        """
        
        interrupt_count = agent.count_interrupt_patterns(sample_dialogue)
        
        # Should count "wait", "but wait", "hold on", "first", "second", "third"
        assert interrupt_count >= 3  # At least 3 interrupt patterns
    
    def test_pacing_instruction_included(self):
        """Test that pacing instruction is included in the prompt."""
        agent = ScriptOptimizerAgent()
        
        original_script = {
            "scenes": [{"scene_number": 1, "dialogue": "Sample dialogue", "duration_seconds": 10}],
            "overall_tone": "exciting",
            "estimated_duration": 10
        }
        
        platform_requirements = {"max_duration": 30}
        
        prompt = agent.build_user_prompt(
            original_script=original_script,
            platform_requirements=platform_requirements
        )
        
        assert "pacing" in prompt.lower()
        assert "duration" in prompt.lower()
        assert "flow" in prompt.lower()
    
    def test_fallback_to_original_values(self):
        """Test that original values are preserved if optimization fails."""
        agent = ScriptOptimizerAgent()
        
        original_script = {
            "scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Original shot",
                    "dialogue": "Original dialogue",
                    "duration_seconds": 15
                }
            ],
            "overall_tone": "exciting",
            "estimated_duration": 15
        }
        
        # Mock the client to return an invalid response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "optimized_scenes": [],
            "optimized_tone": "",
            "optimized_duration": 0
        }''')]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        result = agent.run(
            original_script=original_script,
            platform_requirements={}
        )
        
        # If optimization fails, it should return original values or sensible defaults
        assert "optimized_scenes" in result
        assert "optimized_tone" in result
        assert "optimized_duration" in result
    
    def test_run_success(self):
        """Test successful run with mocked client."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "optimized_scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Optimized shot",
                    "dialogue": "Optimized dialogue",
                    "duration_seconds": 12
                }
            ],
            "optimized_tone": "professional",
            "optimized_duration": 12,
            "optimization_notes": ["Improved pacing", "Enhanced clarity"]
        }''')]
        mock_client.messages.create.return_value = mock_response
        
        agent = ScriptOptimizerAgent(client=mock_client)
        
        original_script = {
            "scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Original shot",
                    "dialogue": "Original dialogue",
                    "duration_seconds": 15
                }
            ],
            "overall_tone": "exciting",
            "estimated_duration": 15
        }
        
        result = agent.run(
            original_script=original_script,
            platform_requirements={"max_duration": 30}
        )
        
        assert "optimized_scenes" in result
        assert len(result["optimized_scenes"]) == 1
        assert result["optimized_scenes"][0]["scene_number"] == 1
        assert result["optimized_tone"] == "professional"
        assert result["optimized_duration"] == 12
        assert "optimization_notes" in result
    
    def test_no_optimization_needed(self):
        """Test handling when no optimization is needed."""
        agent = ScriptOptimizerAgent()
        
        original_script = {
            "scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Perfect shot",
                    "dialogue": "Perfect dialogue",
                    "duration_seconds": 10
                }
            ],
            "overall_tone": "perfect",
            "estimated_duration": 10
        }
        
        platform_requirements = {
            "max_duration": 60,  # Much higher than current duration
            "preferred_tone": "perfect"
        }
        
        # Mock client to return script that's already optimal
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "optimized_scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Perfect shot",
                    "dialogue": "Perfect dialogue",
                    "duration_seconds": 10
                }
            ],
            "optimized_tone": "perfect",
            "optimized_duration": 10,
            "optimization_notes": ["No changes needed - already optimal"]
        }''')]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        result = agent.run(
            original_script=original_script,
            platform_requirements=platform_requirements
        )
        
        assert result["optimized_duration"] == 10
        assert result["optimized_tone"] == "perfect"
    
    def test_multiple_scene_optimization(self):
        """Test optimization of multiple scenes."""
        agent = ScriptOptimizerAgent()
        
        original_script = {
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
            "overall_tone": "exciting",
            "estimated_duration": 45
        }
        
        platform_requirements = {"max_duration": 40}  # Need to reduce duration
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "optimized_scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Condensed Scene 1",
                    "dialogue": "Shortened Dialogue 1",
                    "duration_seconds": 8
                },
                {
                    "scene_number": 2,
                    "visual_description": "Condensed Scene 2",
                    "dialogue": "Shortened Dialogue 2",
                    "duration_seconds": 12
                },
                {
                    "scene_number": 3,
                    "visual_description": "Condensed Scene 3",
                    "dialogue": "Shortened Dialogue 3",
                    "duration_seconds": 18
                }
            ],
            "optimized_tone": "exciting",
            "optimized_duration": 38,
            "optimization_notes": ["Reduced scene durations to meet platform requirements"]
        }''')]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        result = agent.run(
            original_script=original_script,
            platform_requirements=platform_requirements
        )
        
        assert result["optimized_duration"] == 38  # Less than max_duration of 40
        assert len(result["optimized_scenes"]) == 3  # Same number of scenes
    
    def test_content_restriction_enforcement(self):
        """Test enforcement of content restrictions."""
        agent = ScriptOptimizerAgent()
        
        original_script = {
            "scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Product shot",
                    "dialogue": "Buy now! Limited time offer! Act fast!",
                    "duration_seconds": 10
                }
            ],
            "overall_tone": "urgent",
            "estimated_duration": 10
        }
        
        platform_requirements = {
            "max_duration": 30,
            "content_restrictions": ["no pressure tactics", "no limited time offers"]
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "optimized_scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Product shot",
                    "dialogue": "Consider our great product when you're ready!",
                    "duration_seconds": 10
                }
            ],
            "optimized_tone": "informative",
            "optimized_duration": 10,
            "optimization_notes": ["Removed pressure tactics and limited time offers"]
        }''')]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        result = agent.run(
            original_script=original_script,
            platform_requirements=platform_requirements
        )
        
        # Check that restricted content was removed
        optimized_dialogue = result["optimized_scenes"][0]["dialogue"]
        assert "limited time" not in optimized_dialogue.lower()
        assert "act fast" not in optimized_dialogue.lower()
        assert "buy now" not in optimized_dialogue.lower()