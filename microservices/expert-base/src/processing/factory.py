"""
Factory for creating processing pipelines.

This module provides a factory for creating processing pipelines based on
configuration provided by expert modes.
"""

from typing import Dict, Any, Optional
from loguru import logger

class ProcessorFactory:
    """
    Factory for creating processing pipelines.
    
    This class creates and configures processing pipelines based on the
    processor type specified in the expert mode configuration.
    """
    
    def __init__(self, model_provider):
        """
        Initialize the ProcessorFactory.
        
        Args:
            model_provider: The model provider for LLM inference.
        """
        self.model_provider = model_provider
        self.processors = {
            "content_generation_pipeline": self._create_generation_pipeline,
            "content_analysis_pipeline": self._create_analysis_pipeline,
            "content_review_pipeline": self._create_review_pipeline,
        }
        logger.info("Initialized ProcessorFactory")
    
    def create_processor(self, processor_id: str):
        """
        Create a processor pipeline based on the processor ID.
        
        Args:
            processor_id: The ID of the processor to create.
            
        Returns:
            A processor instance.
            
        Raises:
            ValueError: If the processor ID is not supported.
        """
        if processor_id not in self.processors:
            raise ValueError(f"Unsupported processor ID: {processor_id}")
            
        return self.processors[processor_id]()
    
    def _create_generation_pipeline(self):
        """
        Create a content generation pipeline.
        
        Returns:
            A content generation pipeline.
        """
        from src.processing.pipelines import ContentGenerationPipeline
        return ContentGenerationPipeline(self.model_provider)
    
    def _create_analysis_pipeline(self):
        """
        Create a content analysis pipeline.
        
        Returns:
            A content analysis pipeline.
        """
        from src.processing.pipelines import ContentAnalysisPipeline
        return ContentAnalysisPipeline(self.model_provider)
    
    def _create_review_pipeline(self):
        """
        Create a content review pipeline.
        
        Returns:
            A content review pipeline.
        """
        from src.processing.pipelines import ContentReviewPipeline
        return ContentReviewPipeline(self.model_provider) 