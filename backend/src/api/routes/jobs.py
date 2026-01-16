"""Job routes for video generation workflow."""
import json

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter
from fastapi.responses import Response

from src.api.dependencies.auth import AuthenticatedUser
from src.api.models.jobs import (
    CreateJobRequest,
    JobListResponse,
    JobResponse,
    JobStatus,
    RegenerateJobRequest,
)
from src.shared.cache_service import get_cache_service
from src.shared.config import get_settings
from src.shared.db import get_db
from src.shared.exceptions import NotFoundError, ValidationError
from src.shared.logging import get_logger

router = APIRouter(prefix="/jobs", tags=["Jobs"])
logger = get_logger(__name__)


def _job_to_response(job: dict) -> JobResponse:
    """Convert job dict to response model."""
    return JobResponse(
        job_id=job["job_id"],
        user_id=job["user_id"],
        product_id=job["product_id"],
        status=JobStatus(job["status"]),
        adjustments=job.get("adjustments", {}),
        step_outputs=job.get("step_outputs", {}),
        video_url=None,  # Video URLs served via cache endpoints
        audio_url=None,  # Audio URLs served via cache endpoints
        error_message=job.get("error_message"),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
    )


@router.post("/", response_model=JobResponse)
async def create_job(
    request: CreateJobRequest,
    current_user: AuthenticatedUser,
) -> JobResponse:
    """
    Create a new video generation job.

    Triggers the Step Functions workflow for processing.
    """
    settings = get_settings()
    db = get_db()

    # Verify product exists
    product = db.get_product(current_user.user_id, request.product_id)
    if not product:
        raise NotFoundError("Product", request.product_id)

    # Create job record
    job = db.create_job(
        user_id=current_user.user_id,
        product_id=request.product_id,
        adjustments=request.adjustments.model_dump() if request.adjustments else {},
    )

    # Start Step Functions execution
    sfn_client = boto3.client("stepfunctions", region_name=settings.aws_region)

    execution_input = {
        "user_id": current_user.user_id,
        "job_id": job["job_id"],
        "product_id": request.product_id,
        "product": {
            "title": product["title"],
            "description": product["description"],
            "price": product["price"],
            "image_keys": product["image_keys"],
        },
        "adjustments": job["adjustments"],
    }

    try:
        response = sfn_client.start_execution(
            stateMachineArn=settings.stepfunctions_state_machine_arn,
            name=f"job-{job['job_id']}",
            input=json.dumps(execution_input, default=str),
        )
        logger.info(
            "step_function_started",
            job_id=job["job_id"],
            execution_arn=response.get("executionArn")
        )
    except ClientError as e:
        # Update job status to failed if we can't start execution
        try:
            db.update_job_status(
                current_user.user_id,
                job["job_id"],
                status="FAILED",
                error_message=f"Failed to start workflow: {str(e)}",
            )
        except Exception:
            # If we can't update the job status, log the error
            logger.warning("failed_to_update_job_status", job_id=job["job_id"], error=str(e))
        raise

    return _job_to_response(job)


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    current_user: AuthenticatedUser,
    status: JobStatus | None = None,
    limit: int = 50,
) -> JobListResponse:
    """
    List all jobs for the current user.

    Optionally filter by status.
    """
    db = get_db()

    jobs = db.list_jobs(
        user_id=current_user.user_id,
        limit=limit,
        status=status.value if status else None,
    )

    job_responses = [_job_to_response(job) for job in jobs]

    return JobListResponse(jobs=job_responses, count=len(job_responses))


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user: AuthenticatedUser,
) -> JobResponse:
    """
    Get a specific job by ID.
    """
    db = get_db()

    job = db.get_job(current_user.user_id, job_id)
    if not job:
        raise NotFoundError("Job", job_id)

    return _job_to_response(job)


