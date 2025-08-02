"""
Base component interface for processing pipeline components.

This module defines the base interface that all processing components must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseComponent(ABC):
    """
    Base interface for all processing pipeline components.
    
    All processing components must implement this interface to be used
    in processing pipelines.
    """
    
    @abstractmethod
    async def process(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the content with the given context.
        
        Args:
            content: The content to process.
            context: The processing context, including configuration and knowledge.
            
        Returns:
            A dictionary containing the processing result.
        """
        pass
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> bool:
        """
        Validate the configuration for this component.
        
        Args:
            config: The configuration to validate.
            
        Returns:
            True if the configuration is valid, False otherwise.
        """
        pass


class ContentEnhancementComponent(BaseComponent):
    """
    Base class for content enhancement components.
    
    Content enhancement components improve or generate content based on
    the input content and context.
    """
    
    async def process(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance the content with the given context.
        
        Args:
            content: The content to enhance.
            context: The processing context.
            
        Returns:
            A dictionary containing the enhanced content.
        """
        raise NotImplementedError("Subclasses must implement process()")
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """
        Validate the configuration for this component.
        
        Args:
            config: The configuration to validate.
            
        Returns:
            True if the configuration is valid, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement validate()")


class ContentAnalysisComponent(BaseComponent):
    """
    Base class for content analysis components.
    
    Content analysis components analyze content and provide feedback or metrics.
    """
    
    async def process(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the content with the given context.
        
        Args:
            content: The content to analyze.
            context: The processing context.
            
        Returns:
            A dictionary containing the analysis results.
        """
        raise NotImplementedError("Subclasses must implement process()")
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """
        Validate the configuration for this component.
        
        Args:
            config: The configuration to validate.
            
        Returns:
            True if the configuration is valid, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement validate()")


class ContentReviewComponent(BaseComponent):
    """
    Base class for content review components.
    
    Content review components review content and provide feedback on quality,
    compliance, etc.
    """
    
    async def process(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review the content with the given context.
        
        Args:
            content: The content to review.
            context: The processing context.
            
        Returns:
            A dictionary containing the review results.
        """
        raise NotImplementedError("Subclasses must implement process()")
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """
        Validate the configuration for this component.
        
        Args:
            config: The configuration to validate.
            
        Returns:
            True if the configuration is valid, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement validate()") 