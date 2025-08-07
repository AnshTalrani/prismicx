"""
Whisper ASR Wrapper

This module provides a wrapper around OpenAI's Whisper model for speech-to-text conversion.
"""

import os
import tempfile
from typing import List, Optional
import whisper
import numpy as np
from pydub import AudioSegment

from ..base_recognizer import BaseRecognizer, AudioInput, TranscriptionResult
from src.config.logging_config import get_logger


class WhisperRecognizer(BaseRecognizer):
    """Whisper-based speech recognition implementation."""
    
    def __init__(self, config: dict):
        """Initialize the Whisper recognizer."""
        super().__init__(config)
        self.logger = get_logger(self.__class__.__name__)
        self.model_size = config.get("model_size", "base")
        self.device = config.get("device", "cpu")
        self.language = config.get("language", None)
        self.model = None
        self.is_loaded = False
        
    async def load_model(self):
        """Load the Whisper model."""
        try:
            self.logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size, device=self.device)
            self.is_loaded = True
            self.logger.info("Whisper model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {str(e)}")
            raise
    
    async def transcribe(self, audio: AudioInput) -> TranscriptionResult:
        """Transcribe audio to text."""
        if not self.is_loaded:
            await self.load_model()
        
        try:
            # Convert audio to the format Whisper expects
            audio_array = self._prepare_audio(audio)
            
            # Transcribe with Whisper
            result = self.model.transcribe(
                audio_array,
                language=self.language,
                fp16=False
            )
            
            return TranscriptionResult(
                text=result["text"].strip(),
                language=result.get("language", self.language),
                confidence=result.get("avg_logprob", 0.0),
                segments=result.get("segments", []),
                metadata={
                    "model_size": self.model_size,
                    "device": self.device,
                    "processing_time": result.get("processing_time", 0.0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {str(e)}")
            raise
    
    async def transcribe_batch(self, audio_list: List[AudioInput]) -> List[TranscriptionResult]:
        """Transcribe multiple audio files."""
        results = []
        for audio in audio_list:
            result = await self.transcribe(audio)
            results.append(result)
        return results
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return whisper.available_models()
    
    def get_model_info(self) -> dict:
        """Get model information."""
        return {
            "name": "Whisper",
            "version": whisper.__version__,
            "model_size": self.model_size,
            "device": self.device,
            "language": self.language,
            "is_loaded": self.is_loaded
        }
    
    def _prepare_audio(self, audio: AudioInput) -> np.ndarray:
        """Prepare audio for Whisper processing."""
        try:
            if audio.audio_data:
                # If we have raw audio data, convert it to the right format
                if isinstance(audio.audio_data, bytes):
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                        temp_file.write(audio.audio_data)
                        temp_path = temp_file.name
                    
                    # Load with pydub and convert to numpy array
                    audio_segment = AudioSegment.from_file(temp_path)
                    audio_array = np.array(audio_segment.get_array_of_samples())
                    
                    # Clean up temp file
                    os.unlink(temp_path)
                    
                    return audio_array
                else:
                    return np.array(audio.audio_data)
            
            elif audio.file_path:
                # Load from file
                audio_segment = AudioSegment.from_file(audio.file_path)
                return np.array(audio_segment.get_array_of_samples())
            
            else:
                raise ValueError("No audio data or file path provided")
                
        except Exception as e:
            self.logger.error(f"Failed to prepare audio: {str(e)}")
            raise 