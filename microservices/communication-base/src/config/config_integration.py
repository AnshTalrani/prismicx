"""
Config Integration

Integrates the configuration system with the rest of the application.
Sets up the config manager, watcher, and provides interfaces for other components.

Basic usage:
    from src.config.config_integration import ConfigIntegration
    
    # Get singleton instance
    config_integration = ConfigIntegration()
    
    # Initialize with config directory
    config_integration.initialize("/path/to/config")
    
    # Get config for a specific bot
    sales_config = config_integration.get_config("sales")
    
    # Get a specific config value
    temperature = config_integration.get_value("sales", "models.llm.temperature", default=0.7)
"""

import os
import logging
from typing import Dict, Any, Optional, List

from src.config.config_loader import ConfigLoader
from src.config.config_inheritance import ConfigInheritance
from src.config.config_manager import ConfigManager
from src.config.config_watcher import ConfigWatcher

class ConfigIntegration:
    """
    Integrates the configuration system with the rest of the application.
    
    Acts as a facade for the configuration system, providing simplified access
    to configurations while handling all the complexity of loading, inheritance,
    and hot-reloading behind the scenes.
    """
    
    # Singleton instance
    _instance = None
    
    def __new__(cls):
        """Ensure ConfigIntegration is a singleton."""
        if cls._instance is None:
            cls._instance = super(ConfigIntegration, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the ConfigIntegration."""
        if self._initialized:
            return
            
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
        self.config_watcher = None
        self._initialized = True
    
    def initialize(self, config_dir: str, 
                  base_config_name: str = "base.yaml",
                  bot_config_dir: str = "bots", 
                  enable_hot_reload: bool = True,
                  hot_reload_interval: float = 5.0) -> bool:
        """
        Initialize the configuration system.
        
        Args:
            config_dir: Directory containing configuration files
            base_config_name: Name of the base config file
            bot_config_dir: Subdirectory containing bot-specific configs
            enable_hot_reload: Whether to enable hot reloading of configs
            hot_reload_interval: Interval in seconds for checking config changes
            
        Returns:
            True if initialization was successful, False otherwise
        """
        # Initialize the config manager
        success = self.config_manager.initialize(
            config_dir=config_dir,
            base_config_filename=base_config_name,
            bot_config_subdir=bot_config_dir
        )
        
        if not success:
            self.logger.error("Failed to initialize config manager")
            return False
            
        # Set up hot reloading if enabled
        if enable_hot_reload:
            self._setup_hot_reload(config_dir, hot_reload_interval)
            
        self.logger.info("Config integration initialized successfully")
        return True
    
    def _setup_hot_reload(self, config_dir: str, interval: float) -> None:
        """
        Set up hot reloading for configuration files.
        
        Args:
            config_dir: Directory containing configuration files
            interval: Check interval in seconds
        """
        # If a watcher is already running, stop it
        if self.config_watcher and self.config_watcher.is_running():
            self.config_watcher.stop()
            
        # Create a callback that reloads configs when changes are detected
        def on_config_change():
            self.logger.info("Configuration changes detected, reloading...")
            self.config_manager.reload()
            # You could emit an event here to notify other components
            
        # Create and start the config watcher
        self.config_watcher = ConfigWatcher(
            config_dir=config_dir,
            callback=on_config_change,
            interval=interval
        )
        self.config_watcher.start()
        
        self.logger.info(f"Config hot-reloading enabled with interval {interval}s")
    
    def shutdown(self) -> None:
        """Shut down the configuration system cleanly."""
        if self.config_watcher:
            self.config_watcher.stop()
        self.logger.info("Config integration shut down")
    
    def get_base_config(self) -> Dict[str, Any]:
        """
        Get the base configuration.
        
        Returns:
            The base configuration dictionary
        """
        return self.config_manager.get_base_config()
    
    def get_config(self, bot_type: str) -> Dict[str, Any]:
        """
        Get the configuration for a specific bot type with proper inheritance.
        
        Args:
            bot_type: The type of bot (e.g., 'consultancy', 'sales', 'support')
            
        Returns:
            The merged configuration dictionary for the bot
        """
        return self.config_manager.get_bot_config(bot_type)
    
    def get_session_config(self, session_id: str, bot_type: str,
                          session_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get configuration for a specific session with all appropriate overrides.
        
        Args:
            session_id: The unique session identifier
            bot_type: The type of bot for this session
            session_overrides: Session-specific configuration overrides
            
        Returns:
            The merged configuration dictionary for the session
        """
        return self.config_manager.get_session_config(session_id, bot_type, session_overrides)
    
    def get_value(self, bot_type: str, path: str, default: Any = None,
                 session_id: Optional[str] = None,
                 session_overrides: Optional[Dict[str, Any]] = None) -> Any:
        """
        Get a specific configuration value using dot notation.
        
        Args:
            bot_type: The type of bot
            path: Dot-separated path to the value
            default: Default value to return if path does not exist
            session_id: Optional session ID for session-specific config
            session_overrides: Optional session-specific overrides
            
        Returns:
            The value at the specified path or the default if not found
        """
        return self.config_manager.get_value(
            bot_type=bot_type,
            path=path,
            default=default,
            session_id=session_id,
            session_overrides=session_overrides
        )
    
    def update_session_config(self, session_id: str, bot_type: str,
                             updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update session-specific configuration overrides.
        
        Args:
            session_id: The unique session identifier
            bot_type: The type of bot for this session
            updates: Configuration updates to apply (can use dot notation keys)
            
        Returns:
            The updated merged configuration for the session
        """
        return self.config_manager.update_session_config(session_id, bot_type, updates)
    
    def reload_configs(self) -> bool:
        """
        Manually reload all configurations from disk.
        
        Returns:
            True if reload was successful, False otherwise
        """
        return self.config_manager.reload()
    
    def clear_session_cache(self, session_id: Optional[str] = None) -> None:
        """
        Clear cached session configurations.
        
        Args:
            session_id: If provided, only clear cache for this session
        """
        self.config_manager.clear_session_cache(session_id)
    
    def get_bot_types(self) -> List[str]:
        """
        Get a list of all available bot types.
        
        Returns:
            List of bot type strings
        """
        return list(self.config_manager.bot_configs.keys())
    
    def get_config_section(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get a configuration section using dot notation.
        
        Args:
            path: Dot-separated path to the section
            
        Returns:
            The configuration section or None if not found
        """
        # Parse the path to determine bot type and section path
        parts = path.split(".")
        
        # Check if the path starts with a bot type
        bot_types = self.get_bot_types()
        if parts[0] in bot_types:
            bot_type = parts[0]
            section_path = ".".join(parts[1:])
            config = self.get_config(bot_type)
        else:
            # Try to get from all bot types
            for bot_type in bot_types:
                config = self.get_config(bot_type)
                result = self._get_nested_value(config, path)
                if isinstance(result, dict):
                    return result
            return None
            
        # Get the section from the config
        return self._get_nested_value(config, section_path)
    
    def get_config_value(self, path: str, default: Any = None) -> Any:
        """
        Get a specific configuration value using dot notation from any bot.
        
        Args:
            path: Dot-separated path to the value
            default: Default value to return if path does not exist
            
        Returns:
            The value at the specified path or the default if not found
        """
        # Parse the path to determine bot type and value path
        parts = path.split(".")
        
        # Check if the path starts with a bot type
        bot_types = self.get_bot_types()
        if parts[0] in bot_types:
            bot_type = parts[0]
            value_path = ".".join(parts[1:])
            return self.get_value(bot_type, value_path, default=default)
        
        # Try to get from all bot types
        for bot_type in bot_types:
            value = self.get_value(bot_type, path, default=None)
            if value is not None:
                return value
        
        return default
    
    def _get_nested_value(self, config: Dict[str, Any], path: str) -> Any:
        """
        Get a nested value from a dictionary using dot notation.
        
        Args:
            config: Configuration dictionary
            path: Dot-separated path to the value
            
        Returns:
            The value at the path or None if not found
        """
        if not path:
            return config
            
        parts = path.split(".")
        current = config
        
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
            
        return current


# Create the singleton instance
config_integration = ConfigIntegration() 