"""Image Generator Agent - Generates opening and bridge frames for split video ads."""
from typing import Any

from pydantic import Field

from src.agents.base import AgentInput, AgentOutput, BaseAgent
from src.shared.logging import get_logger


logger = get_logger(__name__)


class ImageGeneratorInput(AgentInput):
    """Input for Image Generator Agent."""

    # Product information
    product_title: str
    product_description: str
    product_category: str = "kitchen"
    
    # Visual guidance from product analyzer
    visual_elements: list[str] = Field(default_factory=list)
    key_features: list[str] = Field(default_factory=list)
    price_positioning: str = "mid-range"
    
    # Script context
    hook: str = ""
    call_to_action: str = ""
    full_visual_description: str = ""
    
    # Scene information for split videos
    scenes: list[dict] = Field(default_factory=list)
    target_duration: int = 15  # Total video duration in seconds
    
    # Style preferences
    style_preference: str = "modern"  # modern, classic, minimalist, warm
    color_scheme: str | None = None  # Optional color preference


class ImageGeneratorOutput(AgentOutput):
    """Output from Image Generator Agent."""

    # Generated prompts for Azure FLUX
    opening_frame_prompt: str = Field(
        ..., description="Prompt for generating the opening frame (start of video 1)"
    )
    bridge_frame_prompt: str = Field(
        ..., description="Prompt for generating the bridge frame (end of video 1 / connection point for video 2)"
    )
    
    # Generated image URLs (populated after Azure generation)
    opening_frame_url: str = ""
    bridge_frame_url: str = ""
    
    # S3 keys for stored images
    opening_frame_key: str = ""
    bridge_frame_key: str = ""
    
    # Style consistency metadata
    style_description: str = Field(
        ..., description="Detailed style description for video generation consistency"
    )
    visual_continuity_notes: str = ""
    
    # Split video prompts
    first_half_prompt: str = Field(
        default="", description="Video generation prompt for first half"
    )
    second_half_prompt: str = Field(
        default="", description="Video generation prompt for second half"
    )
    
    # Scene split information
    first_half_scenes: list[dict] = Field(default_factory=list)
    second_half_scenes: list[dict] = Field(default_factory=list)
    bridge_scene_description: str = ""
    
    # Video generation guidance
    motion_suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested camera movements and transitions"
    )


