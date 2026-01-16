"""Product Analyzer Agent - Extracts features from product images and metadata."""
import base64
from typing import Any

from pydantic import Field

from src.agents.base import AgentInput, AgentOutput, BaseAgent
from src.shared.storage import get_storage


class ProductAnalyzerInput(AgentInput):
    """Input for Product Analyzer."""

    title: str
    description: str
    price: str
    image_keys: list[str] = Field(..., min_length=1, max_length=5)


class ProductAnalyzerOutput(AgentOutput):
    """Output from Product Analyzer."""

    key_features: list[str] = Field(default_factory=list, description="Main product features")
    unique_selling_points: list[str] = Field(default_factory=list, description="USPs")
    target_audience: str = ""
    visual_elements: list[str] = Field(default_factory=list, description="Notable visual elements from images")
    product_category: str = ""
    price_positioning: str = ""  # "budget", "mid-range", "premium"
    suggested_hooks: list[str] = Field(default_factory=list, description="Attention-grabbing hooks")
    raw_analysis: str = ""  # Full analysis text


class ProductAnalyzerAgent(BaseAgent):
    """Analyzes product images and metadata to extract key information."""

    name = "ProductAnalyzer"
    description = "Analyzes product images and metadata to extract features, USPs, and visual elements"
    model = "gpt-4o"
    max_tokens = 2048
    temperature = 0.3  # Lower temperature for analysis

    @property
    def system_prompt(self) -> str:
        return """You are an expert product analyst specializing in e-commerce and video marketing.

Your task is to analyze product images and metadata to extract:
1. Key features and specifications
2. Unique selling points (USPs)
3. Target audience characteristics
4. Visual elements suitable for video content
5. Price positioning (budget/mid-range/premium)
6. Suggested hooks for short-form video

Focus on aspects that would be compelling in a 30-60 second video ad.

You must respond with valid JSON using the following structure:
{
    "key_features": ["feature1", "feature2", ...],
    "unique_selling_points": ["usp1", "usp2", ...],
    "target_audience": "description of target audience",
    "visual_elements": ["element1", "element2", ...],
    "product_category": "category name",
    "price_positioning": "budget|mid-range|premium",
    "suggested_hooks": ["hook1", "hook2", ...],
    "raw_analysis": "detailed analysis text"
}"""

    def build_user_prompt(self, input_data: ProductAnalyzerInput, context: dict[str, Any]) -> str:
        """Build user prompt with product metadata."""
        # Fetch and encode images for OpenAI vision API
        storage = get_storage()
        image_contents = []

        for key in input_data.image_keys[:3]:  # Limit to 3 images for cost
            try:
                image_data = storage.download_file("images", key)
                encoded = base64.b64encode(image_data).decode("utf-8")
                # Determine media type from key
                if key.endswith(".png"):
                    media_type = "image/png"
                elif key.endswith(".webp"):
                    media_type = "image/webp"
                else:
                    media_type = "image/jpeg"
                # OpenAI vision format
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{encoded}",
                    },
                })
            except Exception as e:
                self.logger.warning("image_fetch_failed", key=key, error=str(e))

        # Store images for use in run method
        self._pending_images = image_contents

        return f"""Analyze this product for video marketing:

PRODUCT TITLE: {input_data.title}

PRODUCT DESCRIPTION: {input_data.description}

PRICE: {input_data.price}

Please analyze the product images and metadata above, then provide your analysis in the specified JSON format."""

    def run(self, input_data: ProductAnalyzerInput, context: dict[str, Any] | None = None) -> ProductAnalyzerOutput:
        """Override run to handle vision API with images."""
        from openai import APIError, RateLimitError

        from src.shared.exceptions import OpenAIError, OpenAIRateLimitError

        context = context or {}

        try:
            # Build user prompt and capture images
            user_prompt = self.build_user_prompt(input_data, context)
            images = getattr(self, "_pending_images", [])

            # Build content array with images and text for OpenAI vision
            user_content: list[dict] = [{"type": "text", "text": user_prompt}]
            user_content.extend(images)

            response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_content},
                ],
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )

            response_text = response.choices[0].message.content

            self.logger.info(
                "agent_run_complete",
                agent=self.name,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
            )

            return self.parse_response(response_text, input_data)

        except RateLimitError as e:
            raise OpenAIRateLimitError(str(e))
        except APIError as e:
            raise OpenAIError(str(e), status_code=e.status_code)

    def parse_response(self, response_text: str, input_data: ProductAnalyzerInput) -> ProductAnalyzerOutput:
        """Parse LLM response into structured output."""
        data = self._extract_json_from_response(response_text)

        return ProductAnalyzerOutput(
            success=True,
            key_features=data.get("key_features", []),
            unique_selling_points=data.get("unique_selling_points", []),
            target_audience=data.get("target_audience", ""),
            visual_elements=data.get("visual_elements", []),
            product_category=data.get("product_category", ""),
            price_positioning=data.get("price_positioning", "mid-range"),
            suggested_hooks=data.get("suggested_hooks", []),
            raw_analysis=data.get("raw_analysis", ""),
        )
