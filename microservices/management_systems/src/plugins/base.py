"""
Base plugin module defining the plugin interface and common functionality.

This module provides the base class that all plugins must inherit from,
ensuring a consistent interface and providing common utility methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PluginBase(ABC):
    """Base class for all plugins in the system."""
    
    def __init__(self, plugin_id: str, version: str = "0.1.0"):
        """Initialize the plugin.
        
        Args:
            plugin_id: Unique identifier for the plugin
            version: Version string following semantic versioning
        """
        self.plugin_id = plugin_id
        self.version = version
        self.enabled = True
        self.config: Dict[str, Any] = {}
        
    @property
    def name(self) -> str:
        """Get the human-readable name of the plugin."""
        return self.__class__.__name__
        
    @property
    def description(self) -> str:
        """Get the plugin description."""
        return self.__doc__ or "No description available"
        
    @property
    def dependencies(self) -> List[str]:
        """Get the list of plugin dependencies."""
        return []
        
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the plugin with the provided settings.
        
        Args:
            config: Dictionary containing plugin configuration
        """
        self.config.update(config)
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the plugin.
        
        This method is called when the plugin is first loaded.
        Implement any setup logic here.
        """
        pass
        
    @abstractmethod
    async def start(self) -> None:
        """Start the plugin.
        
        This method is called when the plugin should begin its main operation.
        """
        pass
        
    @abstractmethod
    async def stop(self) -> None:
        """Stop the plugin.
        
        This method is called when the plugin should cease operation.
        Implement cleanup logic here.
        """
        pass
        
    async def reload(self) -> None:
        """Reload the plugin.
        
        Default implementation stops and starts the plugin.
        Override if custom reload behavior is needed.
        """
        await self.stop()
        await self.start()
        
    def enable(self) -> None:
        """Enable the plugin."""
        self.enabled = True
        logger.info(f"Plugin {self.name} enabled")
        
    def disable(self) -> None:
        """Disable the plugin."""
        self.enabled = False
        logger.info(f"Plugin {self.name} disabled")
        
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The configuration value or default
        """
        return self.config.get(key, default)
        
    def __repr__(self) -> str:
        """Get string representation of the plugin."""
        return f"{self.name}(id={self.plugin_id}, version={self.version})" 