"""Unit tests for Agent Handler."""
from unittest.mock import MagicMock, patch

import pytest

from src.agents.handler import AGENTS, STATUS_MAP, _build_input, handler


def test_agents_mapping():
    """Test that AGENTS mapping contains all expected agents."""
    expected_agents = {"analyze", "market_insight", "generate", "optimize", "review"}
    assert set(AGENTS.keys()) == expected_agents
    
    # Verify each agent has both class and input
    for task, (agent_class, input_class) in AGENTS.items():
        assert hasattr(agent_class, '__name__')
        assert hasattr(input_class, '__name__')


def test_status_map():
    """Test that STATUS_MAP contains all expected tasks."""
    expected_tasks = {"analyze", "market_insight", "generate", "optimize", "review"}
    assert set(STATUS_MAP.keys()) == expected_tasks
    
    # Verify status values are valid
    for status in STATUS_MAP.values():
        assert status in ["ANALYZING", "SCRIPTING", "PROCESSING"]


def test_build_input_analyze():
    """Test _build_input for analyze task."""
    event = {
        "job_id": "job123",
        "user_id": "user456",
        "product": {
            "title": "Test Product",
            "description": "Test Description",
            "price": "$19.99",
            "image_keys": ["img1.jpg", "img2.jpg"]
        }
    }
    
    input_class = AGENTS["analyze"][1]  # ProductAnalyzerInput
    input_data = _build_input("analyze", event, input_class)
    
    assert input_data.job_id == "job123"
    assert input_data.user_id == "user456"
    assert input_data.title == "Test Product"
    assert input_data.description == "Test Description"
    assert input_data.price == "$19.99"
    assert input_data.image_keys == ["img1.jpg", "img2.jpg"]


def test_build_input_market_insight():
    """Test _build_input for market_insight task."""
    event = {
        "job_id": "job123",
        "user_id": "user456",
        "context": {
            "analyze": {
                "output": {
                    "product_category": "Electronics",
                    "target_audience": "Young professionals",
                    "key_features": ["Wireless", "Fast charging"],
                    "price_positioning": "premium"
                }
            }
        }
    }
    
    input_class = AGENTS["market_insight"][1]  # MarketInsightInput
    input_data = _build_input("market_insight", event, input_class)
    
    assert input_data.job_id == "job123"
    assert input_data.user_id == "user456"
    assert input_data.product_category == "Electronics"
    assert input_data.target_audience == "Young professionals"
    assert input_data.key_features == ["Wireless", "Fast charging"]
    assert input_data.price_positioning == "premium"


def test_build_input_generate():
    """Test _build_input for generate task."""
    event = {
        "job_id": "job123",
        "user_id": "user456",
        "product": {
            "title": "Test Product",
            "price": "$19.99"
        },
        "context": {
            "analyze": {
                "output": {
                    "key_features": ["Feature 1", "Feature 2"],
                    "unique_selling_points": ["USP 1"],
                    "target_audience": "Young people",
                    "visual_elements": ["Element 1"],
                    "price_positioning": "mid-range",
                    "suggested_hooks": ["Hook 1"]
                }
            },
            "market_insight": {
                "output": {
                    "content_angles": ["Angle 1"],
                    "trending_formats": ["Format 1"],
                    "platform_tips": {"tiktok": "Tip 1"},
                    "suggested_music_style": "Upbeat"
                }
            }
        },
        "adjustments": {
            "target_duration": 30,
            "tone": "energetic",
            "emphasis": "quality"
        }
    }
    
    input_class = AGENTS["generate"][1]  # ScriptGeneratorInput
    input_data = _build_input("generate", event, input_class)
    
    assert input_data.job_id == "job123"
    assert input_data.user_id == "user456"
    assert input_data.product_title == "Test Product"
    assert input_data.price == "$19.99"
    assert input_data.key_features == ["Feature 1", "Feature 2"]
    assert input_data.content_angles == ["Angle 1"]
    assert input_data.trending_formats == ["Format 1"]
    assert input_data.target_duration == 30
    assert input_data.tone == "energetic"
    assert input_data.emphasis == "quality"


def test_build_input_optimize():
    """Test _build_input for optimize task."""
    event = {
        "job_id": "job123",
        "user_id": "user456",
        "context": {
            "generate": {
                "output": {
                    "hook": "Original hook",
                    "scenes": [{"scene_number": 1}],
                    "call_to_action": "Buy now",
                    "full_voiceover_text": "Full script",
                    "estimated_duration_seconds": 45
                }
            }
        },
        "adjustments": {
            "primary_platform": "tiktok",
            "trending_formats": ["Trend 1"],
            "platform_tips": {"tiktok": "Tip"},
            "tone": "funny",
            "pacing": "fast"
        }
    }
    
    input_class = AGENTS["optimize"][1]  # ScriptOptimizerInput
    input_data = _build_input("optimize", event, input_class)
    
    assert input_data.job_id == "job123"
    assert input_data.user_id == "user456"
    assert input_data.hook == "Original hook"
    assert input_data.scenes == [{"scene_number": 1}]
    assert input_data.primary_platform == "tiktok"
    assert input_data.trending_formats == ["Trend 1"]
    assert input_data.tone == "funny"
    assert input_data.pacing == "fast"


