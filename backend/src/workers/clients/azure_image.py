"""Azure OpenAI FLUX-1.1-pro image generation API client."""
import base64
from typing import Any

from openai import OpenAI

from src.shared.exceptions import AzureImageError
from src.shared.logging import get_logger


logger = get_logger(__name__)


class AzureImageResponse:
    """Response model for Azure FLUX image generation."""
    
    def __init__(self, data: Any) -> None:
        self.created = getattr(data, "created", 0)
        self.image_b64 = ""
        self.image_bytes: bytes | None = None
        
        if hasattr(data, "data") and data.data:
            first_image = data.data[0]
            self.image_b64 = getattr(first_image, "b64_json", "") or ""
            if self.image_b64:
                self.image_bytes = base64.b64decode(self.image_b64)


class AzureImageClient:
    """Client for Azure OpenAI FLUX-1.1-pro image generation.

    Provides methods for:
    - Generating images from text prompts
    - Creating consistent style images for video frames

    Example:
        >>> client = AzureImageClient(
        ...     api_key="your-key",
        ...     endpoint="https://your-resource.openai.azure.com/openai/v1/"
        ... )
        >>> result = await client.generate_image(
        ...     prompt="A modern kitchen with stainless steel appliances",
        ...     size="1024x1024"
        ... )
        >>> with open("output.png", "wb") as f:
        ...     f.write(result.image_bytes)
    """

    # Azure FLUX supported sizes (max width/height: 1440)
    SUPPORTED_SIZES = ["1024x1024", "1024x768", "768x1024", "1440x1024", "1024x1440"]

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment_name: str = "FLUX-1.1-pro",
    ) -> None:
        """Initialize Azure FLUX client.

        Args:
            api_key: Azure OpenAI API key
            endpoint: Azure OpenAI endpoint URL (e.g., https://your-resource.openai.azure.com/openai/v1/)
            deployment_name: Model deployment name (default: FLUX-1.1-pro)
        """
        self._api_key = api_key
        self._endpoint = endpoint.rstrip("/") + "/"
        self._deployment_name = deployment_name
        
        # Initialize OpenAI client with Azure endpoint
        self._client = OpenAI(
            base_url=self._endpoint,
            api_key=self._api_key,
        )
        
        logger.info(
            "azure_flux_client_initialized",
            endpoint=self._endpoint,
            deployment=self._deployment_name,
        )

    def generate_image(
        self,
        prompt: str,
        size: str = "1440x1024",  # 16:9 landscape for video frames (max 1440)
        n: int = 1,
    ) -> AzureImageResponse:
        """Generate an image using Azure FLUX-1.1-pro.

        Args:
            prompt: Text prompt describing the image to generate
            size: Image size (1024x1024, 1024x768, 768x1024, 1440x1024, 1024x1440)
            n: Number of images to generate (default: 1)

        Returns:
            AzureImageResponse with image bytes

        Raises:
            AzureImageError: If API call fails

        Example:
            >>> result = client.generate_image(
            ...     prompt="Modern kitchen with sleek appliances",
            ...     size="1440x1024"
            ... )
            >>> with open("frame.png", "wb") as f:
            ...     f.write(result.image_bytes)
        """
        # Validate size
        if size not in self.SUPPORTED_SIZES:
            logger.warning(
                "unsupported_size_using_default",
                requested=size,
                using="1440x1024",
            )
            size = "1440x1024"

        logger.info(
            "generating_image",
            prompt_length=len(prompt),
            size=size,
            model=self._deployment_name,
        )

        try:
            response = self._client.images.generate(
                model=self._deployment_name,
                prompt=prompt,
                n=n,
                size=size,
            )

            result = AzureImageResponse(response)

            logger.info(
                "image_generation_complete",
                has_image=bool(result.image_bytes),
                image_size=len(result.image_bytes) if result.image_bytes else 0,
            )

            return result

        except Exception as e:
            logger.error("image_generation_failed", error=str(e))
            raise AzureImageError(f"Image generation failed: {e}")

    def generate_video_frame(
        self,
        product_description: str,
        frame_type: str,  # "opening" or "closing"
        style_reference: str | None = None,
        visual_elements: list[str] | None = None,
    ) -> AzureImageResponse:
        """Generate a video frame image for kitchen product advertisement.

        Args:
            product_description: Description of the kitchen product
            frame_type: Type of frame ("opening" or "closing")
            style_reference: Optional style description for consistency
            visual_elements: List of visual elements to include

        Returns:
            AzureImageResponse with generated frame image

        Example:
            >>> opening_frame = client.generate_video_frame(
            ...     product_description="Stainless steel air fryer with digital display",
            ...     frame_type="opening",
            ...     visual_elements=["modern kitchen", "countertop setting"]
            ... )
        """
        elements_text = ""
        if visual_elements:
            elements_text = f", featuring {', '.join(visual_elements)}"

        style_text = ""
        if style_reference:
            style_text = f" Style: {style_reference}."

        if frame_type == "opening":
            prompt = f"""Professional product photography for video advertisement opening frame.
Kitchen product: {product_description}{elements_text}.
High-end commercial photography style, clean modern kitchen background, 
dramatic lighting highlighting the product, photorealistic quality.
No people, no faces, no text overlays. Focus on the product in an elegant kitchen setting.{style_text}"""
        else:  # closing
            prompt = f"""Professional product photography for video advertisement closing frame.
Kitchen product: {product_description}{elements_text}.
Hero shot of the product, slightly elevated angle, premium feel,
clean modern kitchen background, soft gradient lighting.
No people, no faces, no text overlays. Product as the hero element.{style_text}"""

        return self.generate_image(
            prompt=prompt,
            size="1792x1024",  # 16:9 landscape for video
        )

    async def close(self) -> None:
        """Close client connections (no-op for sync client)."""
        pass


# Singleton instance
_azure_image_client: AzureImageClient | None = None


def get_azure_image_client() -> AzureImageClient:
    """Get Azure image client singleton instance.

    Returns:
        AzureImageClient instance

    Raises:
        AzureImageError: If client cannot be initialized
    """
    global _azure_image_client

    if _azure_image_client is None:
        from src.shared.config import get_settings
        from src.shared.secrets import get_secrets

        settings = get_settings()
        secrets = get_secrets()

        try:
            api_key = secrets.get_secret(settings.secrets_azure_image_key)
            endpoint = settings.azure_openai_endpoint

            if not endpoint:
                raise AzureImageError("Azure OpenAI endpoint not configured")

            _azure_image_client = AzureImageClient(
                api_key=api_key,
                endpoint=endpoint,
                deployment_name=settings.azure_flux_deployment_name,
            )
        except Exception as e:
            raise AzureImageError(f"Failed to initialize Azure image client: {e}")

    return _azure_image_client

    return _azure_image_client
