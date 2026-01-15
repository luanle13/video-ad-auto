"""Redis cache client wrapper."""
from functools import lru_cache

import redis
import structlog

logger = structlog.get_logger(__name__)


class CacheClient:
    """Redis cache client with common operations.

    Provides a simple interface for caching with Redis, supporting
    both binary and text data with configurable TTL.
    """

    def __init__(self, url: str, default_ttl: int = 3600) -> None:
        """Initialize the cache client.

        Args:
            url: Redis connection URL (e.g., redis://localhost:6379/0).
            default_ttl: Default time-to-live in seconds for cached items.
        """
        self._url = url
        self._default_ttl = default_ttl
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        """Lazily initialize and return the Redis client."""
        if self._client is None:
            self._client = redis.from_url(self._url, decode_responses=False)
            logger.info("redis_client_initialized", url=self._url)
        return self._client

    def set(self, key: str, value: bytes, ttl: int | None = None) -> bool:
        """Store a binary value in the cache.

        Args:
            key: Cache key.
            value: Binary data to store.
            ttl: Time-to-live in seconds. Uses default_ttl if not specified.

        Returns:
            True if the value was set successfully.
        """
        effective_ttl = ttl if ttl is not None else self._default_ttl
        try:
            result = self.client.setex(key, effective_ttl, value)
            logger.debug("cache_set", key=key, ttl=effective_ttl, size=len(value))
            return bool(result)
        except redis.RedisError as e:
            logger.error("cache_set_error", key=key, error=str(e))
            return False

    def get(self, key: str) -> bytes | None:
        """Retrieve a binary value from the cache.

        Args:
            key: Cache key.

        Returns:
            The cached binary data, or None if not found.
        """
        try:
            value = self.client.get(key)
            if value is not None:
                logger.debug("cache_hit", key=key)
            else:
                logger.debug("cache_miss", key=key)
            return value  # type: ignore[return-value]
        except redis.RedisError as e:
            logger.error("cache_get_error", key=key, error=str(e))
            return None

    def set_text(self, key: str, value: str, ttl: int | None = None) -> bool:
        """Store a text value in the cache.

        Args:
            key: Cache key.
            value: Text data to store.
            ttl: Time-to-live in seconds. Uses default_ttl if not specified.

        Returns:
            True if the value was set successfully.
        """
        return self.set(key, value.encode("utf-8"), ttl)

    def get_text(self, key: str) -> str | None:
        """Retrieve a text value from the cache.

        Args:
            key: Cache key.

        Returns:
            The cached text data, or None if not found.
        """
        value = self.get(key)
        if value is None:
            return None
        return value.decode("utf-8")

    def delete(self, key: str) -> bool:
        """Delete a key from the cache.

        Args:
            key: Cache key to delete.

        Returns:
            True if the key was deleted, False otherwise.
        """
        try:
            result = self.client.delete(key)
            logger.debug("cache_delete", key=key, deleted=bool(result))
            return bool(result)
        except redis.RedisError as e:
            logger.error("cache_delete_error", key=key, error=str(e))
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: Cache key to check.

        Returns:
            True if the key exists, False otherwise.
        """
        try:
            result = self.client.exists(key)
            return bool(result)
        except redis.RedisError as e:
            logger.error("cache_exists_error", key=key, error=str(e))
            return False

    def ttl(self, key: str) -> int:
        """Get the remaining time-to-live for a key.

        Args:
            key: Cache key.

        Returns:
            TTL in seconds, -1 if key has no expiry, -2 if key doesn't exist.
        """
        try:
            return self.client.ttl(key)  # type: ignore[return-value]
        except redis.RedisError as e:
            logger.error("cache_ttl_error", key=key, error=str(e))
            return -2

    def extend_ttl(self, key: str, ttl: int) -> bool:
        """Extend the time-to-live for an existing key.

        Args:
            key: Cache key.
            ttl: New time-to-live in seconds.

        Returns:
            True if the TTL was extended, False if the key doesn't exist.
        """
        try:
            result = self.client.expire(key, ttl)
            logger.debug("cache_extend_ttl", key=key, ttl=ttl, success=bool(result))
            return bool(result)
        except redis.RedisError as e:
            logger.error("cache_extend_ttl_error", key=key, error=str(e))
            return False


_cache_instance: CacheClient | None = None


@lru_cache
def get_cache() -> CacheClient:
    """Get the singleton cache client instance.

    The Redis URL is read from the REDIS_URL environment variable,
    defaulting to redis://localhost:6379/0 for local development.

    Returns:
        The singleton CacheClient instance.
    """
    import os

    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    default_ttl = int(os.environ.get("REDIS_DEFAULT_TTL", "3600"))
    return CacheClient(url=url, default_ttl=default_ttl)
