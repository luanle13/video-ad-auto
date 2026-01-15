"""Tests for the media cache service."""
import base64
import hashlib
from unittest.mock import MagicMock, patch

import pytest

from src.shared.cache_service import (
    AUDIO_TTL,
    IMAGE_TTL,
    REGEN_TTL,
    VIDEO_TTL,
    CacheService,
    get_cache_service,
)


class TestTTLConstants:
    """Tests for TTL constants."""

    def test_image_ttl(self):
        """Test IMAGE_TTL is 2 hours."""
        assert IMAGE_TTL == 7200

    def test_audio_ttl(self):
        """Test AUDIO_TTL is 1 hour."""
        assert AUDIO_TTL == 3600

    def test_video_ttl(self):
        """Test VIDEO_TTL is 1 hour."""
        assert VIDEO_TTL == 3600

    def test_regen_ttl(self):
        """Test REGEN_TTL is 24 hours."""
        assert REGEN_TTL == 86400


class TestCacheServiceInit:
    """Tests for CacheService initialization."""

    def test_init(self):
        """Test CacheService initialization."""
        mock_cache = MagicMock()
        service = CacheService(cache_client=mock_cache)
        assert service._cache == mock_cache


class TestCacheServiceKeyGeneration:
    """Tests for cache key generation methods."""

    def test_image_key(self):
        """Test image key format."""
        mock_cache = MagicMock()
        service = CacheService(cache_client=mock_cache)
        key = service._image_key("user123", "img456")
        assert key == "image:user123:img456"

    def test_image_meta_key(self):
        """Test image metadata key format."""
        mock_cache = MagicMock()
        service = CacheService(cache_client=mock_cache)
        key = service._image_meta_key("user123", "img456")
        assert key == "image_meta:user123:img456"

    def test_audio_key(self):
        """Test audio key format."""
        mock_cache = MagicMock()
        service = CacheService(cache_client=mock_cache)
        key = service._audio_key("user123", "job789")
        assert key == "audio:user123:job789"

    def test_video_key(self):
        """Test video key format."""
        mock_cache = MagicMock()
        service = CacheService(cache_client=mock_cache)
        key = service._video_key("user123", "job789")
        assert key == "video:user123:job789"

    def test_generate_image_id(self):
        """Test image ID generation is hash-based."""
        mock_cache = MagicMock()
        service = CacheService(cache_client=mock_cache)
        data = b"test image data"
        image_id = service._generate_image_id(data)

        # Should be first 16 chars of SHA-256 hash
        expected = hashlib.sha256(data).hexdigest()[:16]
        assert image_id == expected
        assert len(image_id) == 16

    def test_generate_image_id_deterministic(self):
        """Test same data produces same image ID."""
        mock_cache = MagicMock()
        service = CacheService(cache_client=mock_cache)
        data = b"test image data"

        id1 = service._generate_image_id(data)
        id2 = service._generate_image_id(data)

        assert id1 == id2

    def test_generate_image_id_different_data(self):
        """Test different data produces different image IDs."""
        mock_cache = MagicMock()
        service = CacheService(cache_client=mock_cache)

        id1 = service._generate_image_id(b"data1")
        id2 = service._generate_image_id(b"data2")

        assert id1 != id2


class TestCacheServiceStoreImage:
    """Tests for CacheService.store_image method."""

    def test_store_image_success(self):
        """Test successful image storage."""
        mock_cache = MagicMock()
        mock_cache.set.return_value = True
        mock_cache.set_text.return_value = True
        service = CacheService(cache_client=mock_cache)

        data = b"fake image data"
        result = service.store_image("user123", data, "image/png")

        expected_id = hashlib.sha256(data).hexdigest()[:16]
        assert result == expected_id
        mock_cache.set.assert_called_once_with(
            f"image:user123:{expected_id}", data, IMAGE_TTL
        )
        mock_cache.set_text.assert_called_once_with(
            f"image_meta:user123:{expected_id}", "image/png", IMAGE_TTL
        )

    def test_store_image_data_failure(self):
        """Test image storage when data storage fails."""
        mock_cache = MagicMock()
        mock_cache.set.return_value = False
        service = CacheService(cache_client=mock_cache)

        result = service.store_image("user123", b"data", "image/png")

        assert result is None
        mock_cache.set_text.assert_not_called()

    def test_store_image_meta_failure(self):
        """Test image storage when metadata storage fails."""
        mock_cache = MagicMock()
        mock_cache.set.return_value = True
        mock_cache.set_text.return_value = False
        mock_cache.delete.return_value = True
        service = CacheService(cache_client=mock_cache)

        result = service.store_image("user123", b"data", "image/png")

        assert result is None
        # Should clean up data key
        mock_cache.delete.assert_called_once()


