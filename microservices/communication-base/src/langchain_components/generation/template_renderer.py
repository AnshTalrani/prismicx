"""
Template renderer for structuring response generation.

This module provides functionality to apply bot-specific templates to responses,
handle variable substitution, and format rich content templates.
"""

import logging
import json
import os
import re
from string import Template
from typing import Dict, Any, List, Optional, Union
import yaml

from src.config.config_inheritance import ConfigInheritance

class TemplateRenderer:
    """
    Template renderer for structured response generation.
    
    This class provides functionality to:
    1. Apply bot-specific templates to responses
    2. Handle variable substitution and formatting
    3. Support rich content templates with multiple formats
    """
    
    def __init__(self):
        """Initialize the template renderer."""
        self.logger = logging.getLogger(__name__)
        self.config_inheritance = ConfigInheritance()
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self) -> None:
        """
        Load templates from configuration and template files.
        """
        try:
            # Base template directory
            template_dir = os.path.join("src", "langchain_components", "generation", "templates")
            
            # Load templates for each bot type
            for bot_type in ["consultancy", "sales", "support"]:
                bot_templates = {}
                
                # Get template config for this bot type
                config = self.config_inheritance.get_config(bot_type)
                template_config = config.get("chain_config", {}).get("prompt", {}).get("templates", {})
                
                # Load templates from config paths
                for template_name, template_info in template_config.items():
                    if isinstance(template_info, dict) and "path" in template_info:
                        template_path = template_info["path"]
                        try:
                            # Determine file type from extension
                            if template_path.endswith(".json"):
                                with open(template_path, 'r') as f:
                                    template_data = json.load(f)
                            elif template_path.endswith((".yaml", ".yml")):
                                with open(template_path, 'r') as f:
                                    template_data = yaml.safe_load(f)
                            else:
                                with open(template_path, 'r') as f:
                                    template_data = f.read()
                            
                            bot_templates[template_name] = template_data
                        except Exception as e:
                            self.logger.error(f"Failed to load template from {template_path}: {e}")
                    elif isinstance(template_info, str):
                        # Direct template string
                        bot_templates[template_name] = template_info
                
                # Load default templates from template directory
                bot_template_dir = os.path.join(template_dir, bot_type)
                if os.path.exists(bot_template_dir):
                    for filename in os.listdir(bot_template_dir):
                        template_name = os.path.splitext(filename)[0]
                        template_path = os.path.join(bot_template_dir, filename)
                        
                        # Skip if already loaded from config
                        if template_name in bot_templates:
                            continue
                        
                        try:
                            # Determine file type from extension
                            if filename.endswith(".json"):
                                with open(template_path, 'r') as f:
                                    template_data = json.load(f)
                            elif filename.endswith((".yaml", ".yml")):
                                with open(template_path, 'r') as f:
                                    template_data = yaml.safe_load(f)
                            else:
                                with open(template_path, 'r') as f:
                                    template_data = f.read()
                            
                            bot_templates[template_name] = template_data
                        except Exception as e:
                            self.logger.error(f"Failed to load template from {template_path}: {e}")
                
                # Store templates for this bot type
                self.templates[bot_type] = bot_templates
                
                self.logger.info(f"Loaded {len(bot_templates)} templates for {bot_type} bot")
                
        except Exception as e:
            self.logger.error(f"Error loading templates: {e}")
    
    def render_template(
        self, 
        template_name: str, 
        context: Dict[str, Any], 
        bot_type: str
    ) -> str:
        """
        Render a template with the provided context.
        
        Args:
            template_name: Name of the template to render
            context: Context variables for substitution
            bot_type: Type of bot
            
        Returns:
            Rendered template string
        """
        try:
            # Get templates for this bot type
            bot_templates = self.templates.get(bot_type, {})
            
            # Check if template exists
            if template_name not in bot_templates:
                self.logger.warning(f"Template '{template_name}' not found for {bot_type} bot")
                return self._fallback_template(context, bot_type)
            
            template = bot_templates[template_name]
            
            # Handle different template types
            if isinstance(template, str):
                # Simple string template
                return self._render_string_template(template, context)
            elif isinstance(template, dict):
                # Complex structured template
                return self._render_structured_template(template, context)
            else:
                self.logger.error(f"Unsupported template type for '{template_name}': {type(template)}")
                return self._fallback_template(context, bot_type)
                
        except Exception as e:
            self.logger.error(f"Error rendering template '{template_name}': {e}")
            return self._fallback_template(context, bot_type)
    
    def _render_string_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Render a string template with variable substitution.
        
        Args:
            template: Template string
            context: Context variables
            
        Returns:
            Rendered template
        """
        # Replace any None values with empty strings to avoid Template errors
        safe_context = {k: (v if v is not None else "") for k, v in context.items()}
        
        try:
            # Use string.Template for variable substitution
            template_obj = Template(template)
            return template_obj.safe_substitute(safe_context)
        except Exception as e:
            self.logger.error(f"Error in string template rendering: {e}")
            # Fall back to simple format-based replacement for basic substitution
            for key, value in safe_context.items():
                placeholder = "${" + key + "}"
                template = template.replace(placeholder, str(value))
            return template
    
    def _render_structured_template(self, template: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Render a structured template (e.g., JSON/YAML).
        
        Args:
            template: Template structure
            context: Context variables
            
        Returns:
            Rendered template as a string
        """
        # Check if this is a component-based template
        if "components" in template:
            return self._render_component_template(template, context)
        
        # Check if this is a conditional template
        if "conditions" in template:
            return self._render_conditional_template(template, context)
        
        # Regular structured template
        rendered = {}
        for key, value in template.items():
            if isinstance(value, str):
                rendered[key] = self._render_string_template(value, context)
            elif isinstance(value, dict):
                rendered[key] = self._render_structured_template(value, context)
            elif isinstance(value, list):
                rendered[key] = [
                    self._render_structured_template(item, context) if isinstance(item, dict)
                    else self._render_string_template(item, context) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                rendered[key] = value
        
        # Convert back to string based on format
        output_format = template.get("format", "text")
        if output_format == "json":
            return json.dumps(rendered, indent=2)
        elif output_format in ["yaml", "yml"]:
            return yaml.dump(rendered)
        else:
            # Default to text format with sections
            sections = []
            for key, value in rendered.items():
                if key != "format":
                    if isinstance(value, (dict, list)):
                        sections.append(f"{key}:\n{json.dumps(value, indent=2)}")
                    else:
                        sections.append(f"{key}: {value}")
            return "\n\n".join(sections)
    
    def _render_component_template(self, template: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Render a template composed of multiple components.
        
        Args:
            template: Component template structure
            context: Context variables
            
        Returns:
            Rendered template
        """
        components = template.get("components", [])
        sections = []
        
        for component in components:
            # Skip component if condition is defined and not met
            if "condition" in component:
                condition = component["condition"]
                variable = condition.get("variable")
                operator = condition.get("operator", "exists")
                value = condition.get("value")
                
                if not self._evaluate_condition(variable, operator, value, context):
                    continue
            
            # Get component content
            content = component.get("content", "")
            
            # Render content based on type
            if isinstance(content, str):
                rendered_content = self._render_string_template(content, context)
            elif isinstance(content, dict):
                rendered_content = self._render_structured_template(content, context)
            else:
                rendered_content = str(content)
            
            # Add to sections
            if rendered_content:
                sections.append(rendered_content)
        
        # Join with separators if defined
        separator = template.get("separator", "\n\n")
        return separator.join(sections)
    
    def _render_conditional_template(self, template: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Render a template with conditional branches.
        
        Args:
            template: Conditional template structure
            context: Context variables
            
        Returns:
            Rendered template
        """
        conditions = template.get("conditions", [])
        
        # Default content if no conditions match
        default_content = template.get("default", "")
        
        for condition in conditions:
            variable = condition.get("variable")
            operator = condition.get("operator", "equals")
            value = condition.get("value")
            content = condition.get("content", "")
            
            if self._evaluate_condition(variable, operator, value, context):
                # Render matching content
                if isinstance(content, str):
                    return self._render_string_template(content, context)
                elif isinstance(content, dict):
                    return self._render_structured_template(content, context)
                else:
                    return str(content)
        
        # No conditions matched, use default
        if isinstance(default_content, str):
            return self._render_string_template(default_content, context)
        elif isinstance(default_content, dict):
            return self._render_structured_template(default_content, context)
        else:
            return str(default_content)
    
    def _evaluate_condition(
        self, 
        variable: str, 
        operator: str, 
        value: Any, 
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate a condition against the context.
        
        Args:
            variable: Variable name to check
            operator: Comparison operator
            value: Value to compare against
            context: Context variables
            
        Returns:
            True if condition is met, False otherwise
        """
        # Get variable value from context
        var_value = context.get(variable)
        
        # Evaluate based on operator
        if operator == "exists":
            return variable in context and var_value is not None
        elif operator == "not_exists":
            return variable not in context or var_value is None
        elif operator == "equals":
            return var_value == value
        elif operator == "not_equals":
            return var_value != value
        elif operator == "contains":
            if isinstance(var_value, (list, str)):
                return value in var_value
            return False
        elif operator == "not_contains":
            if isinstance(var_value, (list, str)):
                return value not in var_value
            return True
        elif operator == "greater_than":
            try:
                return float(var_value) > float(value)
            except (ValueError, TypeError):
                return False
        elif operator == "less_than":
            try:
                return float(var_value) < float(value)
            except (ValueError, TypeError):
                return False
        elif operator == "matches":
            if isinstance(var_value, str) and isinstance(value, str):
                return bool(re.search(value, var_value))
            return False
        else:
            self.logger.warning(f"Unknown condition operator: {operator}")
            return False
    
    def _fallback_template(self, context: Dict[str, Any], bot_type: str) -> str:
        """
        Generate a fallback response when a template is not found.
        
        Args:
            context: Context variables
            bot_type: Type of bot
            
        Returns:
            Fallback response
        """
        # Extract key information from context
        query = context.get("query", "")
        answer = context.get("answer", "")
        sources = context.get("sources", [])
        
        # Create basic response
        if answer:
            response = answer
        else:
            # Generate simple response based on query
            if bot_type == "consultancy":
                response = f"Based on your question about {query}, I'd recommend consulting with our business experts."
            elif bot_type == "sales":
                response = f"Thank you for your interest in {query}. I'd be happy to provide more information about our products."
            elif bot_type == "support":
                response = f"I understand you're having an issue with {query}. Let me help you resolve that."
            else:
                response = f"Thank you for your question about {query}. I'll do my best to assist you."
        
        # Add sources if available
        if sources:
            response += "\n\nSources:"
            for i, source in enumerate(sources, 1):
                source_text = source.get("text", "")
                source_name = source.get("name", f"Source {i}")
                if source_text:
                    response += f"\n{i}. {source_name}: {source_text[:100]}..."
        
        return response
    
    def get_available_templates(self, bot_type: str) -> List[str]:
        """
        Get available templates for a specific bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            List of available template names
        """
        bot_templates = self.templates.get(bot_type, {})
        return list(bot_templates.keys())
    
    def format_output(
        self, 
        content: Union[str, Dict[str, Any]], 
        format_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format output in specified format.
        
        Args:
            content: Content to format
            format_type: Format type (text, markdown, json, html)
            context: Optional context for additional formatting
            
        Returns:
            Formatted output
        """
        context = context or {}
        
        if isinstance(content, dict):
            # Convert dict to appropriate format
            if format_type == "json":
                return json.dumps(content, indent=2)
            elif format_type == "markdown":
                return self._dict_to_markdown(content)
            elif format_type == "html":
                return self._dict_to_html(content)
            else:
                # Default to text
                return self._dict_to_text(content)
        else:
            # String content
            if format_type == "markdown":
                # Basic markdown enhancement
                return content
            elif format_type == "html":
                # Convert to simple HTML
                return f"<p>{content.replace('\n\n', '</p><p>').replace('\n', '<br>')}</p>"
            elif format_type == "json":
                # Wrap in a JSON object
                return json.dumps({"response": content}, indent=2)
            else:
                # Return as plain text
                return content
    
    def _dict_to_markdown(self, data: Dict[str, Any]) -> str:
        """Convert dictionary to Markdown format."""
        lines = []
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"## {key}")
                lines.append(self._dict_to_markdown(value))
            elif isinstance(value, list):
                lines.append(f"## {key}")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(self._dict_to_markdown(item))
                    else:
                        lines.append(f"- {item}")
            else:
                lines.append(f"**{key}**: {value}")
        
        return "\n\n".join(lines)
    
    def _dict_to_html(self, data: Dict[str, Any]) -> str:
        """Convert dictionary to HTML format."""
        lines = ["<div>"]
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"<h2>{key}</h2>")
                lines.append(self._dict_to_html(value))
            elif isinstance(value, list):
                lines.append(f"<h2>{key}</h2><ul>")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f"<li>{self._dict_to_html(item)}</li>")
                    else:
                        lines.append(f"<li>{item}</li>")
                lines.append("</ul>")
            else:
                lines.append(f"<p><strong>{key}:</strong> {value}</p>")
        
        lines.append("</div>")
        return "\n".join(lines)
    
    def _dict_to_text(self, data: Dict[str, Any]) -> str:
        """Convert dictionary to plain text format."""
        lines = []
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for sub_key, sub_value in value.items():
                    lines.append(f"  {sub_key}: {sub_value}")
            elif isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    if isinstance(item, dict):
                        for sub_key, sub_value in item.items():
                            lines.append(f"  - {sub_key}: {sub_value}")
                    else:
                        lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {value}")
        
        return "\n".join(lines)


# Create singleton instance
template_renderer = TemplateRenderer() 