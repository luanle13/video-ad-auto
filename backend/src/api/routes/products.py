"""Product routes for managing user products."""
from fastapi import APIRouter

from src.api.dependencies.auth import AuthenticatedUser
from src.api.models.products import (
    CreateProductRequest,
    ImageUploadRequest,
    ImageUploadResponse,
    ProductResponse,
)
from src.shared.db import get_db
from src.shared.logging import get_logger
from src.shared.storage import get_storage

router = APIRouter()
logger = get_logger(__name__)


def _product_to_response(product: dict, storage_client) -> ProductResponse:
    """Convert product dict to response model with presigned URLs."""
    image_urls = []
    for key in product.get("image_keys", []):
        try:
            url = storage_client.generate_download_url("images", key)
            image_urls.append(url)
        except Exception:
            # If URL generation fails, skip this URL
            pass

    return ProductResponse(
        product_id=product["product_id"],
        user_id=product["user_id"],
        title=product["title"],
        description=product["description"],
        price=product["price"],
        image_keys=product.get("image_keys", []),
        image_urls=image_urls,
        created_at=product["created_at"],
        updated_at=product["updated_at"],
    )


@router.get("", response_model=list[ProductResponse])
async def list_products(
    current_user: AuthenticatedUser,
) -> list[ProductResponse]:
    """
    List all products for the current user.

    Returns products sorted by creation date (newest first).
    """
    db = get_db()
    storage = get_storage()

    products = db.list_products(user_id=current_user.user_id)

    logger.info(
        "products_listed",
        user_id=current_user.user_id,
        count=len(products),
    )

    return [_product_to_response(p, storage) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    current_user: AuthenticatedUser,
) -> ProductResponse:
    """
    Get a specific product by ID.

    Only returns products owned by the current user.
    """
    db = get_db()
    storage = get_storage()

    product = db.get_product(user_id=current_user.user_id, product_id=product_id)

    logger.info(
        "product_retrieved",
        user_id=current_user.user_id,
        product_id=product_id,
    )

    return _product_to_response(product, storage)


@router.post("", response_model=ProductResponse)
async def create_product(
    request: CreateProductRequest,
    current_user: AuthenticatedUser,
) -> ProductResponse:
    """
    Create a new product.

    Image keys should be obtained from the upload-url endpoint first.
    """
    db = get_db()
    storage = get_storage()

    product = db.create_product(
        user_id=current_user.user_id,
        title=request.title,
        description=request.description,
        price=request.price,
        image_keys=request.image_keys,
    )

    logger.info(
        "product_created",
        user_id=current_user.user_id,
        product_id=product["product_id"],
        image_count=len(request.image_keys),
    )

    return _product_to_response(product, storage)


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    current_user: AuthenticatedUser,
) -> dict:
    """
    Delete a product.

    Only deletes products owned by the current user.
    Note: This does not delete associated images from S3.
    """
    db = get_db()

    # Verify product exists and belongs to user (will raise NotFoundError if not)
    db.get_product(user_id=current_user.user_id, product_id=product_id)

    # Delete the product
    db.delete_product(user_id=current_user.user_id, product_id=product_id)

    logger.info(
        "product_deleted",
        user_id=current_user.user_id,
        product_id=product_id,
    )

    return {"message": "Product deleted successfully"}


@router.post("/upload-url", response_model=ImageUploadResponse)
async def get_upload_url(
    request: ImageUploadRequest,
    current_user: AuthenticatedUser,
) -> ImageUploadResponse:
    """
    Get a presigned URL for uploading a product image.

    The returned URL and fields should be used to upload the file directly to S3.
    After upload, use the returned key when creating the product.
    """
    storage = get_storage()

    # Generate a unique key for the image
    key = storage.generate_image_key(
        user_id=current_user.user_id,
        filename=request.filename,
    )

    # Generate presigned POST URL
    presigned_data = storage.generate_upload_url(
        bucket_type="images",
        key=key,
        content_type=request.content_type,
    )

    logger.info(
        "upload_url_generated",
        user_id=current_user.user_id,
        key=key,
        content_type=request.content_type,
    )

    return ImageUploadResponse(
        key=key,
        url=presigned_data["url"],
        fields=presigned_data["fields"],
    )