class TestCacheServiceGetImage:
    """Tests for CacheService.get_image method."""

    def test_get_image_success(self):
        """Test successful image retrieval."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = b"image data"
        mock_cache.get_text.return_value = "image/jpeg"
        service = CacheService(cache_client=mock_cache)

        result = service.get_image("user123", "img456")

        assert result == (b"image data", "image/jpeg")
        mock_cache.get.assert_called_once_with("image:user123:img456")
        mock_cache.get_text.assert_called_once_with("image_meta:user123:img456")

    def test_get_image_not_found(self):
        """Test image retrieval when not found."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        service = CacheService(cache_client=mock_cache)

        result = service.get_image("user123", "nonexistent")

        assert result is None
        mock_cache.get_text.assert_not_called()

    def test_get_image_missing_meta(self):
        """Test image retrieval when metadata is missing."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = b"image data"
        mock_cache.get_text.return_value = None
        service = CacheService(cache_client=mock_cache)

        result = service.get_image("user123", "img456")

        # Should default to octet-stream
        assert result == (b"image data", "application/octet-stream")


class TestCacheServiceGetImageBase64:
    """Tests for CacheService.get_image_base64 method."""

    def test_get_image_base64_success(self):
        """Test successful base64 image retrieval."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = b"image data"
        mock_cache.get_text.return_value = "image/png"
        service = CacheService(cache_client=mock_cache)

        result = service.get_image_base64("user123", "img456")

        expected_b64 = base64.b64encode(b"image data").decode("ascii")
        assert result == f"data:image/png;base64,{expected_b64}"

    def test_get_image_base64_not_found(self):
        """Test base64 image retrieval when not found."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        service = CacheService(cache_client=mock_cache)

        result = service.get_image_base64("user123", "nonexistent")

        assert result is None

    def test_get_image_base64_format(self):
        """Test base64 data URL format is correct."""
        mock_cache = MagicMock()
        test_data = b"\x89PNG\r\n\x1a\n"  # PNG magic bytes
        mock_cache.get.return_value = test_data
        mock_cache.get_text.return_value = "image/png"
        service = CacheService(cache_client=mock_cache)

        result = service.get_image_base64("user123", "img456")

        assert result.startswith("data:image/png;base64,")
        # Verify it's valid base64
        b64_part = result.split(",")[1]
        decoded = base64.b64decode(b64_part)
        assert decoded == test_data


class TestCacheServiceExtendImageTTL:
    """Tests for CacheService.extend_image_ttl method."""

    def test_extend_image_ttl_success(self):
        """Test successful TTL extension."""
        mock_cache = MagicMock()
        mock_cache.extend_ttl.return_value = True
        service = CacheService(cache_client=mock_cache)

        result = service.extend_image_ttl("user123", "img456")

        assert result is True
        assert mock_cache.extend_ttl.call_count == 2
        mock_cache.extend_ttl.assert_any_call("image:user123:img456", IMAGE_TTL)
        mock_cache.extend_ttl.assert_any_call("image_meta:user123:img456", IMAGE_TTL)

    def test_extend_image_ttl_not_found(self):
        """Test TTL extension when image not found."""
        mock_cache = MagicMock()
        mock_cache.extend_ttl.return_value = False
        service = CacheService(cache_client=mock_cache)

        result = service.extend_image_ttl("user123", "nonexistent")

        assert result is False

    def test_extend_image_ttl_partial_failure(self):
        """Test TTL extension when only one key exists."""
        mock_cache = MagicMock()
        mock_cache.extend_ttl.side_effect = [True, False]
        service = CacheService(cache_client=mock_cache)

        result = service.extend_image_ttl("user123", "img456")

        assert result is False


class TestCacheServiceStoreAudio:
    """Tests for CacheService.store_audio method."""

    def test_store_audio_success(self):
        """Test successful audio storage."""
        mock_cache = MagicMock()
        mock_cache.set.return_value = True
        service = CacheService(cache_client=mock_cache)

        result = service.store_audio("user123", "job789", b"audio data")

        assert result is True
        mock_cache.set.assert_called_once_with(
            "audio:user123:job789", b"audio data", AUDIO_TTL
        )

    def test_store_audio_failure(self):
        """Test audio storage failure."""
        mock_cache = MagicMock()
        mock_cache.set.return_value = False
        service = CacheService(cache_client=mock_cache)

        result = service.store_audio("user123", "job789", b"audio data")

        assert result is False


class TestCacheServiceGetAudio:
    """Tests for CacheService.get_audio method."""

    def test_get_audio_success(self):
        """Test successful audio retrieval."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = b"audio data"
        service = CacheService(cache_client=mock_cache)

        result = service.get_audio("user123", "job789")

        assert result == b"audio data"
        mock_cache.get.assert_called_once_with("audio:user123:job789")

    def test_get_audio_not_found(self):
        """Test audio retrieval when not found."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        service = CacheService(cache_client=mock_cache)

        result = service.get_audio("user123", "nonexistent")

        assert result is None


class TestCacheServiceStoreVideo:
    """Tests for CacheService.store_video method."""

    def test_store_video_success(self):
        """Test successful video storage."""
        mock_cache = MagicMock()
        mock_cache.set.return_value = True
        service = CacheService(cache_client=mock_cache)

        result = service.store_video("user123", "job789", b"video data")

        assert result is True
        mock_cache.set.assert_called_once_with(
            "video:user123:job789", b"video data", VIDEO_TTL
        )

    def test_store_video_failure(self):
        """Test video storage failure."""
        mock_cache = MagicMock()
        mock_cache.set.return_value = False
        service = CacheService(cache_client=mock_cache)

        result = service.store_video("user123", "job789", b"video data")

        assert result is False


class TestCacheServiceGetVideo:
    """Tests for CacheService.get_video method."""

    def test_get_video_success(self):
        """Test successful video retrieval."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = b"video data"
        service = CacheService(cache_client=mock_cache)

        result = service.get_video("user123", "job789")

        assert result == b"video data"
        mock_cache.get.assert_called_once_with("video:user123:job789")

    def test_get_video_not_found(self):
        """Test video retrieval when not found."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        service = CacheService(cache_client=mock_cache)

        result = service.get_video("user123", "nonexistent")

        assert result is None


class TestGetCacheService:
    """Tests for get_cache_service singleton function."""

    @patch("src.shared.cache_service.get_cache")
    def test_get_cache_service_returns_instance(self, mock_get_cache):
        """Test get_cache_service returns a CacheService instance."""
        get_cache_service.cache_clear()
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        service = get_cache_service()

        assert isinstance(service, CacheService)
        assert service._cache == mock_cache

    @patch("src.shared.cache_service.get_cache")
    def test_get_cache_service_singleton(self, mock_get_cache):
        """Test get_cache_service returns the same instance."""
        get_cache_service.cache_clear()
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        service1 = get_cache_service()
        service2 = get_cache_service()

        assert service1 is service2
        # get_cache should only be called once due to caching
        mock_get_cache.assert_called_once()


class TestCacheServiceIntegration:
    """Integration-style tests for CacheService."""

    def test_store_and_retrieve_image(self):
        """Test storing and retrieving an image."""
        mock_cache = MagicMock()
        mock_cache.set.return_value = True
        mock_cache.set_text.return_value = True
        mock_cache.get.return_value = b"image data"
        mock_cache.get_text.return_value = "image/png"
        service = CacheService(cache_client=mock_cache)

        # Store
        image_id = service.store_image("user1", b"image data", "image/png")
        assert image_id is not None

        # Retrieve
        result = service.get_image("user1", image_id)
        assert result is not None
        assert result[0] == b"image data"
        assert result[1] == "image/png"

    def test_store_and_retrieve_audio(self):
        """Test storing and retrieving audio."""
        mock_cache = MagicMock()
        mock_cache.set.return_value = True
        mock_cache.get.return_value = b"audio data"
        service = CacheService(cache_client=mock_cache)

        # Store
        success = service.store_audio("user1", "job1", b"audio data")
        assert success is True

        # Retrieve
        result = service.get_audio("user1", "job1")
        assert result == b"audio data"

    def test_store_and_retrieve_video(self):
        """Test storing and retrieving video."""
        mock_cache = MagicMock()
        mock_cache.set.return_value = True
        mock_cache.get.return_value = b"video data"
        service = CacheService(cache_client=mock_cache)

        # Store
        success = service.store_video("user1", "job1", b"video data")
        assert success is True

        # Retrieve
        result = service.get_video("user1", "job1")
        assert result == b"video data"

    def test_user_isolation(self):
        """Test that different users have isolated caches."""
        mock_cache = MagicMock()
        service = CacheService(cache_client=mock_cache)

        # Keys should be different for different users
        key1 = service._image_key("user1", "img1")
        key2 = service._image_key("user2", "img1")

        assert key1 != key2
        assert "user1" in key1
        assert "user2" in key2
