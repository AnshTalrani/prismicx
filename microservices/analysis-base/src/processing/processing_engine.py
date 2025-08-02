"""
Processing Engine Module for Analysis Base

This module provides the ProcessingEngine class which coordinates the processing
of analysis contexts through various components and pipelines.
"""

import time
from typing import Dict, List, Any, Optional, Tuple
import structlog
from datetime import datetime

from src.config.settings import Settings
from src.processing.component_registry import ComponentRegistry
from src.processing.pipeline import Pipeline, PipelineFactory
from src.common.exceptions import ProcessingError


class ProcessingEngine:
    """
    Processing engine for executing analysis pipelines.
    
    The engine is responsible for creating and executing pipelines based on context
    configuration, managing the flow of data between components, and handling
    processing errors.
    """
    
    def __init__(
        self,
        settings: Settings,
        component_registry: ComponentRegistry,
        pipeline_factory: PipelineFactory
    ):
        """
        Initialize the processing engine.
        
        Args:
            settings: Application settings
            component_registry: Registry of available components
            pipeline_factory: Factory for creating processing pipelines
        """
        self.logger = structlog.get_logger(name="processing_engine")
        self.settings = settings
        self.component_registry = component_registry
        self.pipeline_factory = pipeline_factory
    
    async def process_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single context.
        
        Args:
            context: The context to process
            
        Returns:
            Dict[str, Any]: Processing results
            
        Raises:
            ProcessingError: If processing fails
        """
        context_id = context.get("_id", "unknown")
        context_type = context.get("type", "default")
        pipeline_id = context.get("pipeline_id")
        
        self.logger.info("Processing context", context_id=context_id, type=context_type)
        
        start_time = time.time()
        
        try:
            # Create pipeline based on context configuration
            pipeline = await self._create_pipeline(context)
            
            # Execute the pipeline
            result, metrics = await self._execute_pipeline(pipeline, context)
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Add processing metrics to result
            result["_metrics"] = {
                **metrics,
                "total_processing_time_ms": processing_time_ms
            }
            
            self.logger.info(
                "Context processed successfully",
                context_id=context_id,
                processing_time_ms=processing_time_ms
            )
            
            return result
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            self.logger.error(
                "Error processing context",
                context_id=context_id,
                error=str(e),
                processing_time_ms=processing_time_ms
            )
            
            # Determine if retry is recommended
            retry_recommended = self._should_retry_error(e)
            
            # Create meaningful error message
            if isinstance(e, ProcessingError):
                raise e
            else:
                raise ProcessingError(
                    message=f"Unexpected error processing context: {str(e)}",
                    component="processing_engine",
                    retry_recommended=retry_recommended,
                    original_error=e
                )
    
    async def _create_pipeline(self, context: Dict[str, Any]) -> Pipeline:
        """
        Create a pipeline for processing the context.
        
        Args:
            context: The context to process
            
        Returns:
            Pipeline: The configured pipeline
            
        Raises:
            ProcessingError: If pipeline creation fails
        """
        try:
            # Get pipeline configuration
            pipeline_id = context.get("pipeline_id")
            pipeline_config = context.get("pipeline_config", {})
            context_type = context.get("type", "default")
            
            if pipeline_id:
                # Create pipeline from predefined configuration
                pipeline = await self.pipeline_factory.create_pipeline_by_id(pipeline_id)
            else:
                # Create pipeline from context configuration or default for the type
                pipeline = await self.pipeline_factory.create_pipeline(
                    context_type,
                    pipeline_config
                )
            
            return pipeline
        
        except Exception as e:
            self.logger.error(
                "Error creating pipeline",
                context_id=context.get("_id", "unknown"),
                error=str(e)
            )
            raise ProcessingError(
                message=f"Failed to create processing pipeline: {str(e)}",
                component="pipeline_factory",
                retry_recommended=False,
                original_error=e
            )
    
    async def _execute_pipeline(
        self, 
        pipeline: Pipeline, 
        context: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Execute a pipeline on a context.
        
        Args:
            pipeline: The pipeline to execute
            context: The context to process
            
        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: (Processing results, Metrics)
            
        Raises:
            ProcessingError: If pipeline execution fails
        """
        try:
            # Prepare context for processing
            processing_context = self._prepare_context(context)
            
            # Execute the pipeline
            result = await pipeline.execute(processing_context)
            
            # Extract metrics
            metrics = {
                "component_timings": pipeline.get_component_timings(),
                "component_count": len(pipeline.components)
            }
            
            return result, metrics
            
        except ProcessingError as e:
            # Pass through component-specific errors
            raise e
        except Exception as e:
            # Wrap unexpected errors
            raise ProcessingError(
                message=f"Pipeline execution failed: {str(e)}",
                component="processing_engine",
                retry_recommended=self._should_retry_error(e),
                original_error=e
            )
    
    def _prepare_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare context for processing by creating a copy and adding required fields.
        
        Args:
            context: The original context
            
        Returns:
            Dict[str, Any]: The prepared context
        """
        # Create a copy to avoid modifying the original
        processing_context = context.copy()
        
        # Ensure data field exists
        if "data" not in processing_context:
            processing_context["data"] = {}
            
        # Add processing metadata
        processing_context["_processing"] = {
            "started_at": datetime.utcnow().isoformat(),
            "engine_version": self.settings.version
        }
        
        # Add empty results container
        processing_context["_results"] = {}
        
        return processing_context
    
    def _should_retry_error(self, error: Exception) -> bool:
        """
        Determine if an error should trigger a retry.
        
        Args:
            error: The error to evaluate
            
        Returns:
            bool: True if retry is recommended, False otherwise
        """
        # ProcessingError already has retry recommendation
        if isinstance(error, ProcessingError):
            return error.retry_recommended
            
        # Default retry rules for common errors
        if isinstance(error, (TimeoutError, ConnectionError)):
            # Network or timeout errors can often be resolved with a retry
            return True
            
        # Check error type against configurable list of retryable errors
        error_type = type(error).__name__
        retryable_errors = self.settings.processing.retryable_errors
        
        return error_type in retryable_errors 