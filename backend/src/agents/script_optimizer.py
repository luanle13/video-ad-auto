"""Script Optimizer Agent - Refines scripts for engagement and platform optimization."""
from typing import Any

from pydantic import BaseModel, Field

from src.agents.base import AgentInput, AgentOutput, BaseAgent


class OptimizedScene(BaseModel):
    """An optimized scene with engagement notes."""

    scene_number: int
    duration_seconds: int
    visual_description: str
    voiceover_text: str
    text_overlay: str | None = None
    transition: str = "cut"
    engagement_note: str | None = Field(None, description="Why this works")
    pattern_interrupt: bool = Field(default=False, description="Is this a pattern interrupt?")


class ScriptOptimizerInput(AgentInput):
    """Input for Script Optimizer Agent."""

    # From Script Generator
    hook: str
    scenes: list[dict[str, Any]]
    call_to_action: str
    full_voiceover_text: str
    estimated_duration_seconds: int

    # Platform targeting
    primary_platform: str = Field(default="tiktok", description="tiktok|facebook|shopee")

    # Market context
    trending_formats: list[str] = Field(default_factory=list)
    platform_tips: dict[str, str] = Field(default_factory=dict)

    # User preferences
    tone: str | None = None
    emphasis: str | None = None
    pacing: str | None = Field(None, description="fast|medium|slow")


class ScriptOptimizerOutput(AgentOutput):
    """Output from Script Optimizer Agent."""

    # Optimized script
    optimized_hook: str
    optimized_scenes: list[dict[str, Any]]
    optimized_cta: str
    optimized_voiceover: str

    # Optimization details
    pacing_notes: list[str] = Field(default_factory=list)
    engagement_hooks: list[str] = Field(default_factory=list, description="Pattern interrupts added")
    platform_adjustments: dict[str, str] = Field(default_factory=dict)

    # Metrics
    estimated_duration_seconds: int
    scene_count: int
    pattern_interrupt_count: int = Field(default=0)

    # Comparison
    changes_summary: str = Field(..., description="Summary of optimizations made")


