"""Tests for agent Lambda handler."""

import os
from typing import Any
from unittest.mock import Mock, patch

import pytest

from src.agents.handler import AGENTS, STATUS_MAP, _build_input, handler


# Set fake API key for tests
@pytest.fixture(autouse=True)
def mock_anthropic_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set fake Anthropic API key for all tests."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key-1234567890")


@pytest.fixture
def base_event() -> dict[str, Any]:
    """Base event structure."""
    return {
        "user_id": "usr_test_123",
        "job_id": "job_test_456",
        "product": {
            "id": "prod_789",
            "title": "Wireless Earbuds Pro",
            "description": "High-quality wireless earbuds with ANC",
            "price": "799,000 VND",
            "url": "https://example.com/product",
            "image_keys": ["s3://bucket/image1.jpg", "s3://bucket/image2.jpg"],
        },
        "context": {},
        "adjustments": {},
    }


@pytest.fixture
def analyze_event(base_event: dict[str, Any]) -> dict[str, Any]:
    """Event for analyze task."""
    event = base_event.copy()
    event["task"] = "analyze"
    return event


@pytest.fixture
def generate_event(base_event: dict[str, Any]) -> dict[str, Any]:
    """Event for generate task."""
    event = base_event.copy()
    event["task"] = "generate"
    event["context"] = {
        "analyze": {
            "output": {
                "key_features": ["Active noise cancellation", "40-hour battery"],
                "unique_selling_points": ["Best ANC at this price"],
                "target_audience": "Tech-savvy millennials",
                "visual_elements": ["Sleek black design", "Compact case"],
                "price_positioning": "mid-range",
                "suggested_hooks": ["$30 earbuds that rival AirPods"],
            }
        }
    }
    event["adjustments"] = {
        "target_duration": 45,
        "tone": "energetic",
    }
    return event


@pytest.fixture
def optimize_event(base_event: dict[str, Any]) -> dict[str, Any]:
    """Event for optimize task."""
    event = base_event.copy()
    event["task"] = "optimize"
    event["context"] = {
        "generate": {
            "output": {
                "hook": "Check out these earbuds",
                "scenes": [
                    {"scene_number": 1, "duration_seconds": 10, "visual_description": "Product reveal", "voiceover_text": "Check out these earbuds"},
                    {"scene_number": 2, "duration_seconds": 10, "visual_description": "Feature showcase", "voiceover_text": "Great sound quality"},
                    {"scene_number": 3, "duration_seconds": 10, "visual_description": "CTA", "voiceover_text": "Buy now"},
                ],
                "call_to_action": "Link in bio",
                "full_voiceover_text": "Check out these earbuds. Great sound quality. Buy now.",
                "estimated_duration_seconds": 30,
            }
        }
    }
    event["adjustments"] = {
        "primary_platform": "tiktok",
        "pacing": "fast",
    }
    return event


@pytest.fixture
def review_event(base_event: dict[str, Any]) -> dict[str, Any]:
    """Event for review task."""
    event = base_event.copy()
    event["task"] = "review"
    event["context"] = {
        "analyze": {
            "output": {
                "key_features": ["Active noise cancellation", "40-hour battery"],
                "unique_selling_points": ["Best ANC at this price"],
            }
        },
        "optimize": {
            "output": {
                "optimized_hook": "Wait... $30 earbuds with WHAT features? 🤯",
                "optimized_scenes": [
                    {"scene_number": 1, "duration_seconds": 3, "visual_description": "Dramatic reveal", "voiceover_text": "Wait... $30 earbuds with WHAT features?"},
                    {"scene_number": 2, "duration_seconds": 7, "visual_description": "Feature showcase", "voiceover_text": "Active noise cancellation, 40 hour battery"},
                    {"scene_number": 3, "duration_seconds": 5, "visual_description": "CTA", "voiceover_text": "Link in bio"},
                ],
                "optimized_cta": "Link in bio before they sell out 🏃",
                "optimized_voiceover": "Wait... $30 earbuds with WHAT features? Active noise cancellation, 40 hour battery. Link in bio before they sell out.",
                "estimated_duration_seconds": 15,
                "pacing_notes": ["Reduced hook to 3s", "Added urgency to CTA"],
                "engagement_hooks": ["Curiosity gap", "FOMO"],
            }
        },
    }
    event["adjustments"] = {
        "primary_platform": "tiktok",
        "brand_voice": "Casual and enthusiastic",
    }
    return event


