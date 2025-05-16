"""
Plugin watcher module for hot-reloading functionality.

This module implements a file system watcher that monitors plugin directories
for changes and triggers reloading of plugins when necessary.
"""

import logging
from pathlib import Path
from typing import Callable, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from .config import plugin_config

logger = logging.getLogger(__name__)

class PluginEventHandler(FileSystemEventHandler):
    """Event handler for plugin file changes."""
    
    def __init__(self, callback: Callable[[Path], None]):
        """Initialize the event handler.
        
        Args:
            callback: Function to call when a plugin file changes
        """
        self.callback = callback
        self._processing: Set[Path] = set()
        
    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events.
        
        Args:
            event: The file system event that occurred
        """
        if not event.is_directory and event.src_path.endswith('.py'):
            path = Path(event.src_path)
            if path not in self._processing:
                self._processing.add(path)
                try:
                    self.callback(path)
                finally:
                    self._processing.remove(path)

class PluginWatcher:
    """Watches plugin directories for changes and triggers reloading."""
    
    def __init__(self, reload_callback: Callable[[Path], None]):
        """Initialize the plugin watcher.
        
        Args:
            reload_callback: Function to call when a plugin needs to be reloaded
        """
        self.observer = Observer()
        self.handler = PluginEventHandler(reload_callback)
        
    def start(self) -> None:
        """Start watching plugin directories."""
        if not plugin_config.ENABLE_HOT_RELOAD:
            logger.info("Hot-reloading is disabled")
            return
            
        # Watch main plugin directory
        self.observer.schedule(self.handler, str(plugin_config.PLUGIN_DIR), recursive=True)
        
        # Watch additional directories
        for plugin_dir in plugin_config.ADDITIONAL_PLUGIN_DIRS:
            self.observer.schedule(self.handler, str(plugin_dir), recursive=True)
            
        self.observer.start()
        logger.info("Plugin watcher started")
        
    def stop(self) -> None:
        """Stop watching plugin directories."""
        self.observer.stop()
        self.observer.join()
        logger.info("Plugin watcher stopped") 