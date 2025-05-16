"""
Processing Pipeline Module

This module provides the pipeline implementation for processing contexts
through a series of components.
"""

import asyncio
import structlog
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime

from ..adapters.repository import Repository
from ..common.config import Settings
from .base_component import BaseComponent

# Configure structured logging
logger = structlog.get_logger(__name__)

class ProcessingPipeline:
    """
    Processing pipeline that executes a series of components on context data.
    
    This class:
    - Coordinates the execution of processing components
    - Handles both single context and batch processing
    - Tracks processing metrics and performance
    """
    
    def __init__(
        self,
        components: List[BaseComponent],
        repository: Repository,
        settings: Settings
    ):
        """
        Initialize the processing pipeline.
        
        Args:
            components: List of processing components to execute in sequence
            repository: Data repository for storing results
            settings: Application configuration settings
        """
        self.components = components
        self.repository = repository
        self.settings = settings
        
        # Set up metrics
        self.metrics = {
            "processed_count": 0,
            "success_count": 0,
            "error_count": 0,
            "avg_processing_time_ms": 0
        }
        
        logger.info(
            "Processing pipeline initialized",
            component_count=len(components),
            component_names=[c.__class__.__name__ for c in components]
        )
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single context through the pipeline.
        
        Args:
            context: The context document to process
            
        Returns:
            The processed context with final result
        """
        start_time = datetime.utcnow()
        context_id = str(context.get("_id", "unknown"))
        template_id = context.get("template_id", "unknown")
        
        logger.info(
            "Starting context processing",
            context_id=context_id,
            template_id=template_id
        )
        
        # Create a working copy with additional fields for processing
        working_context = context.copy()
        working_context["processing_start"] = start_time.isoformat()
        working_context["status"] = "processing"
        working_context["_temp_results"] = {}  # Temporary storage for intermediate results
        working_context["errors"] = []
        
        try:
            # Run the context through each component in sequence
            final_result = None
            for i, component in enumerate(self.components):
                component_name = component.__class__.__name__
                component_start = datetime.utcnow()
                
                logger.debug(
                    "Running component",
                    context_id=context_id,
                    component=component_name
                )
                
                try:
                    # Execute the component
                    component_result = await component.process(working_context)
                    
                    # Store as temporary result for next components to use
                    if component_result:
                        working_context["_temp_results"][component_name] = component_result
                        # If this is the last component, store as the final result
                        if i == len(self.components) - 1:
                            final_result = component_result
                    
                    component_duration = (datetime.utcnow() - component_start).total_seconds() * 1000
                    logger.debug(
                        "Component completed successfully",
                        context_id=context_id,
                        component=component_name,
                        duration_ms=component_duration
                    )
                    
                except Exception as e:
                    # Track component failure
                    error_info = {
                        "component": component_name,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    working_context["errors"].append(error_info)
                    
                    logger.error(
                        "Component failed",
                        context_id=context_id,
                        component=component_name,
                        error=str(e),
                        exc_info=True
                    )
                    
                    # Check if we should continue processing despite error
                    if not component.continue_on_error:
                        raise
            
            # Mark as completed if we get through all components
            working_context["status"] = "completed"
            working_context["processing_end"] = datetime.utcnow().isoformat()
            working_context["results"] = final_result  # Only store the final result
            self.metrics["success_count"] += 1
            
            # Remove temporary results
            if "_temp_results" in working_context:
                del working_context["_temp_results"]
            
        except Exception as e:
            # Mark as failed if any non-continuing error occurs
            working_context["status"] = "failed"
            working_context["processing_end"] = datetime.utcnow().isoformat()
            
            # Record the error if not already captured by component error
            if not working_context.get("errors"):
                working_context["errors"].append({
                    "component": "pipeline",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Set results to None for failed processing
            working_context["results"] = None
            
            # Remove temporary results
            if "_temp_results" in working_context:
                del working_context["_temp_results"]
                
            self.metrics["error_count"] += 1
            
            logger.error(
                "Context processing failed",
                context_id=context_id,
                error=str(e)
            )
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Update metrics
        self.metrics["processed_count"] += 1
        total_processed = self.metrics["processed_count"]
        current_avg_time = self.metrics["avg_processing_time_ms"]
        
        # Recalculate running average
        self.metrics["avg_processing_time_ms"] = (
            (current_avg_time * (total_processed - 1) + processing_time) / total_processed
        )
        
        logger.info(
            "Completed context processing",
            context_id=context_id,
            status=working_context["status"],
            duration_ms=processing_time
        )
        
        return working_context
    
    async def process_batch(self, contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of contexts through the pipeline.
        
        This method optimizes processing by running compatible components in batch mode
        and falling back to individual processing for other components.
        
        Args:
            contexts: List of context documents to process
            
        Returns:
            List of processed contexts with results
        """
        if not contexts:
            return []
        
        start_time = datetime.utcnow()
        context_count = len(contexts)
        template_id = contexts[0].get("template_id") if contexts else None
        
        logger.info(
            "Starting batch processing",
            context_count=context_count,
            template_id=template_id
        )
        
        # Create working copies with additional fields
        working_contexts = []
        for context in contexts:
            working_context = context.copy()
            working_context["processing_start"] = start_time.isoformat()
            working_context["status"] = "processing"
            working_context["_temp_results"] = {}  # Temporary storage for intermediate results
            working_context["errors"] = []
            working_contexts.append(working_context)
        
        try:
            # Process through each component
            for component_idx, component in enumerate(self.components):
                component_name = component.__class__.__name__
                component_start = datetime.utcnow()
                
                logger.debug(
                    "Running batch component",
                    context_count=context_count,
                    component=component_name
                )
                
                if hasattr(component, "process_batch") and callable(getattr(component, "process_batch")):
                    # Component supports batch processing
                    try:
                        # Execute batch processing
                        batch_results = await component.process_batch(working_contexts)
                        
                        # Store results for each context
                        if batch_results:
                            for i, context in enumerate(working_contexts):
                                if i < len(batch_results):
                                    # Store as temporary result
                                    context["_temp_results"][component_name] = batch_results[i]
                                    
                                    # If this is the last component, store as the final result
                                    if component_idx == len(self.components) - 1:
                                        context["results"] = batch_results[i]
                        
                        component_duration = (datetime.utcnow() - component_start).total_seconds() * 1000
                        logger.debug(
                            "Batch component completed",
                            context_count=context_count,
                            component=component_name,
                            duration_ms=component_duration
                        )
                        
                    except Exception as e:
                        # Track batch failure
                        error_info = {
                            "component": component_name,
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                        # Add error to all contexts
                        for context in working_contexts:
                            context["errors"].append(error_info)
                        
                        logger.error(
                            "Batch component failed",
                            context_count=context_count,
                            component=component_name,
                            error=str(e),
                            exc_info=True
                        )
                        
                        # Check if we should continue processing despite error
                        if not component.continue_on_error:
                            raise
                    
                else:
                    # Fall back to individual processing
                    for i, context in enumerate(working_contexts):
                        try:
                            # Execute the component individually
                            single_result = await component.process(context)
                            
                            # Store the component's results as temporary
                            if single_result:
                                context["_temp_results"][component_name] = single_result
                                
                                # If this is the last component, store as the final result
                                if component_idx == len(self.components) - 1:
                                    context["results"] = single_result
                                
                        except Exception as e:
                            # Track individual failure
                            error_info = {
                                "component": component_name,
                                "error": str(e),
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            context["errors"].append(error_info)
                            
                            logger.error(
                                "Individual component failed",
                                context_id=str(context.get("_id", "unknown")),
                                component=component_name,
                                error=str(e)
                            )
                            
                            # Check if we should continue processing despite error
                            if not component.continue_on_error:
                                # Mark just this context as failed
                                context["status"] = "failed"
                    
                    component_duration = (datetime.utcnow() - component_start).total_seconds() * 1000
                    logger.debug(
                        "Individual processing completed",
                        context_count=context_count,
                        component=component_name,
                        duration_ms=component_duration
                    )
            
            # Mark completion status for each context and clean up temporary results
            processing_end = datetime.utcnow().isoformat()
            for context in working_contexts:
                if context["status"] != "failed":  # Skip already failed contexts
                    context["status"] = "completed"
                context["processing_end"] = processing_end
                
                # If failed and no result set, ensure results is None
                if context["status"] == "failed" and "results" not in context:
                    context["results"] = None
                
                # Remove temporary results
                if "_temp_results" in context:
                    del context["_temp_results"]
            
            # Update metrics
            success_count = sum(1 for c in working_contexts if c["status"] == "completed")
            error_count = sum(1 for c in working_contexts if c["status"] == "failed")
            
            self.metrics["processed_count"] += context_count
            self.metrics["success_count"] += success_count
            self.metrics["error_count"] += error_count
            
        except Exception as e:
            # Batch-level failure
            processing_end = datetime.utcnow().isoformat()
            error_info = {
                "component": "pipeline",
                "error": str(e),
                "timestamp": processing_end
            }
            
            # Mark all contexts as failed
            for context in working_contexts:
                context["status"] = "failed"
                context["processing_end"] = processing_end
                context["errors"].append(error_info)
                context["results"] = None  # Set results to None for failed contexts
                
                # Remove temporary results
                if "_temp_results" in context:
                    del context["_temp_results"]
            
            self.metrics["processed_count"] += context_count
            self.metrics["error_count"] += context_count
            
            logger.error(
                "Batch processing failed",
                context_count=context_count,
                error=str(e),
                exc_info=True
            )
        
        # Calculate processing time
        batch_processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        avg_per_context = batch_processing_time / context_count if context_count > 0 else 0
        
        # Update average processing time metric
        total_processed = self.metrics["processed_count"]
        current_avg_time = self.metrics["avg_processing_time_ms"]
        
        # Recalculate running average
        self.metrics["avg_processing_time_ms"] = (
            (current_avg_time * (total_processed - context_count) + batch_processing_time) / total_processed
        )
        
        logger.info(
            "Completed batch processing",
            context_count=context_count,
            success_count=sum(1 for c in working_contexts if c["status"] == "completed"),
            error_count=sum(1 for c in working_contexts if c["status"] == "failed"),
            total_duration_ms=batch_processing_time,
            avg_per_context_ms=avg_per_context
        )
        
        return working_contexts
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current processing metrics.
        
        Returns:
            Dictionary containing pipeline metrics
        """
        return {
            **self.metrics,
            "timestamp": datetime.utcnow().isoformat()
        }