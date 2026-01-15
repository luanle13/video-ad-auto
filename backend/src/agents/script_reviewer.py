"""Script Reviewer Agent - Quality control and compliance checking."""
from typing import Any

from pydantic import BaseModel, Field

from src.agents.base import AgentInput, AgentOutput, BaseAgent


class ReviewFeedback(BaseModel):
    """Specific feedback item."""

    category: str = Field(..., description="hook|content|cta|compliance|pacing|engagement")
    severity: str = Field(..., description="critical|warning|suggestion")
    issue: str
    recommendation: str
    scene_number: int | None = None


class ScriptReviewerInput(AgentInput):
    """Input for Script Reviewer Agent."""

    # Optimized script
    hook: str
    scenes: list[dict[str, Any]]
    call_to_action: str
    full_voiceover_text: str
    estimated_duration_seconds: int

    # Original product info for fact-checking
    product_title: str
    product_price: str
    key_features: list[str]
    unique_selling_points: list[str]

    # Optimization context
    pacing_notes: list[str] = Field(default_factory=list)
    engagement_hooks: list[str] = Field(default_factory=list)

    # Review parameters
    target_platform: str = "tiktok"
    brand_voice: str | None = Field(None, description="Description of brand voice to maintain")


class ScriptReviewerOutput(AgentOutput):
    """Output from Script Reviewer Agent."""

    # Review decision
    approved: bool = Field(..., description="Whether script passes review")
    overall_score: int = Field(..., ge=1, le=10, description="Overall quality score")

    # Feedback
    feedback: list[dict[str, Any]] = Field(default_factory=list)
    critical_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)

    # Compliance
    compliance_passed: bool = True
    compliance_issues: list[str] = Field(default_factory=list)

    # Final script (with any auto-fixes applied)
    final_hook: str = ""
    final_scenes: list[dict[str, Any]] = Field(default_factory=list)
    final_cta: str = ""
    final_voiceover: str = ""

    # Review summary
    review_summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    areas_for_improvement: list[str] = Field(default_factory=list)


