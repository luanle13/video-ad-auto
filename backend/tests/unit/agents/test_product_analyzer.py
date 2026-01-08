"""Unit tests for Product Analyzer agent."""
import base64
from typing import Any
from unittest.mock import Mock, patch

import pytest
from anthropic.types import Message, Usage
from anthropic.types.text_block import TextBlock

from src.agents.product_analyzer import (
    ProductAnalyzerAgent,
    ProductAnalyzerInput,
    ProductAnalyzerOutput,
)


@pytest.fixture
def sample_product_input() -> ProductAnalyzerInput:
    """Create sample product analyzer input."""
    return ProductAnalyzerInput(
        job_id="job_123",
        user_id="user_456",
        title="Wireless Bluetooth Headphones",
        description="Premium noise-cancelling wireless headphones with 30-hour battery life",
        price="1,299,000 VND",
        image_keys=["products/user_456/headphones_1.jpg", "products/user_456/headphones_2.jpg"],
    )


@pytest.fixture
def sample_analysis_response() -> dict[str, Any]:
    """Create sample analysis response."""
    return {
        "key_features": [
            "Active noise cancellation",
            "30-hour battery life",
            "Wireless Bluetooth 5.0",
            "Premium sound quality",
        ],
        "unique_selling_points": [
            "Industry-leading 30-hour battery",
            "Advanced noise cancellation technology",
            "Premium materials and build quality",
        ],
        "target_audience": "Young professionals and commuters aged 25-40 who value quality audio and comfort",
        "visual_elements": [
            "Sleek matte black finish",
            "Foldable design",
            "LED battery indicator",
            "Cushioned ear cups",
        ],
        "product_category": "Audio & Electronics",
        "price_positioning": "mid-range",
        "suggested_hooks": [
            "Silence the world with 30 hours of premium sound",
            "Your commute just got quieter",
            "Premium audio without the premium price tag",
        ],
        "raw_analysis": "These wireless headphones target the mid-range market with premium features...",
    }


@pytest.fixture
def mock_anthropic_response(sample_analysis_response: dict[str, Any]) -> Message:
    """Create mock Anthropic API response with vision."""
    import json

    return Message(
        id="msg_vision_123",
        type="message",
        role="assistant",
        content=[
            TextBlock(
                type="text",
                text=f"```json\n{json.dumps(sample_analysis_response, indent=2)}\n```",
            )
        ],
        model="claude-sonnet-4-20250514",
        stop_reason="end_turn",
        usage=Usage(
            input_tokens=1500,  # Higher due to images
            output_tokens=400,
        ),
    )


@pytest.fixture
def mock_image_data() -> bytes:
    """Create mock image data."""
    # Simple 1x1 red pixel PNG
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    )


class TestProductAnalyzerInput:
    """Tests for ProductAnalyzerInput model."""

    def test_valid_input(self) -> None:
        """Test valid product analyzer input."""
        input_data = ProductAnalyzerInput(
            job_id="job_123",
            user_id="user_456",
            title="Test Product",
            description="Test description",
            price="100 VND",
            image_keys=["image1.jpg"],
        )

        assert input_data.job_id == "job_123"
        assert input_data.title == "Test Product"
        assert len(input_data.image_keys) == 1

    def test_min_images_validation(self) -> None:
        """Test minimum images validation."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProductAnalyzerInput(
                job_id="job_123",
                user_id="user_456",
                title="Test",
                description="Test",
                price="100",
                image_keys=[],  # Empty list should fail
            )

    def test_max_images_validation(self) -> None:
        """Test maximum images validation."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProductAnalyzerInput(
                job_id="job_123",
                user_id="user_456",
                title="Test",
                description="Test",
                price="100",
                image_keys=[f"image{i}.jpg" for i in range(10)],  # Too many
            )


class TestProductAnalyzerOutput:
    """Tests for ProductAnalyzerOutput model."""

    def test_default_values(self) -> None:
        """Test default values in output."""
        output = ProductAnalyzerOutput()

        assert output.success is True
        assert output.key_features == []
        assert output.unique_selling_points == []
        assert output.target_audience == ""
        assert output.visual_elements == []
        assert output.product_category == ""
        assert output.price_positioning == ""
        assert output.suggested_hooks == []
        assert output.raw_analysis == ""

    def test_with_data(self, sample_analysis_response: dict[str, Any]) -> None:
        """Test output with full data."""
        output = ProductAnalyzerOutput(**sample_analysis_response)

        assert len(output.key_features) == 4
        assert len(output.unique_selling_points) == 3
        assert output.target_audience.startswith("Young professionals")
        assert output.price_positioning == "mid-range"
        assert len(output.suggested_hooks) == 3


