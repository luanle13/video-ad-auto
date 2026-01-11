from unittest.mock import MagicMock, patch
import pytest
from src.agents.script_reviewer import ScriptReviewerAgent  # Assuming the agent is in src.agents.script_reviewer


class TestScriptReviewerAgent:
    
    def test_approved_response_parsing(self):
        """Test parsing of approved response."""
        agent = ScriptReviewerAgent()
        
        response_data = {
            "approved": True,
            "feedback": "Script looks great! Good pacing and clear messaging.",
            "compliance_issues": [],
            "suggestions": ["Consider adding a stronger call to action"]
        }
        
        parsed = agent.parse_response(response_data)
        
        assert parsed["approved"] == True
        assert "feedback" in parsed
        assert "compliance_issues" in parsed
        assert "suggestions" in parsed
        assert len(parsed["compliance_issues"]) == 0
        assert len(parsed["suggestions"]) == 1
    
    def test_rejected_response_parsing(self):
        """Test parsing of rejected response."""
        agent = ScriptReviewerAgent()
        
        response_data = {
            "approved": False,
            "feedback": "Script has compliance issues that need to be addressed.",
            "compliance_issues": [
                "Exaggerated health claims in scene 2",
                "Missing disclosure in scene 3"
            ],
            "suggestions": [
                "Reword health claims to be more accurate",
                "Add required disclosure statement"
            ]
        }
        
        parsed = agent.parse_response(response_data)
        
        assert parsed["approved"] == False
        assert "feedback" in parsed
        assert "compliance_issues" in parsed
        assert "suggestions" in parsed
        assert len(parsed["compliance_issues"]) == 2
        assert len(parsed["suggestions"]) == 2
    
    def test_compliance_failure_forces_rejection(self):
        """Test that compliance failures force rejection."""
        agent = ScriptReviewerAgent()
        
        # Response with compliance issues should result in rejection
        response_data = {
            "approved": True,  # Incorrectly marked as approved
            "feedback": "Good script",
            "compliance_issues": ["Major compliance violation"],
            "suggestions": []
        }
        
        parsed = agent.parse_response(response_data)
        
        # Even if approved is True in the response, presence of compliance issues should override
        assert parsed["approved"] == False
        assert len(parsed["compliance_issues"]) == 1
        assert "compliance_issues" in parsed["feedback"].lower() or "needs_revision" in parsed["feedback"].lower()
    
    def test_feedback_categorization(self):
        """Test that feedback is categorized properly."""
        agent = ScriptReviewerAgent()
        
        response_data = {
            "approved": False,
            "feedback": "Pacing issues in scenes 1-3, compliance violations in scene 5, unclear messaging in scene 7",
            "compliance_issues": ["Compliance issue in scene 5"],
            "suggestions": [
                "Slow down pacing in opening scenes",
                "Clarify messaging in final scene"
            ]
        }
        
        parsed = agent.parse_response(response_data)
        
        # Check that feedback contains the original feedback
        assert "pacing" in parsed["feedback"].lower()
        assert "compliance" in parsed["feedback"].lower()
        assert "messaging" in parsed["feedback"].lower()
        
        # Check that suggestions are preserved
        assert len(parsed["suggestions"]) == 2
    
    def test_run_success_approved(self):
        """Test successful run with approved script."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "approved": true,
            "feedback": "Script is excellent and compliant.",
            "compliance_issues": [],
            "suggestions": ["Minor typo in scene 2"]
        }''')]
        mock_client.messages.create.return_value = mock_response
        
        agent = ScriptReviewerAgent(client=mock_client)
        
        script = {
            "scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Product shot",
                    "dialogue": "Check out our amazing product!",
                    "duration_seconds": 10
                }
            ],
            "overall_tone": "exciting",
            "estimated_duration": 10
        }
        
        result = agent.run(script=script)
        
        assert result["approved"] == True
        assert "feedback" in result
        assert len(result["compliance_issues"]) == 0
        assert len(result["suggestions"]) == 1
    
    def test_run_success_rejected(self):
        """Test successful run with rejected script."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "approved": false,
            "feedback": "Script has compliance issues.",
            "compliance_issues": ["Exaggerated claims in scene 1"],
            "suggestions": ["Rephrase claims to be more accurate"]
        }''')]
        mock_client.messages.create.return_value = mock_response
        
        agent = ScriptReviewerAgent(client=mock_client)
        
        script = {
            "scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Product shot",
                    "dialogue": "This will cure all your problems!",
                    "duration_seconds": 10
                }
            ],
            "overall_tone": "exciting",
            "estimated_duration": 10
        }
        
        result = agent.run(script=script)
        
        assert result["approved"] == False
        assert "feedback" in result
        assert len(result["compliance_issues"]) == 1
        assert len(result["suggestions"]) == 1
    
    def test_empty_script_handling(self):
        """Test handling of empty script."""
        agent = ScriptReviewerAgent()
        
        response_data = {
            "approved": False,
            "feedback": "No content to review.",
            "compliance_issues": ["Script is empty"],
            "suggestions": ["Add content to the script"]
        }
        
        parsed = agent.parse_response(response_data)
        
        assert parsed["approved"] == False
        assert len(parsed["compliance_issues"]) >= 1
        assert len(parsed["suggestions"]) >= 1
    
    def test_multiple_compliance_issues(self):
        """Test handling of multiple compliance issues."""
        agent = ScriptReviewerAgent()
        
        response_data = {
            "approved": False,
            "feedback": "Multiple issues found.",
            "compliance_issues": [
                "Issue 1: Exaggerated claim in scene 1",
                "Issue 2: Missing disclosure in scene 3",
                "Issue 3: Copyright concern in scene 5",
                "Issue 4: Inappropriate content in scene 7",
                "Issue 5: Misleading pricing in scene 9"
            ],
            "suggestions": [
                "Rephrase claim in scene 1",
                "Add disclosure to scene 3",
                "Review copyrighted material in scene 5",
                "Modify content in scene 7",
                "Correct pricing info in scene 9"
            ]
        }
        
        parsed = agent.parse_response(response_data)
        
        assert parsed["approved"] == False
        assert len(parsed["compliance_issues"]) == 5
        assert len(parsed["suggestions"]) == 5
    
    def test_no_issues_found(self):
        """Test response when no issues are found."""
        agent = ScriptReviewerAgent()
        
        response_data = {
            "approved": True,
            "feedback": "Perfect script, no issues found!",
            "compliance_issues": [],
            "suggestions": []
        }
        
        parsed = agent.parse_response(response_data)
        
        assert parsed["approved"] == True
        assert len(parsed["compliance_issues"]) == 0
        assert len(parsed["suggestions"]) == 0
        assert "perfect" in parsed["feedback"].lower() or "no issues" in parsed["feedback"].lower()
    
    def test_build_prompt_with_script_details(self):
        """Test that prompt includes script details."""
        agent = ScriptReviewerAgent()
        
        script = {
            "scenes": [
                {
                    "scene_number": 1,
                    "visual_description": "Product introduction",
                    "dialogue": "Introducing our amazing product!",
                    "duration_seconds": 10
                }
            ],
            "overall_tone": "exciting",
            "estimated_duration": 10
        }
        
        platform_requirements = {
            "content_policy": "No exaggerated claims",
            "duration_limits": {"min": 5, "max": 60}
        }
        
        prompt = agent.build_user_prompt(
            script=script,
            platform_requirements=platform_requirements
        )
        
        # Check that script details are included in the prompt
        assert "amazing product" in prompt
        assert "exciting" in prompt
        assert "10" in prompt  # duration
        assert "introducing" in prompt
        assert "exaggerated claims" in prompt.lower()
        assert "policy" in prompt.lower()