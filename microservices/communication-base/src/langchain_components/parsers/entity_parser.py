"""
Entity-aware parser for extracting structured entities from LLM responses.

This module provides a parser that extracts structured entities from LLM responses,
validates them against configured schemas, and tracks consistency across conversation turns.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Type, Union
from pydantic import BaseModel, ValidationError, create_model

from langchain.output_parsers import StructuredOutputParser
from langchain.output_parsers.format_instructions import STRUCTURED_FORMAT_INSTRUCTIONS
from langchain.schema import OutputParserException

class EntityParser(StructuredOutputParser):
    """
    Entity-aware parser for extracting structured entities from LLM responses.
    
    This class extends StructuredOutputParser to provide entity extraction,
    validation against schemas, and tracking of entity consistency across turns.
    """
    
    def __init__(
        self,
        schema_registry: Any,
        bot_type: str,
        entity_types: Optional[List[str]] = None,
        tracking_enabled: bool = True,
        **kwargs
    ):
        """
        Initialize entity parser.
        
        Args:
            schema_registry: Registry for entity schema lookup
            bot_type: Type of bot
            entity_types: Types of entities to extract (None for all)
            tracking_enabled: Whether to track entity consistency
        """
        # Get available schemas from registry
        schemas = schema_registry.get_schemas_for_bot(bot_type, entity_types)
        
        if not schemas:
            response_schemas = [
                {"name": "generic_entity", "type": "object", "description": "A generic entity"}
            ]
        else:
            response_schemas = [
                {
                    "name": schema_name,
                    "type": "object", 
                    "description": schema.get("description", f"A {schema_name} entity")
                }
                for schema_name, schema in schemas.items()
            ]
            
        # Initialize base parser
        super().__init__(response_schemas)
        
        self.schema_registry = schema_registry
        self.bot_type = bot_type
        self.entity_types = entity_types
        self.tracking_enabled = tracking_enabled
        self.logger = logging.getLogger(__name__)
        
        # Entity tracking for consistency
        self.tracked_entities = {}
    
    def get_format_instructions(self) -> str:
        """
        Get format instructions for the LLM.
        
        Returns:
            Formatting instructions string
        """
        # Get schemas from registry for format instructions
        schemas = self.schema_registry.get_schemas_for_bot(self.bot_type, self.entity_types)
        schema_descriptions = []
        
        for name, schema in schemas.items():
            required = schema.get("required", [])
            properties = schema.get("properties", {})
            
            property_desc = []
            for prop_name, prop_details in properties.items():
                req_marker = "*" if prop_name in required else ""
                prop_type = prop_details.get("type", "string")
                prop_desc = prop_details.get("description", "")
                
                property_desc.append(f"  - {prop_name}{req_marker}: {prop_type} - {prop_desc}")
            
            schema_desc = [
                f"{name}:",
                f"  {schema.get('description', '')}",
                "  Properties:"
            ] + property_desc
            
            schema_descriptions.append("\n".join(schema_desc))
        
        schema_text = "\n\n".join(schema_descriptions)
        
        # Create format instructions
        return f"""Extract entities from the text according to these schemas:

{schema_text}

Entities should be returned as a JSON object with entity names as keys and entity details as values.
If an entity has multiple instances, return an array of objects.

Example:
```json
{{
  "person": {{
    "name": "John Smith",
    "age": 35,
    "occupation": "engineer"
  }},
  "organization": [
    {{
      "name": "Acme Corp",
      "industry": "technology"
    }},
    {{
      "name": "Globex",
      "industry": "manufacturing"
    }}
  ]
}}
```

