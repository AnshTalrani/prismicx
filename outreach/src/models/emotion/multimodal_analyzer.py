"""
Multimodal Emotion Analyzer

This module provides emotion detection from both audio and text inputs.
"""

import numpy as np
from typing import List, Optional, Dict, Any
from transformers import pipeline
import librosa

from ..emotion.base_analyzer import BaseEmotionAnalyzer, EmotionResult, EmotionCategory, AudioInput, TextInput, MultimodalInput
from src.config.logging_config import get_logger


class MultimodalEmotionAnalyzer(BaseEmotionAnalyzer):
    """Multimodal emotion detection implementation."""
    
    def __init__(self, config: dict):
        """Initialize the emotion analyzer."""
        super().__init__(config)
        self.logger = get_logger(self.__class__.__name__)
        self.model_path = config.get("model_path")
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.device = config.get("device", "cpu")
        self.text_classifier = None
        self.audio_classifier = None
        self.is_loaded = False
        
    async def load_model(self):
        """Load the emotion detection models."""
        try:
            self.logger.info("Loading emotion detection models")
            
            # Load text emotion classifier
            self.text_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=self.device
            )
            
            # For audio, we'll use a mock implementation for now
            # In production, you'd load a proper audio emotion model
            self.audio_classifier = MockAudioEmotionClassifier()
            
            self.is_loaded = True
            self.logger.info("Emotion detection models loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load emotion detection models: {str(e)}")
            raise
    
    async def analyze_audio(self, audio: AudioInput) -> EmotionResult:
        """Analyze emotion from audio."""
        if not self.is_loaded:
            await self.load_model()
        
        try:
            # Extract audio features
            audio_features = self._extract_audio_features(audio)
            
            # Analyze emotion
            emotion_data = await self.audio_classifier.analyze(audio_features)
            
            return EmotionResult(
                primary_emotion=emotion_data["primary_emotion"],
                confidence=emotion_data["confidence"],
                emotions=emotion_data["emotions"],
                metadata={
                    "model": "MultimodalEmotionAnalyzer",
                    "input_type": "audio",
                    "duration": emotion_data.get("duration", 0.0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Audio emotion analysis failed: {str(e)}")
            raise
    
    async def analyze_text(self, text: TextInput) -> EmotionResult:
        """Analyze emotion from text."""
        if not self.is_loaded:
            await self.load_model()
        
        try:
            # Analyze text emotion
            result = self.text_classifier(text.text)
            
            # Map to our emotion categories
            emotion_mapping = {
                "joy": EmotionCategory.HAPPY,
                "sadness": EmotionCategory.SAD,
                "anger": EmotionCategory.ANGRY,
                "fear": EmotionCategory.FEARFUL,
                "surprise": EmotionCategory.SURPRISED,
                "disgust": EmotionCategory.DISGUSTED,
                "neutral": EmotionCategory.NEUTRAL
            }
            
            primary_emotion = emotion_mapping.get(result[0]["label"], EmotionCategory.NEUTRAL)
            confidence = result[0]["score"]
            
            # Create emotions dict
            emotions = {}
            for item in result:
                emotion = emotion_mapping.get(item["label"], EmotionCategory.NEUTRAL)
                emotions[emotion.value] = item["score"]
            
            return EmotionResult(
                primary_emotion=primary_emotion,
                confidence=confidence,
                emotions=emotions,
                metadata={
                    "model": "MultimodalEmotionAnalyzer",
                    "input_type": "text",
                    "text_length": len(text.text)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Text emotion analysis failed: {str(e)}")
            raise
    
    async def analyze_multimodal(self, input_data: MultimodalInput) -> EmotionResult:
        """Analyze emotion from both audio and text."""
        if not self.is_loaded:
            await self.load_model()
        
        try:
            # Analyze both modalities
            audio_result = await self.analyze_audio(input_data.audio)
            text_result = await self.analyze_text(input_data.text)
            
            # Combine results (simple averaging for now)
            combined_emotions = {}
            all_emotions = set(audio_result.emotions.keys()) | set(text_result.emotions.keys())
            
            for emotion in all_emotions:
                audio_score = audio_result.emotions.get(emotion, 0.0)
                text_score = text_result.emotions.get(emotion, 0.0)
                combined_emotions[emotion] = (audio_score + text_score) / 2
            
            # Find primary emotion
            primary_emotion = max(combined_emotions.items(), key=lambda x: x[1])
            
            return EmotionResult(
                primary_emotion=EmotionCategory(primary_emotion[0]),
                confidence=primary_emotion[1],
                emotions=combined_emotions,
                metadata={
                    "model": "MultimodalEmotionAnalyzer",
                    "input_type": "multimodal",
                    "audio_confidence": audio_result.confidence,
                    "text_confidence": text_result.confidence
                }
            )
            
        except Exception as e:
            self.logger.error(f"Multimodal emotion analysis failed: {str(e)}")
            raise
    
    def get_supported_emotions(self) -> List[EmotionCategory]:
        """Get list of supported emotions."""
        return list(EmotionCategory)
    
    def get_model_info(self) -> dict:
        """Get model information."""
        return {
            "name": "MultimodalEmotionAnalyzer",
            "model_path": self.model_path,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "is_loaded": self.is_loaded
        }
    
    def _extract_audio_features(self, audio: AudioInput) -> np.ndarray:
        """Extract audio features for emotion analysis."""
        try:
            if audio.audio_data:
                # Convert bytes to numpy array
                if isinstance(audio.audio_data, bytes):
                    # Load audio from bytes
                    import io
                    audio_array, sample_rate = librosa.load(io.BytesIO(audio.audio_data), sr=None)
                else:
                    audio_array = np.array(audio.audio_data)
            elif audio.file_path:
                # Load from file
                audio_array, sample_rate = librosa.load(audio.file_path, sr=None)
            else:
                raise ValueError("No audio data provided")
            
            # Extract MFCC features
            mfcc = librosa.feature.mfcc(y=audio_array, sr=sample_rate, n_mfcc=13)
            
            return mfcc
            
        except Exception as e:
            self.logger.error(f"Failed to extract audio features: {str(e)}")
            raise


class MockAudioEmotionClassifier:
    """Mock audio emotion classifier for development."""
    
    async def analyze(self, audio_features: np.ndarray) -> Dict[str, Any]:
        """Mock emotion analysis."""
        # Return random emotion for development
        import random
        
        emotions = ["happy", "sad", "angry", "fearful", "surprised", "disgusted", "neutral"]
        primary_emotion = random.choice(emotions)
        confidence = random.uniform(0.6, 0.9)
        
        return {
            "primary_emotion": primary_emotion,
            "confidence": confidence,
            "emotions": {
                emotion: random.uniform(0.0, 1.0) for emotion in emotions
            },
            "duration": audio_features.shape[1] / 22050  # Rough estimate
        } 