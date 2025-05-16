"""
Plugin registry with hot-reloading and dependency management.
"""

import os
import sys
import importlib
import importlib.util
import logging
from typing import Dict, Type, Optional, List
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .base import PluginBase, PluginMetadata

logger = logging.getLogger(__name__)

class PluginFileHandler(FileSystemEventHandler):
    """Handler for plugin file changes."""
    
    def __init__(self, registry):
        """Initialize with registry reference."""
        self.registry = registry
        
    def on_modified(self, event):
        """Handle file modification events."""
        if event.src_path.endswith(".py"):
            logger.info(f"Detected changes in {event.src_path}")
            self.registry.reload_plugin(event.src_path)

class ModuleRegistry:
    """Registry for managing plugins with hot-reloading."""
    
    _instance = None
    _plugins: Dict[str, Type[PluginBase]] = {}
    _file_paths: Dict[str, str] = {}
    _last_reload: Dict[str, float] = {}
    _observer: Optional[Observer] = None
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super(ModuleRegistry, cls).__new__(cls)
        return cls._instance
        
    @classmethod
    def load_plugins(cls, plugin_dir: str):
        """
        Load plugins from directory.
        
        Args:
            plugin_dir: Directory containing plugins
        """
        cls._setup_hot_reload(plugin_dir)
        
        for root, _, files in os.walk(plugin_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    file_path = os.path.join(root, file)
                    cls._load_plugin_from_file(file_path)
                    
    @classmethod
    def _setup_hot_reload(cls, plugin_dir: str):
        """Setup hot-reloading for plugin directory."""
        if cls._observer:
            cls._observer.stop()
            
        cls._observer = Observer()
        handler = PluginFileHandler(cls)
        cls._observer.schedule(handler, plugin_dir, recursive=True)
        cls._observer.start()
        
    @classmethod
    def _load_plugin_from_file(cls, file_path: str) -> bool:
        """
        Load plugin from file.
        
        Args:
            file_path: Path to plugin file
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                return False
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find plugin class
            for item in dir(module):
                obj = getattr(module, item)
                if (isinstance(obj, type) and 
                    issubclass(obj, PluginBase) and 
                    obj != PluginBase):
                    plugin = obj()
                    metadata = plugin.get_metadata()
                    cls._register_plugin(metadata.name, obj, file_path)
                    return True
                    
        except Exception as e:
            logger.error(f"Error loading plugin from {file_path}: {str(e)}")
            
        return False
        
    @classmethod
    def _register_plugin(cls, name: str, plugin_class: Type[PluginBase], file_path: str):
        """Register plugin with dependency validation."""
        try:
            # Create instance to validate metadata
            plugin = plugin_class()
            metadata = plugin.get_metadata()
            
            # Check dependencies
            cls._validate_dependencies(metadata)
            
            # Register plugin
            cls._plugins[name] = plugin_class
            cls._file_paths[name] = file_path
            cls._last_reload[name] = time.time()
            
            logger.info(f"Registered plugin {name} v{metadata.version}")
            
        except Exception as e:
            logger.error(f"Failed to register plugin {name}: {str(e)}")
            
    @classmethod
    def _validate_dependencies(cls, metadata: PluginMetadata):
        """Validate plugin dependencies."""
        for dep_name, dep_version in metadata.dependencies.items():
            if dep_name not in cls._plugins:
                raise ValueError(f"Missing dependency: {dep_name}")
                
            dep_plugin = cls._plugins[dep_name]()
            dep_metadata = dep_plugin.get_metadata()
            
            if not cls._version_satisfies(dep_metadata.version, dep_version):
                raise ValueError(
                    f"Version mismatch for {dep_name}: "
                    f"required {dep_version}, found {dep_metadata.version}"
                )
                
    @staticmethod
    def _version_satisfies(version: str, requirement: str) -> bool:
        """Check if version satisfies requirement."""
        try:
            return semver.VersionInfo.parse(version).satisfies(requirement)
        except ValueError:
            return False
            
    @classmethod
    def reload_plugin(cls, file_path: str):
        """Reload plugin from file."""
        # Find plugin by file path
        for name, path in cls._file_paths.items():
            if path == file_path:
                # Prevent rapid reloads
                if time.time() - cls._last_reload.get(name, 0) < 1:
                    return
                    
                logger.info(f"Reloading plugin {name}")
                if cls._load_plugin_from_file(file_path):
                    logger.info(f"Successfully reloaded plugin {name}")
                break
                
    @classmethod
    def get_plugin(cls, name: str) -> Optional[Type[PluginBase]]:
        """Get plugin by name."""
        return cls._plugins.get(name)
        
    @classmethod
    def list_plugins(cls) -> List[Dict[str, str]]:
        """List all registered plugins with metadata."""
        plugins = []
        for name, plugin_class in cls._plugins.items():
            try:
                plugin = plugin_class()
                metadata = plugin.get_metadata()
                plugins.append({
                    "name": name,
                    "version": metadata.version,
                    "description": metadata.description,
                    "author": metadata.author
                })
            except Exception as e:
                logger.error(f"Error getting metadata for {name}: {str(e)}")
                
        return plugins 