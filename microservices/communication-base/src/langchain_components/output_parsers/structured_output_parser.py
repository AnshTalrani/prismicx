"""
Structured output parser for LangChain components.

This module provides a specialized output parser that can handle complex structured
outputs from LLMs, with robust error handling and fallback mechanisms.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Type, Union, Callable
import json

from langchain.output_parsers import PydanticOutputParser
from langchain.output_parsers.base import OutputParser
from langchain.schema import BaseOutputParser
from pydantic import BaseModel, ValidationError

class StructuredOutputParser(BaseOutputParser):
    """
    Enhanced output parser for handling structured outputs with robust error handling.
    
    This parser extends LangChain's parsing capabilities with:
    1. Multiple format support (JSON, YAML, Key-Value)
    2. Error recovery and partial extraction
    3. Fallback values and default handling
    """
    
    def __init__(
        self,
        pydantic_object: Optional[Type[BaseModel]] = None,
        expected_keys: Optional[List[str]] = None,
        expected_format: str = "json",
        fallback_parser: Optional[OutputParser] = None,
        partial_parse: bool = True
    ):
        """
        Initialize the structured output parser.
        
        Args:
            pydantic_object: Pydantic model to parse into (optional)
            expected_keys: List of expected keys in the output (if no pydantic model)
            expected_format: Expected format of output (json, yaml, key-value)
            fallback_parser: Parser to use if primary parsing fails
            partial_parse: Whether to attempt partial parsing on failure
        """
        self.logger = logging.getLogger(__name__)
        self.pydantic_object = pydantic_object
        self.expected_keys = expected_keys or []
        self.expected_format = expected_format.lower()
        self.fallback_parser = fallback_parser
        self.partial_parse = partial_parse
        
        # Initialize pydantic parser if model provided
        self.pydantic_parser = None
        if pydantic_object:
            self.pydantic_parser = PydanticOutputParser(pydantic_object=pydantic_object)
    
    def parse(self, text: str) -> Union[Dict[str, Any], BaseModel, List[Dict[str, Any]]]:
        """
        Parse the output text into the expected structure.
        
        Args:
            text: Text to parse
            
        Returns:
            Parsed structure (dictionary, Pydantic model, or list)
        """
        try:
            # First, try to extract structured blocks
            extracted_text = self._extract_structured_blocks(text)
            
            # Try primary parsing based on expected format
            if self.expected_format == "json":
                parsed = self._parse_json(extracted_text)
            elif self.expected_format in ["yaml", "yml"]:
                parsed = self._parse_yaml(extracted_text)
            elif self.expected_format == "key-value":
                parsed = self._parse_key_value(extracted_text)
            else:
                # Default to JSON parsing
                parsed = self._parse_json(extracted_text)
            
            # If we have a pydantic model, validate against it
            if self.pydantic_parser and parsed:
                if isinstance(parsed, list):
                    # Try to validate each item in list
                    validated_items = []
                    for item in parsed:
                        try:
                            validated = self.pydantic_object.parse_obj(item)
                            validated_items.append(validated)
                        except ValidationError as e:
                            self.logger.warning(f"Validation error for item: {e}")
                            if self.partial_parse:
                                validated_items.append(item)  # Keep original on failure
                    return validated_items
                else:
                    # Validate single object
                    return self.pydantic_object.parse_obj(parsed)
            
            return parsed
            
        except Exception as e:
            self.logger.error(f"Error parsing output: {e}")
            
            # Try fallback parser if provided
            if self.fallback_parser:
                try:
                    return self.fallback_parser.parse(text)
                except Exception as fallback_e:
                    self.logger.error(f"Fallback parser failed: {fallback_e}")
            
            # Try partial parsing if enabled
            if self.partial_parse:
                try:
                    return self._extract_partial(text)
                except Exception as partial_e:
                    self.logger.error(f"Partial parsing failed: {partial_e}")
            
            # Last resort: return empty dict
            if self.pydantic_object:
                # Create empty instance with default values
                return self.pydantic_object.construct()
            else:
                return {}
    
    def _extract_structured_blocks(self, text: str) -> str:
        """
        Extract structured blocks from text (code blocks, etc.).
        
        Args:
            text: Input text
            
        Returns:
            Extracted structured content
        """
        # Try to extract JSON code blocks
        json_matches = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text)
        if json_matches:
            # Return the first JSON block
            return json_matches[0].strip()
        
        # Try to extract YAML code blocks if expected
        if self.expected_format in ["yaml", "yml"]:
            yaml_matches = re.findall(r"```(?:yaml|yml)?\s*([\s\S]*?)```", text)
            if yaml_matches:
                return yaml_matches[0].strip()
        
        # Check for any code blocks
        code_blocks = re.findall(r"```([\s\S]*?)```", text)
        if code_blocks:
            return code_blocks[0].strip()
        
        # No blocks found, return original text
        return text
    
    def _parse_json(self, text: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Parse JSON from text.
        
        Args:
            text: JSON text to parse
            
        Returns:
            Parsed JSON object
        """
        # Try to extract JSON object pattern
        json_pattern = r"(\{.*\}|\[.*\])"
        
        # Look for JSON objects
        json_matches = re.search(json_pattern, text, re.DOTALL)
        if json_matches:
            json_str = json_matches.group(0)
            return json.loads(json_str)
        
        # Fallback to parsing the entire text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Clean up text by removing common prefixes
            cleaned_text = re.sub(r"^[^{[]*", "", text)
            # And removing trailing text
            cleaned_text = re.sub(r"[^}\]]*$", "", cleaned_text)
            
            # Try parsing again
            return json.loads(cleaned_text)
    
    def _parse_yaml(self, text: str) -> Dict[str, Any]:
        """
        Parse YAML from text.
        
        Args:
            text: YAML text to parse
            
        Returns:
            Parsed YAML object
        """
        import yaml
        
        try:
            return yaml.safe_load(text)
        except Exception:
            # Try to clean up text
            lines = text.split("\n")
            # Filter out lines that don't look like YAML
            cleaned_lines = [line for line in lines if ":" in line or line.strip().startswith("-")]
            return yaml.safe_load("\n".join(cleaned_lines))
    
    def _parse_key_value(self, text: str) -> Dict[str, Any]:
        """
        Parse key-value pairs from text.
        
        Args:
            text: Text containing key-value pairs
            
        Returns:
            Dictionary of key-value pairs
        """
        result = {}
        
        # Split text into lines
        lines = text.split("\n")
        
        # Process each line
        for line in lines:
            line = line.strip()
            if not line or ":" not in line:
                continue
            
            # Split on first colon
            parts = line.split(":", 1)
            if len(parts) != 2:
                continue
            
            key = parts[0].strip()
            value = parts[1].strip()
            
            # Skip if key is empty
            if not key:
                continue
            
            # Process multi-level keys
            keys = [k.strip() for k in key.split(".")]
            
            # Build nested structure
            current = result
            for i, k in enumerate(keys):
                if i == len(keys) - 1:
                    # Final key, set value
                    current[k] = value
                else:
                    # Intermediate key, ensure dict exists
                    if k not in current:
                        current[k] = {}
                    current = current[k]
        
        return result
    
    def _extract_partial(self, text: str) -> Dict[str, Any]:
        """
        Extract partial data when full parsing fails.
        
        Args:
            text: Text to extract from
            
        Returns:
            Extracted partial data
        """
        result = {}
        
        # Try to extract key-value pairs using regex
        if self.expected_keys:
            for key in self.expected_keys:
                # Look for patterns like "key: value" or "key = value"
                pattern = rf'["\']?{re.escape(key)}["\']?\s*[:=]\s*["\']?(.*?)["\']?(?:,|\n|$)'
                match = re.search(pattern, text)
                if match:
                    value = match.group(1).strip()
                    # Remove trailing commas or quotes
                    value = re.sub(r'[,"\']+$', '', value)
                    result[key] = value
        
        # Look for any JSON-like structures
        json_parts = re.findall(r'["\'](\w+)["\']:\s*["\']?([^,"\'{}[\]]+)["\']?', text)
        for key, value in json_parts:
            if key not in result:
                result[key] = value.strip()
        
        return result
    
    def get_format_instructions(self) -> str:
        """
        Get format instructions for the LLM.
        
        Returns:
            Formatting instructions string
        """
        if self.pydantic_parser:
            return self.pydantic_parser.get_format_instructions()
        
        if self.expected_format == "json":
            keys_str = ", ".join([f'"{key}"' for key in self.expected_keys])
            return (
                f"Return the output as a JSON object with the following keys: {keys_str}.\n"
                f"Format the output as a valid JSON object."
            )
        elif self.expected_format in ["yaml", "yml"]:
            keys_str = "\n".join([f"- {key}: <value>" for key in self.expected_keys])
            return (
                f"Return the output as YAML with the following structure:\n{keys_str}"
            )
        else:
            keys_str = "\n".join([f"{key}: <value>" for key in self.expected_keys])
            return (
                f"Return the output as key-value pairs:\n{keys_str}"
            )


