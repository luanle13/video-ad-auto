from unittest.mock import MagicMock, patch
import pytest
from src.agents.product_analyzer import ProductAnalyzerAgent  # Assuming the agent is in src.agents.product_analyzer
from tests.fixtures.factories import create_product


@pytest.fixture
def sample_product_input():
    """Sample product input for testing."""
    return {
        "title": "Premium Wireless Headphones",
        "description": "High-quality wireless headphones with noise cancellation and 30-hour battery life.",
        "price": 199.99,
        "image_urls": [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg"
        ]
    }


@pytest.fixture
def mock_analyzer_response():
    """Mock analyzer response with valid JSON."""
    return {
        "product_summary": "Premium wireless headphones with advanced noise cancellation technology",
        "key_features": [
            "Active Noise Cancellation",
            "30-hour battery life",
            "Bluetooth 5.0 connectivity",
            "Memory foam ear cushions",
            "Quick charge feature"
        ],
        "suggested_hooks": [
            "Experience crystal-clear sound with our premium headphones",
            "Say goodbye to noise with our industry-leading ANC technology",
            "Enjoy 30 hours of uninterrupted music on a single charge"
        ],
        "target_audience": "Music lovers, commuters, professionals",
        "unique_selling_points": [
            "Best-in-class noise cancellation",
            "All-day comfort",
            "Superior sound quality"
        ]
    }


class TestProductAnalyzerAgent:
    
    def test_build_user_prompt_includes_product_info(self, sample_product_input):
        """Test that user prompt includes product information."""
        agent = ProductAnalyzerAgent()
        
        prompt = agent.build_user_prompt(sample_product_input)
        
        assert sample_product_input["title"] in prompt
        assert sample_product_input["description"] in prompt
        assert str(sample_product_input["price"]) in prompt
    
    def test_build_user_prompt_includes_images(self, sample_product_input):
        """Test that user prompt includes image information."""
        agent = ProductAnalyzerAgent()
        
        prompt = agent.build_user_prompt(sample_product_input)
        
        for img_url in sample_product_input["image_urls"]:
            assert img_url in prompt
    
    def test_parse_response_valid(self, mock_analyzer_response):
        """Test parsing valid response."""
        agent = ProductAnalyzerAgent()
        
        parsed = agent.parse_response(mock_analyzer_response)
        
        assert "product_summary" in parsed
        assert "key_features" in parsed
        assert "suggested_hooks" in parsed
        assert isinstance(parsed["key_features"], list)
        assert isinstance(parsed["suggested_hooks"], list)
        assert len(parsed["key_features"]) <= 5  # Max 5 features
        assert len(parsed["suggested_hooks"]) <= 3  # Max 3 hooks
    
    def test_parse_response_missing_fields(self, mock_analyzer_response):
        """Test parsing response with missing fields (should use defaults)."""
        agent = ProductAnalyzerAgent()
        
        # Remove some fields from the response
        incomplete_response = mock_analyzer_response.copy()
        del incomplete_response["suggested_hooks"]
        del incomplete_response["target_audience"]
        
        parsed = agent.parse_response(incomplete_response)
        
        # Should have defaults for missing fields
        assert "product_summary" in parsed
        assert "key_features" in parsed
        assert "suggested_hooks" in parsed  # Should have default value
        assert "target_audience" in parsed  # Should have default value
        assert parsed["suggested_hooks"] == []  # Default to empty list
        assert parsed["target_audience"] == ""  # Default to empty string
    
    def test_run_success(self, sample_product_input, mock_analyzer_response):
        """Test successful run with mocked client."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=str(mock_analyzer_response))]
        mock_client.messages.create.return_value = mock_response
        
        agent = ProductAnalyzerAgent(client=mock_client)
        
        result = agent.run(sample_product_input)
        
        # Verify the result structure
        assert "product_summary" in result
        assert "key_features" in result
        assert "suggested_hooks" in result
        assert len(result["key_features"]) <= 5
        assert len(result["suggested_hooks"]) <= 3
        
        # Verify the client was called
        mock_client.messages.create.assert_called_once()
    
    def test_key_features_limit(self, mock_analyzer_response):
        """Test that key features are limited to max 5."""
        agent = ProductAnalyzerAgent()
        
        # Create a response with more than 5 features
        extended_response = mock_analyzer_response.copy()
        extended_response["key_features"] = [
            "Feature 1",
            "Feature 2", 
            "Feature 3",
            "Feature 4",
            "Feature 5",
            "Feature 6",  # This should be trimmed
            "Feature 7"   # This should be trimmed
        ]
        
        parsed = agent.parse_response(extended_response)
        
        assert len(parsed["key_features"]) == 5  # Should be limited to 5
    
    def test_suggested_hooks_limit(self, mock_analyzer_response):
        """Test that suggested hooks are limited to max 3."""
        agent = ProductAnalyzerAgent()
        
        # Create a response with more than 3 hooks
        extended_response = mock_analyzer_response.copy()
        extended_response["suggested_hooks"] = [
            "Hook 1",
            "Hook 2",
            "Hook 3", 
            "Hook 4",  # This should be trimmed
            "Hook 5",  # This should be trimmed
            "Hook 6"   # This should be trimmed
        ]
        
        parsed = agent.parse_response(extended_response)
        
        assert len(parsed["suggested_hooks"]) == 3  # Should be limited to 3
    
    def test_empty_product_input(self):
        """Test handling of empty product input."""
        agent = ProductAnalyzerAgent()
        
        empty_input = {
            "title": "",
            "description": "",
            "price": 0,
            "image_urls": []
        }
        
        # Mock the client to return a valid response even for empty input
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"product_summary": "Empty product", "key_features": [], "suggested_hooks": []}')]
        mock_client.messages.create.return_value = mock_response
        
        agent.client = mock_client
        
        result = agent.run(empty_input)
        
        assert "product_summary" in result
        assert isinstance(result["key_features"], list)
        assert isinstance(result["suggested_hooks"], list)
    
    def test_product_with_many_images(self, sample_product_input):
        """Test handling of product with many images."""
        agent = ProductAnalyzerAgent()
        
        # Add many images to the sample input
        many_images = [f"https://example.com/image{i}.jpg" for i in range(10)]
        sample_product_input["image_urls"] = many_images
        
        prompt = agent.build_user_prompt(sample_product_input)
        
        # Verify all image URLs are included in the prompt
        for img_url in many_images:
            assert img_url in prompt
    
    def test_parse_response_with_extra_fields(self, mock_analyzer_response):
        """Test parsing response with extra unexpected fields."""
        agent = ProductAnalyzerAgent()
        
        # Add extra fields to the response
        extended_response = mock_analyzer_response.copy()
        extended_response["extra_field"] = "extra_value"
        extended_response["another_field"] = {"nested": "value"}
        
        parsed = agent.parse_response(extended_response)
        
        # Should still contain the expected fields
        assert "product_summary" in parsed
        assert "key_features" in parsed
        assert "suggested_hooks" in parsed
        # Extra fields should be preserved
        assert "extra_field" in parsed
        assert "another_field" in parsed