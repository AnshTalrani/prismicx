"""
Adapter Manager

This module implements the AdapterManager class, which manages the relationship
between models and adapters, including activation, deactivation, and tracking
of active adapters.

Basic usage:
    manager = AdapterManager()
    manager.activate_adapter(model, "sales")
    manager.switch_adapter(model, "support")
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
import threading

from src.models.adapters.base_adapter import BaseAdapter, AdapterError
from src.models.adapters.adapter_registry import AdapterRegistry


class AdapterActivationError(Exception):
    """Exception raised for adapter activation errors."""
    pass


class AdapterManager:
    """
    Manages adapter activation and model integration.
    
    This class is responsible for:
    - Activating and deactivating adapters for models
    - Tracking which adapters are active for which models
    - Ensuring compatibility between models and adapters
    - Handling adapter switching and composition
    
    It follows the singleton pattern to ensure centralized adapter management.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Ensure only one instance of AdapterManager exists."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AdapterManager, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the manager if not already initialized."""
        if self._initialized:
            return
            
        self.logger = logging.getLogger(__name__)
        self.registry = AdapterRegistry.get_instance()
        
        # Dictionary mapping model IDs to active adapter names
        self._active_adapters: Dict[str, Set[str]] = {}
        
        # Dictionary mapping model IDs to model objects
        self._managed_models: Dict[str, Any] = {}
        
        self._initialized = True
        self.logger.info("Adapter manager initialized")
    
    @classmethod
    def get_instance(cls) -> 'AdapterManager':
        """
        Get the singleton instance of the AdapterManager.
        
        Returns:
            The AdapterManager instance
        """
        return cls()
    
    def get_adapter(self, adapter_name: str) -> Optional[BaseAdapter]:
        """
        Get an adapter by name from the registry.
        
        Args:
            adapter_name: Name of the adapter to retrieve
            
        Returns:
            The adapter if found, None otherwise
        """
        return self.registry.get_adapter(adapter_name)
    
    def get_adapters_for_bot(self, bot_type: str) -> List[BaseAdapter]:
        """
        Get all adapters suitable for a specific bot type.
        
        This maps bot types to appropriate adapter types:
        - "sales" -> "sales" adapters
        - "support" -> "support" adapters
        - "consultancy" -> "persuasion" adapters
        
        Args:
            bot_type: The type of bot (sales, support, consultancy)
            
        Returns:
            List of adapters suitable for the bot type
        """
        adapter_type_map = {
            "sales": "sales",
            "support": "support",
            "consultancy": "persuasion"
        }
        
        adapter_type = adapter_type_map.get(bot_type, bot_type)
        return self.registry.get_adapters_by_type(adapter_type)
    
    def get_adapter_config(self, adapter_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration of an adapter.
        
        Args:
            adapter_name: Name of the adapter
            
        Returns:
            The adapter's configuration or None if adapter not found
        """
        adapter = self.get_adapter(adapter_name)
        if adapter is None:
            return None
        return adapter.config.copy() if hasattr(adapter, "config") else {}
    
    def _get_model_id(self, model: Any) -> str:
        """
        Get a unique identifier for a model.
        
        Args:
            model: The model to identify
            
        Returns:
            A string identifier for the model
        """
        # Use model's name attribute if available
        if hasattr(model, "name"):
            return str(model.name)
            
        # Use model's config name if available (transformers models)
        if hasattr(model, "config") and hasattr(model.config, "name_or_path"):
            return str(model.config.name_or_path)
            
        # Fall back to object ID
        return str(id(model))
    
    def _register_model(self, model: Any) -> str:
        """
        Register a model with the manager.
        
        Args:
            model: The model to register
            
        Returns:
            The model ID
        """
        model_id = self._get_model_id(model)
        
        if model_id not in self._managed_models:
            self._managed_models[model_id] = model
            self._active_adapters[model_id] = set()
            self.logger.info(f"Registered model: {model_id}")
        
        return model_id
    
    def get_active_adapters(self, model: Any) -> List[str]:
        """
        Get the names of active adapters for a model.
        
        Args:
            model: The model to check
            
        Returns:
            List of active adapter names
        """
        model_id = self._get_model_id(model)
        
        if model_id not in self._active_adapters:
            return []
            
        return list(self._active_adapters[model_id])
    
    def is_adapter_active(self, model: Any, adapter_name: str) -> bool:
        """
        Check if an adapter is active for a model.
        
        Args:
            model: The model to check
            adapter_name: Name of the adapter to check
            
        Returns:
            True if the adapter is active, False otherwise
        """
        model_id = self._get_model_id(model)
        
        if model_id not in self._active_adapters:
            return False
            
        return adapter_name in self._active_adapters[model_id]
    
    def activate_adapter(self, model: Any, adapter_name: str, 
                         config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Activate an adapter for a model.
        
        Args:
            model: The model to activate the adapter for
            adapter_name: Name of the adapter to activate
            config: Optional configuration overrides
            
        Returns:
            True if activation was successful, False otherwise
            
        Raises:
            AdapterActivationError: If adapter activation fails
        """
        # Get the adapter
        adapter = self.get_adapter(adapter_name)
        if adapter is None:
            raise AdapterActivationError(f"Adapter '{adapter_name}' not found")
            
        # Register the model
        model_id = self._register_model(model)
        
        # Check if already active
        if adapter_name in self._active_adapters[model_id]:
            self.logger.info(f"Adapter '{adapter_name}' is already active for model {model_id}")
            return True
            
        # Initialize the adapter if needed
        if not adapter._is_initialized and not adapter.initialize():
            raise AdapterActivationError(f"Failed to initialize adapter '{adapter_name}'")
            
        # Apply the adapter to the model
        try:
            success = adapter.apply_to_model(model, config)
            
            if success:
                # Track the activation
                self._active_adapters[model_id].add(adapter_name)
                self.logger.info(f"Activated adapter '{adapter_name}' for model {model_id}")
                return True
            else:
                self.logger.error(f"Failed to apply adapter '{adapter_name}' to model {model_id}")
                return False
                
        except AdapterError as e:
            self.logger.error(f"Error activating adapter '{adapter_name}': {e}")
            raise AdapterActivationError(f"Error activating adapter '{adapter_name}': {e}")
    
    def deactivate_adapter(self, model: Any, adapter_name: str) -> bool:
        """
        Deactivate an adapter for a model.
        
        Args:
            model: The model to deactivate the adapter for
            adapter_name: Name of the adapter to deactivate
            
        Returns:
            True if deactivation was successful, False otherwise
        """
        # Get the adapter
        adapter = self.get_adapter(adapter_name)
        if adapter is None:
            self.logger.warning(f"Adapter '{adapter_name}' not found")
            return False
            
        # Get model ID
        model_id = self._get_model_id(model)
        
        # Check if active
        if model_id not in self._active_adapters or adapter_name not in self._active_adapters[model_id]:
            self.logger.info(f"Adapter '{adapter_name}' is not active for model {model_id}")
            return True
            
        # Remove the adapter from the model
        try:
            success = adapter.remove_from_model(model)
            
            if success:
                # Update tracking
                self._active_adapters[model_id].remove(adapter_name)
                self.logger.info(f"Deactivated adapter '{adapter_name}' for model {model_id}")
                return True
            else:
                self.logger.error(f"Failed to remove adapter '{adapter_name}' from model {model_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deactivating adapter '{adapter_name}': {e}")
            return False
    
    def switch_adapter(self, model: Any, adapter_name: str, 
                       config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Switch to a different adapter for a model, deactivating others.
        
        Args:
            model: The model to switch adapters for
            adapter_name: Name of the adapter to switch to
            config: Optional configuration overrides
            
        Returns:
            True if the switch was successful, False otherwise
        """
        # Register the model
        model_id = self._register_model(model)
        
        # Deactivate all currently active adapters
        current_adapters = list(self._active_adapters[model_id])
        for current_adapter in current_adapters:
            if current_adapter != adapter_name:
                self.deactivate_adapter(model, current_adapter)
        
        # Activate the new adapter if it's not already active
        if not self.is_adapter_active(model, adapter_name):
            return self.activate_adapter(model, adapter_name, config)
        
        return True
    
    def activate_adapters_for_bot(self, model: Any, bot_type: str, 
                                 config: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Activate all appropriate adapters for a specific bot type.
        
        Args:
            model: The model to activate adapters for
            bot_type: The type of bot (sales, support, consultancy)
            config: Optional configuration overrides
            
        Returns:
            List of activated adapter names
        """
        # Get all adapters for this bot type
        adapters = self.get_adapters_for_bot(bot_type)
        
        activated = []
        for adapter in adapters:
            try:
                if self.activate_adapter(model, adapter.name, config):
                    activated.append(adapter.name)
            except AdapterActivationError as e:
                self.logger.error(f"Failed to activate adapter '{adapter.name}' for bot type '{bot_type}': {e}")
        
        return activated
    
    def deactivate_all_adapters(self, model: Any) -> bool:
        """
        Deactivate all adapters for a model.
        
        Args:
            model: The model to deactivate adapters for
            
        Returns:
            True if all deactivations were successful, False otherwise
        """
        model_id = self._get_model_id(model)
        
        if model_id not in self._active_adapters:
            return True
            
        success = True
        active_adapters = list(self._active_adapters[model_id])
        
        for adapter_name in active_adapters:
            if not self.deactivate_adapter(model, adapter_name):
                success = False
        
        return success 