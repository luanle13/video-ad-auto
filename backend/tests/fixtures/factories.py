from datetime import datetime
import uuid
from typing import Dict, List, Optional


def create_user(user_id: str = None, email: str = None) -> dict:
    """Create sample user data."""
    return {
        "user_id": user_id or str(uuid.uuid4()),
        "email": email or f"test-{uuid.uuid4().hex[:8]}@example.com",
        "created_at": datetime.utcnow().isoformat()
    }


def create_product(user_id: str, product_id: str = None) -> dict:
    """Create sample product data."""
    return {
        "product_id": product_id or str(uuid.uuid4()),
        "user_id": user_id,
        "title": f"Test Product {uuid.uuid4().hex[:8]}",
        "description": "This is a sample product description for testing purposes.",
        "price": 29.99,
        "image_keys": [f"images/{uuid.uuid4().hex[:8]}.jpg"],
        "image_urls": [f"https://test-images.s3.amazonaws.com/images/{uuid.uuid4().hex[:8]}.jpg"],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


def create_job(user_id: str, product_id: str, job_id: str = None) -> dict:
    """Create sample job data."""
    return {
        "job_id": job_id or str(uuid.uuid4()),
        "user_id": user_id,
        "product_id": product_id,
        "status": "PENDING",
        "adjustments": create_adjustments(),
        "step_outputs": {
            "product_analysis": {
                "title": f"Test Product {uuid.uuid4().hex[:8]}",
                "description": "Sample product description",
                "features": ["Feature 1", "Feature 2", "Feature 3"]
            },
            "script": {
                "content": "Welcome to our amazing product! This innovative solution brings you the best features and benefits.",
                "duration": 30
            },
            "tts_generation": {
                "audio_url": f"https://test-audio.s3.amazonaws.com/audio/{uuid.uuid4().hex[:8]}.mp3"
            },
            "video_generation": {
                "video_url": f"https://test-videos.s3.amazonaws.com/videos/{uuid.uuid4().hex[:8]}.mp4"
            }
        },
        "video_url": f"https://test-videos.s3.amazonaws.com/videos/{uuid.uuid4().hex[:8]}.mp4",
        "audio_url": f"https://test-audio.s3.amazonaws.com/audio/{uuid.uuid4().hex[:8]}.mp3",
        "error_message": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


def create_adjustments() -> dict:
    """Create sample adjustments."""
    return {
        "background_style": "minimal white",
        "tone": "energetic",
        "emphasis": "product features",
        "duration_preference": 45,
        "additional_instructions": "Include upbeat music and bright colors"
    }


def create_sample_image_data() -> bytes:
    """Create sample image data for testing."""
    # Create a minimal PNG image (1x1 pixel)
    return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\xdac\xf8\x0f\x00\x00\x01\x01\x00\x01}\x8d\x88\x8c\x00\x00\x00\x00IEND\xaeB`\x82'


def create_sample_audio_data() -> bytes:
    """Create sample audio data for testing."""
    # Create minimal WAV header (not a real audio file, just for testing purposes)
    return b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'


def create_credentials_status() -> dict:
    """Create sample credentials status data."""
    return {
        "tiktok_configured": True,
        "shopee_configured": False,
        "facebook_configured": True
    }