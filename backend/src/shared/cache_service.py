"""Media cache service for images, audio, and video."""
import base64
import hashlib
from functools import lru_cache

import structlog

from src.shared.cache import CacheClient, get_cache

logger = structlog.get_logger(__name__)

# TTL Constants (in seconds)
IMAGE_TTL = 7200  # 2 hours
AUDIO_TTL = 3600  # 1 hour
VIDEO_TTL = 3600  # 1 hour
REGEN_TTL = 86400  # 24 hours for regeneration


class CacheService:
    """Service for caching media files (images, audio, video).

    Provides high-level caching operations for media content with
    appropriate TTLs and key namespacing per user.
    """

    def __init__(self, cache_client: CacheClient) -> None:
        """Initialize the cache service.

        Args:
            cache_client: The underlying cache client to use.
        """
        self._cache = cache_client

    def _image_key(self, user_id: str, image_id: str) -> str:
        """Generate cache key for image data."""
        return f"image:{user_id}:{image_id}"

    def _image_meta_key(self, user_id: str, image_id: str) -> str:
        """Generate cache key for image metadata (content type)."""
        return f"image_meta:{user_id}:{image_id}"

    def _audio_key(self, user_id: str, job_id: str) -> str:
        """Generate cache key for audio data."""
        return f"audio:{user_id}:{job_id}"

    def _video_key(self, user_id: str, job_id: str) -> str:
        """Generate cache key for video data."""
        return f"video:{user_id}:{job_id}"

    def _generate_image_id(self, data: bytes) -> str:
        """Generate a hash-based image ID from image data.

        Uses SHA-256 hash truncated to 16 characters for
        content-addressable caching (deduplication).

        Args:
            data: Image binary data.

        Returns:
            A 16-character hex string image ID.
        """
        return hashlib.sha256(data).hexdigest()[:16]

    def store_image(
        self, user_id: str, data: bytes, content_type: str
    ) -> str | None:
        """Store an image in the cache.

        Args:
            user_id: User ID for namespacing.
            data: Image binary data.
            content_type: MIME type of the image (e.g., 'image/png').

        Returns:
            The generated image ID, or None if storage failed.
        """
        image_id = self._generate_image_id(data)
        data_key = self._image_key(user_id, image_id)
        meta_key = self._image_meta_key(user_id, image_id)

        # Store image data
        if not self._cache.set(data_key, data, IMAGE_TTL):
            logger.error(
                "cache_service_store_image_failed",
                user_id=user_id,
                image_id=image_id,
            )
            return None

        # Store content type
        if not self._cache.set_text(meta_key, content_type, IMAGE_TTL):
            logger.error(
                "cache_service_store_image_meta_failed",
                user_id=user_id,
                image_id=image_id,
            )
            # Clean up data key on meta failure
            self._cache.delete(data_key)
            return None

        logger.info(
            "cache_service_image_stored",
            user_id=user_id,
            image_id=image_id,
            content_type=content_type,
            size=len(data),
        )
        return image_id

    def get_image(
        self, user_id: str, image_id: str
    ) -> tuple[bytes, str] | None:
        """Retrieve an image from the cache.

        Args:
            user_id: User ID for namespacing.
            image_id: The image ID to retrieve.

        Returns:
            Tuple of (image_data, content_type), or None if not found.
        """
        data_key = self._image_key(user_id, image_id)
        meta_key = self._image_meta_key(user_id, image_id)

        data = self._cache.get(data_key)
        if data is None:
            logger.debug(
                "cache_service_image_not_found",
                user_id=user_id,
                image_id=image_id,
            )
            return None

        content_type = self._cache.get_text(meta_key)
        if content_type is None:
            # Default to octet-stream if metadata is missing
            content_type = "application/octet-stream"
            logger.warning(
                "cache_service_image_meta_missing",
                user_id=user_id,
                image_id=image_id,
            )

        return (data, content_type)

    def get_image_base64(self, user_id: str, image_id: str) -> str | None:
        """Retrieve an image as a base64 data URL.

        Args:
            user_id: User ID for namespacing.
            image_id: The image ID to retrieve.

        Returns:
            Data URL string (e.g., 'data:image/png;base64,...'), or None if not found.
        """
        result = self.get_image(user_id, image_id)
        if result is None:
            return None

        data, content_type = result
        encoded = base64.b64encode(data).decode("ascii")
        return f"data:{content_type};base64,{encoded}"

    def extend_image_ttl(self, user_id: str, image_id: str) -> bool:
        """Extend the TTL for a cached image.

        Args:
            user_id: User ID for namespacing.
            image_id: The image ID to extend.

        Returns:
            True if TTL was extended, False if image not found.
        """
        data_key = self._image_key(user_id, image_id)
        meta_key = self._image_meta_key(user_id, image_id)

        data_extended = self._cache.extend_ttl(data_key, IMAGE_TTL)
        meta_extended = self._cache.extend_ttl(meta_key, IMAGE_TTL)

        if data_extended:
            logger.debug(
                "cache_service_image_ttl_extended",
                user_id=user_id,
                image_id=image_id,
            )

        return data_extended and meta_extended

    def store_audio(self, user_id: str, job_id: str, data: bytes) -> bool:
        """Store audio data in the cache.

        Args:
            user_id: User ID for namespacing.
            job_id: Job ID associated with the audio.
            data: Audio binary data.

        Returns:
            True if storage succeeded, False otherwise.
        """
        key = self._audio_key(user_id, job_id)
        success = self._cache.set(key, data, AUDIO_TTL)

        if success:
            logger.info(
                "cache_service_audio_stored",
                user_id=user_id,
                job_id=job_id,
                size=len(data),
            )
        else:
            logger.error(
                "cache_service_store_audio_failed",
                user_id=user_id,
                job_id=job_id,
            )

        return success

    def get_audio(self, user_id: str, job_id: str) -> bytes | None:
        """Retrieve audio data from the cache.

        Args:
            user_id: User ID for namespacing.
            job_id: Job ID associated with the audio.

        Returns:
            Audio binary data, or None if not found.
        """
        key = self._audio_key(user_id, job_id)
        data = self._cache.get(key)

        if data is None:
            logger.debug(
                "cache_service_audio_not_found",
                user_id=user_id,
                job_id=job_id,
            )

        return data

    def store_video(self, user_id: str, job_id: str, data: bytes) -> bool:
        """Store video data in the cache.

        Args:
            user_id: User ID for namespacing.
            job_id: Job ID associated with the video.
            data: Video binary data.

        Returns:
            True if storage succeeded, False otherwise.
        """
        key = self._video_key(user_id, job_id)
        success = self._cache.set(key, data, VIDEO_TTL)

        if success:
            logger.info(
                "cache_service_video_stored",
                user_id=user_id,
                job_id=job_id,
                size=len(data),
            )
        else:
            logger.error(
                "cache_service_store_video_failed",
                user_id=user_id,
                job_id=job_id,
            )

        return success

    def get_video(self, user_id: str, job_id: str) -> bytes | None:
        """Retrieve video data from the cache.

        Args:
            user_id: User ID for namespacing.
            job_id: Job ID associated with the video.

        Returns:
            Video binary data, or None if not found.
        """
        key = self._video_key(user_id, job_id)
        data = self._cache.get(key)

        if data is None:
            logger.debug(
                "cache_service_video_not_found",
                user_id=user_id,
                job_id=job_id,
            )

        return data


@lru_cache
def get_cache_service() -> CacheService:
    """Get the singleton cache service instance.

    Returns:
        The singleton CacheService instance.
    """
    return CacheService(cache_client=get_cache())
