"""
Factory for creating and configuring LLM instances.
Provides a centralized way to access language models with consistent configuration.
"""

import logging
from typing import Any, Dict, Optional, Union

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from langchain_cohere import ChatCohere

from src.config.config_inheritance import ConfigInheritance


class LLMFactory:
    """
    Factory for creating and configuring LLM instances.
    
    Provides a centralized way to access different language models with consistent
    configuration. Supports multiple model providers and caches models for reuse.
    """
    
    def __init__(self):
        """Initialize the LLM factory."""
        self.config_inheritance = ConfigInheritance()
        self.logger = logging.getLogger(__name__)
        self._model_cache = {}
    
    def get_llm(
        self,
        model_name: str = None,
        temperature: float = None,
        max_tokens: int = None,
        bot_type: str = None,
        streaming: bool = False,
        **kwargs
    ) -> BaseChatModel:
        """
        Get an LLM instance with the specified configuration.
        
        Args:
            model_name: Name of the model to use (e.g., "gpt-3.5-turbo", "claude-3-opus")
            temperature: Temperature setting for the model
            max_tokens: Maximum tokens to generate
            bot_type: Type of bot to get configuration for
            streaming: Whether to enable streaming responses
            **kwargs: Additional model-specific parameters
            
        Returns:
            Configured LLM instance
        """
        # If bot_type is provided, get config from inheritance system
        config = {}
        if bot_type:
            try:
                config = self.config_inheritance.get_config(bot_type)
            except Exception as e:
                self.logger.error(f"Error getting config for bot type {bot_type}: {e}")
        
        # Get model parameters
        model_name = model_name or config.get("llm.model_name", "gpt-3.5-turbo")
        temperature = temperature if temperature is not None else config.get("llm.temperature", 0.7)
        max_tokens = max_tokens if max_tokens is not None else config.get("llm.max_tokens", 1000)
        
        # Create cache key
        cache_key = f"{model_name}_{temperature}_{max_tokens}_{streaming}"
        for k, v in sorted(kwargs.items()):
            cache_key += f"_{k}_{v}"
        
        # Check cache
        if cache_key in self._model_cache:
            return self._model_cache[cache_key]
        
        # Create new model
        try:
            model = self._create_model(model_name, temperature, max_tokens, streaming, **kwargs)
            self._model_cache[cache_key] = model
            return model
        except Exception as e:
            self.logger.error(f"Error creating LLM {model_name}: {e}")
            # Fallback to default model
            return self._create_default_model()
    
    def _create_model(
        self,
        model_name: str,
        temperature: float,
        max_tokens: int,
        streaming: bool,
        **kwargs
    ) -> BaseChatModel:
        """
        Create an LLM instance based on the model name.
        
        Args:
            model_name: Name of the model to use
            temperature: Temperature setting
            max_tokens: Maximum tokens to generate
            streaming: Whether to enable streaming responses
            **kwargs: Additional model-specific parameters
            
        Returns:
            Configured LLM instance
        """
        # Common parameters for all models
        common_params = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "streaming": streaming,
            **kwargs
        }
        
        if "gpt" in model_name.lower() or "openai" in model_name.lower():
            # OpenAI models
            return ChatOpenAI(
                model_name=model_name,
                **common_params
            )
            
        elif "claude" in model_name.lower() or "anthropic" in model_name.lower():
            # Anthropic models
            return ChatAnthropic(
                model_name=model_name,
                **common_params
            )
            
        elif "palm" in model_name.lower() or "gemini" in model_name.lower():
            # Google models
            return ChatGoogleGenerativeAI(
                model=model_name,
                **common_params
            )
            
        elif "cohere" in model_name.lower() or "command" in model_name.lower():
            # Cohere models
            return ChatCohere(
                model=model_name,
                **common_params
            )
            
        else:
            # Unknown model type, try OpenAI as fallback
            self.logger.warning(f"Unknown model type: {model_name}, using OpenAI")
            return ChatOpenAI(
                model_name=model_name,
                **common_params
            )
    
    def _create_default_model(self) -> BaseChatModel:
        """
        Create a default model as fallback.
        
        Returns:
            Default LLM instance
        """
        self.logger.warning("Creating default model as fallback")
        return ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1000
        )


# Global instance
llm_factory = LLMFactory() 