"""Product models."""
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

from src.shared.validators import sanitize_html, validate_safe_filename

# Custom types with HTML sanitization
SanitizedStr = Annotated[str, AfterValidator(sanitize_html)]
SafeFilenameStr = Annotated[str, AfterValidator(validate_safe_filename)]


class ImageUploadRequest(BaseModel):
    """Request for presigned upload URL."""

    filename: SafeFilenameStr = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Filename with valid image extension",
    )
    content_type: str = Field(
        ...,
        pattern=r"^image/(jpeg|png|webp)$",
        description="Must be image/jpeg, image/png, or image/webp",
    )


class ImageUploadResponse(BaseModel):
    """Presigned upload URL response."""

    key: str
    url: str
    fields: dict[str, str]


class CreateProductRequest(BaseModel):
    """Create product request."""

    title: SanitizedStr = Field(..., min_length=1, max_length=200)
    description: SanitizedStr = Field(..., min_length=1, max_length=2000)
    price: str = Field(
        ...,
        pattern=r"^\d+(\.\d{1,2})?$",
        max_length=50,
        description="Price as string, e.g., '99.99'",
    )
    image_keys: list[str] = Field(..., min_length=1, max_length=5)


class UpdateProductRequest(BaseModel):
    """Update product request."""

    title: SanitizedStr | None = Field(None, min_length=1, max_length=200)
    description: SanitizedStr | None = Field(None, min_length=1, max_length=2000)
    price: str | None = Field(None, pattern=r"^\d+(\.\d{1,2})?$", max_length=50)


class ProductResponse(BaseModel):
    """Product response."""

    product_id: str
    user_id: str
    title: str
    description: str
    price: str
    image_keys: list[str]
    image_urls: list[str] = Field(default_factory=list, description="Presigned download URLs")
    created_at: str
    updated_at: str


class ImageUploadedResponse(BaseModel):
    """Response after direct image upload."""

    image_id: str = Field(..., description="Cache-generated image ID")
    product_id: str