def test_build_input_review():
    """Test _build_input for review task."""
    event = {
        "job_id": "job123",
        "user_id": "user456",
        "product": {
            "title": "Test Product",
            "price": "$19.99"
        },
        "context": {
            "analyze": {
                "output": {
                    "key_features": ["Feature 1"],
                    "unique_selling_points": ["USP 1"]
                }
            },
            "optimize": {
                "output": {
                    "optimized_hook": "Optimized hook",
                    "optimized_scenes": [{"scene_number": 1}],
                    "optimized_cta": "Optimized CTA",
                    "optimized_voiceover": "Optimized voiceover",
                    "pacing_notes": ["Note 1"],
                    "engagement_hooks": ["Hook 1"]
                }
            }
        },
        "adjustments": {
            "primary_platform": "tiktok",
            "brand_voice": "Professional"
        }
    }
    
    input_class = AGENTS["review"][1]  # ScriptReviewerInput
    input_data = _build_input("review", event, input_class)
    
    assert input_data.job_id == "job123"
    assert input_data.user_id == "user456"
    assert input_data.hook == "Optimized hook"
    assert input_data.scenes == [{"scene_number": 1}]
    assert input_data.product_title == "Test Product"
    assert input_data.product_price == "$19.99"
    assert input_data.key_features == ["Feature 1"]
    assert input_data.target_platform == "tiktok"
    assert input_data.brand_voice == "Professional"


def test_handler_unknown_task():
    """Test handler with unknown task."""
    event = {
        "task": "unknown_task",
        "user_id": "user456",
        "job_id": "job123"
    }
    context = {}
    
    with pytest.raises(ValueError, match="Unknown task: unknown_task"):
        handler(event, context)


@patch('src.agents.handler.get_db')
@patch('src.agents.handler.AGENTS')
def test_handler_success(mock_agents, mock_get_db):
    """Test handler success case."""
    # Mock agent and input class
    mock_agent_class = MagicMock()
    mock_agent_class.__name__ = "MockAgent"  # Fix the __name__ attribute
    mock_agent_instance = MagicMock()
    mock_agent_output = MagicMock()
    mock_agent_output.success = True
    mock_agent_output.model_dump.return_value = {"result": "success", "success": True}
    mock_agent_instance.run.return_value = mock_agent_output
    mock_agent_class.return_value = mock_agent_instance

    mock_input_class = MagicMock()
    mock_input_instance = MagicMock()
    mock_input_class.return_value = mock_input_instance

    mock_agents.__getitem__.return_value = (mock_agent_class, mock_input_class)
    mock_agents.__contains__.return_value = True

    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    event = {
        "task": "analyze",
        "user_id": "user456",
        "job_id": "job123",
        "product": {
            "title": "Test Product",
            "description": "Test Description",
            "price": "$19.99",
            "image_keys": ["img1.jpg"]
        }
    }
    context = {}

    result = handler(event, context)

    # Verify the result
    assert result["task"] == "analyze"
    assert result["success"] is True
    assert result["output"] == {"result": "success", "success": True}

    # Verify DB calls
    mock_db.update_job_status.assert_called()
    mock_db.update_job_step_output.assert_called()


@patch('src.agents.handler.get_db')
@patch('src.agents.handler.AGENTS')
def test_handler_agent_error(mock_agents, mock_get_db):
    """Test handler when agent throws an error."""
    # Mock agent to throw an exception
    mock_agent_class = MagicMock()
    mock_agent_class.__name__ = "MockAgent"  # Fix the __name__ attribute
    mock_agent_instance = MagicMock()
    mock_agent_class.return_value = mock_agent_instance
    mock_agent_instance.run.side_effect = Exception("Agent error")

    mock_input_class = MagicMock()
    mock_input_instance = MagicMock()
    mock_input_class.return_value = mock_input_instance

    mock_agents.__getitem__.return_value = (mock_agent_class, mock_input_class)
    mock_agents.__contains__.return_value = True

    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    event = {
        "task": "analyze",
        "user_id": "user456",
        "job_id": "job123",
        "product": {
            "title": "Test Product",
            "description": "Test Description",
            "price": "$19.99",
            "image_keys": ["img1.jpg"]
        }
    }
    context = {}

    with pytest.raises(Exception, match="Agent error"):
        handler(event, context)

    # Verify DB was called to update status to FAILED
    mock_db.update_job_status.assert_called_with("user456", "job123", "FAILED", error_message="Agent error")