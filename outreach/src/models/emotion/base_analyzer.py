"""
Base Emotion Detection Interface

This module defines the base interface for all emotion detection models,
providing a common API for emotion analysis from audio and text.
"""

import abc
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum

import numpy as np


class EmotionCategory(str, Enum):
    """Supported emotion categories."""
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    NEUTRAL = "neutral"
    EXCITED = "excited"
    CALM = "calm"
    FRUSTRATED = "frustrated"
    SURPRISED = "surprised"
    FEARFUL = "fearful"
    DISGUSTED = "disgusted"


@dataclass
class EmotionResult:
    """Result of emotion analysis."""
    
    primary_emotion: EmotionCategory
    confidence: float
    all_emotions: Dict[EmotionCategory, float]
    metadata: Optional[Dict] = None


@dataclass
class AudioInput:
    """Audio input for emotion analysis."""
    
    data: np.ndarray
    sample_rate: int
    duration: Optional[float] = None
    metadata: Optional[Dict] = None


@dataclass
class TextInput:
    """Text input for emotion analysis."""
    
    text: str
    language: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class MultimodalInput:
    """Multimodal input combining audio and text."""
    
    audio: Optional[AudioInput] = None
    text: Optional[TextInput] = None
    metadata: Optional[Dict] = None


class BaseEmotionAnalyzer(abc.ABC):
    """Base interface for all emotion detection models."""
    
    def __init__(self, config: Dict):
        """Initialize the analyzer with configuration."""
        self.config = config
        self.model = None
        self.is_loaded = False
        self.supported_emotions = list(EmotionCategory)
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
    
    @abc.abstractmethod
    def load_model(self) -> None:
        """Load the emotion detection model."""
        pass
    
    @abc.abstractmethod
    def analyze_audio(self, audio: AudioInput) -> EmotionResult:
        """Analyze emotion from audio."""
        pass
    
    @abc.abstractmethod
    def analyze_text(self, text: TextInput) -> EmotionResult:
        """Analyze emotion from text."""
        pass
    
    @abc.abstractmethod
    def analyze_multimodal(self, input_data: MultimodalInput) -> EmotionResult:
        """Analyze emotion from multimodal input (audio + text)."""
        pass
    
    @abc.abstractmethod
    def get_supported_emotions(self) -> List[EmotionCategory]:
        """Get list of supported emotion categories."""
        pass
    
    @abc.abstractmethod
    def get_model_info(self) -> Dict:
        """Get information about the loaded model."""
        pass
    
    def is_model_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self.is_loaded
    
    def validate_audio(self, audio: AudioInput) -> bool:
        """Validate audio input."""
        if audio.sample_rate <= 0:
            return False
        
        if len(audio.data) == 0:
            return False
        
        # Check for reasonable duration (can be overridden)
        if audio.duration and (audio.duration < 0.1 or audio.duration > 300):  # 0.1s to 5min
            return False
        
        return True
    
    def validate_text(self, text: TextInput) -> bool:
        """Validate text input."""
        if not text.text or not text.text.strip():
            return False
        
        # Check for reasonable length (can be overridden)
        if len(text.text) > 10000:  # 10k characters limit
            return False
        
        return True
    
    def preprocess_audio(self, audio: AudioInput) -> np.ndarray:
        """Preprocess audio for emotion analysis."""
        # Default implementation - can be overridden by subclasses
        
        # Ensure audio is float32
        if audio.data.dtype != np.float32:
            audio_data = audio.data.astype(np.float32)
        else:
            audio_data = audio.data.copy()
        
        # Normalize audio
        if audio_data.max() > 0:
            audio_data = audio_data / audio_data.max()
        
        # Resample if needed (simplified)
        target_sample_rate = 16000  # Common sample rate for emotion models
        if audio.sample_rate != target_sample_rate:
            # This is a simplified implementation
            # Real implementations would use proper resampling
            pass
        
        return audio_data
    
    def preprocess_text(self, text: TextInput) -> str:
        """Preprocess text for emotion analysis."""
        # Default implementation - can be overridden by subclasses
        
        processed_text = text.text.strip()
        
        # Basic text normalization
        processed_text = processed_text.lower()
        processed_text = processed_text.replace("  ", " ")
        
        return processed_text
    
    def combine_emotions(
        self, 
        audio_emotion: Optional[EmotionResult], 
        text_emotion: Optional[EmotionResult],
        audio_weight: float = 0.6,
        text_weight: float = 0.4
    ) -> EmotionResult:
        """Combine emotions from audio and text analysis."""
        
        if audio_emotion and text_emotion:
            # Combine both results
            combined_emotions = {}
            
            for emotion in self.supported_emotions:
                audio_score = audio_emotion.all_emotions.get(emotion, 0.0)
                text_score = text_emotion.all_emotions.get(emotion, 0.0)
                
                combined_score = (audio_score * audio_weight + text_score * text_weight)
                combined_emotions[emotion] = combined_score
            
            # Find primary emotion
            primary_emotion = max(combined_emotions.items(), key=lambda x: x[1])
            
            return EmotionResult(
                primary_emotion=primary_emotion[0],
                confidence=primary_emotion[1],
                all_emotions=combined_emotions,
                metadata={
                    "audio_emotion": audio_emotion.primary_emotion.value,
                    "text_emotion": text_emotion.primary_emotion.value,
                    "audio_weight": audio_weight,
                    "text_weight": text_weight
                }
            )
        
        elif audio_emotion:
            return audio_emotion
        
        elif text_emotion:
            return text_emotion
        
        else:
            # Return neutral if no analysis available
            return EmotionResult(
                primary_emotion=EmotionCategory.NEUTRAL,
                confidence=1.0,
                all_emotions={EmotionCategory.NEUTRAL: 1.0},
                metadata={"fallback": True}
            )
    
    def is_emotion_confident(self, result: EmotionResult) -> bool:
        """Check if emotion detection is confident enough."""
        return result.confidence >= self.confidence_threshold
    
    def get_emotion_intensity(self, result: EmotionResult) -> str:
        """Get emotion intensity level."""
        if result.confidence >= 0.9:
            return "very_high"
        elif result.confidence >= 0.7:
            return "high"
        elif result.confidence >= 0.5:
            return "medium"
        elif result.confidence >= 0.3:
            return "low"
        else:
            return "very_low"
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics for the model."""
        return {
            "model": self.get_model_info().get("name", "unknown"),
            "supported_emotions": len(self.supported_emotions),
            "confidence_threshold": self.confidence_threshold,
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


class EmotionAnalyzerFactory:
    """Factory for creating emotion analyzers."""
    
    _analyzers = {}
    
    @classmethod
    def register(cls, name: str, analyzer_class: type):
        """Register an analyzer class."""
        cls._analyzers[name] = analyzer_class
    
    @classmethod
    def create(cls, name: str, config: Dict) -> BaseEmotionAnalyzer:
        """Create an analyzer instance."""
        if name not in cls._analyzers:
            raise ValueError(f"Unknown analyzer: {name}")
        
        analyzer_class = cls._analyzers[name]
        return analyzer_class(config)
    
    @classmethod
    def get_available_analyzers(cls) -> List[str]:
        """Get list of available analyzers."""
        return list(cls._analyzers.keys())


# Common exceptions
class EmotionAnalyzerError(Exception):
    """Base exception for emotion analyzer errors."""
    pass


class ModelNotLoadedError(EmotionAnalyzerError):
    """Raised when trying to use a model that hasn't been loaded."""
    pass


class AudioAnalysisError(EmotionAnalyzerError):
    """Raised when there's an error during audio analysis."""
    pass


class TextAnalysisError(EmotionAnalyzerError):
    """Raised when there's an error during text analysis."""
    pass


class MultimodalAnalysisError(EmotionAnalyzerError):
    """Raised when there's an error during multimodal analysis."""
    pass 