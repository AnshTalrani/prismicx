"""
Base Language Model (LLM) Interface

This module defines the base interface for all Language Models,
providing a common API for text generation and analysis.
"""

import abc
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum


class MessageRole(str, Enum):
    """Role of a message in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class Message:
    """A message in a conversation."""
    
    role: MessageRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict] = None
    metadata: Optional[Dict] = None


@dataclass
class GenerationResult:
    """Result of text generation."""
    
    text: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict] = None
    metadata: Optional[Dict] = None


@dataclass
class EmbeddingResult:
    """Result of text embedding."""
    
    embeddings: List[List[float]]
    model: str
    usage: Optional[Dict] = None
    metadata: Optional[Dict] = None


class BaseLLM(abc.ABC):
    """Base interface for all Language Models."""
    
    def __init__(self, config: Dict):
        """Initialize the LLM with configuration."""
        self.config = config
        self.model = None
        self.is_loaded = False
        self.context_window = 4096  # Default context window size
    
    @abc.abstractmethod
    def load_model(self) -> None:
        """Load the language model."""
        pass
    
    @abc.abstractmethod
    def generate(
        self, 
        messages: List[Message], 
        **kwargs
    ) -> GenerationResult:
        """Generate text based on conversation messages."""
        pass
    
    @abc.abstractmethod
    def generate_stream(
        self, 
        messages: List[Message], 
        **kwargs
    ):
        """Generate text stream based on conversation messages."""
        pass
    
    @abc.abstractmethod
    def embed(self, texts: List[str]) -> EmbeddingResult:
        """Generate embeddings for text."""
        pass
    
    @abc.abstractmethod
    def get_model_info(self) -> Dict:
        """Get information about the loaded model."""
        pass
    
    def is_model_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self.is_loaded
    
    def validate_messages(self, messages: List[Message]) -> bool:
        """Validate conversation messages."""
        if not messages:
            return False
        
        for message in messages:
            if not isinstance(message, Message):
                return False
            if not message.content or not message.role:
                return False
        
        return True
    
    def truncate_messages(
        self, 
        messages: List[Message], 
        max_tokens: Optional[int] = None
    ) -> List[Message]:
        """Truncate messages to fit within context window."""
        if not max_tokens:
            max_tokens = self.context_window
        
        # Simple token estimation (can be overridden by subclasses)
        total_tokens = 0
        truncated_messages = []
        
        for message in reversed(messages):
            estimated_tokens = len(message.content.split()) * 1.3  # Rough estimation
            if total_tokens + estimated_tokens <= max_tokens:
                truncated_messages.insert(0, message)
                total_tokens += estimated_tokens
            else:
                break
        
        return truncated_messages
    
    def create_system_message(self, content: str) -> Message:
        """Create a system message."""
        return Message(role=MessageRole.SYSTEM, content=content)
    
    def create_user_message(self, content: str) -> Message:
        """Create a user message."""
        return Message(role=MessageRole.USER, content=content)
    
    def create_assistant_message(self, content: str) -> Message:
        """Create an assistant message."""
        return Message(role=MessageRole.ASSISTANT, content=content)
    
    def format_conversation(self, messages: List[Message]) -> str:
        """Format conversation messages as a single string."""
        formatted = []
        for message in messages:
            role_prefix = message.role.value.upper()
            formatted.append(f"{role_prefix}: {message.content}")
        
        return "\n".join(formatted)
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics for the model."""
        return {
            "model": self.get_model_info().get("name", "unknown"),
            "context_window": self.context_window,
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


class LLMFactory:
    """Factory for creating Language Models."""
    
    _models = {}
    
    @classmethod
    def register(cls, name: str, model_class: type):
        """Register a model class."""
        cls._models[name] = model_class
    
    @classmethod
    def create(cls, name: str, config: Dict) -> BaseLLM:
        """Create a model instance."""
        if name not in cls._models:
            raise ValueError(f"Unknown model: {name}")
        
        model_class = cls._models[name]
        return model_class(config)
    
    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available models."""
        return list(cls._models.keys())


# Common exceptions
class LLMError(Exception):
    """Base exception for LLM errors."""
    pass


class ModelNotLoadedError(LLMError):
    """Raised when trying to use a model that hasn't been loaded."""
    pass


class GenerationError(LLMError):
    """Raised when there's an error during text generation."""
    pass


class EmbeddingError(LLMError):
    """Raised when there's an error during embedding generation."""
    pass


class ContextLengthError(LLMError):
    """Raised when input exceeds context window."""
    pass