class RobustPydanticOutputParser(PydanticOutputParser):
    """
    A more robust version of PydanticOutputParser with error recovery.
    
    This parser extends the standard PydanticOutputParser with:
    1. Better code block extraction
    2. Partial parsing on failure
    3. Flexible field mapping
    """
    
    def __init__(
        self, 
        pydantic_object: Type[BaseModel],
        partial_parse: bool = True,
        field_mapping: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the robust Pydantic output parser.
        
        Args:
            pydantic_object: Pydantic model to parse into
            partial_parse: Whether to attempt partial parsing on failure
            field_mapping: Mapping of LLM output fields to Pydantic model fields
        """
        super().__init__(pydantic_object=pydantic_object)
        self.logger = logging.getLogger(__name__)
        self.partial_parse = partial_parse
        self.field_mapping = field_mapping or {}
    
    def parse(self, text: str) -> BaseModel:
        """
        Parse text into a Pydantic object with robust error handling.
        
        Args:
            text: Text to parse
            
        Returns:
            Parsed Pydantic object
        """
        try:
            # First try standard parsing
            return super().parse(text)
        except Exception as e:
            self.logger.warning(f"Standard parsing failed: {e}")
            
            # Try to extract JSON from code blocks
            try:
                json_matches = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text)
                if json_matches:
                    for json_text in json_matches:
                        try:
                            data = json.loads(json_text.strip())
                            # Apply field mapping if provided
                            if self.field_mapping:
                                mapped_data = {}
                                for llm_field, model_field in self.field_mapping.items():
                                    if llm_field in data:
                                        mapped_data[model_field] = data[llm_field]
                                data = {**data, **mapped_data}
                            return self.pydantic_object.parse_obj(data)
                        except Exception:
                            continue
            except Exception:
                pass
            
            # Try regex-based extraction if partial parsing is enabled
            if self.partial_parse:
                try:
                    partial_data = self._extract_fields(text)
                    
                    # Try to construct a valid object
                    try:
                        return self.pydantic_object.parse_obj(partial_data)
                    except ValidationError:
                        # If validation fails, try with default field values
                        default_instance = self.pydantic_object.construct()
                        default_dict = default_instance.dict()
                        
                        # Merge partial data with defaults
                        merged_data = {**default_dict, **partial_data}
                        return self.pydantic_object.parse_obj(merged_data)
                        
                except Exception as partial_e:
                    self.logger.error(f"Partial parsing failed: {partial_e}")
            
            # If all else fails, create an empty instance
            self.logger.error(f"Parsing failed, returning default instance: {e}")
            return self.pydantic_object.construct()
    
    def _extract_fields(self, text: str) -> Dict[str, Any]:
        """
        Extract fields from text using regex patterns.
        
        Args:
            text: Text to extract fields from
            
        Returns:
            Dictionary of extracted field values
        """
        result = {}
        
        # Get field names from the Pydantic model
        field_names = list(self.pydantic_object.__annotations__.keys())
        
        # Get field names from mapping as well
        for llm_field in self.field_mapping.keys():
            if llm_field not in field_names:
                field_names.append(llm_field)
        
        # Try to extract each field
        for field in field_names:
            # Look for different patterns
            patterns = [
                rf'["\']?{field}["\']?\s*[:=]\s*["\']?(.*?)["\']?(?:,|\n|$)',  # field: value or field = value
                rf'{field}:\s*(.*?)(?:$|\n)',  # field: value (YAML style)
                rf'{field} - (.*?)(?:$|\n)',  # field - value 
                rf'{field}:\s*(.+?)(?:$|\n|",|\',)',  # More flexible field: value
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Remove trailing commas, quotes, etc.
                    value = re.sub(r'[,"\'}\]]+$', '', value)
                    
                    # Map field if needed
                    target_field = self.field_mapping.get(field, field)
                    result[target_field] = value
                    break
        
        return result


# Export parser factory function
def create_parser(
    model_type: Optional[Type[BaseModel]] = None,
    format_type: str = "json",
    expected_keys: Optional[List[str]] = None,
    partial_parse: bool = True,
    field_mapping: Optional[Dict[str, str]] = None
) -> BaseOutputParser:
    """
    Create an appropriate parser based on the provided parameters.
    
    Args:
        model_type: Pydantic model type (optional)
        format_type: Expected format of output (json, yaml, key-value)
        expected_keys: List of expected keys (if no model provided)
        partial_parse: Whether to attempt partial parsing on failure
        field_mapping: Mapping of LLM output fields to model fields
        
    Returns:
        Appropriate output parser
    """
    if model_type:
        if field_mapping or partial_parse:
            return RobustPydanticOutputParser(
                pydantic_object=model_type,
                partial_parse=partial_parse,
                field_mapping=field_mapping
            )
        else:
            return PydanticOutputParser(pydantic_object=model_type)
    else:
        return StructuredOutputParser(
            expected_keys=expected_keys or [],
            expected_format=format_type,
            partial_parse=partial_parse
        ) 