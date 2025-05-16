"""
Configuration settings for the plugin system.

This module contains configuration settings for the plugin system, including
plugin directories, scan intervals, and other parameters.
"""

from pathlib import Path
from typing import List, Optional
from pydantic import BaseSettings, DirectoryPath

class PluginConfig(BaseSettings):
    """Plugin system configuration settings."""
    
    # Base directory for plugin files
    PLUGIN_DIR: DirectoryPath = Path(__file__).parent.parent / "plugins"
    
    # Additional plugin directories to scan
    ADDITIONAL_PLUGIN_DIRS: List[DirectoryPath] = []
    
    # Hot-reloading settings
    ENABLE_HOT_RELOAD: bool = True
    HOT_RELOAD_INTERVAL: float = 1.0  # seconds
    
    # Plugin validation settings
    STRICT_DEPENDENCY_CHECK: bool = True
    ALLOW_BETA_PLUGINS: bool = False
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    class Config:
        """Pydantic configuration."""
        env_prefix = "PLUGIN_"
        case_sensitive = True

# Create a global instance of the config
plugin_config = PluginConfig() 