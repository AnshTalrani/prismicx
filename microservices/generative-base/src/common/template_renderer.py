"""
Template Renderer Module

This module provides functionality for rendering prompt templates with variable
substitution, conditionals, and loops.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Union, Callable
import jinja2

logger = logging.getLogger(__name__)

class TemplateRenderer:
    """
    Renders templates with variable substitution and control structures.
    
    Uses Jinja2 for advanced template rendering with support for:
    - Variable substitution
    - Conditionals (if/else)
    - Loops (for/each)
    - Filters and formatting
    """
    
    def __init__(self):
        """Initialize the template renderer with custom filters and extensions."""
        # Create Jinja2 environment
        self.env = jinja2.Environment(
            autoescape=False,  # No HTML escaping for prompt templates
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        self._register_custom_filters()
        
        logger.info("Template renderer initialized")
    
    def _register_custom_filters(self):
        """Register custom filters for use in templates."""
        # Text processing filters
        self.env.filters['truncate_words'] = self._truncate_words
        self.env.filters['capitalize_first'] = self._capitalize_first
        self.env.filters['list_to_text'] = self._list_to_text
        
        # Data formatting filters
        self.env.filters['format_number'] = self._format_number
        
        logger.debug("Custom filters registered")
    
    def render_template(self, template_str: str, variables: Dict[str, Any]) -> str:
        """
        Render a template string with the provided variables.
        
        Args:
            template_str: The template string to render
            variables: Dictionary of variables to use in the template
            
        Returns:
            The rendered template string
        """
        try:
            # Parse the template
            template = self.env.from_string(template_str)
            
            # Render with variables
            rendered = template.render(**variables)
            
            return rendered
            
        except jinja2.exceptions.TemplateError as e:
            logger.error(f"Template rendering error: {str(e)}")
            # Return a safe fallback or the original with error note
            return f"Error rendering template: {str(e)}\n\nOriginal template:\n{template_str}"
        
        except Exception as e:
            logger.error(f"Unexpected error in template rendering: {str(e)}")
            return f"Error: {str(e)}"
    
    def render_prompt(self, prompt_template: str, context: Dict[str, Any], 
                     parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Render a prompt template with context and parameters.
        
        Args:
            prompt_template: The prompt template string
            context: The processing context (data)
            parameters: Optional additional parameters
            
        Returns:
            The rendered prompt string
        """
        # Combine context and parameters
        variables = {}
        variables.update(context)
        
        # Add parameters under a 'parameters' key if provided
        if parameters:
            variables['parameters'] = parameters
        
        return self.render_template(prompt_template, variables)
    
    # Custom filter implementations
    
    def _truncate_words(self, value: str, length: int = 30, suffix: str = '...') -> str:
        """Truncate text to a specified number of words."""
        if not value:
            return ""
            
        words = value.split()
        if len(words) <= length:
            return value
            
        return ' '.join(words[:length]) + suffix
    
    def _capitalize_first(self, value: str) -> str:
        """Capitalize only the first character of the string."""
        if not value:
            return ""
            
        return value[0].upper() + value[1:]
    
    def _list_to_text(self, value: List[str], conjunction: str = 'and') -> str:
        """Convert a list to a natural language enumeration."""
        if not value:
            return ""
            
        if len(value) == 1:
            return value[0]
            
        if len(value) == 2:
            return f"{value[0]} {conjunction} {value[1]}"
            
        return ', '.join(value[:-1]) + f', {conjunction} ' + value[-1]
    
    def _format_number(self, value: Union[int, float], precision: int = 2) -> str:
        """Format a number with specified precision."""
        if isinstance(value, int):
            return str(value)
            
        if isinstance(value, float):
            return f"{value:.{precision}f}"
            
        return str(value) 