"""
Worker Service Module

This module provides the worker service for processing generative tasks.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..common.config import Settings
from ..processing.pipeline import ProcessingPipeline
from ..processing.context_poller import ContextPoller
from ..processing.pipeline_builder import PipelineBuilder
from ..infrastructure.repository.repository import Repository

logger = logging.getLogger(__name__)


class WorkerService:
    """
    Worker service for processing generative tasks.
    
    The worker service polls for pending contexts, processes them through
    the pipeline, and updates their status and results.
    """
    
    def __init__(
        self,
        settings: Settings,
        pipeline: ProcessingPipeline,
        repository: Repository,
        poller: ContextPoller,
        pipeline_builder: Optional[PipelineBuilder] = None
    ):
        """
        Initialize the worker service.
        
        Args:
            settings: Configuration settings
            pipeline: Default processing pipeline
            repository: Repository for storing and retrieving contexts
            poller: Poller for getting pending contexts
            pipeline_builder: Optional builder for template-specific pipelines
        """
        self.settings = settings
        self.pipeline = pipeline
        self.repository = repository
        self.poller = poller
        self.pipeline_builder = pipeline_builder
        self.active = False
        self.active_workers = 0
        self.batch_size = settings.batch_size
        self.batch_wait_time = settings.batch_wait_time
        self.batch_processing_enabled = settings.batch_processing_enabled
        
        # Metrics
        self.metrics = {
            "processed_count": 0,
            "success_count": 0,
            "error_count": 0,
            "avg_processing_time_ms": 0,
            "template_metrics": {}
        }
        
        # Template-specific pipelines cache
        self.template_pipelines = {}
        
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get worker service metrics.
        
        Returns:
            Dictionary of worker metrics
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "running": self.active,
            "active_workers": self.active_workers,
            "batch_mode": self.batch_processing_enabled,
            "processed_count": self.metrics["processed_count"],
            "success_count": self.metrics["success_count"],
            "error_count": self.metrics["error_count"],
            "avg_processing_time_ms": self.metrics["avg_processing_time_ms"],
            "template_metrics": self.metrics["template_metrics"]
        }
        
    async def initialize(self):
        """Initialize the worker service."""
        logger.info("Initializing worker service")
        
    async def start(self):
        """Start the worker service."""
        if self.active:
            logger.warning("Worker service already running")
            return False
            
        logger.info("Starting worker service")
        self.active = True
        
        # Start the main processing loop
        asyncio.create_task(self._processing_loop())
        
        return True
        
    async def stop(self):
        """Stop the worker service."""
        logger.info("Stopping worker service")
        self.active = False
        
        # Wait for all active workers to complete
        while self.active_workers > 0:
            logger.info(f"Waiting for {self.active_workers} active workers to complete")
            await asyncio.sleep(1)
            
        logger.info("Worker service stopped")
        
    async def _processing_loop(self):
        """Main processing loop."""
        logger.info("Starting processing loop")
        
        while self.active:
            try:
                # Check if batch processing is enabled
                if self.batch_processing_enabled and self.batch_size > 1:
                    await self._process_batch_with_flow()
                else:
                    # Process a single context with appropriate flow
                    context, flow_id = await self.poller.get_next_context_and_flow()
                    if context:
                        await self._process_context_with_flow(context, flow_id)
                    else:
                        # No pending contexts, sleep for poll interval
                        await asyncio.sleep(self.settings.poll_interval)
                        
            except Exception as e:
                logger.error(f"Error in processing loop: {str(e)}", exc_info=True)
                await asyncio.sleep(self.settings.poll_interval)
                
        logger.info("Processing loop stopped")
    
    async def _process_context_with_flow(self, context: Dict[str, Any], flow_id: Optional[str] = None):
        """
        Process a single context with the appropriate flow.
        
        Args:
            context: The context to process
            flow_id: Optional ID of the flow to use
        """
        start_time = time.time()
        context_id = str(context.get("_id", "unknown"))
        batch_id = context.get("batch_id")
        template_id = context.get("template_id")
        
        self.active_workers += 1
        
        try:
            logger.info(f"Processing context: {context_id}, template: {template_id}, flow: {flow_id}")
            
            # Update status to processing
            await self.repository.update_context(
                context_id=context_id,
                update={
                    "$set": {
                        "status": "processing",
                        "processing_start": datetime.utcnow().isoformat()
                    }
                }
            )
            
            # Get the appropriate pipeline for this template
            pipeline = await self._get_pipeline_for_template(template_id) if template_id else self.pipeline
            
            # Process the context
            processed_context = await pipeline.process(context)
            
            # Extract batch_id from the context if available
            batch_id = processed_context.get("batch_id", batch_id)
            
            # Update the context with results
            await self.repository.update_context(
                context_id=context_id,
                update={
                    "$set": {
                        "status": "completed",
                        "results": processed_context.get("results", {}),
                        "processing_end": datetime.utcnow().isoformat(),
                        "batch_id": batch_id
                    }
                }
            )
            
            # Update metrics
            self._update_metrics(True, template_id, start_time)
            
            logger.info(f"Context processed successfully: {context_id}, template: {template_id}")
            
        except Exception as e:
            logger.error(f"Error processing context {context_id}: {str(e)}", exc_info=True)
            
            # Update status to failed
            await self.repository.update_context(
                context_id=context_id,
                update={
                    "$set": {
                        "status": "failed",
                        "error": str(e),
                        "processing_end": datetime.utcnow().isoformat(),
                        "batch_id": batch_id
                    }
                }
            )
            
            # Update metrics
            self._update_metrics(False, template_id, start_time)
            
        finally:
            self.active_workers -= 1
    
    async def _process_batch_with_flow(self):
        """Process a batch of pending contexts with the appropriate flow."""
        # Poll for a batch of pending contexts with their flow
        contexts, flow_id = await self.poller.get_batch_contexts_for_flow(
            batch_size=self.batch_size,
            wait_time=self.batch_wait_time
        )
        
        if not contexts:
            # No pending contexts, sleep for poll interval
            await asyncio.sleep(self.settings.poll_interval)
            return
        
        batch_size = len(contexts)
        batch_id = contexts[0].get("batch_id") if contexts else None
        template_id = contexts[0].get("template_id") if contexts else None
        
        logger.info(
            "Processing context batch",
            batch_size=batch_size,
            batch_id=batch_id,
            template_id=template_id,
            flow_id=flow_id
        )
        
        # Get the appropriate pipeline for this template
        pipeline = await self._get_pipeline_for_template(template_id) if template_id else self.pipeline
        
        try:
            # Process the batch
            start_time = time.time()
            processed_contexts = await pipeline.process_batch(contexts)
            
            # Update each context with its results
            for context, processed_context in zip(contexts, processed_contexts):
                context_id = str(context.get("_id"))
                status = processed_context.get("status", "completed")
                
                update = {
                    "status": status,
                    "processing_end": datetime.utcnow().isoformat(),
                    "batch_id": batch_id
                }
                
                if status == "completed":
                    update["results"] = processed_context.get("results", {})
                elif status == "failed":
                    update["error"] = processed_context.get("error", "Unknown error")
                
                # Update the context in the repository
                await self.repository.update_context(
                    context_id=context_id,
                    update={"$set": update}
                )
                
                # Update metrics - count each context separately
                success = (status == "completed")
                self._update_metrics(success, template_id, start_time)
            
            logger.info(
                "Batch processing completed",
                batch_size=batch_size,
                template_id=template_id,
                success_count=sum(1 for c in processed_contexts if c.get("status") == "completed"),
                error_count=sum(1 for c in processed_contexts if c.get("status") == "failed")
            )
            
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}", exc_info=True)
            
            # Mark all contexts as failed
            for context in contexts:
                context_id = str(context.get("_id"))
                
                await self.repository.update_context(
                    context_id=context_id,
                    update={
                        "$set": {
                            "status": "failed",
                            "error": f"Batch processing error: {str(e)}",
                            "processing_end": datetime.utcnow().isoformat(),
                            "batch_id": batch_id
                        }
                    }
                )
                
                # Update metrics for each failed context
                self._update_metrics(False, template_id, start_time)
    
    async def _get_pipeline_for_template(self, template_id: str) -> ProcessingPipeline:
        """
        Get or create a pipeline for a specific template.
        
        Args:
            template_id: The template ID
            
        Returns:
            The appropriate processing pipeline for the template
        """
        # Use cached pipeline if available
        if template_id in self.template_pipelines:
            return self.template_pipelines[template_id]
            
        # Try to create a template-specific pipeline if pipeline builder is available
        if self.pipeline_builder:
            try:
                pipeline = self.pipeline_builder.build_pipeline_for_template(
                    template_id=template_id,
                    repository=self.repository,
                    settings=self.settings
                )
                
                if pipeline:
                    # Cache the pipeline for future use
                    self.template_pipelines[template_id] = pipeline
                    logger.info(f"Created template-specific pipeline for {template_id}")
                    return pipeline
            except Exception as e:
                logger.error(f"Failed to create pipeline for template {template_id}: {str(e)}")
                # Fall back to default pipeline
        
        # Use default pipeline if no template-specific pipeline could be created
        return self.pipeline
    
    async def process_context(self, context: Dict[str, Any]):
        """
        Process a specific context.
        
        This method is intended to be called from API endpoints.
        
        Args:
            context: The context to process or context ID
        """
        # If context is a string (ID), fetch the context
        if isinstance(context, str):
            context = await self.repository.get_context(context)
            
        if not context:
            logger.error("Context not found")
            return
            
        # Determine the flow based on the template
        template_id = context.get("template_id")
        flow_id = None
        
        if self.pipeline_builder and self.pipeline_builder.config_loader:
            flow_config = self.pipeline_builder.config_loader.get_flow_for_template(template_id)
            if flow_config:
                flow_id = flow_config.get('id')
        
        # Process the context
        await self._process_context_with_flow(context, flow_id)

    def _update_metrics(self, success: bool, template_id: Optional[str], start_time: float):
        """
        Update worker metrics.
        
        Args:
            success: Whether processing was successful
            template_id: Optional template ID for template-specific metrics
            start_time: Start time for calculating duration
        """
        # Calculate processing time
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Update global metrics
        self.metrics["processed_count"] += 1
        
        if success:
            self.metrics["success_count"] += 1
        else:
            self.metrics["error_count"] += 1
            
        # Update running average processing time
        total = self.metrics["processed_count"]
        current_avg = self.metrics["avg_processing_time_ms"]
        self.metrics["avg_processing_time_ms"] = (current_avg * (total - 1) + duration_ms) / total
        
        # Update template-specific metrics if available
        if template_id:
            if template_id not in self.metrics["template_metrics"]:
                self.metrics["template_metrics"][template_id] = {
                    "processed_count": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "avg_processing_time_ms": 0
                }
                
            template_metrics = self.metrics["template_metrics"][template_id]
            template_metrics["processed_count"] += 1
            
            if success:
                template_metrics["success_count"] += 1
            else:
                template_metrics["error_count"] += 1
                
            # Update running average for template
            template_total = template_metrics["processed_count"]
            template_avg = template_metrics["avg_processing_time_ms"]
            template_metrics["avg_processing_time_ms"] = (template_avg * (template_total - 1) + duration_ms) / template_total


