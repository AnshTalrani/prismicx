"""
Adapter Registry

This module implements the AdapterRegistry class, which serves as a central
repository for all available adapters in the system. It provides functionality
for registering, retrieving, and managing adapters.

Basic usage:
    registry = AdapterRegistry.get_instance()
    registry.register_adapter(my_adapter)
    retrieved_adapter = registry.get_adapter("my_adapter_name")
"""

import logging
from typing import Dict, List, Optional, Type, Any, Set
import threading

from src.models.adapters.base_adapter import BaseAdapter


class AdapterRegistry:
    """
    Singleton registry for all adapters in the system.
    
    This class serves as a central repository for all available adapters,
    allowing for discovery and retrieval of adapters by name or type.
    It follows the singleton pattern to ensure only one registry exists.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Ensure only one instance of AdapterRegistry exists."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AdapterRegistry, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the registry if not already initialized."""
        if self._initialized:
            return
            
        self._adapters: Dict[str, BaseAdapter] = {}
        self._adapter_types: Dict[str, Set[str]] = {}
        self.logger = logging.getLogger(__name__)
        self._initialized = True
        self.logger.info("Adapter registry initialized")
    
    @classmethod
    def get_instance(cls) -> 'AdapterRegistry':
        """
        Get the singleton instance of the AdapterRegistry.
        
        Returns:
            The AdapterRegistry instance
        """
        return cls()
    
    def register_adapter(self, adapter: BaseAdapter) -> bool:
        """
        Register an adapter in the registry.
        
        Args:
            adapter: The adapter to register
            
        Returns:
            True if registration was successful, False if adapter name already exists
        """
        adapter_name = adapter.name
        
        if adapter_name in self._adapters:
            self.logger.warning(f"Adapter '{adapter_name}' already registered")
            return False
            
        # Register the adapter
        self._adapters[adapter_name] = adapter
        
        # Track adapter by type
        adapter_type = adapter.adapter_type
        if adapter_type not in self._adapter_types:
            self._adapter_types[adapter_type] = set()
        self._adapter_types[adapter_type].add(adapter_name)
        
        self.logger.info(f"Registered adapter '{adapter_name}' of type '{adapter_type}'")
        return True
        
    def unregister_adapter(self, adapter_name: str) -> bool:
        """
        Remove an adapter from the registry.
        
        Args:
            adapter_name: The name of the adapter to remove
            
        Returns:
            True if unregistration was successful, False if adapter not found
        """
        if adapter_name not in self._adapters:
            self.logger.warning(f"Cannot unregister: Adapter '{adapter_name}' not found")
            return False
            
        # Get the adapter type before removing
        adapter_type = self._adapters[adapter_name].adapter_type
        
        # Remove from main registry
        del self._adapters[adapter_name]
        
        # Remove from type registry
        if adapter_type in self._adapter_types:
            self._adapter_types[adapter_type].discard(adapter_name)
            # Remove the type entry if empty
            if not self._adapter_types[adapter_type]:
                del self._adapter_types[adapter_type]
        
        self.logger.info(f"Unregistered adapter '{adapter_name}'")
        return True
    
    def get_adapter(self, adapter_name: str) -> Optional[BaseAdapter]:
        """
        Get an adapter by name.
        
        Args:
            adapter_name: The name of the adapter to retrieve
            
        Returns:
            The adapter if found, None otherwise
        """
        if adapter_name not in self._adapters:
            self.logger.warning(f"Adapter '{adapter_name}' not found in registry")
            return None
            
        return self._adapters[adapter_name]
    
    def get_adapters_by_type(self, adapter_type: str) -> List[BaseAdapter]:
        """
        Get all adapters of a specific type.
        
        Args:
            adapter_type: The type of adapters to retrieve
            
        Returns:
            List of adapters of the specified type
        """
        if adapter_type not in self._adapter_types:
            self.logger.info(f"No adapters of type '{adapter_type}' found")
            return []
            
        adapter_names = self._adapter_types[adapter_type]
        return [self._adapters[name] for name in adapter_names]
    
    def get_all_adapters(self) -> List[BaseAdapter]:
        """
        Get all registered adapters.
        
        Returns:
            List of all adapters in the registry
        """
        return list(self._adapters.values())
    
    def get_adapter_types(self) -> List[str]:
        """
        Get all registered adapter types.
        
        Returns:
            List of all adapter types
        """
        return list(self._adapter_types.keys())
    
    def get_adapter_names(self, adapter_type: Optional[str] = None) -> List[str]:
        """
        Get names of all registered adapters, optionally filtered by type.
        
        Args:
            adapter_type: Optional type to filter by
            
        Returns:
            List of adapter names
        """
        if adapter_type is not None:
            if adapter_type not in self._adapter_types:
                return []
            return list(self._adapter_types[adapter_type])
        else:
            return list(self._adapters.keys())
    
    def clear(self) -> None:
        """Remove all adapters from the registry."""
        self._adapters.clear()
        self._adapter_types.clear()
        self.logger.info("Adapter registry cleared")
    
    def __contains__(self, adapter_name: str) -> bool:
        """
        Check if an adapter exists in the registry.
        
        Args:
            adapter_name: Name of the adapter to check
            
        Returns:
            True if adapter exists, False otherwise
        """
        return adapter_name in self._adapters
        
    def __len__(self) -> int:
        """
        Get the number of registered adapters.
        
        Returns:
            Number of adapters in the registry
        """
        return len(self._adapters) 