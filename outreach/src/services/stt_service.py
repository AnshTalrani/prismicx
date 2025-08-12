class STTService:
    """
    Speech-to-Text (STT) Service interface for modular integration.
    Implement transcribe() with your preferred engine (e.g., Whisper).
    """
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio bytes to text. Should be implemented by subclass.
        Args:
            audio_bytes: Raw audio data
        Returns:
            Transcribed text string
        """
        raise NotImplementedError("STTService.transcribe must be implemented by subclass")
