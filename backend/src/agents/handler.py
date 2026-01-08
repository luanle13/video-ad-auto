"""Lambda handler for agent execution in Step Functions."""

import json
from typing import Any

from src.agents.product_analyzer import ProductAnalyzerAgent, ProductAnalyzerInput
from src.agents.script_generator import ScriptGeneratorAgent, ScriptGeneratorInput
from src.agents.script_optimizer import ScriptOptimizerAgent, ScriptOptimizerInput
from src.agents.script_reviewer import ScriptReviewerAgent, ScriptReviewerInput
from src.shared.db import get_db
from src.shared.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

# Agent registry mapping task names to (AgentClass, InputClass)
AGENTS = {
    "analyze": (ProductAnalyzerAgent, ProductAnalyzerInput),
    "generate": (ScriptGeneratorAgent, ScriptGeneratorInput),
    "optimize": (ScriptOptimizerAgent, ScriptOptimizerInput),
    "review": (ScriptReviewerAgent, ScriptReviewerInput),
}

# Status mapping for each task
STATUS_MAP = {
    "analyze": "ANALYZING",
    "generate": "SCRIPTING",
    "optimize": "SCRIPTING",
    "review": "SCRIPTING",
}


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda handler for agent execution.

    Expected event structure from Step Functions:
    {
        "task": "analyze|generate|optimize|review",
        "user_id": "usr_...",
        "job_id": "job_...",
        "product": {
            "id": "prod_...",
            "title": "...",
            "description": "...",
            "price": "...",
            "url": "...",
            "image_keys": ["s3_key1", "s3_key2"]
        },
        "context": {
            "analyze": {"output": {...}},
            "generate": {"output": {...}},
            ...
        },
        "adjustments": {
            "tone": "energetic",
            "duration": 45,
            ...
        }
    }

    Returns:
    {
        "task": "analyze",
        "success": true,
        "output": {...}
    }
    """
    task = event.get("task")
    user_id = event["user_id"]
    job_id = event["job_id"]

    logger.info("agent_handler_invoked", task=task, job_id=job_id, user_id=user_id)

    if task not in AGENTS:
        logger.error("unknown_task", task=task, available_tasks=list(AGENTS.keys()))
        raise ValueError(f"Unknown task: {task}. Available tasks: {', '.join(AGENTS.keys())}")

    agent_class, input_class = AGENTS[task]
    db = get_db()

    try:
        # Update job status
        status = STATUS_MAP.get(task, "PROCESSING")
        db.update_job_status(user_id, job_id, status)
        logger.info("job_status_updated", job_id=job_id, status=status)

        # Build input based on task
        input_data = _build_input(task, event, input_class)
        context = event.get("context", {})

        # Run agent
        logger.info("agent_starting", task=task, agent=agent_class.__name__)
        agent = agent_class()
        output = agent.run(input_data, context)

        # Store output in job
        output_dict = output.model_dump()
        db.update_job_step_output(user_id, job_id, task, output_dict)
        logger.info(
            "agent_completed",
            task=task,
            job_id=job_id,
            success=output.success,
        )

        # Return output for next step
        return {
            "task": task,
            "success": output.success,
            "output": output_dict,
        }

    except Exception as e:
        logger.error(
            "agent_handler_error",
            task=task,
            job_id=job_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        # Update job to failed status
        db.update_job_status(user_id, job_id, "FAILED", error_message=str(e))
        raise


def _build_input(task: str, event: dict[str, Any], input_class: type) -> Any:
    """
    Build agent input from event data.

    Args:
        task: Task name (analyze, generate, optimize, review)
        event: Lambda event dictionary
        input_class: Pydantic input model class

    Returns:
        Instance of input_class with populated data
    """
    base = {
        "job_id": event["job_id"],
        "user_id": event["user_id"],
    }

    context = event.get("context", {})
    adjustments = event.get("adjustments", {})

    if task == "analyze":
        # Product analyzer input
        product = event["product"]
        return input_class(
            **base,
            title=product["title"],
            description=product.get("description", ""),
            price=product["price"],
            image_keys=product.get("image_keys", []),
        )

    elif task == "generate":
        # Script generator input from analyzer output
        analysis = context.get("analyze", {}).get("output", {})

        return input_class(
            **base,
            product_title=event["product"]["title"],
            price=event["product"]["price"],
            key_features=analysis.get("key_features", []),
            unique_selling_points=analysis.get("unique_selling_points", []),
            target_audience=analysis.get("target_audience", ""),
            visual_elements=analysis.get("visual_elements", []),
            price_positioning=analysis.get("price_positioning", "mid-range"),
            suggested_hooks=analysis.get("suggested_hooks", []),
            # Market insights would come from insight agent (not yet implemented)
            content_angles=adjustments.get("content_angles", []),
            trending_formats=adjustments.get("trending_formats", []),
            platform_tips=adjustments.get("platform_tips", {}),
            suggested_music_style=adjustments.get("suggested_music_style", ""),
            # User preferences
            target_duration=adjustments.get("target_duration", 45),
            tone=adjustments.get("tone"),
            emphasis=adjustments.get("emphasis"),
        )

    elif task == "optimize":
        # Script optimizer input from generator output
        generation = context.get("generate", {}).get("output", {})

        return input_class(
            **base,
            hook=generation.get("hook", ""),
            scenes=generation.get("scenes", []),
            call_to_action=generation.get("call_to_action", ""),
            full_voiceover_text=generation.get("full_voiceover_text", ""),
            estimated_duration_seconds=generation.get("estimated_duration_seconds", 45),
            primary_platform=adjustments.get("primary_platform", "tiktok"),
            trending_formats=adjustments.get("trending_formats", []),
            platform_tips=adjustments.get("platform_tips", {}),
            tone=adjustments.get("tone"),
            pacing=adjustments.get("pacing"),
        )

    elif task == "review":
        # Script reviewer input from optimizer output
        optimization = context.get("optimize", {}).get("output", {})
        analysis = context.get("analyze", {}).get("output", {})

        return input_class(
            **base,
            hook=optimization.get("optimized_hook", ""),
            scenes=optimization.get("optimized_scenes", []),
            call_to_action=optimization.get("optimized_cta", ""),
            full_voiceover_text=optimization.get("optimized_voiceover", ""),
            estimated_duration_seconds=optimization.get("estimated_duration_seconds", 45),
            # Original product info for fact-checking
            product_title=event["product"]["title"],
            product_price=event["product"]["price"],
            key_features=analysis.get("key_features", []),
            unique_selling_points=analysis.get("unique_selling_points", []),
            # Optimization context
            pacing_notes=optimization.get("pacing_notes", []),
            engagement_hooks=optimization.get("engagement_hooks", []),
            # Review parameters
            target_platform=adjustments.get("primary_platform", "tiktok"),
            brand_voice=adjustments.get("brand_voice"),
        )

    else:
        logger.error("unhandled_task_in_build_input", task=task)
        raise ValueError(f"Input building not implemented for task: {task}")