class ScriptReviewerAgent(BaseAgent):
    """Reviews scripts for quality, compliance, and brand consistency."""

    name = "ScriptReviewer"
    description = "Performs quality control and compliance checking on video scripts"
    max_tokens = 2500
    temperature = 0.3  # Lower temperature for consistent evaluation

    COMPLIANCE_RULES = [
        "No false or misleading claims about product capabilities",
        "No exaggerated health or safety claims",
        "Price claims must be accurate",
        "No prohibited words: 'guaranteed', 'miracle', '100% effective'",
        "CTA must not be deceptive or manipulative",
        "No copyright-infringing content suggestions",
        "No discriminatory or offensive content",
        "Claims must be substantiated by product info",
    ]

    QUALITY_CRITERIA = [
        "Hook captures attention within platform requirements",
        "Clear value proposition within first 5 seconds",
        "Logical flow from problem to solution to CTA",
        "Voiceover is natural and conversational",
        "Visual descriptions are actionable for video production",
        "CTA is clear, specific, and compelling",
        "Pacing appropriate for platform",
        "Engagement hooks present throughout",
    ]

    @property
    def system_prompt(self) -> str:
        compliance_text = "\n".join(f"- {rule}" for rule in self.COMPLIANCE_RULES)
        quality_text = "\n".join(f"- {criterion}" for criterion in self.QUALITY_CRITERIA)

        return f"""You are an expert content reviewer specializing in short-form video scripts for e-commerce.

Your task is to review video scripts for:

1. COMPLIANCE (Must Pass)
{compliance_text}

2. QUALITY CRITERIA
{quality_text}

3. BRAND CONSISTENCY
- Tone matches brand voice (if specified)
- Messaging is consistent throughout
- No conflicting claims

4. ENGAGEMENT EFFECTIVENESS
- Hook is compelling
- Pattern interrupts are effective
- CTA drives action

SCORING:
- 9-10: Excellent, ready for production
- 7-8: Good, minor suggestions only
- 5-6: Acceptable, some improvements needed
- 3-4: Needs revision, significant issues
- 1-2: Reject, major problems

AUTO-FIX:
For minor issues, provide corrected versions in the final script.
For major issues, reject and provide specific feedback.

You must respond with valid JSON using the following structure:
{{
    "approved": true,
    "overall_score": 8,
    "feedback": [
        {{
            "category": "hook|content|cta|compliance|pacing|engagement",
            "severity": "critical|warning|suggestion",
            "issue": "Description of issue",
            "recommendation": "How to fix",
            "scene_number": null
        }}
    ],
    "critical_issues": ["Issue 1", "Issue 2"],
    "warnings": ["Warning 1"],
    "suggestions": ["Suggestion 1"],
    "compliance_passed": true,
    "compliance_issues": [],
    "final_hook": "Approved/fixed hook",
    "final_scenes": [],
    "final_cta": "Approved/fixed CTA",
    "final_voiceover": "Complete approved voiceover",
    "review_summary": "Brief summary of review",
    "strengths": ["Strength 1", "Strength 2"],
    "areas_for_improvement": ["Area 1"]
}}"""

    def build_user_prompt(self, input_data: ScriptReviewerInput, context: dict[str, Any]) -> str:
        """Build user prompt with script and product info for fact-checking."""
        scenes_text = ""
        for scene in input_data.scenes:
            scenes_text += f"""
Scene {scene.get('scene_number', '?')} ({scene.get('duration_seconds', '?')}s):
  Visual: {scene.get('visual_description', '')}
  Voiceover: {scene.get('voiceover_text', '')}
  Text Overlay: {scene.get('text_overlay', 'None')}
  Engagement Note: {scene.get('engagement_note', 'None')}
"""

        features_text = "\n".join(f"- {f}" for f in input_data.key_features[:5])
        usps_text = "\n".join(f"- {u}" for u in input_data.unique_selling_points[:3])

        brand_voice_instruction = ""
        if input_data.brand_voice:
            brand_voice_instruction = f"\n\nBRAND VOICE TO MAINTAIN:\n{input_data.brand_voice}"

        return f"""Review this video script for quality and compliance:

=== SCRIPT TO REVIEW ===

HOOK: {input_data.hook}

SCENES:
{scenes_text}

CALL TO ACTION: {input_data.call_to_action}

FULL VOICEOVER:
{input_data.full_voiceover_text}

DURATION: {input_data.estimated_duration_seconds} seconds
PLATFORM: {input_data.target_platform}

=== PRODUCT INFORMATION (for fact-checking) ===

PRODUCT: {input_data.product_title}
PRICE: {input_data.product_price}

VERIFIED FEATURES:
{features_text}

VERIFIED USPs:
{usps_text}
{brand_voice_instruction}

=== OPTIMIZATION CONTEXT ===

PACING ADJUSTMENTS MADE:
{chr(10).join('- ' + note for note in input_data.pacing_notes) if input_data.pacing_notes else 'None noted'}

ENGAGEMENT HOOKS ADDED:
{chr(10).join('- ' + hook for hook in input_data.engagement_hooks) if input_data.engagement_hooks else 'None noted'}

Review this script thoroughly. Approve only if it meets all compliance requirements and scores 7 or above on quality."""

    def parse_response(self, response_text: str, input_data: ScriptReviewerInput) -> ScriptReviewerOutput:
        """Parse LLM response into structured output."""
        data = self._extract_json_from_response(response_text)

        # Process feedback items
        feedback = []
        critical_issues = []
        warnings = []
        suggestions = []

        for item in data.get("feedback", []):
            severity = item.get("severity", "suggestion")
            issue = item.get("issue", "")

            if severity == "critical":
                critical_issues.append(issue)
            elif severity == "warning":
                warnings.append(issue)
            else:
                suggestions.append(issue)

            feedback.append({
                "category": item.get("category", "content"),
                "severity": severity,
                "issue": issue,
                "recommendation": item.get("recommendation", ""),
                "scene_number": item.get("scene_number"),
            })

        # Determine approval
        approved = data.get("approved", False)
        compliance_passed = data.get("compliance_passed", True)
        overall_score = data.get("overall_score", 5)

        # If compliance fails, force rejection
        if not compliance_passed:
            approved = False

        # Get final script (original if rejected without fixes)
        final_scenes = data.get("final_scenes", input_data.scenes)

        return ScriptReviewerOutput(
            success=True,
            approved=approved,
            overall_score=overall_score,
            feedback=feedback,
            critical_issues=data.get("critical_issues", critical_issues),
            warnings=data.get("warnings", warnings),
            suggestions=data.get("suggestions", suggestions),
            compliance_passed=compliance_passed,
            compliance_issues=data.get("compliance_issues", []),
            final_hook=data.get("final_hook", input_data.hook),
            final_scenes=final_scenes,
            final_cta=data.get("final_cta", input_data.call_to_action),
            final_voiceover=data.get("final_voiceover", input_data.full_voiceover_text),
            review_summary=data.get("review_summary", ""),
            strengths=data.get("strengths", []),
            areas_for_improvement=data.get("areas_for_improvement", []),
        )
