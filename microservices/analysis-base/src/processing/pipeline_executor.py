"""
Pipeline executor for the analysis-base microservice.

This module provides the PipelineExecutor class, which is responsible for
executing pipelines and handling errors, metrics, and retries.
"""
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from src.processing.pipeline import Pipeline, PipelineFactory


class PipelineExecutor:
    """
    Executor for processing pipelines.
    
    This class is responsible for executing pipelines on contexts,
    handling errors, collecting metrics, and managing retries.
    
    Attributes:
        logger (logging.Logger): Logger for the executor
        pipeline_factory (PipelineFactory): Factory for creating pipelines
        max_retries (int): Maximum number of retries for a failed context
    """
    
    def __init__(
        self, 
        pipeline_factory: PipelineFactory, 
        max_retries: int = 3
    ):
        """
        Initialize the pipeline executor.
        
        Args:
            pipeline_factory: Factory for creating pipelines
            max_retries: Maximum number of retries for a failed context
        """
        self.logger = logging.getLogger("pipeline_executor")
        self.pipeline_factory = pipeline_factory
        self.max_retries = max_retries
        
        # Execution metrics
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.retried_executions = 0
    
    async def execute_pipeline(
        self, 
        pipeline: Pipeline, 
        context: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any], Optional[Exception]]:
        """
        Execute a pipeline on a context.
        
        Args:
            pipeline: Pipeline to execute
            context: Context to process
            
        Returns:
            Tuple[bool, Dict[str, Any], Optional[Exception]]: Tuple containing:
                - Success flag
                - Processed context (or original context if failed)
                - Exception if failure occurred, None otherwise
        """
        self.total_executions += 1
        
        # Initialize execution context with metadata
        execution_context = context.copy()
        execution_context.setdefault("_metadata", {})
        execution_context["_metadata"]["execution"] = {
            "start_time": time.time(),
            "retry_count": execution_context.get("_metadata", {}).get("execution", {}).get("retry_count", 0)
        }
        
        try:
            # Execute the pipeline
            self.logger.info(f"Executing pipeline: {pipeline.name}")
            processed_context = await pipeline.process(execution_context)
            
            # Update metrics
            self.successful_executions += 1
            
            # Record completion
            processed_context["_metadata"]["execution"]["end_time"] = time.time()
            processed_context["_metadata"]["execution"]["duration"] = (
                processed_context["_metadata"]["execution"]["end_time"] - 
                processed_context["_metadata"]["execution"]["start_time"]
            )
            processed_context["_metadata"]["execution"]["status"] = "success"
            
            return True, processed_context, None
            
        except Exception as e:
            # Update metrics
            self.failed_executions += 1
            
            # Record failure
            execution_context["_metadata"]["execution"]["end_time"] = time.time()
            execution_context["_metadata"]["execution"]["duration"] = (
                execution_context["_metadata"]["execution"]["end_time"] - 
                execution_context["_metadata"]["execution"]["start_time"]
            )
            execution_context["_metadata"]["execution"]["status"] = "error"
            execution_context["_metadata"]["execution"]["error"] = str(e)
            
            self.logger.error(f"Pipeline execution failed: {str(e)}")
            
            return False, execution_context, e
    
    async def execute_with_retry(
        self, 
        pipeline: Pipeline, 
        context: Dict[str, Any], 
        max_retries: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any], Optional[Exception]]:
        """
        Execute a pipeline with retry support.
        
        Args:
            pipeline: Pipeline to execute
            context: Context to process
            max_retries: Maximum number of retries, defaults to self.max_retries
            
        Returns:
            Tuple[bool, Dict[str, Any], Optional[Exception]]: Tuple containing:
                - Success flag
                - Final processed context
                - Final exception if all retries failed, None otherwise
        """
        if max_retries is None:
            max_retries = self.max_retries
        
        retry_context = context.copy()
        retry_context.setdefault("_metadata", {}).setdefault("execution", {})
        retry_context["_metadata"]["execution"]["retry_count"] = 0
        
        last_error = None
        
        # Initial attempt
        success, result, error = await self.execute_pipeline(pipeline, retry_context)
        if success:
            return success, result, None
        
        last_error = error
        
        # Retry logic
        for retry in range(max_retries):
            retry_context = result.copy()
            retry_context["_metadata"]["execution"]["retry_count"] += 1
            
            self.logger.info(
                f"Retrying pipeline execution: {retry + 1}/{max_retries}"
            )
            self.retried_executions += 1
            
            success, result, error = await self.execute_pipeline(pipeline, retry_context)
            if success:
                return success, result, None
            
            last_error = error
        
        self.logger.error(
            f"Pipeline execution failed after {max_retries} retries: {str(last_error)}"
        )
        
        return False, result, last_error
    
    async def execute_for_analysis_type(
        self, 
        analysis_type: str, 
        context: Dict[str, Any],
        configuration: Optional[Dict[str, Any]] = None,
        with_retry: bool = True
    ) -> Tuple[bool, Dict[str, Any], Optional[Exception]]:
        """
        Execute a pipeline for a specific analysis type.
        
        Args:
            analysis_type: Type of analysis (e.g., "descriptive", "diagnostic")
            context: Context to process
            configuration: Configuration for the pipeline
            with_retry: Whether to use retry logic
            
        Returns:
            Tuple[bool, Dict[str, Any], Optional[Exception]]: Tuple containing:
                - Success flag
                - Processed context (or original context if failed)
                - Exception if failure occurred, None otherwise
        """
        try:
            # Create pipeline for the analysis type
            pipeline = self.pipeline_factory.create_pipeline_for_analysis_type(
                analysis_type, configuration
            )
            
            if with_retry:
                return await self.execute_with_retry(pipeline, context)
            else:
                return await self.execute_pipeline(pipeline, context)
                
        except Exception as e:
            self.logger.error(
                f"Failed to create pipeline for analysis type: {analysis_type} - {str(e)}"
            )
            
            # Update context with error information
            context.setdefault("_metadata", {}).setdefault("execution", {})
            context["_metadata"]["execution"]["status"] = "error"
            context["_metadata"]["execution"]["error"] = str(e)
            
            return False, context, e
    
    def get_metrics(self) -> Dict[str, int]:
        """
        Get execution metrics.
        
        Returns:
            Dict[str, int]: Dictionary of execution metrics
        """
        return {
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "retried_executions": self.retried_executions
        }
    
    def reset_metrics(self) -> None:
        """Reset execution metrics."""
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.retried_executions = 0 