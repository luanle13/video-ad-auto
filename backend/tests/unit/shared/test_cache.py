"""Tests for the Redis cache client."""
import os
from unittest.mock import MagicMock, patch

import pytest
import redis

from src.shared.cache import CacheClient, get_cache


class TestCacheClient:
    """Tests for CacheClient class."""

    def test_init(self):
        """Test CacheClient initialization."""
        client = CacheClient(url="redis://localhost:6379/0", default_ttl=7200)
        assert client._url == "redis://localhost:6379/0"
        assert client._default_ttl == 7200
        assert client._client is None

    def test_default_ttl(self):
        """Test default TTL value."""
        client = CacheClient(url="redis://localhost:6379/0")
        assert client._default_ttl == 3600

    @patch("src.shared.cache.redis.from_url")
    def test_client_lazy_initialization(self, mock_from_url):
        """Test that Redis client is lazily initialized."""
        mock_redis = MagicMock()
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        assert client._client is None

        # Access the client property
        result = client.client
        assert result == mock_redis
        mock_from_url.assert_called_once_with(
            "redis://localhost:6379/0", decode_responses=False
        )

    @patch("src.shared.cache.redis.from_url")
    def test_client_cached_after_first_access(self, mock_from_url):
        """Test that Redis client is cached after first access."""
        mock_redis = MagicMock()
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        _ = client.client
        _ = client.client

        # Should only be called once
        mock_from_url.assert_called_once()


class TestCacheClientSet:
    """Tests for CacheClient.set method."""

    @patch("src.shared.cache.redis.from_url")
    def test_set_success(self, mock_from_url):
        """Test successful set operation."""
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0", default_ttl=3600)
        result = client.set("test_key", b"test_value")

        assert result is True
        mock_redis.setex.assert_called_once_with("test_key", 3600, b"test_value")

    @patch("src.shared.cache.redis.from_url")
    def test_set_with_custom_ttl(self, mock_from_url):
        """Test set with custom TTL."""
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0", default_ttl=3600)
        result = client.set("test_key", b"test_value", ttl=600)

        assert result is True
        mock_redis.setex.assert_called_once_with("test_key", 600, b"test_value")

    @patch("src.shared.cache.redis.from_url")
    def test_set_error(self, mock_from_url):
        """Test set operation with Redis error."""
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = redis.RedisError("Connection failed")
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.set("test_key", b"test_value")

        assert result is False


class TestCacheClientGet:
    """Tests for CacheClient.get method."""

    @patch("src.shared.cache.redis.from_url")
    def test_get_hit(self, mock_from_url):
        """Test cache hit."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = b"test_value"
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.get("test_key")

        assert result == b"test_value"
        mock_redis.get.assert_called_once_with("test_key")

    @patch("src.shared.cache.redis.from_url")
    def test_get_miss(self, mock_from_url):
        """Test cache miss."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.get("nonexistent_key")

        assert result is None

    @patch("src.shared.cache.redis.from_url")
    def test_get_error(self, mock_from_url):
        """Test get operation with Redis error."""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = redis.RedisError("Connection failed")
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.get("test_key")

        assert result is None


class TestCacheClientText:
    """Tests for CacheClient text methods."""

    @patch("src.shared.cache.redis.from_url")
    def test_set_text(self, mock_from_url):
        """Test set_text encodes string to bytes."""
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.set_text("test_key", "hello world")

        assert result is True
        mock_redis.setex.assert_called_once_with(
            "test_key", 3600, b"hello world"
        )

    @patch("src.shared.cache.redis.from_url")
    def test_set_text_with_ttl(self, mock_from_url):
        """Test set_text with custom TTL."""
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.set_text("test_key", "hello world", ttl=120)

        assert result is True
        mock_redis.setex.assert_called_once_with(
            "test_key", 120, b"hello world"
        )

    @patch("src.shared.cache.redis.from_url")
    def test_get_text_hit(self, mock_from_url):
        """Test get_text decodes bytes to string."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = b"hello world"
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.get_text("test_key")

        assert result == "hello world"

    @patch("src.shared.cache.redis.from_url")
    def test_get_text_miss(self, mock_from_url):
        """Test get_text returns None on cache miss."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.get_text("nonexistent_key")

        assert result is None

    @patch("src.shared.cache.redis.from_url")
    def test_set_text_unicode(self, mock_from_url):
        """Test set_text with unicode characters."""
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.set_text("test_key", "Xin chào Việt Nam")

        assert result is True
        mock_redis.setex.assert_called_once_with(
            "test_key", 3600, "Xin chào Việt Nam".encode("utf-8")
        )


class TestCacheClientDelete:
    """Tests for CacheClient.delete method."""

    @patch("src.shared.cache.redis.from_url")
    def test_delete_existing_key(self, mock_from_url):
        """Test deleting an existing key."""
        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.delete("test_key")

        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    @patch("src.shared.cache.redis.from_url")
    def test_delete_nonexistent_key(self, mock_from_url):
        """Test deleting a nonexistent key."""
        mock_redis = MagicMock()
        mock_redis.delete.return_value = 0
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.delete("nonexistent_key")

        assert result is False

    @patch("src.shared.cache.redis.from_url")
    def test_delete_error(self, mock_from_url):
        """Test delete operation with Redis error."""
        mock_redis = MagicMock()
        mock_redis.delete.side_effect = redis.RedisError("Connection failed")
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.delete("test_key")

        assert result is False


