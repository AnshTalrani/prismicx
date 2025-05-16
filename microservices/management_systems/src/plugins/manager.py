"""
Plugin manager module for handling plugin lifecycle and management.

This module provides the PluginManager class which is responsible for:
- Loading and unloading plugins
- Managing plugin lifecycle (initialize, start, stop)
- Handling plugin dependencies
- Managing plugin configuration
- Coordinating hot-reloading
"""

import asyncio
import importlib
import inspect
import logging
import sys
from pathlib import Path
from typing import Dict, List, Type, Optional, Any, Set
from concurrent.futures import ThreadPoolExecutor

from .base import PluginBase
from .watcher import PluginWatcher

logger = logging.getLogger(__name__)

class PluginManager:
    """Manages the lifecycle and operations of plugins."""
    
    def __init__(self, plugin_dir: str, config: Dict[str, Any]):
        """Initialize the plugin manager.
        
        Args:
            plugin_dir: Directory containing plugin modules
            config: Configuration dictionary for plugins
        """
        self.plugin_dir = Path(plugin_dir)
        self.config = config
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_classes: Dict[str, Type[PluginBase]] = {}
        self._executor = ThreadPoolExecutor()
        self._watcher: Optional[PluginWatcher] = None
        
    async def initialize(self) -> None:
        """Initialize the plugin manager and load plugins."""
        # Ensure plugin directory exists
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Add plugin directory to Python path
        if str(self.plugin_dir) not in sys.path:
            sys.path.append(str(self.plugin_dir))
            
        # Set up plugin watcher if hot-reload is enabled
        if self.config.get('enable_hot_reload', False):
            self._watcher = PluginWatcher(
                str(self.plugin_dir),
                self._handle_plugin_change
            )
            await asyncio.get_event_loop().run_in_executor(
                self._executor,
                self._watcher.start
            )
            
        # Load all plugins
        await self.load_all_plugins()
        
    async def load_all_plugins(self) -> None:
        """Load all plugins from the plugin directory."""
        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.stem.startswith("__"):
                continue
            await self.load_plugin(plugin_file.stem)
            
    async def load_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """Load a plugin by name.
        
        Args:
            plugin_name: Name of the plugin module to load
            
        Returns:
            Optional[PluginBase]: Loaded plugin instance or None if loading fails
        """
        try:
            # Import or reload the module
            if plugin_name in sys.modules:
                module = importlib.reload(sys.modules[plugin_name])
            else:
                module = importlib.import_module(plugin_name)
                
            # Find plugin class in module
            plugin_class = None
            for item_name, item in inspect.getmembers(module):
                if (inspect.isclass(item) and 
                    issubclass(item, PluginBase) and 
                    item != PluginBase):
                    plugin_class = item
                    break
                    
            if not plugin_class:
                logger.error(f"No plugin class found in {plugin_name}")
                return None
                
            # Create plugin instance
            plugin = plugin_class(plugin_name)
            
            # Configure plugin
            plugin_config = self.config.get('plugins', {}).get(plugin_name, {})
            plugin.configure(plugin_config)
            
            # Initialize plugin
            await plugin.initialize()
            
            # Store plugin
            self.plugins[plugin_name] = plugin
            self.plugin_classes[plugin_name] = plugin_class
            
            logger.info(f"Loaded plugin: {plugin_name}")
            return plugin
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {str(e)}")
            return None
            
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin by name.
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            bool: True if plugin was unloaded successfully
        """
        if plugin_name not in self.plugins:
            return False
            
        try:
            plugin = self.plugins[plugin_name]
            await plugin.stop()
            del self.plugins[plugin_name]
            del self.plugin_classes[plugin_name]
            logger.info(f"Unloaded plugin: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {str(e)}")
            return False
            
    async def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin by name.
        
        Args:
            plugin_name: Name of the plugin to reload
            
        Returns:
            bool: True if plugin was reloaded successfully
        """
        await self.unload_plugin(plugin_name)
        plugin = await self.load_plugin(plugin_name)
        return plugin is not None
        
    async def start_all_plugins(self) -> None:
        """Start all loaded plugins."""
        for plugin in self.plugins.values():
            try:
                await plugin.start()
                logger.info(f"Started plugin: {plugin.name}")
            except Exception as e:
                logger.error(f"Failed to start plugin {plugin.name}: {str(e)}")
                
    async def stop_all_plugins(self) -> None:
        """Stop all loaded plugins."""
        for plugin in self.plugins.values():
            try:
                await plugin.stop()
                logger.info(f"Stopped plugin: {plugin.name}")
            except Exception as e:
                logger.error(f"Failed to stop plugin {plugin.name}: {str(e)}")
                
    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """Get a plugin instance by name.
        
        Args:
            plugin_name: Name of the plugin to get
            
        Returns:
            Optional[PluginBase]: Plugin instance or None if not found
        """
        return self.plugins.get(plugin_name)
        
    def list_plugins(self) -> List[str]:
        """Get a list of loaded plugin names.
        
        Returns:
            List[str]: List of plugin names
        """
        return list(self.plugins.keys())
        
    async def _handle_plugin_change(self, plugin_path: Path) -> None:
        """Handle plugin file changes for hot-reloading.
        
        Args:
            plugin_path: Path to the changed plugin file
        """
        plugin_name = plugin_path.stem
        if plugin_name in self.plugins:
            logger.info(f"Hot-reloading plugin: {plugin_name}")
            await self.reload_plugin(plugin_name)
            
    async def shutdown(self) -> None:
        """Shutdown the plugin manager and cleanup resources."""
        await self.stop_all_plugins()
        
        if self._watcher:
            await asyncio.get_event_loop().run_in_executor(
                self._executor,
                self._watcher.stop
            )
            
        self._executor.shutdown() 