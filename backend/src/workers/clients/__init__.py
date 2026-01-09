"""Client utilities for external API integrations."""
from src.workers.clients.base import BaseAPIClient
from src.workers.clients.elevenlabs import ElevenLabsClient
from src.workers.clients.elevenlabs_models import (
    ElevenLabsVoice,
    TTSRequest,
    TTSResponse,
    VoiceSettings,
)
from src.workers.clients.kling import KlingClient, KlingJobResponse
from src.workers.clients.polly import PollyClient, get_polly_client
from src.workers.clients.polly_models import (
    PollyEngine,
    PollyTTSResponse,
    PollyVoice,
)
from src.workers.clients.retry import RetryConfig

__all__ = [
    # Base client
    "BaseAPIClient",
    # Retry configuration
    "RetryConfig",
    # ElevenLabs client
    "ElevenLabsClient",
    # ElevenLabs models
    "ElevenLabsVoice",
    "VoiceSettings",
    "TTSRequest",
    "TTSResponse",
    # Kling client
    "KlingClient",
    "KlingJobResponse",
    # Polly client
    "PollyClient",
    "get_polly_client",
    # Polly models
    "PollyVoice",
    "PollyEngine",
    "PollyTTSResponse",
]