@pytest.fixture
def mock_agent_output() -> Mock:
    """Mock agent output."""
    output = Mock()
    output.success = True
    output.model_dump.return_value = {
        "success": True,
        "data": "test_output",
    }
    return output


class TestAgentRegistry:
    """Tests for agent registry."""

    def test_agents_registered(self) -> None:
        """Test all required agents are registered."""
        assert "analyze" in AGENTS
        assert "generate" in AGENTS
        assert "optimize" in AGENTS
        assert "review" in AGENTS

    def test_status_map_defined(self) -> None:
        """Test status map covers all tasks."""
        for task in AGENTS.keys():
            assert task in STATUS_MAP


class TestBuildInput:
    """Tests for _build_input function."""

    def test_build_analyze_input(self, analyze_event: dict[str, Any]) -> None:
        """Test building input for analyze task."""
        from src.agents.product_analyzer import ProductAnalyzerInput

        input_data = _build_input("analyze", analyze_event, ProductAnalyzerInput)

        assert isinstance(input_data, ProductAnalyzerInput)
        assert input_data.job_id == "job_test_456"
        assert input_data.user_id == "usr_test_123"
        assert input_data.title == "Wireless Earbuds Pro"
        assert input_data.description == "High-quality wireless earbuds with ANC"
        assert input_data.price == "799,000 VND"
        assert len(input_data.image_keys) == 2

    def test_build_generate_input(self, generate_event: dict[str, Any]) -> None:
        """Test building input for generate task."""
        from src.agents.script_generator import ScriptGeneratorInput

        input_data = _build_input("generate", generate_event, ScriptGeneratorInput)

        assert isinstance(input_data, ScriptGeneratorInput)
        assert input_data.job_id == "job_test_456"
        assert input_data.user_id == "usr_test_123"
        assert input_data.product_title == "Wireless Earbuds Pro"
        assert input_data.price == "799,000 VND"
        assert len(input_data.key_features) == 2
        assert len(input_data.unique_selling_points) == 1
        assert input_data.target_audience == "Tech-savvy millennials"
        assert input_data.target_duration == 45
        assert input_data.tone == "energetic"

    def test_build_optimize_input(self, optimize_event: dict[str, Any]) -> None:
        """Test building input for optimize task."""
        from src.agents.script_optimizer import ScriptOptimizerInput

        input_data = _build_input("optimize", optimize_event, ScriptOptimizerInput)

        assert isinstance(input_data, ScriptOptimizerInput)
        assert input_data.job_id == "job_test_456"
        assert input_data.hook == "Check out these earbuds"
        assert len(input_data.scenes) == 3
        assert input_data.call_to_action == "Link in bio"
        assert input_data.primary_platform == "tiktok"
        assert input_data.pacing == "fast"

    def test_build_review_input(self, review_event: dict[str, Any]) -> None:
        """Test building input for review task."""
        from src.agents.script_reviewer import ScriptReviewerInput

        input_data = _build_input("review", review_event, ScriptReviewerInput)

        assert isinstance(input_data, ScriptReviewerInput)
        assert input_data.job_id == "job_test_456"
        assert input_data.hook == "Wait... $30 earbuds with WHAT features? 🤯"
        assert len(input_data.scenes) == 3
        assert input_data.product_title == "Wireless Earbuds Pro"
        assert len(input_data.key_features) == 2
        assert len(input_data.pacing_notes) == 2
        assert len(input_data.engagement_hooks) == 2
        assert input_data.target_platform == "tiktok"
        assert input_data.brand_voice == "Casual and enthusiastic"

    def test_build_input_with_missing_context(self, base_event: dict[str, Any]) -> None:
        """Test building input handles missing context gracefully."""
        from src.agents.script_generator import ScriptGeneratorInput

        event = base_event.copy()
        event["task"] = "generate"
        # No context provided

        input_data = _build_input("generate", event, ScriptGeneratorInput)

        # Should use empty defaults
        assert input_data.key_features == []
        assert input_data.unique_selling_points == []
        assert input_data.target_audience == ""

    def test_build_input_unknown_task(self, base_event: dict[str, Any]) -> None:
        """Test building input for unknown task raises error."""
        from src.agents.product_analyzer import ProductAnalyzerInput

        with pytest.raises(ValueError, match="Input building not implemented"):
            _build_input("unknown_task", base_event, ProductAnalyzerInput)


