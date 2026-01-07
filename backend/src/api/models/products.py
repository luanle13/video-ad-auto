"""Product models."""
from pydantic import BaseModel, Field


class ImageUploadRequest(BaseModel):
    """Request for presigned upload URL."""
    
    filename: str
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
    
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    price: str = Field(..., pattern=r"^\d+(\.\d{1,2})?$", description="Price as string, e.g., '99.99'")
    image_keys: list[str] = Field(..., min_length=1, max_length=5)


class UpdateProductRequest(BaseModel):
    """Update product request."""
    
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1, max_length=2000)
    price: str | None = Field(None, pattern=r"^\d+(\.\d{1,2})?$")


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