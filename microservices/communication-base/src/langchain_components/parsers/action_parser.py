"""
Action-oriented parser for extracting structured actions from LLM responses.

This module provides a parser that extracts structured actions from LLM responses,
validates them against action schemas, and prepares them for execution.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Union, Set, Type

from langchain.output_parsers import PydanticOutputParser
from langchain.schema import OutputParserException
from pydantic import BaseModel, Field, ValidationError, create_model

class ActionBase(BaseModel):
    """
    Base model for all action types.
    """
    action_type: str = Field(..., description="Type of action to perform")
    priority: int = Field(5, ge=1, le=10, description="Priority level (1-10)")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in this action")

class Action(ActionBase):
    """
    Generic action structure.
    """
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the action"
    )
    description: str = Field("", description="Human-readable description of the action")

class ActionParser:
    """
    Action-oriented parser for extracting structured actions from LLM responses.
    
    This class extracts actions from LLM responses, validates them against schemas,
    and prepares them for execution by appropriate handlers.
    """
    
    def __init__(
        self,
        schema_registry: Any = None,
        bot_type: Optional[str] = None,
        config_integration: Any = None,
        default_actions: Optional[List[str]] = None,
        validate_schemas: bool = True
    ):
        """
        Initialize action parser.
        
        Args:
            schema_registry: Registry for action schema lookup
            bot_type: Type of bot
            config_integration: Integration with the config system
            default_actions: Default action types to extract
            validate_schemas: Whether to validate against schemas
        """
        self.schema_registry = schema_registry
        self.bot_type = bot_type
        self.config_integration = config_integration
        self.default_actions = default_actions or ["lookup", "search", "retrieve", "calculate"]
        self.validate_schemas = validate_schemas
        self.logger = logging.getLogger(__name__)
        
        # Action type to model mapping
        self.action_models = {}
        
        # Initialize action schemas
        self._init_action_schemas()
    
    def _init_action_schemas(self) -> None:
        """
        Initialize action schemas from registry or defaults.
        """
        # If schema registry is available, load schemas from it
        if self.schema_registry and self.bot_type:
            try:
                action_schemas = self.schema_registry.get_action_schemas(self.bot_type)
                if action_schemas:
                    for action_type, schema in action_schemas.items():
                        self._register_action_model(action_type, schema)
                else:
                    self._init_default_action_models()
            except Exception as e:
                self.logger.warning(f"Failed to load action schemas: {e}")
                self._init_default_action_models()
        else:
            self._init_default_action_models()
    
    def _init_default_action_models(self) -> None:
        """
        Initialize default action models.
        """
        # Lookup action
        self._register_action_model("lookup", {
            "properties": {
                "entity": {"type": "string", "description": "Entity to look up"},
                "attribute": {"type": "string", "description": "Specific attribute to retrieve"},
                "context": {"type": "string", "description": "Additional context"}
            },
            "required": ["entity"]
        })
        
        # Search action
        self._register_action_model("search", {
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "filters": {"type": "object", "description": "Search filters"},
                "max_results": {"type": "integer", "description": "Maximum number of results"}
            },
            "required": ["query"]
        })
        
        # Retrieve action
        self._register_action_model("retrieve", {
            "properties": {
                "document_id": {"type": "string", "description": "Document identifier"},
                "section": {"type": "string", "description": "Specific section to retrieve"},
                "format": {"type": "string", "description": "Desired format"}
            },
            "required": ["document_id"]
        })
        
        # Calculate action
        self._register_action_model("calculate", {
            "properties": {
                "expression": {"type": "string", "description": "Expression to calculate"},
                "precision": {"type": "integer", "description": "Decimal precision"}
            },
            "required": ["expression"]
        })
    
    def _register_action_model(self, action_type: str, schema: Dict[str, Any]) -> None:
        """
        Register a Pydantic model for an action type.
        
        Args:
            action_type: Type of action
            schema: JSON schema for action parameters
        """
        try:
            # Create field definitions for model
            field_definitions = {
                "action_type": (str, Field(action_type, const=True)),
                "priority": (int, Field(5, ge=1, le=10)),
                "confidence": (float, Field(1.0, ge=0.0, le=1.0)),
                "description": (str, Field(""))
            }
            
            # Add fields from schema
            for field_name, field_schema in schema.get("properties", {}).items():
                field_type = str  # Default to string
                
                # Map JSON schema types to Python types
                if field_schema.get("type") == "integer":
                    field_type = int
                elif field_schema.get("type") == "number":
                    field_type = float
                elif field_schema.get("type") == "boolean":
                    field_type = bool
                elif field_schema.get("type") == "object":
                    field_type = Dict[str, Any]
                elif field_schema.get("type") == "array":
                    field_type = List[Any]
                
                # Check if field is required
                if field_name in schema.get("required", []):
                    field_definitions[field_name] = (
                        field_type,
                        Field(..., description=field_schema.get("description", ""))
                    )
                else:
                    field_definitions[field_name] = (
                        Optional[field_type],
                        Field(None, description=field_schema.get("description", ""))
                    )
            
            # Create model
            model = create_model(
                f"{action_type.capitalize()}Action",
                **field_definitions
            )
            
            # Register model
            self.action_models[action_type] = model
            
        except Exception as e:
            self.logger.error(f"Failed to register action model for {action_type}: {e}")
    
    def extract_actions(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract actions from text.
        
        Args:
            text: Text to parse for actions
            
        Returns:
            List of extracted actions
            
        Raises:
            OutputParserException: If action extraction fails
        """
        # Try different extraction approaches
        actions = []
        
        # First, try to extract JSON blocks that might contain actions
        json_actions = self._extract_json_actions(text)
        if json_actions:
            actions.extend(json_actions)
        
        # If no actions found in JSON, try pattern-based extraction
        if not actions:
            pattern_actions = self._extract_pattern_actions(text)
            if pattern_actions:
                actions.extend(pattern_actions)
        
        # Validate and process extracted actions
        return self._process_actions(actions)
    
    def _extract_json_actions(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract actions from JSON blocks in text.
        
        Args:
            text: Text to parse
            
        Returns:
            List of actions extracted from JSON
        """
        actions = []
        
        # Look for JSON blocks
        json_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        matches = re.finditer(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                json_str = match.group(1)
                json_data = json.loads(json_str)
                
                # Check if it's a single action or a list of actions
                if isinstance(json_data, list):
                    for item in json_data:
                        if "action_type" in item:
                            actions.append(item)
                elif isinstance(json_data, dict) and "action_type" in json_data:
                    actions.append(json_data)
                elif isinstance(json_data, dict) and "actions" in json_data:
                    # Handle case where actions are nested under "actions" key
                    action_list = json_data["actions"]
                    if isinstance(action_list, list):
                        for item in action_list:
                            if isinstance(item, dict) and "action_type" in item:
                                actions.append(item)
            except json.JSONDecodeError:
                continue
        
        # If no actions found in code blocks, try extracting JSON directly
        if not actions:
            try:
                # Find anything that looks like a complete JSON object
                json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
                matches = re.finditer(json_pattern, text, re.DOTALL)
                
                for match in matches:
                    try:
                        json_str = match.group(0)
                        json_data = json.loads(json_str)
                        
                        if isinstance(json_data, dict) and "action_type" in json_data:
                            actions.append(json_data)
                    except json.JSONDecodeError:
                        continue
            except Exception:
                pass
        
        return actions
    
    def _extract_pattern_actions(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract actions using regex patterns.
        
        Args:
            text: Text to parse
            
        Returns:
            List of actions extracted using patterns
        """
        actions = []
        
        # Look for action declarations in natural language
        for action_type in self.default_actions:
            patterns = [
                # Standard pattern: Action: type(param=value)
                rf"(?:Action|{action_type})[:\s]+{action_type}\s*\(([^)]+)\)",
                # Alternative pattern: "perform a {action_type} with {params}"
                rf"(?:perform|execute|do|run)(?:\s+a)?(?:\s+an)?\s+{action_type}(?:\s+with|\s+using)?\s+([^\.]+)",
                # Direct mention: "use {action_type} to {action_desc}"
                rf"use\s+{action_type}(?:\s+to|\s+for)?\s+([^\.]+)"
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    try:
                        # Extract parameters from match
                        params_str = match.group(1).strip()
                        
                        # Parse parameters
                        params = {}
                        
                        # Check for key=value pairs
                        param_pattern = r"(\w+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|(\S+))"
                        param_matches = re.finditer(param_pattern, params_str)
                        
                        for param_match in param_matches:
                            key = param_match.group(1)
                            # Value could be in any of the capturing groups (quoted or unquoted)
                            value = param_match.group(2) or param_match.group(3) or param_match.group(4)
                            params[key] = value
                        
                        # If no structured params found, use the whole string as a description
                        if not params:
                            action = {
                                "action_type": action_type,
                                "description": params_str
                            }
                            
                            # Try to extract obvious parameters from description
                            if ":" in params_str:
                                parts = params_str.split(":", 1)
                                key = parts[0].strip().lower()
                                value = parts[1].strip()
                                if key in ["query", "entity", "expression"]:
                                    action[key] = value
                        else:
                            action = {
                                "action_type": action_type,
                                **params
                            }
                        
                        actions.append(action)
                    except Exception as e:
                        self.logger.debug(f"Failed to parse action parameters: {e}")
                        continue
        
        return actions
    
    def _process_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and validate extracted actions.
        
        Args:
            actions: List of extracted actions
            
        Returns:
            List of processed and validated actions
        """
        processed_actions = []
        
        for action_data in actions:
            try:
                action_type = action_data.get("action_type")
                
                # Skip if no action type
                if not action_type:
                    continue
                
                # Validate against model if available and validation is enabled
                if self.validate_schemas and action_type in self.action_models:
                    model_cls = self.action_models[action_type]
                    validated_action = model_cls(**action_data)
                    processed_action = validated_action.dict()
                else:
                    # Create a generic Action object
                    # Extract known action fields
                    action_fields = {}
                    parameter_fields = {}
                    
                    for key, value in action_data.items():
                        if key in ["action_type", "priority", "confidence", "description"]:
                            action_fields[key] = value
                        else:
                            parameter_fields[key] = value
                    
                    # Set parameters
                    if not "parameters" in action_data and parameter_fields:
                        action_fields["parameters"] = parameter_fields
                    
                    generic_action = Action(**action_fields)
                    processed_action = generic_action.dict()
                
                processed_actions.append(processed_action)
                
            except ValidationError as e:
                self.logger.warning(f"Action validation failed: {e}")
                # Include the action but mark as invalid
                action_data["validation_errors"] = str(e)
                processed_actions.append(action_data)
            except Exception as e:
                self.logger.warning(f"Action processing failed: {e}")
                continue
        
        # Sort by priority (if specified)
        processed_actions.sort(
            key=lambda x: x.get("priority", 5),
            reverse=True  # Higher priority first
        )
        
        return processed_actions
    
    def get_format_instructions(self) -> str:
        """
        Get format instructions for the LLM.
        
        Returns:
            Formatting instructions string
        """
        # Get available action types
        action_types = list(self.action_models.keys()) if self.action_models else self.default_actions
        
        # Build instructions based on available actions
        action_descriptions = []
        for action_type in action_types:
            if action_type in self.action_models:
                model = self.action_models[action_type]
                fields = []
                
                for field_name, field_info in model.__fields__.items():
                    if field_name not in ["action_type", "priority", "confidence"]:
                        required = field_info.required
                        desc = field_info.field_info.description
                        field_str = f"  - {field_name}"
                        if required:
                            field_str += " (required)"
                        if desc:
                            field_str += f": {desc}"
                        fields.append(field_str)
                
                if fields:
                    action_descriptions.append(f"{action_type}:\n" + "\n".join(fields))
            else:
                # Generic description for default actions
                if action_type == "lookup":
                    action_descriptions.append(f"{action_type}:\n  - entity (required): Entity to look up\n  - attribute: Specific attribute to retrieve")
                elif action_type == "search":
                    action_descriptions.append(f"{action_type}:\n  - query (required): Search query\n  - filters: Search filters")
                elif action_type == "retrieve":
                    action_descriptions.append(f"{action_type}:\n  - document_id (required): Document identifier\n  - section: Specific section to retrieve")
                elif action_type == "calculate":
                    action_descriptions.append(f"{action_type}:\n  - expression (required): Expression to calculate")
        
        action_descriptions_str = "\n\n".join(action_descriptions)
        
        return f"""When you need to perform specific actions, return them in a structured format.
Available actions:

{action_descriptions_str}

Format actions as JSON, including the action_type and required parameters:

```json
{{
  "action_type": "action_name",
  "priority": 5,  // optional, 1-10 (higher is more important)
  "parameters": {{
    "param1": "value1",
    "param2": "value2"
  }}
}}
```

You can also include multiple actions:

```json
[
  {{
    "action_type": "action1",
    "param1": "value1"
  }},
  {{
    "action_type": "action2",
    "param2": "value2"
  }}
]
```

Use these structured actions when you need to perform specific tasks rather than just responding with text.""" 