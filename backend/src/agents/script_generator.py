"""Script Generator Agent - Creates initial video scripts."""
from typing import Any

from pydantic import BaseModel, Field

from src.agents.base import AgentInput, AgentOutput, BaseAgent


class SceneDescription(BaseModel):
    """A single scene in the video script."""

    scene_number: int
    duration_seconds: int = Field(..., ge=1, le=20)
    visual_description: str = Field(..., description="What appears on screen")
    voiceover_text: str = Field(..., description="Narration for this scene")
    text_overlay: str | None = Field(None, description="On-screen text/caption")
    transition: str = Field(default="cut", description="Transition to next scene")


class ScriptGeneratorInput(AgentInput):
    """Input for Script Generator Agent."""

    # From Product Analyzer
    product_title: str
    key_features: list[str]
    unique_selling_points: list[str]
    target_audience: str
    visual_elements: list[str]
    price: str
    price_positioning: str
    suggested_hooks: list[str]

    # From Market Insight
    content_angles: list[str]
    trending_formats: list[str]
    platform_tips: dict[str, str]
    suggested_music_style: str

    # User preferences
    target_duration: int = Field(default=45, ge=30, le=60, description="Target video duration in seconds")
    tone: str | None = Field(None, description="e.g., 'energetic', 'calm', 'professional'")
    emphasis: str | None = Field(None, description="Feature to emphasize")


class ScriptGeneratorOutput(AgentOutput):
    """Output from Script Generator Agent."""

    # Main script components
    hook: str = Field(..., description="Opening hook (first 3 seconds)")
    scenes: list[dict[str, Any]] = Field(default_factory=list, description="Scene-by-scene breakdown")
    call_to_action: str = Field(..., description="Closing CTA")

    # Full text versions
    full_voiceover_text: str = Field(..., description="Complete voiceover script")
    full_visual_description: str = Field(..., description="Complete visual direction")

    # Metadata
    estimated_duration_seconds: int = Field(..., ge=30, le=60)
    scene_count: int = Field(..., ge=3, le=10)

    # Suggested elements
    suggested_hashtags: list[str] = Field(default_factory=list)
    suggested_music_mood: str = ""
    text_overlays: list[str] = Field(default_factory=list)


