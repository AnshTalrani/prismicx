import torch
import numpy as np
from typing import Optional
from src.services.stt_service import STTService

try:
    import whisper
except ImportError:
    whisper = None

class WhisperSTTService(STTService):
    """
    Whisper-based Speech-to-Text Service implementation.
    """
    def __init__(self, model_name: str = "base", device: Optional[str] = None):
        if whisper is None:
            raise ImportError("whisper package is required for WhisperSTTService")
        self.model = whisper.load_model(model_name)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    async def transcribe(self, audio_bytes: bytes) -> str:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav") as f:
            f.write(audio_bytes)
            f.flush()
            result = self.model.transcribe(f.name)
        return result["text"]
