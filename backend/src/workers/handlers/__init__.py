"""Handler modules for Lambda functions."""
from src.workers.handlers.tts_handler import handler as tts_handler
from src.workers.handlers.video_handler import handler as video_handler


__all__ = [
    "tts_handler",
    "video_handler",
]