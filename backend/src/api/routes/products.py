"""Products routes for image upload and retrieval."""
from fastapi import APIRouter, UploadFile
from fastapi.responses import Response

from src.api.dependencies.auth import AuthenticatedUser
from src.api.models import ImageUploadedResponse
from src.shared.cache_service import get_cache_service
from src.shared.db import get_db
from src.shared.exceptions import (
    FileTooLargeError,
    InvalidFileTypeError,
    NotFoundError,
    ValidationError,
)
from src.shared.logging import get_logger

router = APIRouter(prefix="/products", tags=["Products"])
logger = get_logger(__name__)

# Constants
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/{product_id}/images", response_model=ImageUploadedResponse)
async def upload_image(
    product_id: str,
    file: UploadFile,
    current_user: AuthenticatedUser,
) -> ImageUploadedResponse:
    """Upload an image directly to cache for a product.

    Validates file type (jpeg/png/webp) and size (<5MB), stores in cache,
    and adds the image ID to the product's image_keys.
    """
    db = get_db()
    cache_service = get_cache_service()

    # Verify product exists and belongs to user
    product = db.get_product(current_user.user_id, product_id)
    if not product:
        raise NotFoundError("Product", product_id)

    # Validate content type
    content_type = file.content_type
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise InvalidFileTypeError(list(ALLOWED_CONTENT_TYPES))

    # Read file content
    data = await file.read()

    # Validate file size
    if len(data) > MAX_FILE_SIZE:
        raise FileTooLargeError(max_size_mb=5)

    # Store in cache
    image_id = cache_service.store_image(
        user_id=current_user.user_id,
        data=data,
        content_type=content_type,
    )

    if image_id is None:
        raise ValidationError("Failed to store image in cache")

    # Add image to product
    db.add_product_image(current_user.user_id, product_id, image_id)

    logger.info(
        "image_uploaded",
        user_id=current_user.user_id,
        product_id=product_id,
        image_id=image_id,
        size=len(data),
        content_type=content_type,
    )

    return ImageUploadedResponse(image_id=image_id, product_id=product_id)


@router.get("/{product_id}/images/{image_id}")
async def get_image(
    product_id: str,
    image_id: str,
    current_user: AuthenticatedUser,
) -> Response:
    """Retrieve an image from cache.

    Returns the image bytes with appropriate content type.
    """
    db = get_db()
    cache_service = get_cache_service()

    # Verify product exists and belongs to user
    product = db.get_product(current_user.user_id, product_id)
    if not product:
        raise NotFoundError("Product", product_id)

    # Verify image belongs to product
    if image_id not in product.get("image_keys", []):
        raise NotFoundError("Image", image_id)

    # Retrieve from cache
    result = cache_service.get_image(current_user.user_id, image_id)

    if result is None:
        raise NotFoundError("Image", image_id)

    data, content_type = result

    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "private, max-age=3600"},
    )
