"""
Bot Configuration Manager for the Communication Base Microservice.

This module provides a centralized mechanism for loading, validating, and accessing
bot-specific configurations with basic inheritance capabilities.
"""

import json
import os
from typing import Dict, Any, Optional, List, Tuple
import logging


class ConfigManager:
    """
    Simple configuration manager that loads and provides access to bot configurations.
    
    This class handles loading JSON configuration files from a directory,
    optionally merging them with a base configuration, and providing centralized
    access to the loaded configurations.
    """
    
    def __init__(self):
        """Initialize a new ConfigManager instance."""
        self.configs = {}
        self.base_config = {}
        self.logger = logging.getLogger(__name__)
        # Basic validation schemas for each bot type
        self.validation_schemas = self._create_validation_schemas()
    
    def _create_validation_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Create basic validation schemas for bot configurations.
        
        Returns:
            Dict[str, Dict[str, Any]]: Validation schemas for each bot type
        """
        base_schema = {
            "model": {
                "required": True,
                "fields": ["name", "temperature", "max_tokens"]
            },
            "adapter": {
                "required": True,
                "fields": ["enabled"]
            },
            "response": {
                "required": True,
                "fields": ["enhance"]
            }
        }
        
        consultancy_schema = {
            "domains": {
                "required": True
            },
            "frameworks": {
                "required": True,
                "fields": ["enabled"]
            }
        }
        
        sales_schema = {
            "campaign": {
                "required": True,
                "fields": ["name", "stage"]
            },
            "objection_handling": {
                "required": True,
                "fields": ["enabled"]
            }
        }
        
        support_schema = {
            "issue_types": {
                "required": True
            },
            "escalation": {
                "required": True,
                "fields": ["enabled"]
            }
        }
        
        return {
            "base": base_schema,
            "consultancy": consultancy_schema,
            "sales": sales_schema,
            "support": support_schema
        }
    
    def load_configs(self, config_dir: str, base_config_path: Optional[str] = None) -> bool:
        """
        Load all config files from directory and optionally a base config.
        
        Args:
            config_dir: Directory containing bot-specific config files (*.json)
            base_config_path: Optional path to a base config file to merge with bot configs
            
        Returns:
            bool: True if configs were loaded successfully, False otherwise
        """
        try:
            # Load base config if provided
            if base_config_path and os.path.exists(base_config_path):
                with open(base_config_path, 'r') as f:
                    self.base_config = json.load(f)
                self.logger.info(f"Loaded base config from {base_config_path}")
            
            # Load bot-specific configs
            for filename in os.listdir(config_dir):
                if not filename.endswith('.json'):
                    continue
                    
                bot_type = filename.replace('.json', '')
                config_path = os.path.join(config_dir, filename)
                
                try:
                    with open(config_path, 'r') as f:
                        bot_config = json.load(f)
                        
                    # Merge with base config if exists
                    if self.base_config:
                        merged_config = self._merge_configs(self.base_config, bot_config)
                    else:
                        merged_config = bot_config
                    
                    # Validate the merged config
                    validation_errors = self.validate_config(bot_type, merged_config)
                    if validation_errors:
                        self.logger.warning(f"Config validation errors for {bot_type}: {validation_errors}")
                        # We still load the config but log the warnings
                    
                    self.configs[bot_type] = merged_config
                    self.logger.info(f"Loaded config for bot type '{bot_type}' from {config_path}")
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON in config file {config_path}: {e}")
                    return False
                except Exception as e:
                    self.logger.error(f"Error loading config from {config_path}: {e}")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to load configurations: {e}")
            return False
    
    def _merge_configs(self, base: Dict[str, Any], specific: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simple merge of base and specific configs.
        
        Args:
            base: Base configuration dictionary
            specific: Bot-specific configuration dictionary
            
        Returns:
            Dict[str, Any]: Merged configuration dictionary
        """
        result = base.copy()
        
        for key, value in specific.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def get_config(self, bot_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific bot type.
        
        Args:
            bot_type: The type of bot (consultancy, sales, support)
            
        Returns:
            Dict[str, Any]: The configuration for the specified bot type
            
        Raises:
            KeyError: If the specified bot type is not found
        """
        if bot_type not in self.configs:
            raise KeyError(f"Bot type '{bot_type}' not found. Available types: {list(self.configs.keys())}")
        return self.configs[bot_type]
    
    def validate_config(self, bot_type: str, config: Dict[str, Any]) -> List[str]:
        """
        Validate a configuration against the appropriate schema.
        
        Args:
            bot_type: The type of bot (consultancy, sales, support)
            config: The configuration to validate
            
        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []
        
        # Validate against base schema first
        base_errors = self._validate_against_schema(config, self.validation_schemas["base"])
        if base_errors:
            errors.extend([f"Base config: {error}" for error in base_errors])
        
        # Validate against bot-specific schema if available
        if bot_type in self.validation_schemas:
            bot_errors = self._validate_against_schema(config, self.validation_schemas[bot_type])
            if bot_errors:
                errors.extend([f"{bot_type} config: {error}" for error in bot_errors])
        
        return errors
    
    def _validate_against_schema(self, config: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """
        Validate a configuration section against a schema section.
        
        Args:
            config: The configuration section to validate
            schema: The schema section to validate against
            
        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []
        
        for key, field_schema in schema.items():
            # Check required fields
            if field_schema.get("required", False) and key not in config:
                errors.append(f"Missing required field '{key}'")
                continue
            
            # Skip validation if field is not present
            if key not in config:
                continue
            
            # Check if the field is a dictionary and has required sub-fields
            if isinstance(config[key], dict) and "fields" in field_schema:
                for subfield in field_schema["fields"]:
                    if subfield not in config[key]:
                        errors.append(f"Missing required subfield '{key}.{subfield}'")
        
        return errors 