If no entities of a particular type are found, omit that type from the response.
"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse text into structured entities.
        
        Args:
            text: Text to parse
            
        Returns:
            Dictionary of extracted entities
            
        Raises:
            OutputParserException: If parsing fails
        """
        try:
            # Extract JSON from text
            json_str = self._extract_json(text)
            
            # Parse JSON
            extracted_entities = json.loads(json_str)
            
            # Validate against schemas
            validated_entities = self._validate_entities(extracted_entities)
            
            # Track entities if enabled
            if self.tracking_enabled:
                self._track_entities(validated_entities)
            
            return validated_entities
            
        except json.JSONDecodeError as e:
            raise OutputParserException(f"Failed to parse JSON: {e}")
        except ValidationError as e:
            raise OutputParserException(f"Schema validation failed: {e}")
        except Exception as e:
            raise OutputParserException(f"Parsing failed: {e}")
    
    def _extract_json(self, text: str) -> str:
        """
        Extract JSON string from text.
        
        Args:
            text: Text possibly containing JSON
            
        Returns:
            JSON string
        """
        # Look for JSON between triple backticks
        if "```json" in text and "```" in text.split("```json", 1)[1]:
            return text.split("```json", 1)[1].split("```", 1)[0].strip()
        
        # Look for JSON between regular backticks
        if "```" in text and "```" in text.split("```", 1)[1]:
            return text.split("```", 1)[1].split("```", 1)[0].strip()
        
        # Look for anything that might be a JSON object
        if "{" in text and "}" in text:
            potential_json = text[text.find("{"):text.rfind("}")+1]
            try:
                # Validate by parsing
                json.loads(potential_json)
                return potential_json
            except json.JSONDecodeError:
                pass
        
        # If no JSON found, return original text (will likely fail parsing)
        self.logger.warning("No valid JSON found in text")
        return text
    
    def _validate_entities(self, extracted_entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate entities against schemas.
        
        Args:
            extracted_entities: Extracted entity dictionary
            
        Returns:
            Validated entities
            
        Raises:
            ValidationError: If validation fails
        """
        # Get schemas from registry
        schemas = self.schema_registry.get_schemas_for_bot(self.bot_type, self.entity_types)
        validated_entities = {}
        
        # Process each extracted entity
        for entity_name, entity_data in extracted_entities.items():
            # Skip if no corresponding schema
            if entity_name not in schemas:
                self.logger.warning(f"No schema found for entity type: {entity_name}")
                validated_entities[entity_name] = entity_data
                continue
            
            schema = schemas[entity_name]
            
            # Create Pydantic model from schema
            model_class = self._create_model_from_schema(entity_name, schema)
            
            # Validate single entity or list of entities
            if isinstance(entity_data, list):
                validated_list = []
                for item in entity_data:
                    try:
                        validated_item = model_class(**item).dict()
                        validated_list.append(validated_item)
                    except ValidationError as e:
                        self.logger.warning(f"Validation failed for {entity_name}: {e}")
                validated_entities[entity_name] = validated_list
            else:
                try:
                    validated_entity = model_class(**entity_data).dict()
                    validated_entities[entity_name] = validated_entity
                except ValidationError as e:
                    self.logger.warning(f"Validation failed for {entity_name}: {e}")
                    # Keep original data if validation fails
                    validated_entities[entity_name] = entity_data
        
        return validated_entities
    
    def _create_model_from_schema(self, entity_name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
        """
        Create a Pydantic model from a JSON schema.
        
        Args:
            entity_name: Name of the entity
            schema: JSON schema
            
        Returns:
            Pydantic model class
        """
        # Get properties from schema
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Create field definitions
        field_definitions = {}
        
        for field_name, field_schema in properties.items():
            field_type = field_schema.get("type", "string")
            
            # Map JSON schema types to Python types
            if field_type == "string":
                python_type = str
            elif field_type == "integer":
                python_type = int
            elif field_type == "number":
                python_type = float
            elif field_type == "boolean":
                python_type = bool
            elif field_type == "array":
                python_type = List[str]  # Default to List[str]
            elif field_type == "object":
                python_type = Dict[str, Any]
            else:
                python_type = str
            
            # Define if field is required
            if field_name in required:
                field_definitions[field_name] = (python_type, ...)
            else:
                field_definitions[field_name] = (Optional[python_type], None)
        
        # Create model
        return create_model(
            f"{entity_name.capitalize()}Model",
            **field_definitions
        )
    
    def _track_entities(self, entities: Dict[str, Any]) -> None:
        """
        Track entities for consistency across turns.
        
        Args:
            entities: Dictionary of entities
        """
        for entity_name, entity_data in entities.items():
            # Handle both single entities and lists
            if isinstance(entity_data, list):
                for item in entity_data:
                    self._track_single_entity(entity_name, item)
            else:
                self._track_single_entity(entity_name, entity_data)
    
    def _track_single_entity(self, entity_type: str, entity: Dict[str, Any]) -> None:
        """
        Track a single entity.
        
        Args:
            entity_type: Type of entity
            entity: Entity data
        """
        # Skip if no identifying field
        if "name" not in entity and "id" not in entity:
            return
        
        # Use name or id as identifier
        entity_id = entity.get("name", entity.get("id", ""))
        if not entity_id:
            return
        
        # Create tracking key
        tracking_key = f"{entity_type}:{entity_id}"
        
        if tracking_key not in self.tracked_entities:
            # New entity
            self.tracked_entities[tracking_key] = {
                "type": entity_type,
                "id": entity_id,
                "first_seen": {},
                "current": entity,
                "mentions": 1
            }
            # Save first values
            for key, value in entity.items():
                self.tracked_entities[tracking_key]["first_seen"][key] = value
        else:
            # Update existing entity
            tracked = self.tracked_entities[tracking_key]
            tracked["mentions"] += 1
            
            # Update current values
            tracked["current"] = {**tracked["current"], **entity}
    
    def get_tracked_entities(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all tracked entities.
        
        Returns:
            Dictionary of tracked entities
        """
        return self.tracked_entities
    
    def get_entity_consistency(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """
        Get consistency information for an entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity identifier
            
        Returns:
            Dictionary with consistency information
        """
        tracking_key = f"{entity_type}:{entity_id}"
        
        if tracking_key not in self.tracked_entities:
            return {"consistent": True, "differences": {}}
        
        tracked = self.tracked_entities[tracking_key]
        first_seen = tracked["first_seen"]
        current = tracked["current"]
        
        # Check for differences
        differences = {}
        for key, first_value in first_seen.items():
            if key in current and current[key] != first_value:
                differences[key] = {
                    "first": first_value,
                    "current": current[key]
                }
        
        return {
            "consistent": len(differences) == 0,
            "differences": differences,
            "mentions": tracked["mentions"]
        } 