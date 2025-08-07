"""
AI Model Configuration

This module manages configuration for all AI/ML models including
ASR, LLM, TTS, and emotion detection models.
"""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator

from .settings import settings


class WhisperConfig(BaseModel):
    """Configuration for Whisper ASR model."""
    
    model_size: str = Field(default="base", description="Model size (tiny, base, small, medium, large)")
    device: str = Field(default="cpu", description="Device to run on (cpu, cuda, mps)")
    language: Optional[str] = Field(default=None, description="Language code for transcription")
    task: str = Field(default="transcribe", description="Task type (transcribe, translate)")
    temperature: float = Field(default=0.0, description="Sampling temperature")
    best_of: int = Field(default=5, description="Number of candidates to consider")
    beam_size: int = Field(default=5, description="Beam search size")
    patience: float = Field(default=1.0, description="Beam search patience")
    length_penalty: float = Field(default=1.0, description="Length penalty")
    compression_ratio_threshold: float = Field(default=2.4, description="Compression ratio threshold")
    log_prob_threshold: float = Field(default=-1.0, description="Log probability threshold")
    no_speech_threshold: float = Field(default=0.6, description="No speech threshold")
    
    @validator("model_size")
    def validate_model_size(cls, v):
        valid_sizes = ["tiny", "base", "small", "medium", "large"]
        if v not in valid_sizes:
            raise ValueError(f"Model size must be one of {valid_sizes}")
        return v
    
    @validator("device")
    def validate_device(cls, v):
        valid_devices = ["cpu", "cuda", "mps"]
        if v not in valid_devices:
            raise ValueError(f"Device must be one of {valid_devices}")
        return v


class LLMConfig(BaseModel):
    """Configuration for Language Models."""
    
    provider: str = Field(default="openai", description="LLM provider")
    model: str = Field(default="gpt-3.5-turbo", description="Model name")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: int = Field(default=1000, description="Maximum tokens to generate")
    top_p: float = Field(default=1.0, description="Top-p sampling")
    frequency_penalty: float = Field(default=0.0, description="Frequency penalty")
    presence_penalty: float = Field(default=0.0, description="Presence penalty")
    stop_sequences: List[str] = Field(default=[], description="Stop sequences")
    api_key: Optional[str] = Field(default=None, description="API key")
    base_url: Optional[str] = Field(default=None, description="Base URL for API")
    
    @validator("provider")
    def validate_provider(cls, v):
        valid_providers = ["openai", "anthropic", "local"]
        if v not in valid_providers:
            raise ValueError(f"Provider must be one of {valid_providers}")
        return v


class TTSConfig(BaseModel):
    """Configuration for Text-to-Speech models."""
    
    provider: str = Field(default="kokoro", description="TTS provider")
    model_path: Optional[str] = Field(default=None, description="Path to model file")
    device: str = Field(default="cpu", description="Device to run on")
    voice_profile: str = Field(default="default", description="Voice profile to use")
    sample_rate: int = Field(default=22050, description="Output sample rate")
    speed: float = Field(default=1.0, description="Speech speed multiplier")
    pitch: float = Field(default=1.0, description="Pitch adjustment")
    volume: float = Field(default=1.0, description="Volume adjustment")
    
    @validator("provider")
    def validate_provider(cls, v):
        valid_providers = ["kokoro", "espeak", "gtts"]
        if v not in valid_providers:
            raise ValueError(f"Provider must be one of {valid_providers}")
        return v


class EmotionConfig(BaseModel):
    """Configuration for Emotion Detection models."""
    
    model_path: Optional[str] = Field(default=None, description="Path to emotion model")
    device: str = Field(default="cpu", description="Device to run on")
    confidence_threshold: float = Field(default=0.7, description="Confidence threshold")
    emotion_categories: List[str] = Field(
        default=["happy", "sad", "angry", "neutral", "excited", "calm"],
        description="Supported emotion categories"
    )
    multimodal: bool = Field(default=True, description="Enable multimodal analysis")
    audio_weight: float = Field(default=0.6, description="Weight for audio analysis")
    text_weight: float = Field(default=0.4, description="Weight for text analysis")
    
    @validator("confidence_threshold")
    def validate_confidence_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        return v


class ModelRegistry(BaseModel):
    """Registry for all AI models and their configurations."""
    
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    emotion: EmotionConfig = Field(default_factory=EmotionConfig)
    
    # Model loading states
    models_loaded: Dict[str, bool] = Field(default_factory=dict)
    
    def get_model_config(self, model_type: str) -> Union[WhisperConfig, LLMConfig, TTSConfig, EmotionConfig]:
        """Get configuration for a specific model type."""
        if model_type == "whisper":
            return self.whisper
        elif model_type == "llm":
            return self.llm
        elif model_type == "tts":
            return self.tts
        elif model_type == "emotion":
            return self.emotion
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def is_model_loaded(self, model_type: str) -> bool:
        """Check if a model is loaded."""
        return self.models_loaded.get(model_type, False)
    
    def set_model_loaded(self, model_type: str, loaded: bool = True) -> None:
        """Set model loading state."""
        self.models_loaded[model_type] = loaded
    
    def get_loaded_models(self) -> List[str]:
        """Get list of loaded models."""
        return [model_type for model_type, loaded in self.models_loaded.items() if loaded]


def load_model_config_from_settings() -> ModelRegistry:
    """Load model configuration from application settings."""
    
    # Whisper configuration
    whisper_config = WhisperConfig(
        model_size=settings.whisper_model_size,
        device=settings.whisper_device,
        language=settings.whisper_language
    )
    
    # LLM configuration
    llm_config = LLMConfig(
        provider=settings.llm_provider,
        model=settings.openai_model if settings.llm_provider == "openai" else settings.anthropic_model,
        api_key=settings.openai_api_key if settings.llm_provider == "openai" else settings.anthropic_api_key
    )
    
    # TTS configuration
    tts_config = TTSConfig(
        model_path=settings.kokoro_model_path,
        device=settings.kokoro_device,
        voice_profile=settings.kokoro_voice_profile
    )
    
    # Emotion configuration
    emotion_config = EmotionConfig(
        model_path=settings.emotion_model_path,
        device="cpu",  # Default to CPU for emotion detection
        confidence_threshold=settings.emotion_confidence_threshold
    )
    
    return ModelRegistry(
        whisper=whisper_config,
        llm=llm_config,
        tts=tts_config,
        emotion=emotion_config
    )


# Global model registry instance
model_registry = load_model_config_from_settings()


def get_model_config(model_type: str) -> Union[WhisperConfig, LLMConfig, TTSConfig, EmotionConfig]:
    """Get model configuration for the specified type."""
    return model_registry.get_model_config(model_type)


def is_model_available(model_type: str) -> bool:
    """Check if a model is available and loaded."""
    return model_registry.is_model_loaded(model_type)


def get_available_models() -> List[str]:
    """Get list of available models."""
    return model_registry.get_loaded_models() 