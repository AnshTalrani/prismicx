"""
Config Loader

Handles loading configuration files from the filesystem.
Supports YAML and JSON formats with appropriate error handling.

Basic usage:
    loader = ConfigLoader()
    config = loader.load_config("path/to/config.yaml")
"""

import os
import json
import logging
from typing import Dict, Any, Optional

# Only import yaml if it's available
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

class ConfigLoadError(Exception):
    """Exception raised when a configuration file cannot be loaded."""
    pass

class ConfigLoader:
    """
    Loads configuration from files with support for YAML and JSON formats.
    Provides proper error handling and logging.
    """
    
    def __init__(self):
        """Initialize the ConfigLoader."""
        self.logger = logging.getLogger(__name__)
        if not YAML_AVAILABLE:
            self.logger.warning("PyYAML not installed. YAML config files will not be supported.")
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load a configuration file from the given path.
        
        Args:
            config_path: Path to the configuration file (YAML or JSON)
            
        Returns:
            Dictionary containing the loaded configuration
            
        Raises:
            ConfigLoadError: If the file cannot be loaded
        """
        if not os.path.exists(config_path):
            raise ConfigLoadError(f"Config file not found: {config_path}")
            
        file_ext = os.path.splitext(config_path)[1].lower()
        
        try:
            with open(config_path, 'r') as f:
                if file_ext in ('.yaml', '.yml'):
                    if not YAML_AVAILABLE:
                        raise ConfigLoadError("PyYAML not installed. Cannot load YAML config.")
                    return yaml.safe_load(f) or {}
                elif file_ext == '.json':
                    return json.load(f) or {}
                else:
                    raise ConfigLoadError(f"Unsupported config format: {file_ext}")
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigLoadError(f"Failed to parse config file {config_path}: {e}")
        except Exception as e:
            raise ConfigLoadError(f"Error loading config file {config_path}: {e}")
            
    def load_config_directory(self, directory_path: str, recursive: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Load all configuration files from a directory.
        
        Args:
            directory_path: Path to the directory containing config files
            recursive: Whether to recursively search subdirectories
            
        Returns:
            Dictionary mapping filenames (without extension) to their configurations
            
        Raises:
            ConfigLoadError: If the directory cannot be accessed
        """
        if not os.path.isdir(directory_path):
            raise ConfigLoadError(f"Config directory not found: {directory_path}")
            
        configs = {}
        
        try:
            for item in os.listdir(directory_path):
                full_path = os.path.join(directory_path, item)
                
                if os.path.isfile(full_path):
                    file_ext = os.path.splitext(item)[1].lower()
                    if file_ext in ('.yaml', '.yml', '.json'):
                        try:
                            filename = os.path.splitext(item)[0]
                            configs[filename] = self.load_config(full_path)
                        except ConfigLoadError as e:
                            self.logger.warning(f"Skipping file {full_path}: {e}")
                elif recursive and os.path.isdir(full_path):
                    # Recursively load configs from subdirectories
                    sub_configs = self.load_config_directory(full_path, recursive=True)
                    # Prefix subdirectory configs with directory name
                    dir_name = os.path.basename(full_path)
                    for sub_name, sub_config in sub_configs.items():
                        configs[f"{dir_name}.{sub_name}"] = sub_config
        except Exception as e:
            raise ConfigLoadError(f"Error accessing directory {directory_path}: {e}")
            
        return configs 