"""Market Insight Agent - Identifies trends and content angles."""
from typing import Any

from pydantic import Field

from src.agents.base import AgentInput, AgentOutput, BaseAgent


class MarketInsightInput(AgentInput):
    """Input for Market Insight Agent.

    Attributes:
        product_category: Product category (e.g., "Electronics", "Beauty")
        target_audience: Target audience description
        key_features: List of key product features
        price_positioning: Price positioning (e.g., "budget", "mid-range", "premium")
    """

    product_category: str = Field(description="Product category")
    target_audience: str = Field(description="Target audience description")
    key_features: list[str] = Field(description="Key product features")
    price_positioning: str = Field(description="Price positioning")


class MarketInsightOutput(AgentOutput):
    """Output from Market Insight Agent.

    Attributes:
        trending_hashtags: List of relevant trending hashtags
        content_angles: Story angles for video content
        platform_tips: Platform-specific recommendations
        trending_formats: Popular video formats
        suggested_music_style: Recommended music style
        best_posting_times: Optimal posting times
        competitor_insights: Brief market analysis
    """

    trending_hashtags: list[str] = Field(
        default_factory=list,
        description="Trending hashtags for the product",
    )
    content_angles: list[str] = Field(
        default_factory=list,
        description="Story angles for video",
    )
    platform_tips: dict[str, str] = Field(
        default_factory=dict,
        description="Platform-specific recommendations",
    )
    trending_formats: list[str] = Field(
        default_factory=list,
        description="Popular video formats",
    )
    suggested_music_style: str = Field(
        default="",
        description="Recommended music style",
    )
    best_posting_times: list[str] = Field(
        default_factory=list,
        description="Optimal posting times",
    )
    competitor_insights: str = Field(
        default="",
        description="Brief market analysis",
    )


class MarketInsightAgent(BaseAgent):
    """Identifies market trends and content angles for video marketing.

    This agent analyzes product information and provides:
    - Trending hashtags for the Vietnam/SEA market
    - Content angles that resonate with target audience
    - Platform-specific best practices
    - Trending video formats
    - Music style recommendations
    - Optimal posting times

    Example:
        >>> input_data = MarketInsightInput(
        ...     job_id="job_123",
        ...     user_id="usr_456",
        ...     product_category="Electronics",
        ...     target_audience="Tech-savvy millennials",
        ...     key_features=["Wireless", "Fast charging"],
        ...     price_positioning="mid-range",
        ... )
        >>> agent = MarketInsightAgent()
        >>> output = agent.run(input_data)
        >>> print(output.trending_hashtags)
        ['#TechReview', '#GadgetVietnam', ...]
    """

    name = "MarketInsight"
    description = "Analyzes market trends and identifies content angles for short-form video"
    max_tokens = 1536
    temperature = 0.5

    # Static trending data (MVP - replace with API in V2)
    TRENDING_FORMATS = [
        "Before/After transformation",
        "POV (Point of View)",
        "Day in the life",
        "Tutorial/How-to",
        "Unboxing experience",
        "Product comparison",
        "Behind the scenes",
        "Story time",
        "ASMR/Satisfying",
    ]

    @property
    def system_prompt(self) -> str:
        """Return system prompt for the agent."""
        return """You are an expert social media marketing strategist specializing in TikTok, Instagram Reels, and Shopee video content.

Your task is to identify market trends and content angles for product video marketing.

Consider:
1. Current trending hashtags for the product category (focus on Vietnam/SEA market)
2. Content angles that resonate with the target audience
3. Platform-specific best practices (TikTok, Facebook Reels, Shopee)
4. Trending video formats and styles
5. Optimal posting times for Vietnam timezone (GMT+7)

Respond in JSON format:
{
    "trending_hashtags": ["#hashtag1", "#hashtag2", ...],
    "content_angles": ["angle1", "angle2", ...],
    "platform_tips": {
        "tiktok": "tip for TikTok",
        "facebook": "tip for Facebook Reels",
        "shopee": "tip for Shopee Video"
    },
    "trending_formats": ["format1", "format2", ...],
    "suggested_music_style": "description of music style",
    "best_posting_times": ["time1", "time2"],
    "competitor_insights": "brief market analysis"
}"""

    def build_user_prompt(
        self, input_data: MarketInsightInput, context: dict[str, Any]
    ) -> str:
        """Build user prompt from input data.

        Args:
            input_data: MarketInsightInput with product details
            context: Additional context (unused for this agent)

        Returns:
            Formatted user prompt string
        """
        # Limit features to 5 for brevity
        features_text = "\n".join(f"- {f}" for f in input_data.key_features[:5])

        return f"""Analyze market trends for this product:

PRODUCT CATEGORY: {input_data.product_category}
TARGET AUDIENCE: {input_data.target_audience}
PRICE POSITIONING: {input_data.price_positioning}

KEY FEATURES:
{features_text}

Currently popular video formats include:
{', '.join(self.TRENDING_FORMATS)}

Focus on the Vietnam market. Provide specific, actionable insights for short-form video content."""

    def parse_response(
        self, response_text: str, input_data: MarketInsightInput
    ) -> MarketInsightOutput:
        """Parse LLM response into structured output.

        Args:
            response_text: Raw text response from LLM
            input_data: Original input data

        Returns:
            MarketInsightOutput with parsed data
        """
        data = self._extract_json_from_response(response_text)

        return MarketInsightOutput(
            success=True,
            trending_hashtags=data.get("trending_hashtags", [])[:15],  # Limit to 15
            content_angles=data.get("content_angles", []),
            platform_tips=data.get("platform_tips", {}),
            trending_formats=data.get("trending_formats", []),
            suggested_music_style=data.get("suggested_music_style", ""),
            best_posting_times=data.get("best_posting_times", []),
            competitor_insights=data.get("competitor_insights", ""),
        )