class TestCacheClientExists:
    """Tests for CacheClient.exists method."""

    @patch("src.shared.cache.redis.from_url")
    def test_exists_true(self, mock_from_url):
        """Test exists returns True for existing key."""
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 1
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.exists("test_key")

        assert result is True
        mock_redis.exists.assert_called_once_with("test_key")

    @patch("src.shared.cache.redis.from_url")
    def test_exists_false(self, mock_from_url):
        """Test exists returns False for nonexistent key."""
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 0
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.exists("nonexistent_key")

        assert result is False

    @patch("src.shared.cache.redis.from_url")
    def test_exists_error(self, mock_from_url):
        """Test exists operation with Redis error."""
        mock_redis = MagicMock()
        mock_redis.exists.side_effect = redis.RedisError("Connection failed")
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.exists("test_key")

        assert result is False


class TestCacheClientTTL:
    """Tests for CacheClient.ttl method."""

    @patch("src.shared.cache.redis.from_url")
    def test_ttl_existing_key(self, mock_from_url):
        """Test getting TTL for existing key."""
        mock_redis = MagicMock()
        mock_redis.ttl.return_value = 300
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.ttl("test_key")

        assert result == 300
        mock_redis.ttl.assert_called_once_with("test_key")

    @patch("src.shared.cache.redis.from_url")
    def test_ttl_no_expiry(self, mock_from_url):
        """Test TTL returns -1 for key without expiry."""
        mock_redis = MagicMock()
        mock_redis.ttl.return_value = -1
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.ttl("test_key")

        assert result == -1

    @patch("src.shared.cache.redis.from_url")
    def test_ttl_nonexistent_key(self, mock_from_url):
        """Test TTL returns -2 for nonexistent key."""
        mock_redis = MagicMock()
        mock_redis.ttl.return_value = -2
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.ttl("nonexistent_key")

        assert result == -2

    @patch("src.shared.cache.redis.from_url")
    def test_ttl_error(self, mock_from_url):
        """Test TTL operation with Redis error."""
        mock_redis = MagicMock()
        mock_redis.ttl.side_effect = redis.RedisError("Connection failed")
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.ttl("test_key")

        assert result == -2


class TestCacheClientExtendTTL:
    """Tests for CacheClient.extend_ttl method."""

    @patch("src.shared.cache.redis.from_url")
    def test_extend_ttl_success(self, mock_from_url):
        """Test extending TTL for existing key."""
        mock_redis = MagicMock()
        mock_redis.expire.return_value = True
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.extend_ttl("test_key", 600)

        assert result is True
        mock_redis.expire.assert_called_once_with("test_key", 600)

    @patch("src.shared.cache.redis.from_url")
    def test_extend_ttl_nonexistent_key(self, mock_from_url):
        """Test extending TTL for nonexistent key."""
        mock_redis = MagicMock()
        mock_redis.expire.return_value = False
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.extend_ttl("nonexistent_key", 600)

        assert result is False

    @patch("src.shared.cache.redis.from_url")
    def test_extend_ttl_error(self, mock_from_url):
        """Test extend_ttl operation with Redis error."""
        mock_redis = MagicMock()
        mock_redis.expire.side_effect = redis.RedisError("Connection failed")
        mock_from_url.return_value = mock_redis

        client = CacheClient(url="redis://localhost:6379/0")
        result = client.extend_ttl("test_key", 600)

        assert result is False


class TestGetCache:
    """Tests for get_cache singleton function."""

    def test_get_cache_returns_cache_client(self):
        """Test get_cache returns a CacheClient instance."""
        get_cache.cache_clear()  # Clear cache before test
        with patch.dict(os.environ, {"REDIS_URL": "redis://test:6379/0"}):
            cache = get_cache()
            assert isinstance(cache, CacheClient)
            assert cache._url == "redis://test:6379/0"

    def test_get_cache_singleton(self):
        """Test get_cache returns the same instance."""
        get_cache.cache_clear()  # Clear cache before test
        with patch.dict(os.environ, {"REDIS_URL": "redis://test:6379/0"}):
            cache1 = get_cache()
            cache2 = get_cache()
            assert cache1 is cache2

    def test_get_cache_default_url(self):
        """Test get_cache uses default URL when not set."""
        get_cache.cache_clear()
        with patch.dict(os.environ, {}, clear=True):
            # Remove REDIS_URL if it exists
            os.environ.pop("REDIS_URL", None)
            cache = get_cache()
            assert cache._url == "redis://localhost:6379/0"

    def test_get_cache_custom_ttl(self):
        """Test get_cache uses custom default TTL."""
        get_cache.cache_clear()
        with patch.dict(
            os.environ,
            {"REDIS_URL": "redis://test:6379/0", "REDIS_DEFAULT_TTL": "7200"},
        ):
            cache = get_cache()
            assert cache._default_ttl == 7200
