"""
Base Text-to-Speech (TTS) Interface

This module defines the base interface for all TTS models,
providing a common API for text-to-speech conversion.
"""

import abc
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class SynthesisResult:
    """Result of text-to-speech synthesis."""
    
    audio: np.ndarray
    sample_rate: int
    duration: float
    text: str
    voice_profile: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class VoiceProfile:
    """Voice profile configuration."""
    
    name: str
    gender: Optional[str] = None
    age: Optional[str] = None
    language: Optional[str] = None
    accent: Optional[str] = None
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    metadata: Optional[Dict] = None


class BaseSynthesizer(abc.ABC):
    """Base interface for all TTS models."""
    
    def __init__(self, config: Dict):
        """Initialize the synthesizer with configuration."""
        self.config = config
        self.model = None
        self.is_loaded = False
        self.voice_profiles: Dict[str, VoiceProfile] = {}
    
    @abc.abstractmethod
    def load_model(self) -> None:
        """Load the TTS model."""
        pass
    
    @abc.abstractmethod
    def synthesize(
        self, 
        text: str, 
        voice_profile: Optional[str] = None,
        **kwargs
    ) -> SynthesisResult:
        """Synthesize text to speech."""
        pass
    
    @abc.abstractmethod
    def synthesize_batch(
        self, 
        texts: List[str], 
        voice_profile: Optional[str] = None,
        **kwargs
    ) -> List[SynthesisResult]:
        """Synthesize multiple texts in batch."""
        pass
    
    @abc.abstractmethod
    def get_supported_voices(self) -> List[str]:
        """Get list of supported voice profiles."""
        pass
    
    @abc.abstractmethod
    def get_model_info(self) -> Dict:
        """Get information about the loaded model."""
        pass
    
    def is_model_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self.is_loaded
    
    def validate_text(self, text: str) -> bool:
        """Validate input text."""
        if not text or not text.strip():
            return False
        
        # Check for reasonable length (can be overridden)
        if len(text) > 10000:  # 10k characters limit
            return False
        
        return True
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for synthesis."""
        # Default implementation - can be overridden by subclasses
        text = text.strip()
        
        # Basic text normalization
        text = text.replace("  ", " ")  # Remove double spaces
        text = text.replace("\n", " ")  # Replace newlines with spaces
        
        return text
    
    def postprocess_audio(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Postprocess synthesized audio."""
        # Default implementation - can be overridden by subclasses
        
        # Normalize audio
        if audio.max() > 0:
            audio = audio / audio.max() * 0.95
        
        # Ensure audio is float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        
        return audio
    
    def save_audio(self, result: SynthesisResult, filepath: Union[str, Path]) -> None:
        """Save synthesized audio to file."""
        import soundfile as sf
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        sf.write(str(filepath), result.audio, result.sample_rate)
    
    def get_audio_duration(self, result: SynthesisResult) -> float:
        """Get duration of synthesized audio in seconds."""
        return len(result.audio) / result.sample_rate
    
    def create_voice_profile(
        self, 
        name: str, 
        **kwargs
    ) -> VoiceProfile:
        """Create a voice profile."""
        profile = VoiceProfile(name=name, **kwargs)
        self.voice_profiles[name] = profile
        return profile
    
    def get_voice_profile(self, name: str) -> Optional[VoiceProfile]:
        """Get a voice profile by name."""
        return self.voice_profiles.get(name)
    
    def list_voice_profiles(self) -> List[str]:
        """List available voice profiles."""
        return list(self.voice_profiles.keys())
    
    def apply_voice_settings(
        self, 
        audio: np.ndarray, 
        profile: VoiceProfile
    ) -> np.ndarray:
        """Apply voice profile settings to audio."""
        # Default implementation - can be overridden by subclasses
        
        # Apply speed (simple resampling)
        if profile.speed != 1.0:
            # This is a simplified implementation
            # Real implementations would use proper resampling
            pass
        
        # Apply volume
        if profile.volume != 1.0:
            audio = audio * profile.volume
        
        return audio
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics for the model."""
        return {
            "model": self.get_model_info().get("name", "unknown"),
            "voices_available": len(self.voice_profiles),
            "is_loaded": self.is_loaded
        }
    
    def __enter__(self):
        """Context manager entry."""
        if not self.is_loaded:
            self.load_model()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Cleanup if needed
        pass


class SynthesizerFactory:
    """Factory for creating TTS synthesizers."""
    
    _synthesizers = {}
    
    @classmethod
    def register(cls, name: str, synthesizer_class: type):
        """Register a synthesizer class."""
        cls._synthesizers[name] = synthesizer_class
    
    @classmethod
    def create(cls, name: str, config: Dict) -> BaseSynthesizer:
        """Create a synthesizer instance."""
        if name not in cls._synthesizers:
            raise ValueError(f"Unknown synthesizer: {name}")
        
        synthesizer_class = cls._synthesizers[name]
        return synthesizer_class(config)
    
    @classmethod
    def get_available_synthesizers(cls) -> List[str]:
        """Get list of available synthesizers."""
        return list(cls._synthesizers.keys())


# Common exceptions
class SynthesizerError(Exception):
    """Base exception for synthesizer errors."""
    pass


class ModelNotLoadedError(SynthesizerError):
    """Raised when trying to use a model that hasn't been loaded."""
    pass


class SynthesisError(SynthesizerError):
    """Raised when there's an error during synthesis."""
    pass


class VoiceProfileError(SynthesizerError):
    """Raised when there's an error with voice profiles."""
    pass


class TextValidationError(SynthesizerError):
    """Raised when input text is invalid."""
    pass 