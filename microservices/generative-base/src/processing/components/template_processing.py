"""
Template Processing Component

This component handles template-based content generation for contexts.
It processes templates with variables and generates content based on the
template definition and context data.
"""

import asyncio
import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime
import jinja2

from .base import BaseComponent

# Configure structured logging
logger = structlog.get_logger(__name__)

class TemplateProcessingComponent(BaseComponent):
    """
    Component for processing templates and generating content.
    
    This component:
    - Retrieves template definitions
    - Processes template variables using context data
    - Renders content using Jinja2 templates
    - Handles conditional template logic
    """
    
    def __init__(
        self,
        template_cache: Dict[str, Any] = None,
        continue_on_error: bool = False
    ):
        """
        Initialize the template processing component.
        
        Args:
            template_cache: Optional cache of template definitions
            continue_on_error: Whether to continue pipeline processing if this 
                component fails (default: False)
        """
        super().__init__(continue_on_error)
        self.template_cache = template_cache or {}
        self.jinja_env = jinja2.Environment(
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters and functions
        self._register_custom_filters()
        
        logger.info("Template processing component initialized")
    
    def _register_custom_filters(self):
        """Register custom Jinja2 filters and functions."""
        # Register date/time filters
        self.jinja_env.filters["date"] = lambda dt, fmt="%Y-%m-%d": datetime.fromisoformat(dt).strftime(fmt) if dt else ""
        self.jinja_env.filters["time"] = lambda dt, fmt="%H:%M": datetime.fromisoformat(dt).strftime(fmt) if dt else ""
        
        # Register text processing filters
        self.jinja_env.filters["capitalize_first"] = lambda s: s[0].upper() + s[1:] if s else ""
        self.jinja_env.filters["truncate_words"] = lambda s, n: " ".join(s.split()[:n]) + "..." if len(s.split()) > n else s
    
    async def process(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single context with template rendering.
        
        Args:
            context: The context document to process
            
        Returns:
            Dict with template processing results
        """
        if not self.validate_input(context):
            raise ValueError(f"Invalid context for template processing: missing required fields")
        
        context_id = str(context.get("_id", "unknown"))
        template_id = context.get("template_id")
        template_vars = context.get("variables", {})
        
        # Check if we should use the output of a previous component
        # Example: If we depend on a previous component's output
        previous_component = "SomeDataPreparationComponent"  # Replace with actual component name when needed
        previous_result = self.get_previous_result(context, previous_component)
        if previous_result and "enhanced_variables" in previous_result:
            # Merge with or override template_vars with the previous component's output
            template_vars.update(previous_result["enhanced_variables"])
        
        logger.debug(
            "Processing template",
            context_id=context_id,
            template_id=template_id
        )
        
        # Get template definition
        template_def = await self._get_template_definition(template_id)
        
        # Populate any default variables not provided in context
        merged_vars = {
            **template_def.get("default_variables", {}),
            **template_vars
        }
        
        # Process template parts
        result = {
            "template_id": template_id,
            "parts": {}
        }
        
        for part_name, part_template in template_def.get("parts", {}).items():
            try:
                rendered_content = self._render_template(part_template, merged_vars)
                result["parts"][part_name] = rendered_content
                
                logger.debug(
                    "Rendered template part",
                    context_id=context_id,
                    template_id=template_id,
                    part=part_name,
                    content_length=len(rendered_content)
                )
                
            except Exception as e:
                error_msg = f"Failed to render template part {part_name}: {str(e)}"
                logger.error(
                    "Template rendering error",
                    context_id=context_id,
                    template_id=template_id,
                    part=part_name,
                    error=str(e),
                    exc_info=True
                )
                raise ValueError(error_msg)
        
        return result
    
    async def process_batch(self, contexts: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """
        Process a batch of contexts with template rendering.
        
        This implementation optimizes by loading template definitions only once
        for contexts that share the same template_id.
        
        Args:
            contexts: List of context documents to process
            
        Returns:
            List of template processing results
        """
        if not contexts:
            return []
        
        # Group contexts by template_id for more efficient processing
        template_groups = {}
        for context in contexts:
            if not self.validate_input(context):
                raise ValueError(f"Invalid context for template processing: missing required fields")
            
            template_id = context.get("template_id")
            if template_id not in template_groups:
                template_groups[template_id] = []
            template_groups[template_id].append(context)
        
        # Process each template group
        results = [None] * len(contexts)
        context_map = {str(c.get("_id")): i for i, c in enumerate(contexts)}
        
        for template_id, template_contexts in template_groups.items():
            # Get template definition (just once per template)
            template_def = await self._get_template_definition(template_id)
            
            # Process each context with the template
            for context in template_contexts:
                context_id = str(context.get("_id", "unknown"))
                template_vars = context.get("variables", {})
                
                # Check if we should use the output of a previous component
                previous_component = "SomeDataPreparationComponent"  # Replace with actual component name when needed
                previous_result = self.get_previous_result(context, previous_component)
                if previous_result and "enhanced_variables" in previous_result:
                    # Merge with or override template_vars with the previous component's output
                    template_vars.update(previous_result["enhanced_variables"])
                
                # Populate default variables
                merged_vars = {
                    **template_def.get("default_variables", {}),
                    **template_vars
                }
                
                # Process template parts
                result = {
                    "template_id": template_id,
                    "parts": {}
                }
                
                try:
                    for part_name, part_template in template_def.get("parts", {}).items():
                        rendered_content = self._render_template(part_template, merged_vars)
                        result["parts"][part_name] = rendered_content
                    
                    # Store result in correct position
                    results[context_map[context_id]] = result
                    
                except Exception as e:
                    logger.error(
                        "Template batch processing error",
                        context_id=context_id,
                        template_id=template_id,
                        error=str(e)
                    )
                    
                    # Store error result
                    error_result = {
                        "template_id": template_id,
                        "error": str(e),
                        "parts": {}
                    }
                    results[context_map[context_id]] = error_result
                    
                    # If we should stop on errors, raise
                    if not self.continue_on_error:
                        raise
        
        return results
    
    def validate_input(self, context: Dict[str, Any]) -> bool:
        """
        Validate that the context contains all required fields for template processing.
        
        Args:
            context: The context document to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["template_id"]
        return all(field in context for field in required_fields)
    
    async def _get_template_definition(self, template_id: str) -> Dict[str, Any]:
        """
        Get template definition from cache or database.
        
        Args:
            template_id: The template identifier
            
        Returns:
            Template definition
        """
        # Check cache first
        if template_id in self.template_cache:
            return self.template_cache[template_id]
        
        # This would normally be retrieved from a repository
        # For this example, we'll use a simple default template
        # In a real implementation, this would be a database query
        
        template_def = {
            "template_id": template_id,
            "name": f"Template {template_id}",
            "default_variables": {
                "greeting": "Hello",
                "subject": "world",
                "timestamp": datetime.utcnow().isoformat()
            },
            "parts": {
                "subject": "{{ variables.subject|capitalize_first }} Update",
                "body": """
                {{ variables.greeting }}, {{ variables.subject }}!
                
                This is a template-generated message created at {{ variables.timestamp|date }}.
                
                {% if variables.items %}
                Your items:
                {% for item in variables.items %}
                - {{ item.name }}: {{ item.value }}
                {% endfor %}
                {% else %}
                No items to display.
                {% endif %}
                
                Regards,
                The System
                """
            }
        }
        
        # Store in cache for future use
        self.template_cache[template_id] = template_def
        
        return template_def
    
    def _render_template(self, template_str: str, variables: Dict[str, Any]) -> str:
        """
        Render a template string with the provided variables.
        
        Args:
            template_str: Jinja2 template string
            variables: Variables to use for rendering
            
        Returns:
            Rendered template string
        """
        template = self.jinja_env.from_string(template_str)
        return template.render(variables=variables)