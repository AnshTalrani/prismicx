"""
Base component module providing the core component functionality.

This module contains the BaseComponent class which serves as the foundation
for all processing components in the analysis-base microservice.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Type
import logging
import uuid

class BaseComponent(ABC):
    """
    Base class for all processing components in the analysis-base microservice.
    
    This class provides core functionality for configuration loading, 
    decision tree application, and result merging. All analysis components
    should inherit from this class.
    
    Attributes:
        component_id (str): Unique identifier for the component
        logger (logging.Logger): Logger for the component
        configuration (Dict[str, Any]): Component configuration
    """
    
    def __init__(
        self, 
        component_id: Optional[str] = None, 
        configuration: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the base component.
        
        Args:
            component_id: Unique identifier for the component. If not provided,
                a UUID will be generated.
            configuration: Component configuration. If not provided, will be
                loaded using load_configuration().
        """
        self.component_id = component_id or str(uuid.uuid4())
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{self.component_id}")
        self.configuration = configuration or {}
        
        # Validate configuration if provided
        if self.configuration:
            self.validate_config()
    
    def validate_config(self) -> None:
        """
        Validate the component configuration.
        
        This method should be overridden by subclasses to perform
        component-specific configuration validation.
        
        Raises:
            ValueError: If the configuration is invalid.
        """
        pass
    
    def load_configuration(self) -> Dict[str, Any]:
        """
        Load component configuration from the configuration source.
        
        This method can be overridden by subclasses to implement
        component-specific configuration loading logic.
        
        Returns:
            Dict[str, Any]: The loaded configuration
        """
        return self.configuration or {}
    
    def load_model_specification(self, model_name: str) -> Dict[str, Any]:
        """
        Load a model specification from the specifications directory.
        
        Args:
            model_name: Name of the model specification to load
            
        Returns:
            Dict[str, Any]: The loaded model specification
            
        Raises:
            FileNotFoundError: If the specification does not exist
        """
        # This is a placeholder implementation. In a real implementation,
        # this would load specifications from files or a database.
        self.logger.debug(f"Loading model specification: {model_name}")
        return {}
    
    def apply_decision_tree(self, context: Dict[str, Any]) -> str:
        """
        Apply a decision tree to determine the processing strategy.
        
        Args:
            context: The context to process
            
        Returns:
            str: The selected processing strategy
        """
        # This is a placeholder implementation. In a real implementation,
        # this would load and apply decision trees from specifications.
        self.logger.debug("Applying decision tree")
        return "default"
    
    def merge_results(self, context: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge processing results into the context.
        
        Args:
            context: The original context
            results: The processing results to merge
            
        Returns:
            Dict[str, Any]: The updated context with merged results
        """
        merged = context.copy()
        
        # Merge results at the top level
        for key, value in results.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # If both are dictionaries, merge them recursively
                merged[key] = self._merge_dicts(merged[key], value)
            else:
                # Otherwise, overwrite the value
                merged[key] = value
        
        return merged
    
    def _merge_dicts(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge two dictionaries.
        
        Args:
            dict1: Base dictionary
            dict2: Dictionary to merge into base
            
        Returns:
            Dict[str, Any]: Merged dictionary
        """
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # If both values are dictionaries, merge them recursively
                result[key] = self._merge_dicts(result[key], value)
            else:
                # Otherwise, use the value from dict2
                result[key] = value
                
        return result
    
    @abstractmethod
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the provided context.
        
        This method must be implemented by all component subclasses
        to define their specific processing logic.
        
        Args:
            context: The context to process
            
        Returns:
            Dict[str, Any]: The processed context
        """
        pass

    async def process_batch(self, contexts: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """
        Process a batch of contexts.
        
        Default implementation processes each context individually using the
        process method. Components that can optimize batch processing should
        override this method.
        
        Args:
            contexts: List of context documents to process.
                     Access previous component results via context["_temp_results"]
            
        Returns:
            Optional list of processing results in the same order as contexts,
            or None if no results
        """
        # Default implementation processes each context individually
        results = []
        for context in contexts:
            try:
                result = await self.process(context)
                results.append(result)
            except Exception as e:
                self.logger.error("Error processing context in batch", 
                                context_id=context.get("id", "unknown"), 
                                error=str(e))
                if self.continue_on_error:
                    results.append(None)
                else:
                    raise
        return results
    
    def validate_input(self, context: Dict[str, Any]) -> bool:
        """
        Validate that the context contains all required fields for this component.
        
        Args:
            context: The context document to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Default implementation considers all contexts valid
        # Components should override this to enforce specific requirements
        return True
    
    def get_previous_result(self, context: Dict[str, Any], component_name: str) -> Optional[Dict[str, Any]]:
        """
        Get result from a previous component in the pipeline.
        
        Args:
            context: The context document
            component_name: Name of the component whose results to retrieve
            
        Returns:
            The previous component's result or None if not found
        """
        if "_temp_results" in context and component_name in context["_temp_results"]:
            return context["_temp_results"][component_name]
        return None
        
    def handle_error(self, context: Dict[str, Any], error: Exception) -> Dict[str, Any]:
        """
        Handle component-specific errors during processing.
        
        Args:
            context: The context document
            error: The exception that occurred
            
        Returns:
            Updated context with error information
            
        Raises:
            Exception: Re-raises the error if not handling it
        """
        self.logger.error("Error processing context", 
                         context_id=context.get("id", "unknown"), 
                         error=str(error))
        
        # Add error information to context
        if "errors" not in context:
            context["errors"] = []
            
        context["errors"].append({
            "component": self.name,
            "error": str(error),
            "type": error.__class__.__name__
        })
        
        # Re-raise if not configured to continue on error
        if not self.continue_on_error:
            raise error
            
        return context 