class TestProductAnalyzerAgent:
    """Tests for ProductAnalyzerAgent."""

    @patch("src.agents.base.get_anthropic_client")
    def test_agent_initialization(self, mock_get_client: Mock) -> None:
        """Test agent initialization."""
        agent = ProductAnalyzerAgent()

        assert agent.name == "ProductAnalyzer"
        assert agent.model == "claude-sonnet-4-20250514"
        assert agent.temperature == 0.3
        assert agent.max_tokens == 2048

    @patch("src.agents.product_analyzer.get_storage")
    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_with_images(
        self,
        mock_get_client: Mock,
        mock_get_storage: Mock,
        sample_product_input: ProductAnalyzerInput,
        mock_image_data: bytes,
    ) -> None:
        """Test user prompt building with image fetching."""
        mock_storage = Mock()
        mock_storage.download_file.return_value = mock_image_data
        mock_get_storage.return_value = mock_storage

        agent = ProductAnalyzerAgent()
        prompt = agent.build_user_prompt(sample_product_input, {})

        # Verify prompt contains product info
        assert "Wireless Bluetooth Headphones" in prompt
        assert "1,299,000 VND" in prompt
        assert "Premium noise-cancelling" in prompt

        # Verify images were fetched
        assert mock_storage.download_file.call_count == 2
        mock_storage.download_file.assert_any_call("images", "products/user_456/headphones_1.jpg")
        mock_storage.download_file.assert_any_call("images", "products/user_456/headphones_2.jpg")

        # Verify images were stored
        assert hasattr(agent, "_pending_images")
        assert len(agent._pending_images) == 2

        # Verify image format
        image = agent._pending_images[0]
        assert image["type"] == "image"
        assert image["source"]["type"] == "base64"
        assert image["source"]["media_type"] == "image/jpeg"
        assert len(image["source"]["data"]) > 0

    @patch("src.agents.product_analyzer.get_storage")
    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_limits_images(
        self,
        mock_get_client: Mock,
        mock_get_storage: Mock,
        mock_image_data: bytes,
    ) -> None:
        """Test that only 3 images are used even if more provided."""
        mock_storage = Mock()
        mock_storage.download_file.return_value = mock_image_data
        mock_get_storage.return_value = mock_storage

        input_data = ProductAnalyzerInput(
            job_id="job_123",
            user_id="user_456",
            title="Test",
            description="Test",
            price="100",
            image_keys=[f"image{i}.jpg" for i in range(5)],
        )

        agent = ProductAnalyzerAgent()
        agent.build_user_prompt(input_data, {})

        # Should only fetch 3 images
        assert mock_storage.download_file.call_count == 3
        assert len(agent._pending_images) == 3

    @patch("src.agents.product_analyzer.get_storage")
    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_handles_image_errors(
        self,
        mock_get_client: Mock,
        mock_get_storage: Mock,
        sample_product_input: ProductAnalyzerInput,
    ) -> None:
        """Test that image fetch errors are handled gracefully."""
        mock_storage = Mock()
        mock_storage.download_file.side_effect = [
            b"valid_image_data",
            Exception("S3 error"),
        ]
        mock_get_storage.return_value = mock_storage

        agent = ProductAnalyzerAgent()
        prompt = agent.build_user_prompt(sample_product_input, {})

        # Should still build prompt with available images
        assert "Wireless Bluetooth Headphones" in prompt
        assert len(agent._pending_images) == 1  # Only one successful fetch

    @patch("src.agents.product_analyzer.get_storage")
    @patch("src.agents.base.get_anthropic_client")
    def test_build_user_prompt_detects_media_types(
        self,
        mock_get_client: Mock,
        mock_get_storage: Mock,
        mock_image_data: bytes,
    ) -> None:
        """Test media type detection from file extensions."""
        mock_storage = Mock()
        mock_storage.download_file.return_value = mock_image_data
        mock_get_storage.return_value = mock_storage

        input_data = ProductAnalyzerInput(
            job_id="job_123",
            user_id="user_456",
            title="Test",
            description="Test",
            price="100",
            image_keys=["image.png", "image.webp", "image.jpg"],
        )

        agent = ProductAnalyzerAgent()
        agent.build_user_prompt(input_data, {})

        assert agent._pending_images[0]["source"]["media_type"] == "image/png"
        assert agent._pending_images[1]["source"]["media_type"] == "image/webp"
        assert agent._pending_images[2]["source"]["media_type"] == "image/jpeg"

    @patch("src.agents.product_analyzer.get_storage")
    @patch("src.agents.base.get_anthropic_client")
    def test_successful_run_with_vision(
        self,
        mock_get_client: Mock,
        mock_get_storage: Mock,
        sample_product_input: ProductAnalyzerInput,
        mock_image_data: bytes,
        mock_anthropic_response: Message,
    ) -> None:
        """Test successful agent execution with vision API."""
        mock_storage = Mock()
        mock_storage.download_file.return_value = mock_image_data
        mock_get_storage.return_value = mock_storage

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_get_client.return_value = mock_client

        agent = ProductAnalyzerAgent()
        result = agent.run(sample_product_input)

        # Verify result structure
        assert isinstance(result, ProductAnalyzerOutput)
        assert result.success is True
        assert len(result.key_features) == 4
        assert len(result.unique_selling_points) == 3
        assert result.price_positioning == "mid-range"
        assert len(result.suggested_hooks) == 3

        # Verify API call was made with vision format
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs

        # Check content structure (images + text)
        content = call_kwargs["messages"][0]["content"]
        assert isinstance(content, list)
        assert content[0]["type"] == "image"
        assert content[-1]["type"] == "text"

    @patch("src.agents.product_analyzer.get_storage")
    @patch("src.agents.base.get_anthropic_client")
    def test_run_logs_token_usage(
        self,
        mock_get_client: Mock,
        mock_get_storage: Mock,
        sample_product_input: ProductAnalyzerInput,
        mock_image_data: bytes,
        mock_anthropic_response: Message,
    ) -> None:
        """Test that token usage is logged."""
        mock_storage = Mock()
        mock_storage.download_file.return_value = mock_image_data
        mock_get_storage.return_value = mock_storage

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_get_client.return_value = mock_client

        agent = ProductAnalyzerAgent()

        with patch.object(agent.logger, "info") as mock_log:
            agent.run(sample_product_input)

            # Find the LLM call log
            llm_call = [
                call for call in mock_log.call_args_list if call[0][0] == "agent_llm_call"
            ][0]

            assert llm_call.kwargs["input_tokens"] == 1500
            assert llm_call.kwargs["output_tokens"] == 400

    @patch("src.agents.product_analyzer.get_storage")
    @patch("src.agents.base.get_anthropic_client")
    def test_parse_response(
        self,
        mock_get_client: Mock,
        mock_get_storage: Mock,
        sample_product_input: ProductAnalyzerInput,
        sample_analysis_response: dict[str, Any],
    ) -> None:
        """Test response parsing."""
        import json

        agent = ProductAnalyzerAgent()

        response_text = f"```json\n{json.dumps(sample_analysis_response)}\n```"
        output = agent.parse_response(response_text, sample_product_input)

        assert output.success is True
        assert output.key_features == sample_analysis_response["key_features"]
        assert output.unique_selling_points == sample_analysis_response["unique_selling_points"]
        assert output.target_audience == sample_analysis_response["target_audience"]
        assert output.visual_elements == sample_analysis_response["visual_elements"]
        assert output.product_category == sample_analysis_response["product_category"]
        assert output.price_positioning == sample_analysis_response["price_positioning"]
        assert output.suggested_hooks == sample_analysis_response["suggested_hooks"]
        assert output.raw_analysis == sample_analysis_response["raw_analysis"]

    @patch("src.agents.product_analyzer.get_storage")
    @patch("src.agents.base.get_anthropic_client")
    def test_parse_response_with_missing_fields(
        self, mock_get_client: Mock, mock_get_storage: Mock, sample_product_input: ProductAnalyzerInput
    ) -> None:
        """Test response parsing with missing optional fields."""
        agent = ProductAnalyzerAgent()

        response_text = '{"key_features": ["feature1"], "target_audience": "test"}'
        output = agent.parse_response(response_text, sample_product_input)

        assert output.success is True
        assert output.key_features == ["feature1"]
        assert output.target_audience == "test"
        # Missing fields should use defaults
        assert output.unique_selling_points == []
        assert output.visual_elements == []
        assert output.price_positioning == "mid-range"

    @patch("src.agents.product_analyzer.get_storage")
    @patch("src.agents.base.get_anthropic_client")
    def test_run_error_handling(
        self,
        mock_get_client: Mock,
        mock_get_storage: Mock,
        sample_product_input: ProductAnalyzerInput,
    ) -> None:
        """Test error handling during execution."""
        from src.shared.exceptions import AgentError

        mock_storage = Mock()
        mock_storage.download_file.side_effect = Exception("Storage error")
        mock_get_storage.return_value = mock_storage

        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API error")
        mock_get_client.return_value = mock_client

        agent = ProductAnalyzerAgent()

        with pytest.raises(AgentError) as exc_info:
            agent.run(sample_product_input)

        assert "ProductAnalyzer" in str(exc_info.value)

    @patch("src.agents.base.get_anthropic_client")
    def test_system_prompt_content(self, mock_get_client: Mock) -> None:
        """Test system prompt contains required instructions."""
        agent = ProductAnalyzerAgent()

        assert "product analyst" in agent.system_prompt.lower()
        assert "json" in agent.system_prompt.lower()
        assert "key_features" in agent.system_prompt
        assert "unique_selling_points" in agent.system_prompt
        assert "target_audience" in agent.system_prompt
        assert "visual_elements" in agent.system_prompt
        assert "price_positioning" in agent.system_prompt
        assert "suggested_hooks" in agent.system_prompt