@router.post("/{job_id}/regenerate", response_model=JobResponse)
async def regenerate_job(
    job_id: str,
    request: RegenerateJobRequest,
    current_user: AuthenticatedUser,
) -> JobResponse:
    """
    Regenerate video with new adjustments.

    Creates a new job based on the same product with updated adjustments.
    Extends TTL for all product images before regeneration.
    """
    db = get_db()
    cache_service = get_cache_service()

    # Get original job
    original_job = db.get_job(current_user.user_id, job_id)
    if not original_job:
        raise NotFoundError("Job", job_id)

    # Only allow regeneration of completed or failed jobs
    if original_job["status"] not in ("COMPLETE", "FAILED"):
        raise ValidationError(
            f"Cannot regenerate job in status: {original_job['status']}",
            field="job_id",
        )

    # Get product for Step Functions input
    product = db.get_product(current_user.user_id, original_job["product_id"])
    if not product:
        raise NotFoundError("Product", original_job["product_id"])

    # Extend TTL for all product images before regeneration
    for image_id in product.get("image_keys", []):
        cache_service.extend_image_ttl(current_user.user_id, image_id)

    logger.info(
        "image_ttl_extended_for_regeneration",
        job_id=job_id,
        product_id=original_job["product_id"],
        image_count=len(product.get("image_keys", [])),
    )

    # Create new job with merged adjustments
    original_adjustments = original_job.get("adjustments", {})
    new_adjustments = request.adjustments.model_dump(exclude_none=True) if request.adjustments else {}
    merged_adjustments = {**original_adjustments, **new_adjustments}

    new_job = db.create_job(
        user_id=current_user.user_id,
        product_id=original_job["product_id"],
        adjustments=merged_adjustments,
    )

    # Start Step Functions execution
    settings = get_settings()
    sfn_client = boto3.client("stepfunctions", region_name=settings.aws_region)

    execution_input = {
        "user_id": current_user.user_id,
        "job_id": new_job["job_id"],
        "product_id": original_job["product_id"],
        "product": {
            "title": product["title"],
            "description": product["description"],
            "price": product["price"],
            "image_keys": product["image_keys"],
        },
        "adjustments": merged_adjustments,
        "regeneration_of": job_id,
    }

    try:
        response = sfn_client.start_execution(
            stateMachineArn=settings.stepfunctions_state_machine_arn,
            name=f"job-{new_job['job_id']}",
            input=json.dumps(execution_input, default=str),
        )
        logger.info(
            "regeneration_step_function_started",
            original_job_id=job_id,
            new_job_id=new_job["job_id"],
            execution_arn=response.get("executionArn")
        )
    except ClientError as e:
        # Update job status to failed if we can't start execution
        try:
            db.update_job_status(
                current_user.user_id,
                new_job["job_id"],
                status="FAILED",
                error_message=f"Failed to start regeneration workflow: {str(e)}",
            )
        except Exception:
            # If we can't update the job status, log the error
            logger.warning("failed_to_update_regeneration_job_status", job_id=new_job["job_id"], error=str(e))
        raise

    return _job_to_response(new_job)


@router.get("/{job_id}/video")
async def get_video(
    job_id: str,
    current_user: AuthenticatedUser,
) -> Response:
    """
    Get the generated video from cache.

    Returns video bytes with appropriate content type.
    Returns 404 if video has expired from cache.
    """
    db = get_db()
    cache_service = get_cache_service()

    job = db.get_job(current_user.user_id, job_id)
    if not job:
        raise NotFoundError("Job", job_id)

    if job.get("status") != "COMPLETE":
        raise ValidationError(
            f"Video not available. Job status: {job.get('status')}",
            field="job_id",
        )

    # Retrieve video from cache
    video_data = cache_service.get_video(current_user.user_id, job_id)

    if video_data is None:
        raise NotFoundError("Video", job_id)

    logger.info("video_retrieved", job_id=job_id, size=len(video_data))

    return Response(
        content=video_data,
        media_type="video/mp4",
        headers={"Cache-Control": "private, max-age=3600"},
    )