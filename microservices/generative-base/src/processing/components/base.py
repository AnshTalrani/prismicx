"""
Base Component Module

This module defines the base component class that all processing 
components must inherit from.
"""

import abc
from typing import Dict, List, Any, Optional, Union


class BaseComponent(abc.ABC):
    """
    Abstract base class for all processing components.
    
    Components are the building blocks of the processing pipeline and
    perform specific operations on context data. Each component can
    process a single context or a batch of contexts, and can be
    configured to continue or halt processing on errors.
    """
    
    def __init__(self, continue_on_error: bool = False):
        """
        Initialize the component.
        
        Args:
            continue_on_error: Whether to continue pipeline processing if this 
                component fails (default: False)
        """
        self.continue_on_error = continue_on_error
    
    @abc.abstractmethod
    async def process(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single context.
        
        This method must be implemented by all component classes to define
        the specific processing logic for a single context.
        
        Args:
            context: The context document to process. 
                    Access previous component results via context["_temp_results"]
            
        Returns:
            Optional dict with processing results, or None if no results
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
            result = await self.process(context)
            results.append(result)
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