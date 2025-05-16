"""
Schema loader for NLP processing components.
Loads and validates extraction schemas from configuration.
"""

import json
import logging
from typing import Dict, Any, Optional
import jsonschema

from src.config.config_inheritance import ConfigInheritance

class SchemaLoader:
    """
    Loads and validates extraction schemas from configuration.
    Provides schemas for entity extraction, intent classification, etc.
    """
    
    def __init__(self):
        """Initialize the schema loader."""
        self.config_inheritance = ConfigInheritance()
        self.logger = logging.getLogger(__name__)
        self.schemas = {}
        
    def load_schemas(self, bot_type: str) -> Dict[str, Dict[str, Any]]:
        """
        Load all schemas for a specific bot type.
        
        Args:
            bot_type: The type of bot (consultancy, sales, support)
            
        Returns:
            Dictionary of schema names to schema definitions
        """
        config = self.config_inheritance.get_config(bot_type)
        schema_configs = config.get("nlp.schemas", {})
        
        for schema_name, schema_config in schema_configs.items():
            schema_path = schema_config.get("path")
            schema_inline = schema_config.get("schema")
            
            if schema_inline:
                self.schemas[schema_name] = schema_inline
                self.logger.info(f"Loaded inline schema {schema_name} for bot {bot_type}")
            elif schema_path:
                self.schemas[schema_name] = self._load_schema_from_path(schema_path)
                self.logger.info(f"Loaded schema {schema_name} from path {schema_path}")
            else:
                self.logger.warning(f"No schema definition found for {schema_name}")
        
        return self.schemas
    
    def get_schema(self, bot_type: str, schema_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific schema for a bot type.
        
        Args:
            bot_type: The type of bot (consultancy, sales, support)
            schema_name: The name of the schema to retrieve
            
        Returns:
            The schema definition or None if not found
        """
        # Load schemas if not already loaded for this bot type
        if not self.schemas:
            self.load_schemas(bot_type)
            
        return self.schemas.get(schema_name)
    
    def validate_schema(self, schema: Dict[str, Any]) -> bool:
        """
        Validate that a schema is properly formed.
        
        Args:
            schema: The schema to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Validate against meta-schema (JSON Schema Draft 7)
            jsonschema.Draft7Validator.check_schema(schema)
            return True
        except jsonschema.exceptions.SchemaError as e:
            self.logger.error(f"Invalid schema: {e}")
            return False
    
    def _load_schema_from_path(self, path: str) -> Dict[str, Any]:
        """
        Load a schema from a file path.
        
        Args:
            path: Path to the schema file
            
        Returns:
            The loaded schema
        """
        try:
            with open(path, 'r') as f:
                schema = json.load(f)
                return schema
        except (IOError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to load schema from {path}: {e}")
            return {}

# Global instance
schema_loader = SchemaLoader() 