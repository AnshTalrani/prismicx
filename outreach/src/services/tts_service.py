class TTSService:
    """
    Text-to-Speech (TTS) Service interface for modular integration.
    Implement synthesize() with your preferred engine (e.g., Kokoro).
    """
    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize audio from text. Should be implemented by subclass.
        Args:
            text: Text to synthesize
        Returns:
            Audio bytes
        """
        raise NotImplementedError("TTSService.synthesize must be implemented by subclass")
