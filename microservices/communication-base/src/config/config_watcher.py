"""
Config Watcher

Monitors configuration files for changes and triggers reloading when needed.
Uses a simple polling approach for maximum compatibility.

Basic usage:
    from src.config.config_manager import ConfigManager
    
    def on_config_change():
        # Do something when configs change
        print("Config changed!")
    
    watcher = ConfigWatcher(config_dir="path/to/configs", 
                          callback=on_config_change, 
                          interval=5.0)
    watcher.start()
    
    # Later when shutting down
    watcher.stop()
"""

import os
import time
import logging
import threading
from typing import Callable, Dict, List, Set, Optional

class ConfigWatcher:
    """
    Monitors configuration files for changes and triggers reloading.
    Uses a simple polling approach that checks file modification times.
    """
    
    def __init__(self, config_dir: str, 
                callback: Callable[[], None],
                interval: float = 5.0,
                file_patterns: Optional[List[str]] = None):
        """
        Initialize the ConfigWatcher.
        
        Args:
            config_dir: Directory containing configuration files to watch
            callback: Function to call when a configuration change is detected
            interval: Check interval in seconds
            file_patterns: List of file patterns to watch (e.g., ["*.yaml", "*.json"]),
                          or None to watch all files
        """
        self.logger = logging.getLogger(__name__)
        self.config_dir = config_dir
        self.callback = callback
        self.interval = interval
        self.file_patterns = file_patterns or [".yaml", ".yml", ".json"]
        
        self.running = False
        self.thread = None
        self.last_check_time = 0
        self.file_mtimes = {}  # Maps file paths to last modification times
        
    def _matches_pattern(self, filename: str) -> bool:
        """Check if a filename matches any of the watched patterns."""
        return any(filename.endswith(pattern) for pattern in self.file_patterns)
        
    def _scan_directory(self, dir_path: str) -> Dict[str, float]:
        """
        Scan a directory for config files and their modification times.
        Includes subdirectories recursively.
        
        Returns:
            Dictionary mapping file paths to modification times
        """
        result = {}
        
        for root, _, files in os.walk(dir_path):
            for file in files:
                if self._matches_pattern(file):
                    full_path = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(full_path)
                        result[full_path] = mtime
                    except OSError as e:
                        self.logger.warning(f"Error accessing file {full_path}: {e}")
                        
        return result
    
    def _check_for_changes(self) -> bool:
        """
        Check if any config files have changed since the last check.
        
        Returns:
            True if changes were detected, False otherwise
        """
        try:
            # Get current state of files
            current_mtimes = self._scan_directory(self.config_dir)
            
            # If this is the first check, just record the current state
            if not self.file_mtimes:
                self.file_mtimes = current_mtimes
                return False
                
            # Check for new or modified files
            for file_path, mtime in current_mtimes.items():
                if file_path not in self.file_mtimes or mtime > self.file_mtimes[file_path]:
                    self.logger.info(f"Detected change in config file: {file_path}")
                    self.file_mtimes = current_mtimes
                    return True
            
            # Check for deleted files
            for file_path in list(self.file_mtimes.keys()):
                if file_path not in current_mtimes:
                    self.logger.info(f"Config file deleted: {file_path}")
                    self.file_mtimes = current_mtimes
                    return True
                    
            return False
        except Exception as e:
            self.logger.error(f"Error checking for config changes: {e}")
            return False
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop that runs in a separate thread."""
        self.logger.info(f"Config watcher started for directory: {self.config_dir}")
        
        while self.running:
            try:
                # Check for changes
                if self._check_for_changes():
                    try:
                        self.callback()
                    except Exception as e:
                        self.logger.error(f"Error in config change callback: {e}")
                
                # Sleep for the specified interval
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f"Error in config watcher loop: {e}")
                # Don't crash the thread, just continue after a short delay
                time.sleep(1)
    
    def start(self) -> None:
        """Start the config watcher in a background thread."""
        if self.running:
            self.logger.warning("Config watcher is already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        
    def stop(self) -> None:
        """Stop the config watcher thread."""
        if not self.running:
            return
            
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            
        self.logger.info("Config watcher stopped")
            
    def is_running(self) -> bool:
        """Check if the config watcher is currently running."""
        return self.running and self.thread and self.thread.is_alive() 