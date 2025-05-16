"""
Base Adapter

Defines the interface for all adapters in the system.
All concrete adapter implementations should inherit from this base class.

Basic usage:
    class HypnosisAdapter(BaseAdapter):
        def apply_to_model(self, model, config):
            # Apply hypnosis techniques to model
            return True
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class AdapterError(Exception):
    """Base exception class for all adapter-related errors."""
    pass


class BaseAdapter(ABC):
    """
    Base class for all adapters.
    
    Defines the interface that all adapter implementations must follow.
    """
    
    def __init__(self, name: str, adapter_type: str, 
                 path: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the adapter.
        
        Args:
            name: The name of this adapter
            adapter_type: The type of this adapter
            path: Optional path to adapter files or resources
            config: Optional configuration for this adapter
        """
        self.name = name
        self.type = adapter_type
        self.path = path
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self._is_loaded = False
        self._is_initialized = False
        
    @property
    def is_loaded(self) -> bool:
        """Check if the adapter is loaded."""
        return self._is_loaded
        
    @property
    def is_initialized(self) -> bool:
        """Check if the adapter is initialized."""
        return self._is_initialized
    
    def initialize(self) -> bool:
        """
        Initialize the adapter.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if self._is_initialized:
            self.logger.debug(f"Adapter '{self.name}' is already initialized")
            return True
            
        try:
            self._initialize()
            self._is_initialized = True
            self.logger.info(f"Initialized adapter '{self.name}'")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize adapter '{self.name}': {e}")
            return False
    
    def load(self) -> bool:
        """
        Load the adapter.
        
        Returns:
            True if loading was successful, False otherwise
        """
        if self._is_loaded:
            self.logger.debug(f"Adapter '{self.name}' is already loaded")
            return True
            
        if not self._is_initialized:
            if not self.initialize():
                return False
                
        try:
            self._load()
            self._is_loaded = True
            self.logger.info(f"Loaded adapter '{self.name}'")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load adapter '{self.name}': {e}")
            return False
    
    def unload(self) -> bool:
        """
        Unload the adapter.
        
        Returns:
            True if unloading was successful, False otherwise
        """
        if not self._is_loaded:
            self.logger.debug(f"Adapter '{self.name}' is not loaded")
            return True
            
        try:
            self._unload()
            self._is_loaded = False
            self.logger.info(f"Unloaded adapter '{self.name}'")
            return True
        except Exception as e:
            self.logger.error(f"Failed to unload adapter '{self.name}': {e}")
            return False
    
    @abstractmethod
    def apply_to_model(self, model: Any, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Apply this adapter to a model.
        
        Args:
            model: The model to apply the adapter to
            config: Optional configuration for application
            
        Returns:
            True if application was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def remove_from_model(self, model: Any) -> bool:
        """
        Remove this adapter from a model.
        
        Args:
            model: The model to remove the adapter from
            
        Returns:
            True if removal was successful, False otherwise
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this adapter.
        
        Returns:
            Dictionary containing adapter information
        """
        return {
            "name": self.name,
            "type": self.type,
            "path": self.path,
            "is_loaded": self._is_loaded,
            "is_initialized": self._is_initialized
        }
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update the adapter configuration.
        
        Args:
            config: New configuration parameters
        """
        self.config.update(config)
    
    def _initialize(self) -> None:
        """
        Internal method to initialize the adapter.
        
        Override this in concrete implementations to implement adapter-specific initialization.
        """
        pass
    
    def _load(self) -> None:
        """
        Internal method to load the adapter.
        
        Override this in concrete implementations to implement adapter-specific loading.
        """
        pass
    
    def _unload(self) -> None:
        """
        Internal method to unload the adapter.
        
        Override this in concrete implementations to implement adapter-specific unloading.
        """
        pass 