class TestHandler:
    """Tests for Lambda handler."""

    @patch("src.agents.handler.get_db")
    @patch("src.agents.handler.ProductAnalyzerAgent")
    def test_handler_analyze_success(
        self,
        mock_agent_class: Mock,
        mock_get_db: Mock,
        analyze_event: dict[str, Any],
        mock_agent_output: Mock,
    ) -> None:
        """Test handler for analyze task."""
        # Set up mock agent instance
        mock_agent = Mock()
        mock_agent.run.return_value = mock_agent_output
        mock_agent_class.return_value = mock_agent

        # Set up mock DB
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        result = handler(analyze_event, None)

        # Check agent was instantiated
        mock_agent_class.assert_called_once()

        # Check status update
        mock_db.update_job_status.assert_called_once_with(
            "usr_test_123",
            "job_test_456",
            "ANALYZING",
        )

        # Check agent was called
        mock_agent.run.assert_called_once()
        call_args = mock_agent.run.call_args
        assert call_args[0][0].job_id == "job_test_456"
        assert call_args[0][0].title == "Wireless Earbuds Pro"

        # Check output stored
        mock_db.update_job_step_output.assert_called_once_with(
            "usr_test_123",
            "job_test_456",
            "analyze",
            {"success": True, "data": "test_output"},
        )

        # Check return value
        assert result["task"] == "analyze"
        assert result["success"] is True
        assert result["output"]["success"] is True

    @patch("src.agents.handler.get_db")
    @patch("src.agents.handler.ScriptGeneratorAgent")
    def test_handler_generate_success(
        self,
        mock_agent_class: Mock,
        mock_get_db: Mock,
        generate_event: dict[str, Any],
        mock_agent_output: Mock,
    ) -> None:
        """Test handler for generate task."""
        mock_agent = Mock()
        mock_agent.run.return_value = mock_agent_output
        mock_agent_class.return_value = mock_agent

        mock_db = Mock()
        mock_get_db.return_value = mock_db

        result = handler(generate_event, None)

        # Check status update
        mock_db.update_job_status.assert_called_once_with(
            "usr_test_123",
            "job_test_456",
            "SCRIPTING",
        )

        # Check agent was called with context
        mock_agent.run.assert_called_once()
        call_args = mock_agent.run.call_args
        assert call_args[0][1] == generate_event["context"]

        # Check return value
        assert result["task"] == "generate"
        assert result["success"] is True

    @patch("src.agents.handler.get_db")
    @patch("src.agents.handler.ScriptOptimizerAgent")
    def test_handler_optimize_success(
        self,
        mock_agent_class: Mock,
        mock_get_db: Mock,
        optimize_event: dict[str, Any],
        mock_agent_output: Mock,
    ) -> None:
        """Test handler for optimize task."""
        mock_agent = Mock()
        mock_agent.run.return_value = mock_agent_output
        mock_agent_class.return_value = mock_agent

        mock_db = Mock()
        mock_get_db.return_value = mock_db

        result = handler(optimize_event, None)

        assert result["task"] == "optimize"
        assert result["success"] is True

    @patch("src.agents.handler.get_db")
    @patch("src.agents.handler.ScriptReviewerAgent")
    def test_handler_review_success(
        self,
        mock_agent_class: Mock,
        mock_get_db: Mock,
        review_event: dict[str, Any],
        mock_agent_output: Mock,
    ) -> None:
        """Test handler for review task."""
        mock_agent = Mock()
        mock_agent.run.return_value = mock_agent_output
        mock_agent_class.return_value = mock_agent

        mock_db = Mock()
        mock_get_db.return_value = mock_db

        result = handler(review_event, None)

        assert result["task"] == "review"
        assert result["success"] is True

        # Verify brand voice was passed
        call_args = mock_agent.run.call_args
        input_data = call_args[0][0]
        assert input_data.brand_voice == "Casual and enthusiastic"

    @patch("src.agents.handler.get_db")
    def test_handler_unknown_task(
        self,
        mock_get_db: Mock,
        base_event: dict[str, Any],
    ) -> None:
        """Test handler with unknown task."""
        event = base_event.copy()
        event["task"] = "unknown_task"

        with pytest.raises(ValueError, match="Unknown task"):
            handler(event, None)

    @patch("src.agents.handler.get_db")
    @patch("src.agents.handler.ProductAnalyzerAgent")
    def test_handler_agent_failure(
        self,
        mock_agent_class: Mock,
        mock_get_db: Mock,
        analyze_event: dict[str, Any],
    ) -> None:
        """Test handler when agent raises exception."""
        mock_agent = Mock()
        mock_agent.run.side_effect = Exception("Agent processing failed")
        mock_agent_class.return_value = mock_agent

        mock_db = Mock()
        mock_get_db.return_value = mock_db

        with pytest.raises(Exception):
            handler(analyze_event, None)

        # Check job was marked as failed
        mock_db.update_job_status.assert_any_call(
            "usr_test_123",
            "job_test_456",
            "FAILED",
            error_message="Agent processing failed",
        )

    @patch("src.agents.handler.get_db")
    @patch("src.agents.handler.ProductAnalyzerAgent")
    def test_handler_logs_execution(
        self,
        mock_agent_class: Mock,
        mock_get_db: Mock,
        analyze_event: dict[str, Any],
        mock_agent_output: Mock,
    ) -> None:
        """Test handler logs execution details."""
        mock_agent = Mock()
        mock_agent.run.return_value = mock_agent_output
        mock_agent.__class__.__name__ = "ProductAnalyzerAgent"
        mock_agent_class.return_value = mock_agent

        mock_db = Mock()
        mock_get_db.return_value = mock_db

        with patch("src.agents.handler.logger") as mock_logger:
            handler(analyze_event, None)

            # Check logging calls
            assert mock_logger.info.call_count >= 3
            call_args_list = [call[1] for call in mock_logger.info.call_args_list]

            # Check specific log messages
            assert any("agent_handler_invoked" in str(call) for call in call_args_list)
            assert any("job_status_updated" in str(call) for call in call_args_list)
            assert any("agent_completed" in str(call) for call in call_args_list)

    @patch("src.agents.handler.get_db")
    @patch("src.agents.handler.ProductAnalyzerAgent")
    def test_handler_context_passed_to_agent(
        self,
        mock_agent_class: Mock,
        mock_get_db: Mock,
        analyze_event: dict[str, Any],
        mock_agent_output: Mock,
    ) -> None:
        """Test handler passes context to agent.run()."""
        mock_agent = Mock()
        mock_agent.run.return_value = mock_agent_output
        mock_agent_class.return_value = mock_agent

        mock_db = Mock()
        mock_get_db.return_value = mock_db

        custom_context = {"custom_key": "custom_value"}
        analyze_event["context"] = custom_context

        handler(analyze_event, None)

        # Check context was passed
        call_args = mock_agent.run.call_args
        assert call_args[0][1] == custom_context

    @patch("src.agents.handler.get_db")
    @patch("src.agents.handler.ScriptGeneratorAgent")
    def test_handler_adjustments_applied(
        self,
        mock_agent_class: Mock,
        mock_get_db: Mock,
        generate_event: dict[str, Any],
        mock_agent_output: Mock,
    ) -> None:
        """Test handler applies user adjustments to input."""
        mock_agent = Mock()
        mock_agent.run.return_value = mock_agent_output
        mock_agent_class.return_value = mock_agent

        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Add custom adjustments
        generate_event["adjustments"]["target_duration"] = 60
        generate_event["adjustments"]["tone"] = "professional"
        generate_event["adjustments"]["emphasis"] = "features"

        handler(generate_event, None)

        # Check adjustments were applied
        call_args = mock_agent.run.call_args
        input_data = call_args[0][0]
        assert input_data.target_duration == 60
        assert input_data.tone == "professional"
        assert input_data.emphasis == "features"
