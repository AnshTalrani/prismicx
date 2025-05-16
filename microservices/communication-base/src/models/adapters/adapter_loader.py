"""
Adapter loader for loading and validating LoRA adapters.

This module handles the loading and validation of LoRA adapters
from disk or other sources.
"""

import logging
import os
import json
from typing import Dict, Any, Optional, List, Type, Tuple

from src.models.adapters.base_adapter import BaseAdapter, AdapterError
from src.models.adapters.hypnosis_adapter import HypnosisAdapter

class AdapterLoader:
    """Loader for LoRA adapters with validation."""
    
    def __init__(self, adapter_dir: str = None):
        """
        Initialize the adapter loader.
        
        Args:
            adapter_dir: Base directory for adapter files
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.adapter_dir = adapter_dir or os.environ.get(
            "ADAPTER_DIR", 
            "/models/adapters"
        )
        self.logger.info(f"Adapter loader initialized with directory: {self.adapter_dir}")
        
        # Map of adapter types to their classes
        self.adapter_types: Dict[str, Type[BaseAdapter]] = {
            "hypnosis": HypnosisAdapter,
            # Add other adapter types here as they're implemented
        }
    
    def load_adapter_from_path(self, 
                             adapter_path: str, 
                             adapter_type: str, 
                             adapter_id: str = None) -> Optional[BaseAdapter]:
        """
        Load an adapter from a specific path.
        
        Args:
            adapter_path: Path to the adapter
            adapter_type: Type of adapter to load
            adapter_id: Optional ID for the adapter (defaults to basename of path)
            
        Returns:
            Loaded adapter instance if successful, None otherwise
        """
        if adapter_type not in self.adapter_types:
            self.logger.error(f"Unknown adapter type: {adapter_type}")
            return None
            
        adapter_class = self.adapter_types[adapter_type]
        
        if not os.path.exists(adapter_path):
            self.logger.error(f"Adapter path does not exist: {adapter_path}")
            return None
            
        try:
            # Try to load metadata if available
            metadata = self._load_metadata(adapter_path)
            
            # Use basename if ID not provided
            if not adapter_id:
                adapter_id = os.path.basename(adapter_path)
            
            # Create and load the adapter
            adapter = adapter_class(adapter_id=adapter_id, adapter_path=adapter_path, metadata=metadata)
            if not adapter.load():
                self.logger.error(f"Failed to load adapter: {adapter_id}")
                return None
                
            return adapter
            
        except Exception as e:
            self.logger.error(f"Error loading adapter from {adapter_path}: {e}")
            return None
    
    def discover_adapters(self) -> List[Tuple[str, str, str]]:
        """
        Discover available adapters in the adapter directory.
        
        Returns:
            List of tuples (adapter_id, adapter_path, adapter_type)
        """
        discovered = []
        
        try:
            for adapter_type in self.adapter_types.keys():
                type_dir = os.path.join(self.adapter_dir, adapter_type)
                
                if not os.path.exists(type_dir) or not os.path.isdir(type_dir):
                    self.logger.warning(f"Adapter type directory does not exist: {type_dir}")
                    continue
                
                for entry in os.listdir(type_dir):
                    entry_path = os.path.join(type_dir, entry)
                    
                    if os.path.isdir(entry_path):
                        # Check if this is an adapter directory (has config.json or adapter_config.json)
                        if (os.path.exists(os.path.join(entry_path, "config.json")) or
                            os.path.exists(os.path.join(entry_path, "adapter_config.json"))):
                            discovered.append((entry, entry_path, adapter_type))
                            
            self.logger.info(f"Discovered {len(discovered)} adapters")
            return discovered
            
        except Exception as e:
            self.logger.error(f"Error discovering adapters: {e}")
            return []
    
    def load_all_discovered_adapters(self) -> Dict[str, BaseAdapter]:
        """
        Load all discovered adapters.
        
        Returns:
            Dictionary mapping adapter IDs to adapter instances
        """
        adapters = {}
        discovered = self.discover_adapters()
        
        for adapter_id, adapter_path, adapter_type in discovered:
            self.logger.info(f"Loading discovered adapter: {adapter_id} ({adapter_type})")
            adapter = self.load_adapter_from_path(adapter_path, adapter_type, adapter_id)
            
            if adapter:
                adapters[adapter_id] = adapter
                
        self.logger.info(f"Loaded {len(adapters)} adapters")
        return adapters
    
    def _load_metadata(self, adapter_path: str) -> Optional[Dict[str, Any]]:
        """
        Load metadata from an adapter directory.
        
        Args:
            adapter_path: Path to the adapter directory
            
        Returns:
            Metadata dictionary if available, None otherwise
        """
        # Check for config files
        config_paths = [
            os.path.join(adapter_path, "config.json"),
            os.path.join(adapter_path, "adapter_config.json"),
            os.path.join(adapter_path, "metadata.json")
        ]
        
        for path in config_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    self.logger.warning(f"Error loading adapter metadata from {path}: {e}")
        
        return None
    
    def validate_adapter(self, adapter: BaseAdapter) -> bool:
        """
        Validate an adapter for correctness.
        
        Args:
            adapter: The adapter to validate
            
        Returns:
            True if the adapter is valid, False otherwise
        """
        # Basic validation - check if adapter loads
        return adapter.load() 