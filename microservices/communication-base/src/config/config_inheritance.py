"""
Config Inheritance System

Provides functionality for merging configuration dictionaries with proper inheritance.
Base configs are extended/overridden by more specific configs in a clean, predictable way.

Basic usage:
    base_config = {...}
    specific_config = {...}
    inheritance = ConfigInheritance()
    merged = inheritance.merge_configs(base_config, specific_config)
"""

import copy
import logging
from typing import Dict, Any, Optional

class ConfigInheritance:
    """
    Handles merging of configuration dictionaries with proper inheritance.
    
    The inheritance follows these rules:
    1. Values in specific_config override values in base_config
    2. For nested dictionaries, merging is done recursively
    3. Lists and other non-dict values are replaced completely, not merged
    """
    
    def __init__(self):
        """Initialize the ConfigInheritance."""
        self.logger = logging.getLogger(__name__)
    
    def merge_configs(self, base_config: Dict[str, Any], specific_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge base and specific configs with proper inheritance.
        
        Args:
            base_config: The base configuration dictionary
            specific_config: The more specific configuration that overrides base values
            
        Returns:
            A new dictionary with merged configuration values
        """
        if not isinstance(base_config, dict):
            self.logger.warning(f"Base config must be a dictionary, got {type(base_config)}")
            return specific_config if isinstance(specific_config, dict) else {}
            
        if not isinstance(specific_config, dict):
            self.logger.warning(f"Specific config must be a dictionary, got {type(specific_config)}")
            return base_config.copy()
        
        # Start with a shallow copy of the base config
        merged = base_config.copy()
        
        # Merge in the specific config
        for key, value in specific_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                merged[key] = self.merge_configs(merged[key], value)
            else:
                # For non-dictionary values, the specific config overrides the base
                merged[key] = value
                
        return merged
        
    def get_value(self, config: Dict[str, Any], path: str, default: Any = None) -> Any:
        """
        Get a value from a nested dictionary using a dot notation path.
        
        Args:
            config: The configuration dictionary
            path: A dot-separated path to the desired value (e.g., 'models.llm.temperature')
            default: The default value to return if the path doesn't exist
            
        Returns:
            The value at the specified path or the default value if not found
        """
        if not path:
            return default
            
        parts = path.split('.')
        current = config
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
                
        return current
        
    def set_value(self, config: Dict[str, Any], path: str, value: Any) -> Dict[str, Any]:
        """
        Set a value in a nested dictionary using a dot notation path.
        Creates intermediate dictionaries if they don't exist.
        
        Args:
            config: The configuration dictionary to modify
            path: A dot-separated path to where the value should be set
            value: The value to set
            
        Returns:
            The modified config dictionary
        """
        if not path:
            return config
            
        parts = path.split('.')
        current = config
        
        # Traverse to the last level, creating dictionaries as needed
        for i, part in enumerate(parts[:-1]):
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
            
        # Set the value at the final level
        current[parts[-1]] = value
        
        return config 