class ImageGeneratorAgent(BaseAgent):
    """Generates prompts for opening and bridge frames for split video generation.

    This agent creates optimized prompts for generating consistent, high-quality
    images that will serve as the base frames for video generation. The video
    is split into two halves that can be combined using Veo3's extend feature.

    Split Video Strategy:
    - Opening Frame: Start of video 1 (first half)
    - Bridge Frame: End of video 1 / Start point for video 2 (second half)
    - Videos are generated separately and combined via extend feature

    Focus: Kitchen product advertisements
    Output: Photorealistic, no faces, product-centric imagery
    """

    name = "ImageGenerator"
    description = "Generates opening and bridge frame prompts for split kitchen product video ads"
    model = None  # Uses deployment name from settings
    max_tokens = 3000
    temperature = 0.5  # Balanced creativity for visual prompts

    @property
    def system_prompt(self) -> str:
        return """You are an expert visual director specializing in kitchen product advertisements.

Your task is to create detailed image prompts for generating frames of a 15-20 second product 
video advertisement that will be SPLIT INTO TWO HALVES for video generation.

VIDEO SPLIT STRATEGY:
- The video will be generated in 2 parts using image-to-video AI
- Video 1 (first half): Starts from OPENING FRAME
- Video 2 (second half): Starts from BRIDGE FRAME and extends the story
- The BRIDGE FRAME must visually match the end state of video 1 for seamless connection

CRITICAL REQUIREMENTS:
1. NO human faces - only hands, arms, or torso when showing people
2. Focus on the PRODUCT as the hero
3. Modern, professional kitchen setting
4. Photorealistic quality suitable for commercial use
5. 16:9 aspect ratio composition
6. Clean, uncluttered backgrounds
7. Professional lighting that highlights the product
8. BRIDGE FRAME must logically connect the two video halves

KITCHEN PRODUCT FOCUS:
- Show products in realistic kitchen environments
- Emphasize functionality and design
- Include contextual elements (countertops, cabinets, ingredients) without distraction
- Premium, aspirational feel matching price positioning

FRAME TYPES:

OPENING FRAME:
- Establishes the setting and introduces the product
- Creates intrigue and draws viewer attention
- Sets the visual style for the entire video
- Starting point for video generation (first half)

BRIDGE FRAME (CRITICAL):
- This is the END STATE of video 1 and START POINT for video 2
- Must show a natural transition moment in the product demo
- Should capture the product at a mid-point action (e.g., mid-blend, mid-pour)
- Visual style, lighting, and setting MUST match opening frame
- The scene should feel like a natural pause point that can be extended

SPLIT VIDEO PROMPTS:
- First half prompt: Describes the action from opening to bridge
- Second half prompt: Describes the action from bridge to finale

You must respond with valid JSON using the following structure:
{
    "opening_frame_prompt": "Detailed prompt for generating opening frame",
    "bridge_frame_prompt": "Detailed prompt for generating bridge frame (end of video 1)",
    "bridge_scene_description": "Description of what the bridge frame represents in the story",
    "first_half_prompt": "Video generation prompt for first half (opening to bridge)",
    "second_half_prompt": "Video generation prompt for second half (bridge to finale)",
    "style_description": "Detailed description of visual style for video consistency",
    "visual_continuity_notes": "Notes on maintaining visual consistency between frames and halves",
    "motion_suggestions": ["camera movement 1", "transition suggestion 2", ...]
}"""

    def build_user_prompt(self, input_data: ImageGeneratorInput, context: dict[str, Any]) -> str:
        """Build user prompt with product and script context."""
        features_text = "\n".join(f"• {f}" for f in input_data.key_features[:5])
        visual_text = "\n".join(f"• {v}" for v in input_data.visual_elements[:5])

        style_context = ""
        if input_data.style_preference:
            style_context = f"\nSTYLE PREFERENCE: {input_data.style_preference}"
        if input_data.color_scheme:
            style_context += f"\nCOLOR SCHEME: {input_data.color_scheme}"

        script_context = ""
        if input_data.hook:
            script_context += f"\nVIDEO HOOK: {input_data.hook}"
        if input_data.call_to_action:
            script_context += f"\nCALL TO ACTION: {input_data.call_to_action}"
        if input_data.full_visual_description:
            script_context += f"\nSCRIPT VISUAL DIRECTION:\n{input_data.full_visual_description[:500]}"

        # Calculate scene split for video halves
        scenes = input_data.scenes
        total_duration = input_data.target_duration
        half_duration = total_duration // 2
        
        # Split scenes into first and second half
        first_half_scenes = []
        second_half_scenes = []
        accumulated_duration = 0
        
        for scene in scenes:
            scene_duration = scene.get("duration_seconds", scene.get("duration", 3))
            if accumulated_duration < half_duration:
                first_half_scenes.append(scene)
            else:
                second_half_scenes.append(scene)
            accumulated_duration += scene_duration
        
        # Build scene descriptions
        first_half_text = ""
        for scene in first_half_scenes:
            first_half_text += f"\n  Scene {scene.get('scene_number', '?')}: {scene.get('visual_description', scene.get('visual', ''))}"
        
        second_half_text = ""
        for scene in second_half_scenes:
            second_half_text += f"\n  Scene {scene.get('scene_number', '?')}: {scene.get('visual_description', scene.get('visual', ''))}"
        
        # Determine bridge scene (last scene of first half)
        bridge_scene = first_half_scenes[-1] if first_half_scenes else {}
        bridge_scene_text = bridge_scene.get('visual_description', bridge_scene.get('visual', 'Product in action mid-demonstration'))

        return f"""Create image generation prompts for a SPLIT kitchen product video advertisement.

PRODUCT: {input_data.product_title}
CATEGORY: {input_data.product_category}
PRICE POSITIONING: {input_data.price_positioning}

PRODUCT DESCRIPTION:
{input_data.product_description}

KEY FEATURES:
{features_text}

VISUAL ELEMENTS (from product images):
{visual_text}
{style_context}
{script_context}

TOTAL VIDEO DURATION: {total_duration} seconds
VIDEO SPLIT POINT: ~{half_duration} seconds

FIRST HALF SCENES (Video 1: ~{half_duration}s):
{first_half_text}

SECOND HALF SCENES (Video 2: ~{half_duration}s):
{second_half_text}

BRIDGE SCENE (End of Video 1):
{bridge_scene_text}

Generate detailed prompts for:
1. OPENING FRAME: First frame of Video 1 - establishes the scene
2. BRIDGE FRAME: Last frame of Video 1 / Starting point for Video 2 extend
   - This frame should capture the scene at: {bridge_scene_text}
3. FIRST HALF PROMPT: Video generation prompt for Video 1 (opening → bridge)
4. SECOND HALF PROMPT: Video generation prompt for Video 2 (bridge → finale/CTA)

Remember:
- NO human faces (hands only if people are shown)
- Photorealistic commercial photography style
- 16:9 landscape composition
- BRIDGE FRAME must be a natural stopping point that can be extended
- Both video halves must have consistent visual style"""

    def parse_response(self, response_text: str, input_data: ImageGeneratorInput) -> ImageGeneratorOutput:
        """Parse LLM response into structured output."""
        data = self._extract_json_from_response(response_text)
        
        # Calculate scene splits
        scenes = input_data.scenes
        total_duration = input_data.target_duration
        half_duration = total_duration // 2
        
        first_half_scenes = []
        second_half_scenes = []
        accumulated_duration = 0
        
        for scene in scenes:
            scene_duration = scene.get("duration_seconds", scene.get("duration", 3))
            if accumulated_duration < half_duration:
                first_half_scenes.append(scene)
            else:
                second_half_scenes.append(scene)
            accumulated_duration += scene_duration

        return ImageGeneratorOutput(
            success=True,
            opening_frame_prompt=data.get("opening_frame_prompt", ""),
            bridge_frame_prompt=data.get("bridge_frame_prompt", ""),
            style_description=data.get("style_description", ""),
            visual_continuity_notes=data.get("visual_continuity_notes", ""),
            motion_suggestions=data.get("motion_suggestions", []),
            first_half_prompt=data.get("first_half_prompt", ""),
            second_half_prompt=data.get("second_half_prompt", ""),
            first_half_scenes=first_half_scenes,
            second_half_scenes=second_half_scenes,
            bridge_scene_description=data.get("bridge_scene_description", ""),
        )

    def generate_frames(
        self,
        input_data: ImageGeneratorInput,
        context: dict[str, Any] | None = None,
    ) -> ImageGeneratorOutput:
        """Generate frame prompts and then create actual images using Azure FLUX-1.1-pro.

        This method first generates optimized prompts, then calls Azure FLUX
        to create the actual images for split video generation.

        Args:
            input_data: Image generator input
            context: Optional context from previous agents

        Returns:
            ImageGeneratorOutput with prompts and generated image URLs
        """
        # First, generate the prompts using the LLM
        output = self.run(input_data, context)

        if not output.success:
            return output

        # Now generate actual images using Azure FLUX-1.1-pro
        try:
            from src.workers.clients.azure_image import get_azure_image_client
            from src.shared.storage import get_storage

            client = get_azure_image_client()
            storage = get_storage()

            # Generate opening frame
            logger.info(
                "generating_opening_frame",
                job_id=input_data.job_id,
                prompt_length=len(output.opening_frame_prompt),
            )
            opening_result = client.generate_image(
                prompt=output.opening_frame_prompt,
                size="1440x1024",  # 16:9 landscape (max 1440 width)
            )

            # Store opening frame
            if opening_result.image_bytes:
                output.opening_frame_key = f"{input_data.user_id}/{input_data.job_id}/opening_frame.png"
                storage.upload_file("images", output.opening_frame_key, opening_result.image_bytes)
                output.opening_frame_url = storage.generate_download_url("images", output.opening_frame_key)

            # Generate bridge frame
            logger.info(
                "generating_bridge_frame",
                job_id=input_data.job_id,
                prompt_length=len(output.bridge_frame_prompt),
            )
            bridge_result = client.generate_image(
                prompt=output.bridge_frame_prompt,
                size="1440x1024",
            )

            # Store bridge frame
            if bridge_result.image_bytes:
                output.bridge_frame_key = f"{input_data.user_id}/{input_data.job_id}/bridge_frame.png"
                storage.upload_file("images", output.bridge_frame_key, bridge_result.image_bytes)
                output.bridge_frame_url = storage.generate_download_url("images", output.bridge_frame_key)

            logger.info(
                "frames_generated_successfully",
                job_id=input_data.job_id,
                opening_key=output.opening_frame_key,
                bridge_key=output.bridge_frame_key,
            )

        except Exception as e:
            logger.error(
                "frame_generation_failed",
                job_id=input_data.job_id,
                error=str(e),
            )
            output.success = False
            output.error = f"Failed to generate frames: {str(e)}"

        return output
