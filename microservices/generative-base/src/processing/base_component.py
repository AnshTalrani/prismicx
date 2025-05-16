"""
Base Component Module for Generative Base

This module provides the BaseComponent class which serves as the foundation
for all processing components in the generative system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import structlog
import time

# Import the template renderer
from ..common.template_renderer import TemplateRenderer


class BaseComponent(ABC):
    """
    Abstract base class for all processing components.
    
    Components are the building blocks of processing pipelines, each responsible
    for a specific generative task. Subclasses must implement the process and
    validate_config methods.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize the component.
        
        Args:
            name: The name of the component instance
            config: Configuration parameters for the component
        """
        self.name = name
        self.config = config
        self.logger = structlog.get_logger(name=f"component.{name}")
        self.prompt_templates = {}
        self.template_renderer = TemplateRenderer()
        self.continue_on_error = self.config.get('continue_on_error', False)
        self.validate_config()
    
    @abstractmethod
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the context and return the updated context.
        
        This is the main method that subclasses must implement to perform
        their specific processing logic.
        
        Args:
            context: The context to process
            
        Returns:
            The processed context with updated data and results
            
        Raises:
            ProcessingError: If processing fails
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> None:
        """
        Validate the component configuration.
        
        This method should check that all required configuration parameters
        are present and have valid values.
        
        Raises:
            ValueError: If the configuration is invalid
        """
        pass
    
    def validate_input(self, context: Dict[str, Any]) -> bool:
        """
        Validate the input context before processing.
        
        Args:
            context: The context to validate
            
        Returns:
            True if the input is valid, False otherwise
            
        Raises:
            ValueError: If the input is invalid and validation is strict
        """
        # Base implementation checks for data field
        if "data" not in context:
            if not self.get_config_value("allow_missing_data", False):
                raise ValueError(f"Component {self.name}: Context missing 'data' field")
            return False
        return True
    
    async def preprocess(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform any preprocessing before the main processing logic.
        
        Args:
            context: The context to preprocess
            
        Returns:
            The preprocessed context
        """
        # Base implementation just returns the context unchanged
        return context
    
    async def postprocess(self, context: Dict[str, Any], result: Any) -> Dict[str, Any]:
        """
        Perform any postprocessing after the main processing logic.
        
        Args:
            context: The original context
            result: The result from the main processing
            
        Returns:
            The postprocessed context with integrated results
        """
        # Base implementation adds the result to the context
        updated_context = context.copy()
        
        # Ensure _results exists
        if "_results" not in updated_context:
            updated_context["_results"] = {}
        
        # Store the result in the context
        updated_context["_results"][self.name] = result
        
        return updated_context
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value with an optional default.
        
        Args:
            key: The configuration key to look up
            default: Default value if the key is not found
            
        Returns:
            The configuration value or the default
        """
        return self.config.get(key, default)
    
    def get_required_config_value(self, key: str) -> Any:
        """
        Get a required configuration value.
        
        Args:
            key: The configuration key to look up
            
        Returns:
            The configuration value
            
        Raises:
            ValueError: If the key is not in the configuration
        """
        if key not in self.config:
            raise ValueError(f"Component {self.name}: Required configuration key '{key}' not found")
        return self.config[key]
    
    def set_prompt_templates(self, templates: Dict[str, str]) -> None:
        """
        Set prompt templates for the component.
        
        Args:
            templates: Dictionary of template names to template strings
        """
        self.prompt_templates = templates
        self.logger.debug(f"Set {len(templates)} prompt templates", 
                         component=self.name,
                         template_names=list(templates.keys()))
    
    def get_prompt_template(self, template_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a prompt template by name.
        
        Args:
            template_name: Name of the prompt template
            default: Default value if template not found
            
        Returns:
            The prompt template string or None if not found
        """
        return self.prompt_templates.get(template_name, default)
    
    def render_prompt(self, template_name: str, context: Dict[str, Any], 
                     parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Render a prompt template with the provided context and parameters.
        
        Args:
            template_name: Name of the prompt template to render
            context: Processing context to use for variable substitution
            parameters: Optional additional parameters for the template
            
        Returns:
            The rendered prompt string
            
        Raises:
            ValueError: If the template is not found
        """
        template = self.get_prompt_template(template_name)
        if not template:
            raise ValueError(f"Component {self.name}: Prompt template '{template_name}' not found")
        
        return self.template_renderer.render_prompt(template, context, parameters)
    
    def get_previous_result(self, context: Dict[str, Any], component_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the result of a previous component from the context.
        
        Args:
            context: The processing context
            component_name: Name of the component whose result to retrieve
            
        Returns:
            The component's result or None if not found
        """
        if "_results" in context and component_name in context["_results"]:
            return context["_results"][component_name]
        return None
    
    def log_timing(self, operation: str, start_time: float) -> None:
        """
        Log the time taken for an operation.
        
        Args:
            operation: Description of the operation
            start_time: Start time from time.time()
        """
        duration_ms = int((time.time() - start_time) * 1000)
        self.logger.debug(f"{operation} completed", 
                         component=self.name,
                         duration_ms=duration_ms)
    
    def merge_results(self, context: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge generative results into the context.
        
        Args:
            context: The context to update
            results: Results to add to the context
            
        Returns:
            Updated context with merged results
        """
        updated_context = context.copy()
        
        # Ensure _results exists
        if "_results" not in updated_context:
            updated_context["_results"] = {}
            
        # Merge the new results with any existing results for this component
        if self.name in updated_context["_results"]:
            # If existing results is a dict, update it
            if isinstance(updated_context["_results"][self.name], dict) and isinstance(results, dict):
                updated_context["_results"][self.name].update(results)
            else:
                # Otherwise replace with new results
                updated_context["_results"][self.name] = results
        else:
            # No existing results, just store the new ones
            updated_context["_results"][self.name] = results
            
        return updated_context
    
    def extract_tags(self, results: Dict[str, Any]) -> List[str]:
        """
        Extract tags from generative results.
        
        Args:
            results: Generative results
            
        Returns:
            List of extracted tags
        """
        # Default implementation returns empty list
        # Components should override this to implement specific tag extraction logic
        return [] 