class ScriptOptimizerAgent(BaseAgent):
    """Optimizes scripts for maximum engagement and platform fit."""

    name = "ScriptOptimizer"
    description = "Refines video scripts for engagement, pacing, and platform optimization"
    max_tokens = 3000
    temperature = 0.5  # Balanced creativity and consistency

    PLATFORM_REQUIREMENTS = {
        "tiktok": {
            "max_duration": 60,
            "hook_time": 1.5,
            "pattern_interrupt_interval": 5,
            "trending_features": ["duet-friendly ending", "trending sounds reference", "comment bait"],
        },
        "facebook": {
            "max_duration": 60,
            "hook_time": 3,
            "pattern_interrupt_interval": 7,
            "trending_features": ["caption-friendly", "share prompt", "emotional hook"],
        },
        "shopee": {
            "max_duration": 60,
            "hook_time": 2,
            "pattern_interrupt_interval": 6,
            "trending_features": ["price callout", "discount emphasis", "shop link CTA"],
        },
    }

    @property
    def system_prompt(self) -> str:
        return """You are an expert video content optimizer specializing in short-form video engagement.

Your task is to optimize video scripts for maximum engagement by:

1. HOOK OPTIMIZATION (First 1-3 seconds)
   - Make it impossible to scroll past
   - Use curiosity gaps, bold statements, or pattern interrupts
   - Front-load the value proposition

2. PACING OPTIMIZATION
   - Ensure no scene exceeds 7 seconds without a change
   - Add pattern interrupts every 5-7 seconds
   - Vary visual and audio rhythm

3. ENGAGEMENT HOOKS
   - Add "wait for it" moments
   - Include relatable pain points
   - Create emotional peaks

4. PLATFORM-SPECIFIC OPTIMIZATION
   - TikTok: Fast cuts, trending references, duet-friendly
   - Facebook Reels: Caption-friendly, emotional, shareable
   - Shopee: Product-focused, price emphasis, shop CTAs

5. CTA OPTIMIZATION
   - Make action clear and compelling
   - Create urgency without being pushy
   - Platform-appropriate CTA format

PATTERN INTERRUPTS (add every 5-7 seconds):
- Zoom changes
- Scene cuts
- Text overlays appearing
- Sound effects
- Direct address to camera
- Unexpected visual elements

Respond in JSON format:
{
    "optimized_hook": "Improved hook text",
    "optimized_scenes": [
        {
            "scene_number": 1,
            "duration_seconds": 3,
            "visual_description": "Optimized visual",
            "voiceover_text": "Optimized narration",
            "text_overlay": "Key text",
            "transition": "cut|zoom|swipe",
            "engagement_note": "Why this works",
            "pattern_interrupt": true
        }
    ],
    "optimized_cta": "Improved CTA",
    "optimized_voiceover": "Complete optimized narration",
    "pacing_notes": ["Note about pacing change 1", "Note 2"],
    "engagement_hooks": ["Hook 1 added", "Hook 2 added"],
    "platform_adjustments": {
        "adjustment_type": "description of change"
    },
    "estimated_duration_seconds": 45,
    "scene_count": 7,
    "pattern_interrupt_count": 5,
    "changes_summary": "Summary of all optimizations made"
}"""

    def build_user_prompt(self, input_data: ScriptOptimizerInput, context: dict[str, Any]) -> str:
        """Build user prompt with draft script and platform requirements."""
        platform = input_data.primary_platform.lower()
        platform_reqs = self.PLATFORM_REQUIREMENTS.get(platform, self.PLATFORM_REQUIREMENTS["tiktok"])

        scenes_text = ""
        for scene in input_data.scenes:
            scenes_text += f"""
Scene {scene.get('scene_number', '?')} ({scene.get('duration_seconds', '?')}s):
  Visual: {scene.get('visual_description', '')}
  Voiceover: {scene.get('voiceover_text', '')}
  Text: {scene.get('text_overlay', 'None')}
  Transition: {scene.get('transition', 'cut')}
"""

        platform_tips_text = ""
        if input_data.platform_tips:
            platform_tips_text = f"\nPLATFORM-SPECIFIC TIPS:\n{input_data.platform_tips.get(platform, '')}"

        tone_instruction = ""
        if input_data.tone:
            tone_instruction = f"\nMAINTAIN TONE: {input_data.tone}"

        pacing_instruction = ""
        if input_data.pacing:
            pacing_map = {
                "fast": "Quick cuts, high energy, minimal pauses",
                "medium": "Balanced rhythm, natural pauses",
                "slow": "Deliberate pacing, let moments breathe",
            }
            pacing_instruction = f"\nPACING PREFERENCE: {pacing_map.get(input_data.pacing, 'medium')}"

        return f"""Optimize this video script for {platform.upper()}:

CURRENT HOOK: {input_data.hook}

CURRENT SCENES:
{scenes_text}

CURRENT CTA: {input_data.call_to_action}

CURRENT DURATION: {input_data.estimated_duration_seconds} seconds

PLATFORM REQUIREMENTS FOR {platform.upper()}:
- Maximum duration: {platform_reqs['max_duration']}s
- Hook must capture in: {platform_reqs['hook_time']}s
- Pattern interrupt every: {platform_reqs['pattern_interrupt_interval']}s
- Trending features to include: {', '.join(platform_reqs['trending_features'])}

TRENDING FORMATS: {', '.join(input_data.trending_formats[:3]) if input_data.trending_formats else 'N/A'}
{platform_tips_text}
{tone_instruction}
{pacing_instruction}

Optimize this script for maximum engagement on {platform.upper()}. Add pattern interrupts, improve pacing, and make the hook irresistible."""

    def parse_response(self, response_text: str, input_data: ScriptOptimizerInput) -> ScriptOptimizerOutput:
        """Parse LLM response into structured output."""
        data = self._extract_json_from_response(response_text)

        # Process optimized scenes
        optimized_scenes = []
        pattern_interrupt_count = 0
        total_duration = 0

        for scene in data.get("optimized_scenes", []):
            if scene.get("pattern_interrupt"):
                pattern_interrupt_count += 1
            total_duration += scene.get("duration_seconds", 5)
            optimized_scenes.append({
                "scene_number": scene.get("scene_number"),
                "duration_seconds": scene.get("duration_seconds", 5),
                "visual_description": scene.get("visual_description", ""),
                "voiceover_text": scene.get("voiceover_text", ""),
                "text_overlay": scene.get("text_overlay"),
                "transition": scene.get("transition", "cut"),
                "engagement_note": scene.get("engagement_note"),
                "pattern_interrupt": scene.get("pattern_interrupt", False),
            })

        return ScriptOptimizerOutput(
            success=True,
            optimized_hook=data.get("optimized_hook", input_data.hook),
            optimized_scenes=optimized_scenes,
            optimized_cta=data.get("optimized_cta", input_data.call_to_action),
            optimized_voiceover=data.get("optimized_voiceover", ""),
            pacing_notes=data.get("pacing_notes", []),
            engagement_hooks=data.get("engagement_hooks", []),
            platform_adjustments=data.get("platform_adjustments", {}),
            estimated_duration_seconds=data.get("estimated_duration_seconds", total_duration),
            scene_count=len(optimized_scenes),
            pattern_interrupt_count=pattern_interrupt_count,
            changes_summary=data.get("changes_summary", "Script optimized for engagement"),
        )
