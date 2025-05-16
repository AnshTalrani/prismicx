"""
Configuration loader for the analysis-base microservice.

This module provides functionality to load and manage configuration values
from various sources, including configuration files and environment variables.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


class ConfigLoader:
    """
    Configuration loader for the analysis-base microservice.
    
    This class loads and manages configuration values from various sources,
    including configuration files and environment variables.
    
    Attributes:
        logger (logging.Logger): Logger for the config loader
        config_paths (List[str]): Paths to search for configuration files
        env_prefix (str): Prefix for environment variables to consider
        config (Dict[str, Any]): Loaded configuration values
    """
    
    def __init__(
        self,
        config_paths: Optional[List[str]] = None,
        env_prefix: str = "ANALYSIS_"
    ):
        """
        Initialize the configuration loader.
        
        Args:
            config_paths: Paths to search for configuration files
            env_prefix: Prefix for environment variables to consider
        """
        self.logger = logging.getLogger("config_loader")
        
        # Set default configuration paths
        self.config_paths = config_paths or ["config", "/etc/analysis-base", "~/.analysis-base"]
        
        # Set environment variable prefix
        self.env_prefix = env_prefix
        
        # Initialize configuration
        self.config: Dict[str, Any] = {}
        
        # Load configurations
        self._load_config()
    
    def _load_config(self) -> None:
        """
        Load configuration from various sources.
        
        This method loads configuration values from files and environment variables,
        then merges them together.
        """
        # Load from files
        file_config = self._load_from_files()
        
        # Load from environment variables
        env_config = self._load_from_env()
        
        # Merge configurations (environment variables override files)
        self.config = self._merge_configs(file_config, env_config)
        
        self.logger.info(f"Loaded configuration with {len(self.config)} keys")
    
    def _load_from_files(self) -> Dict[str, Any]:
        """
        Load configuration from files.
        
        Returns:
            Dict[str, Any]: Configuration loaded from files
        """
        config: Dict[str, Any] = {}
        
        # Try each configuration path
        for path in self.config_paths:
            expanded_path = os.path.expanduser(path)
            
            # Skip if path doesn't exist
            if not os.path.exists(expanded_path):
                continue
            
            # Check for YAML file
            yaml_path = os.path.join(expanded_path, "config.yaml")
            yml_path = os.path.join(expanded_path, "config.yml")
            
            # Check for JSON file
            json_path = os.path.join(expanded_path, "config.json")
            
            # Try to load YAML file
            if os.path.isfile(yaml_path):
                try:
                    with open(yaml_path, "r") as f:
                        yaml_config = yaml.safe_load(f)
                        if yaml_config and isinstance(yaml_config, dict):
                            config = self._merge_configs(config, yaml_config)
                            self.logger.info(f"Loaded configuration from {yaml_path}")
                except (yaml.YAMLError, IOError) as e:
                    self.logger.warning(f"Error loading configuration from {yaml_path}: {str(e)}")
            
            # Try to load alternative YAML file
            elif os.path.isfile(yml_path):
                try:
                    with open(yml_path, "r") as f:
                        yaml_config = yaml.safe_load(f)
                        if yaml_config and isinstance(yaml_config, dict):
                            config = self._merge_configs(config, yaml_config)
                            self.logger.info(f"Loaded configuration from {yml_path}")
                except (yaml.YAMLError, IOError) as e:
                    self.logger.warning(f"Error loading configuration from {yml_path}: {str(e)}")
            
            # Try to load JSON file
            elif os.path.isfile(json_path):
                try:
                    with open(json_path, "r") as f:
                        json_config = json.load(f)
                        if isinstance(json_config, dict):
                            config = self._merge_configs(config, json_config)
                            self.logger.info(f"Loaded configuration from {json_path}")
                except (json.JSONDecodeError, IOError) as e:
                    self.logger.warning(f"Error loading configuration from {json_path}: {str(e)}")
        
        return config
    
    def _load_from_env(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Returns:
            Dict[str, Any]: Configuration loaded from environment variables
        """
        config: Dict[str, Any] = {}
        
        # Process all environment variables
        for key, value in os.environ.items():
            # Check if the key has the correct prefix
            if not key.startswith(self.env_prefix):
                continue
            
            # Remove the prefix
            config_key = key[len(self.env_prefix):].lower()
            
            # Convert nested keys (e.g., DATABASE_URL -> database.url)
            if "_" in config_key:
                parts = config_key.split("_")
                current = config
                
                # Navigate through nested levels
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    elif not isinstance(current[part], dict):
                        # If the current part exists but is not a dict, make it a dict
                        # This can happen if an environment variable like DATABASE_HOST
                        # comes before DATABASE_HOST_PORT
                        current[part] = {"value": current[part]}
                    
                    current = current[part]
                
                # Set the value at the deepest level
                current[parts[-1]] = self._parse_env_value(value)
            else:
                # Simple key
                config[config_key] = self._parse_env_value(value)
        
        return config
    
    def _parse_env_value(self, value: str) -> Any:
        """
        Parse an environment variable value to the appropriate type.
        
        Args:
            value: Value to parse
            
        Returns:
            Any: Parsed value
        """
        # Check for boolean values
        if value.lower() in ("true", "yes", "1"):
            return True
        elif value.lower() in ("false", "no", "0"):
            return False
        
        # Check for null value
        if value.lower() in ("null", "none"):
            return None
        
        # Check for integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Check for float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Check for JSON
        if value.startswith("{") or value.startswith("["):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # Default to string
        return value
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries.
        
        Args:
            base: Base configuration
            override: Configuration to override with
            
        Returns:
            Dict[str, Any]: Merged configuration
        """
        result = base.copy()
        
        for key, override_value in override.items():
            # If both values are dictionaries, merge them recursively
            if key in result and isinstance(result[key], dict) and isinstance(override_value, dict):
                result[key] = self._merge_configs(result[key], override_value)
            else:
                # Otherwise, override the value
                result[key] = override_value
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (can use dot notation for nested keys)
            default: Default value to return if the key is not found
            
        Returns:
            Any: Configuration value, or default if not found
        """
        # Split the key by dots
        parts = key.split(".")
        current = self.config
        
        # Navigate through nested levels
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (can use dot notation for nested keys)
            value: Value to set
        """
        # Split the key by dots
        parts = key.split(".")
        current = self.config
        
        # Navigate through nested levels
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                current[part] = {}
            
            current = current[part]
        
        # Set the value at the deepest level
        current[parts[-1]] = value


# Create a singleton instance
config_loader = ConfigLoader()

def get_value(key: str, default: Any = None) -> Any:
    """
    Get a configuration value.
    
    Args:
        key: Configuration key (can use dot notation for nested keys)
        default: Default value to return if the key is not found
        
    Returns:
        Any: Configuration value, or default if not found
    """
    return config_loader.get(key, default)

def set_value(key: str, value: Any) -> None:
    """
    Set a configuration value.
    
    Args:
        key: Configuration key (can use dot notation for nested keys)
        value: Value to set
    """
    config_loader.set(key, value)