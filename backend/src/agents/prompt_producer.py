"""Prompt Producer Agent - Generates prompts for video generation."""
from typing import Any

from pydantic import Field

from src.agents.base import AgentInput, AgentOutput, BaseAgent


class VideoPrompt(dict):
    """A single video generation prompt for Kling AI."""

    pass


class PromptProducerInput(AgentInput):
    """Input for Prompt Producer Agent.

    Attributes:
        hook: Opening hook text
        scenes: Scene-by-scene breakdown from script
        call_to_action: Closing CTA
        full_voiceover_text: Complete voiceover script
        product_title: Product name
        visual_elements: Visual elements from product analysis
        target_duration: Target video duration in seconds
    """

    hook: str = Field(description="Opening hook text")
    scenes: list[dict[str, Any]] = Field(description="Scene-by-scene breakdown")
    call_to_action: str = Field(description="Closing CTA")
    full_voiceover_text: str = Field(description="Complete voiceover script")
    product_title: str = Field(description="Product name")
    visual_elements: list[str] = Field(default_factory=list, description="Visual elements")
    target_duration: int = Field(default=20, ge=10, le=60, description="Target duration")


class PromptProducerOutput(AgentOutput):
    """Output from Prompt Producer Agent.

    Attributes:
        video_prompts: List of prompts for each video segment
        master_prompt: Combined prompt for full video generation
        negative_prompt: What to avoid in generation
        style_keywords: Style keywords for consistent look
        camera_movements: Suggested camera movements
        transition_effects: Transition effects between scenes
        audio_sync_notes: Notes for audio synchronization
    """

    video_prompts: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Prompts for each video segment",
    )
    master_prompt: str = Field(
        default="",
        description="Combined prompt for full video",
    )
    negative_prompt: str = Field(
        default="",
        description="What to avoid in generation",
    )
    style_keywords: list[str] = Field(
        default_factory=list,
        description="Style keywords for consistency",
    )
    camera_movements: list[str] = Field(
        default_factory=list,
        description="Camera movement suggestions",
    )
    transition_effects: list[str] = Field(
        default_factory=list,
        description="Transition effects between scenes",
    )
    audio_sync_notes: str = Field(
        default="",
        description="Notes for audio synchronization",
    )


class PromptProducerAgent(BaseAgent):
    """Generates optimized prompts for AI video generation.

    This agent takes the reviewed script and produces:
    - Individual prompts for each video segment
    - A master prompt for overall video style
    - Negative prompts to avoid unwanted content
    - Style and camera movement keywords

    Example:
        >>> input_data = PromptProducerInput(
        ...     job_id="job_123",
        ...     user_id="usr_456",
        ...     hook="Stop scrolling!",
        ...     scenes=[{"visual_description": "Product closeup"}],
        ...     call_to_action="Shop now!",
        ...     full_voiceover_text="...",
        ...     product_title="Wireless Earbuds",
        ... )
        >>> agent = PromptProducerAgent()
        >>> output = agent.run(input_data)
    """

    name = "PromptProducer"
    description = "Generates optimized prompts for AI video generation from scripts"
    model = None  # Uses deployment name from settings
    max_tokens = 2500
    temperature = 0.4  # Lower temperature for consistent prompts

    @property
    def system_prompt(self) -> str:
        """Return system prompt for the agent."""
        return """You are an expert AI video prompt engineer specializing in Kling AI and similar video generation models.

Your task is to convert video scripts into optimized prompts for AI video generation.

PROMPT ENGINEERING PRINCIPLES:
1. Be specific and descriptive about visual elements
2. Include camera angles, movements, and framing
3. Specify lighting, mood, and atmosphere
4. Maintain consistency across all scene prompts
5. Avoid faces and identifiable people (use hands, products, lifestyle shots)

IMPORTANT CONSTRAINTS:
- NO faces or facial features in any prompt
- Focus on: product shots, hands interacting, over-shoulder views, POV angles
- Use cinematic language for professional results
- Include motion descriptions for dynamic video

PROMPT STRUCTURE FOR EACH SCENE:
- Subject: What is shown (product, hands, environment)
- Action: What is happening (movement, interaction)
- Style: Visual style (cinematic, bright, modern)
- Camera: Camera movement (pan, zoom, static)
- Lighting: Light quality (soft, dramatic, natural)

NEGATIVE PROMPT GUIDELINES:
Always exclude: faces, eyes, portraits, blurry, low quality, distorted

You must respond with valid JSON using the following structure:
{
    "video_prompts": [
        {
            "scene_number": 1,
            "duration_seconds": 3,
            "prompt": "Detailed prompt for this scene",
            "camera_movement": "pan right|zoom in|static|dolly",
            "style_notes": "Additional style guidance"
        }
    ],
    "master_prompt": "Overall style prompt for video consistency",
    "negative_prompt": "What to avoid in all scenes",
    "style_keywords": ["keyword1", "keyword2"],
    "camera_movements": ["movement1", "movement2"],
    "transition_effects": ["cut", "fade", "zoom"],
    "audio_sync_notes": "Notes for syncing audio with visuals"
}"""

    def build_user_prompt(
        self, input_data: PromptProducerInput, context: dict[str, Any]
    ) -> str:
        """Build user prompt from script data.

        Args:
            input_data: PromptProducerInput with script details
            context: Additional context (unused for this agent)

        Returns:
            Formatted user prompt string
        """
        scenes_text = ""
        for scene in input_data.scenes:
            scenes_text += f"""
Scene {scene.get('scene_number', '?')} ({scene.get('duration_seconds', '?')}s):
  Visual: {scene.get('visual_description', '')}
  Voiceover: {scene.get('voiceover_text', '')}
  Transition: {scene.get('transition', 'cut')}
"""

        visuals_text = "\n".join(f"- {v}" for v in input_data.visual_elements[:5])

        return f"""Generate video prompts for this script:

PRODUCT: {input_data.product_title}
TARGET DURATION: {input_data.target_duration} seconds

HOOK: {input_data.hook}

SCENES:
{scenes_text}

CALL TO ACTION: {input_data.call_to_action}

VISUAL ELEMENTS FROM PRODUCT:
{visuals_text}

FULL VOICEOVER:
{input_data.full_voiceover_text}

Generate optimized prompts for each scene that will produce high-quality, engaging video content. Remember: NO FACES in any prompt."""

    def parse_response(
        self, response_text: str, input_data: PromptProducerInput
    ) -> PromptProducerOutput:
        """Parse LLM response into structured output.

        Args:
            response_text: Raw text response from LLM
            input_data: Original input data

        Returns:
            PromptProducerOutput with parsed data
        """
        data = self._extract_json_from_response(response_text)

        # Process video prompts
        video_prompts = []
        for prompt in data.get("video_prompts", []):
            video_prompts.append({
                "scene_number": prompt.get("scene_number"),
                "duration_seconds": prompt.get("duration_seconds", 5),
                "prompt": prompt.get("prompt", ""),
                "camera_movement": prompt.get("camera_movement", "static"),
                "style_notes": prompt.get("style_notes", ""),
            })

        return PromptProducerOutput(
            success=True,
            video_prompts=video_prompts,
            master_prompt=data.get("master_prompt", ""),
            negative_prompt=data.get(
                "negative_prompt",
                "face, facial features, eyes, portrait, blurry, low quality, distorted",
            ),
            style_keywords=data.get("style_keywords", []),
            camera_movements=data.get("camera_movements", []),
            transition_effects=data.get("transition_effects", []),
            audio_sync_notes=data.get("audio_sync_notes", ""),
        )