class ScriptGeneratorAgent(BaseAgent):
    """Creates initial video scripts from product analysis and market insights."""

    name = "ScriptGenerator"
    description = "Creates compelling video scripts for short-form product videos"
    max_tokens = 3000
    temperature = 0.7  # Higher creativity for script writing

    @property
    def system_prompt(self) -> str:
        return """You are an expert video scriptwriter specializing in short-form product videos for TikTok, Instagram Reels, and Shopee.

Your task is to create compelling 30–60 second video scripts that:
1. Hook viewers in the first 3 seconds
2. Highlight product benefits (not just features)
3. Create emotional connection with target audience
4. Include clear call-to-action
5. Are optimized for mobile viewing (vertical 9:16)

IMPORTANT VISUAL CONSTRAINTS:
- DO NOT show faces at any time
- If people appear, show ONLY body parts (hands, arms, torso, legs)
- No facial features, eyes, or expressions visible
- Treat people as neutral “characters” demoing the product
- Focus visuals on the product, hands-on usage, close-ups, over-the-shoulder shots, POV angles, and lifestyle action shots
- Avoid any camera angles that could reveal a face (no head-level framing)

SCRIPT STRUCTURE:
- HOOK (0–3s): Attention-grabbing opening using product or action-based visuals
- PROBLEM / DESIRE (3–10s): Relate to viewer’s need using body-only or POV demonstration
- SOLUTION (10–25s): Introduce product as the solution through hands-on usage
- FEATURES / BENEFITS (25–45s): Showcase key selling points with close-ups, motion, or side-by-side comparisons
- SOCIAL PROOF (optional, 5–10s): Text-based reviews, results, before/after shots (no faces)
- CTA (last 5–10s): Clear next step with product-focused visuals

BEST PRACTICES:
- Use conversational, engaging language
- Include pattern interrupts every 5–7 seconds
- Write for spoken word (short sentences, natural rhythm)
- Include visual cues for dynamic editing
- Add text overlay suggestions for key points
- Prioritize product motion, interaction, and tactile feedback

Respond in JSON format:
{
    "hook": "Opening hook text (spoken in first 3 seconds)",
    "scenes": [
        {
            "scene_number": 1,
            "duration_seconds": 3,
            "visual_description": "Describe visuals clearly — body-only, no face, product-focused",
            "voiceover_text": "What is spoken",
            "text_overlay": "On-screen text (optional)",
            "transition": "cut|fade|zoom|swipe"
        }
    ],
    "call_to_action": "Closing CTA text",
    "full_voiceover_text": "Complete narration script",
    "full_visual_description": "Complete visual direction (no-face, body-only, character demo)",
    "estimated_duration_seconds": 45,
    "scene_count": 6,
    "suggested_hashtags": ["#hashtag1", "#hashtag2"],
    "suggested_music_mood": "upbeat electronic",
    "text_overlays": ["Key text 1", "Key text 2"]
}
"""

    def build_user_prompt(self, input_data: ScriptGeneratorInput, context: dict[str, Any]) -> str:
        """Build user prompt with all product and market data."""
        features_text = "\n".join(f"• {f}" for f in input_data.key_features[:5])
        usps_text = "\n".join(f"• {u}" for u in input_data.unique_selling_points[:3])
        hooks_text = "\n".join(f"• {h}" for h in input_data.suggested_hooks[:3])
        angles_text = "\n".join(f"• {a}" for a in input_data.content_angles[:3])
        formats_text = ", ".join(input_data.trending_formats[:4])
        visuals_text = "\n".join(f"• {v}" for v in input_data.visual_elements[:5])

        tone_instruction = ""
        if input_data.tone:
            tone_instruction = f"\nTONE: Make the script {input_data.tone}."

        emphasis_instruction = ""
        if input_data.emphasis:
            emphasis_instruction = f"\nEMPHASIS: Focus especially on: {input_data.emphasis}"

        platform_tips = ""
        if input_data.platform_tips:
            tips = "\n".join(f"• {platform}: {tip}" for platform, tip in input_data.platform_tips.items())
            platform_tips = f"\nPLATFORM TIPS:\n{tips}"

        return f"""Create a {input_data.target_duration}-second video script for this product:

PRODUCT: {input_data.product_title}
PRICE: {input_data.price} ({input_data.price_positioning})
TARGET AUDIENCE: {input_data.target_audience}

KEY FEATURES:
{features_text}

UNIQUE SELLING POINTS:
{usps_text}

VISUAL ELEMENTS (from product images):
{visuals_text}

SUGGESTED HOOKS:
{hooks_text}

CONTENT ANGLES TO CONSIDER:
{angles_text}

TRENDING FORMATS: {formats_text}

MUSIC STYLE: {input_data.suggested_music_style}
{platform_tips}
{tone_instruction}
{emphasis_instruction}

Create a compelling script that will stop scrollers and drive engagement. The script should feel natural and authentic, not salesy."""

    def parse_response(self, response_text: str, input_data: ScriptGeneratorInput) -> ScriptGeneratorOutput:
        """Parse LLM response into structured output."""
        data = self._extract_json_from_response(response_text)

        # Validate and process scenes
        scenes = data.get("scenes", [])
        processed_scenes = []
        total_duration = 0

        for scene in scenes:
            duration = scene.get("duration_seconds", 5)
            total_duration += duration
            processed_scenes.append({
                "scene_number": scene.get("scene_number", len(processed_scenes) + 1),
                "duration_seconds": duration,
                "visual_description": scene.get("visual_description", ""),
                "voiceover_text": scene.get("voiceover_text", ""),
                "text_overlay": scene.get("text_overlay"),
                "transition": scene.get("transition", "cut"),
            })

        return ScriptGeneratorOutput(
            success=True,
            hook=data.get("hook", ""),
            scenes=processed_scenes,
            call_to_action=data.get("call_to_action", ""),
            full_voiceover_text=data.get("full_voiceover_text", ""),
            full_visual_description=data.get("full_visual_description", ""),
            estimated_duration_seconds=data.get("estimated_duration_seconds", total_duration),
            scene_count=len(processed_scenes),
            suggested_hashtags=data.get("suggested_hashtags", [])[:10],
            suggested_music_mood=data.get("suggested_music_mood", ""),
            text_overlays=data.get("text_overlays", []),
        )
