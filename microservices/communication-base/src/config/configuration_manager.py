"""
Config Manager

Central configuration management component that handles loading,
caching, and accessing configuration with proper inheritance.

Basic usage:
    manager = ConfigManager()
    manager.initialize("path/to/config/dir")
    
    # Get bot config with inheritance
    sales_config = manager.get_bot_config("sales")
    
    # Get specific value with dot notation
    value = manager.get_value("sales", "rag.vector_store.similarity")
"""

import os
import logging
import time
from typing import Dict, Any, Optional

from src.config.config_loader import ConfigLoader, ConfigLoadError
from src.config.config_inheritance import ConfigInheritance

class ConfigManager:
    """
    Central manager for configuration that handles loading, inheritance,
    and access to configuration values.
    
    Provides caching for efficiency and convenience methods for accessing
    configuration values.
    """
    
    # Singleton instance
    _instance = None
    
    def __new__(cls):
        """Ensure ConfigManager is a singleton."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the ConfigManager."""
        if self._initialized:
            return
            
        self.logger = logging.getLogger(__name__)
        self.config_loader = ConfigLoader()
        self.config_inheritance = ConfigInheritance()
        
        # Configuration storage
        self.base_config = {}
        self.bot_configs = {}
        self.merged_configs = {}
        self.session_configs = {}
        
        # Paths
        self.config_dir = None
        self.base_config_path = None
        self.bot_config_dir = None
        
        self._initialized = True
    
    def initialize(self, config_dir: str, base_config_filename: str = "base.yaml", 
                   bot_config_subdir: str = "bots") -> bool:
        """
        Initialize the configuration system by loading configs.
        
        Args:
            config_dir: Base directory containing all configurations
            base_config_filename: Filename for the base configuration
            bot_config_subdir: Subdirectory containing bot-specific configs
            
        Returns:
            True if initialization was successful, False otherwise
        """
        self.config_dir = config_dir
        self.base_config_path = os.path.join(config_dir, base_config_filename)
        self.bot_config_dir = os.path.join(config_dir, bot_config_subdir)
        
        try:
            # Load base config
            self.base_config = self.config_loader.load_config(self.base_config_path)
            self.logger.info(f"Loaded base config from {self.base_config_path}")
            
            # Load bot configs
            if os.path.exists(self.bot_config_dir):
                self.bot_configs = self.config_loader.load_config_directory(self.bot_config_dir)
                self.logger.info(f"Loaded {len(self.bot_configs)} bot configs from {self.bot_config_dir}")
            else:
                self.logger.warning(f"Bot config directory not found: {self.bot_config_dir}")
                
            # Clear caches
            self.merged_configs = {}
            self.session_configs = {}
                
            return True
        except ConfigLoadError as e:
            self.logger.error(f"Failed to initialize configuration: {e}")
            return False
    
    def reload(self) -> bool:
        """
        Reload all configurations from disk.
        
        Returns:
            True if reload was successful, False otherwise
        """
        if not self.config_dir:
            self.logger.error("Cannot reload: ConfigManager not initialized")
            return False
            
        return self.initialize(self.config_dir)
    
    def get_base_config(self) -> Dict[str, Any]:
        """
        Get the base configuration.
        
        Returns:
            The base configuration dictionary
        """
        return self.base_config.copy()
    
    def get_bot_config(self, bot_type: str) -> Dict[str, Any]:
        """
        Get the configuration for a specific bot type with proper inheritance.
        
        Args:
            bot_type: The type of bot (e.g., 'consultancy', 'sales', 'support')
            
        Returns:
            The merged configuration dictionary for the bot
        """
        # Return cached merged config if available
        if bot_type in self.merged_configs:
            return self.merged_configs[bot_type]
            
        # Check if bot config exists
        if bot_type not in self.bot_configs:
            self.logger.warning(f"No configuration found for bot type: {bot_type}")
            return self.base_config.copy()
            
        # Merge base config with bot-specific config
        merged = self.config_inheritance.merge_configs(
            self.base_config,
            self.bot_configs[bot_type]
        )
        
        # Cache the merged config
        self.merged_configs[bot_type] = merged
        
        return merged
    
    def get_session_config(self, session_id: str, bot_type: str, 
                          session_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get configuration for a specific session with bot-specific and session-specific overrides.
        
        Args:
            session_id: The unique session identifier
            bot_type: The type of bot for this session
            session_overrides: Session-specific configuration overrides
            
        Returns:
            The merged configuration dictionary for the session
        """
        # Get bot config first (already includes base config)
        bot_config = self.get_bot_config(bot_type)
        
        # If no session overrides, just return the bot config
        if not session_overrides:
            return bot_config
            
        # Generate cache key
        cache_key = f"{session_id}:{bot_type}"
        
        # Check for cached config with these overrides
        if cache_key in self.session_configs:
            cached_config, cached_overrides = self.session_configs[cache_key]
            if cached_overrides == session_overrides:
                return cached_config
        
        # Merge bot config with session-specific overrides
        merged = self.config_inheritance.merge_configs(bot_config, session_overrides)
        
        # Cache the merged config with its overrides
        self.session_configs[cache_key] = (merged, session_overrides)
        
        return merged
    
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
        if session_id and session_overrides:
            config = self.get_session_config(session_id, bot_type, session_overrides)
        else:
            config = self.get_bot_config(bot_type)
            
        return self.config_inheritance.get_value(config, path, default)
    
    def update_session_config(self, session_id: str, bot_type: str, 
                             updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update session-specific configuration overrides.
        
        Args:
            session_id: The unique session identifier
            bot_type: The type of bot for this session
            updates: Configuration updates to apply
            
        Returns:
            The updated merged configuration for the session
        """
        cache_key = f"{session_id}:{bot_type}"
        
        # Get existing overrides or start with empty dict
        if cache_key in self.session_configs:
            _, existing_overrides = self.session_configs[cache_key]
            session_overrides = existing_overrides.copy()
        else:
            session_overrides = {}
            
        # Update with new values
        for path, value in updates.items():
            if '.' in path:
                # Handle nested paths
                parts = path.split('.')
                current = session_overrides
                
                # Navigate to the right level, creating dicts as needed
                for part in parts[:-1]:
                    if part not in current or not isinstance(current[part], dict):
                        current[part] = {}
                    current = current[part]
                    
                # Set the value at the final level
                current[parts[-1]] = value
            else:
                # Direct path
                session_overrides[path] = value
                
        # Return updated config
        return self.get_session_config(session_id, bot_type, session_overrides)
        
    def clear_session_cache(self, session_id: Optional[str] = None) -> None:
        """
        Clear cached session configurations.
        
        Args:
            session_id: If provided, only clear cache for this session
        """
        if session_id:
            # Clear specific session
            keys_to_remove = [key for key in self.session_configs if key.startswith(f"{session_id}:")]
            for key in keys_to_remove:
                del self.session_configs[key]
            self.logger.debug(f"Cleared cache for session {session_id}")
        else:
            # Clear all sessions
            self.session_configs = {}
            self.logger.debug("Cleared all session caches")
            
    def clear_all_caches(self) -> None:
        """Clear all configuration caches."""
        self.merged_configs = {}
        self.session_configs = {}
        self.logger.debug("Cleared all configuration caches") 