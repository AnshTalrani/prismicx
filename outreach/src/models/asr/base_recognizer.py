"""
Base ASR (Automatic Speech Recognition) Interface

This module defines the base interface for all ASR models,
providing a common API for speech-to-text conversion.
"""

import abc
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class TranscriptionResult:
    """Result of speech transcription."""
    
    text: str
    language: Optional[str] = None
    confidence: float = 0.0
    segments: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None


@dataclass
class AudioInput:
    """Audio input for transcription."""
    
    data: Union[np.ndarray, bytes, str, Path]
    sample_rate: int = 16000
    format: str = "wav"
    metadata: Optional[Dict] = None


class BaseRecognizer(abc.ABC):
    """Base interface for all ASR models."""
    
    def __init__(self, config: Dict):
        """Initialize the recognizer with configuration."""
        self.config = config
        self.model = None
        self.is_loaded = False
    
    @abc.abstractmethod
    def load_model(self) -> None:
        """Load the ASR model."""
        pass
    
    @abc.abstractmethod
    def transcribe(self, audio: AudioInput) -> TranscriptionResult:
        """Transcribe audio to text."""
        pass
    
    @abc.abstractmethod
    def transcribe_batch(self, audio_list: List[AudioInput]) -> List[TranscriptionResult]:
        """Transcribe multiple audio files in batch."""
        pass
    
    @abc.abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        pass
    
    @abc.abstractmethod
    def get_model_info(self) -> Dict:
        """Get information about the loaded model."""
        pass
    
    def is_model_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self.is_loaded
    
    def preprocess_audio(self, audio: AudioInput) -> np.ndarray:
        """Preprocess audio data for transcription."""
        # Default implementation - can be overridden by subclasses
        if isinstance(audio.data, np.ndarray):
            return audio.data
        elif isinstance(audio.data, bytes):
            # Convert bytes to numpy array
            import wave
            import io
            with io.BytesIO(audio.data) as audio_file:
                with wave.open(audio_file, 'rb') as wav_file:
                    frames = wav_file.readframes(wav_file.getnframes())
                    audio_array = np.frombuffer(frames, dtype=np.int16)
                    return audio_array.astype(np.float32) / 32768.0
        elif isinstance(audio.data, (str, Path)):
            # Load from file
            import librosa
            audio_array, _ = librosa.load(str(audio.data), sr=audio.sample_rate)
            return audio_array
        else:
            raise ValueError(f"Unsupported audio data type: {type(audio.data)}")
    
    def postprocess_text(self, text: str) -> str:
        """Postprocess transcribed text."""
        # Default implementation - can be overridden by subclasses
        return text.strip()
    
    def validate_audio(self, audio: AudioInput) -> bool:
        """Validate audio input."""
        if audio.sample_rate <= 0:
            return False
        
        if isinstance(audio.data, np.ndarray):
            if len(audio.data) == 0:
                return False
        elif isinstance(audio.data, bytes):
            if len(audio.data) == 0:
                return False
        elif isinstance(audio.data, (str, Path)):
            if not Path(audio.data).exists():
                return False
        else:
            return False
        
        return True
    
    def get_audio_duration(self, audio: AudioInput) -> float:
        """Get duration of audio in seconds."""
        if isinstance(audio.data, np.ndarray):
            return len(audio.data) / audio.sample_rate
        elif isinstance(audio.data, bytes):
            import wave
            import io
            with io.BytesIO(audio.data) as audio_file:
                with wave.open(audio_file, 'rb') as wav_file:
                    return wav_file.getnframes() / wav_file.getframerate()
        elif isinstance(audio.data, (str, Path)):
            import librosa
            duration = librosa.get_duration(path=str(audio.data))
            return duration
        else:
            raise ValueError(f"Cannot determine duration for audio type: {type(audio.data)}")
    
    def __enter__(self):
        """Context manager entry."""
        if not self.is_loaded:
            self.load_model()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Cleanup if needed
        pass


class RecognizerFactory:
    """Factory for creating ASR recognizers."""
    
    _recognizers = {}
    
    @classmethod
    def register(cls, name: str, recognizer_class: type):
        """Register a recognizer class."""
        cls._recognizers[name] = recognizer_class
    
    @classmethod
    def create(cls, name: str, config: Dict) -> BaseRecognizer:
        """Create a recognizer instance."""
        if name not in cls._recognizers:
            raise ValueError(f"Unknown recognizer: {name}")
        
        recognizer_class = cls._recognizers[name]
        return recognizer_class(config)
    
    @classmethod
    def get_available_recognizers(cls) -> List[str]:
        """Get list of available recognizers."""
        return list(cls._recognizers.keys())


# Common exceptions
class RecognizerError(Exception):
    """Base exception for recognizer errors."""
    pass


class ModelNotLoadedError(RecognizerError):
    """Raised when trying to use a model that hasn't been loaded."""
    pass


class AudioProcessingError(RecognizerError):
    """Raised when there's an error processing audio."""
    pass


class TranscriptionError(RecognizerError):
    """Raised when there's an error during transcription."""
    pass 