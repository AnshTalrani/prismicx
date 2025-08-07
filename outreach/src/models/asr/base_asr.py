"""
Base ASR Interface

Defines the abstract base class for all ASR implementations.
New ASR engines should inherit from this class and implement all abstract methods.
"""
from abc import ABC, abstractmethod
from typing import Optional, BinaryIO


class BaseASR(ABC):
    """Abstract base class for ASR implementations."""
    
    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        **kwargs
    ) -> str:
        """Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio data in a supported format
            language: Optional language code (ISO 639-1)
            **kwargs: Additional engine-specific parameters
            
        Returns:
            Transcribed text
        """
        pass
    
    @abstractmethod
    async def transcribe_file(
        self,
        file_path: str,
        language: Optional[str] = None,
        **kwargs
    ) -> str:
        """Transcribe audio from a file.
        
        Args:
            file_path: Path to audio file
            language: Optional language code (ISO 639-1)
            **kwargs: Additional engine-specific parameters
            
        Returns:
            Transcribed text
        """
        pass
