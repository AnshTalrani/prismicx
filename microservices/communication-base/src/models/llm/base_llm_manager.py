"""
Base LLM Manager abstract class for handling language models across different bot types.
Provides common functionality for model loading, caching, and adapter integration.
"""

from abc import ABC, abstractmethod
import os
import logging
from typing import Dict, Any, Optional, List, Union
import structlog
from src.models.adapters.adapter_manager import AdapterManager
from src.models.adapters.adapter_registry import AdapterRegistry
from src.models.llm.model_cache import ModelCache
from src.config.config_integration import ConfigIntegration

# Setup structured logging
logger = structlog.get_logger(__name__)

class ModelLoadingError(Exception):
    """Exception raised when model loading fails."""
    pass

class BaseLLMManager(ABC):
    """
    Base abstract class for LLM handling across different bot types.
    
    This class provides the interface and common functionality for:
    - Loading and managing models
    - Handling adapters
    - Providing model access with appropriate configurations
    - Managing model lifecycle
    """
    
    def __init__(self, bot_type: str):
        """
        Initialize the LLM Manager for a specific bot type.
        
        Args:
            bot_type: The type of bot (consultancy, sales, support)
        """
        self.bot_type = bot_type
        self.models = {}
        self.model_cache = ModelCache()
        self.adapter_manager = AdapterManager()
        self.adapter_registry = AdapterRegistry()
        self.config_integration = ConfigIntegration()
        self.config = self.config_integration.get_config(bot_type)
        
        # Register with model registry for centralized management
        from src.models.llm.model_registry import ModelRegistry
        self.model_registry = ModelRegistry()
        self.model_registry.register_manager(bot_type, self)
        
        logger.info(f"Initialized BaseLLMManager for bot type: {bot_type}")
    
    def load_model(self, model_name: str, model_path: Optional[str] = None, fallback_path: Optional[str] = None) -> Any:
        """
        Load a model with error handling and fallbacks.
        
        Args:
            model_name: Name to reference the model
            model_path: Path to the model
            fallback_path: Path to fallback model if primary fails
            
        Returns:
            The loaded model
            
        Raises:
            ModelLoadingError: If model loading fails and no fallback is available
        """
        if not model_path:
            model_path = self.config.get(f"models.paths.{model_name}", f"models/{self.bot_type}/{model_name}")
        
        # Check cache first
        cached_model = self.model_cache.get(model_path)
        if cached_model:
            logger.info(f"Using cached model: {model_name} from {model_path}")
            return cached_model
        
        try:
            logger.info(f"Loading model: {model_name} from {model_path}")
            model = self._load_specific_model(model_path)
            self.models[model_name] = model
            self.model_cache.add(model_path, model)
            return model
        except Exception as e:
            logger.error(f"Failed to load model {model_name} from {model_path}: {e}")
            if fallback_path:
                logger.info(f"Attempting to load fallback model from {fallback_path}")
                try:
                    fallback_model = self._load_specific_model(fallback_path)
                    self.models[model_name] = fallback_model
                    return fallback_model
                except Exception as fallback_e:
                    logger.error(f"Failed to load fallback model from {fallback_path}: {fallback_e}")
            
            raise ModelLoadingError(f"Failed to load model {model_name} and no fallback available")
    
    def get_model(self, model_name: str) -> Any:
        """
        Get a loaded model by name.
        
        Args:
            model_name: Name of the model to retrieve
            
        Returns:
            The loaded model
            
        Raises:
            KeyError: If the model is not loaded
        """
        if model_name not in self.models:
            logger.warning(f"Model {model_name} not loaded, attempting to load now")
            return self.load_model(model_name)
            
        return self.models[model_name]
    
    def activate_adapter(self, model_name: str, adapter_name: str) -> bool:
        """
        Activate a specific adapter for a model.
        
        Args:
            model_name: Name of the model to use
            adapter_name: Name of the adapter to activate
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Activating adapter {adapter_name} for model {model_name}")
        if model_name not in self.models:
            logger.error(f"Cannot activate adapter: Model {model_name} not loaded")
            return False
            
        model = self.models[model_name]
        return self.adapter_manager.activate_adapter(model, adapter_name)
    
    def get_adapter_list(self) -> List[str]:
        """
        Get list of available adapters for this bot type.
        
        Returns:
            List of adapter names
        """
        return self.adapter_registry.list_adapters(self.bot_type)
    
    def release_model(self, model_name: str) -> None:
        """
        Release model resources when no longer needed.
        
        Args:
            model_name: Name of the model to release
        """
        if model_name in self.models:
            logger.info(f"Releasing model: {model_name}")
            # Implementation depends on specific model type
            del self.models[model_name]
    
    def release_all_models(self) -> None:
        """Release all model resources."""
        logger.info(f"Releasing all models for {self.bot_type}")
        for model_name in list(self.models.keys()):
            self.release_model(model_name)
    
    @abstractmethod
    def _load_specific_model(self, model_path: str) -> Any:
        """
        Load a specific model implementation.
        
        Args:
            model_path: Path to the model
            
        Returns:
            The loaded model
        """
        pass
    
    @abstractmethod
    def prepare_inference_params(self, model_name: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare parameters for model inference.
        
        Args:
            model_name: Name of the model to use
            **kwargs: Additional parameters
            
        Returns:
            Dictionary of parameters for inference
        """
        pass

    def generate_response(self, prompt: str, model=None, **kwargs) -> str:
        """
        Generate a response from the model.
        
        Args:
            prompt: Input prompt for the model
            model: Optional specific model to use (uses default if not provided)
            **kwargs: Additional parameters for generation
            
        Returns:
            Generated response text
        """
        pass

    def get_cached_model(self, model_id: str) -> Optional[Any]:
        """
        Get a model from cache if available.
        
        Args:
            model_id: ID of the model to retrieve
            
        Returns:
            The cached model if available, None otherwise
        """
        return self.models.get(model_id)

    def cache_model(self, model_id: str, model: Any) -> None:
        """
        Cache a model for future use.
        
        Args:
            model_id: ID to use for caching the model
            model: The model to cache
        """
        logger.info(f"Caching model with ID: {model_id}")
        self.models[model_id] = model 