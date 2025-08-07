"""
Base LLM Interface

Defines the abstract base class for all LLM implementations.
New LLM providers should inherit from this class.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union


class BaseLLM(ABC):
    """Abstract base class for LLM implementations."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> str:
        """Generate text completion.
        
        Args:
            prompt: The input prompt
            conversation_history: Optional list of previous messages in the conversation
            **kwargs: Additional model-specific parameters
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Generate chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            **kwargs: Additional model-specific parameters
            
        Returns:
            Generated chat response
        """
        pass
    
    @abstractmethod
    async def get_embeddings(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """Get embeddings for input texts.
        
        Args:
            texts: List of input texts
            **kwargs: Additional model-specific parameters
            
        Returns:
            List of embedding vectors
        """
        pass
