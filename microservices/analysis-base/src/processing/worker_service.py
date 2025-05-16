"""
Worker Service Module

This module provides the worker service that processes contexts in the background.
It manages the polling, processing, and updating of contexts using the processing 
engine and related components.
"""

import asyncio
import structlog
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from ..repository.repository import Repository
from ..config.settings import Settings
from ..processing.processing_engine import ProcessingEngine
from ..common.exceptions import ProcessingError

# Configure structured logging
logger = structlog.get_logger(__name__)

class WorkerService:
    """
    Service for processing contexts in the background.
    
    This service:
    - Polls for pending contexts
    - Processes contexts through the processing engine
    - Updates context status and results
    - Manages the lifecycle of processing jobs
    """
    
    def __init__(
        self,
        repository: Repository,
        settings: Settings,
        processing_engine: ProcessingEngine
    ):
        """
        Initialize the worker service.
        
        Args:
            repository: Data repository
            settings: Application configuration settings
            processing_engine: Processing engine
        """
        self.repository = repository
        self.settings = settings
        self.processing_engine = processing_engine
        
        self.running = False
        self.task = None
        self.batch_mode = settings.batch_processing_enabled
        self.batch_size = settings.batch_size
        
        # Metrics for monitoring
        self.metrics = {
            "processed_count": 0,
            "success_count": 0,
            "error_count": 0,
            "running": False,
            "batch_mode": self.batch_mode,
            "last_processed": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            "Worker service initialized",
            batch_mode=self.batch_mode,
            batch_size=self.batch_size if self.batch_mode else None
        )
        
    async def start(self):
        """Start the worker service."""
        if self.running:
            logger.warning("Worker service already running")
            return
            
        self.running = True
        self.metrics["running"] = True
        self.task = asyncio.create_task(self._run())
        logger.info("Worker service started")
        
    async def stop(self):
        """Stop the worker service."""
        if not self.running:
            logger.warning("Worker service not running")
            return
            
        self.running = False
        self.metrics["running"] = False
        if self.task:
            try:
                # Wait for the task to complete gracefully
                await asyncio.wait_for(self.task, timeout=5.0)
            except asyncio.TimeoutError:
                # Cancel the task if it doesn't complete within timeout
                self.task.cancel()
            try:
                    await self.task
            except asyncio.CancelledError:
                pass
            
            self.task = None
        
        logger.info("Worker service stopped")
    
    async def _run(self):
        """Main processing loop for the worker service."""
        logger.info("Worker service processing loop started")
        
        while self.running:
            try:
                if self.batch_mode:
                    await self._process_batch()
                else:
                    await self._process_single()
                
                # Sleep briefly to avoid tight polling loop
                await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(
                    "Error in worker processing loop",
                    error=str(e),
                    exc_info=True
                )
                
                # Sleep longer on errors to avoid error storms
                await asyncio.sleep(1.0)
        
        logger.info("Worker service processing loop stopped")
    
    async def _process_single(self):
        """Process a single pending context."""
        # Poll for a pending context
        context = await self.repository.get_next_pending_context()
        
        if not context:
            # No pending contexts, sleep for poll interval
            await asyncio.sleep(self.settings.poll_interval)
            return
        
        context_id = context.get("_id", "unknown")
        logger.info(
            "Processing single context",
            context_id=context_id,
            template_id=context.get("template_id")
        )
        
        try:
            # Process the context
            await self.repository.update_context_status(
                context_id=context_id,
                status="processing"
            )
            
            result = await self.processing_engine.process_context(context)
            
            # Update metrics
            self.metrics["processed_count"] += 1
            self.metrics["success_count"] += 1
            self.metrics["last_processed"] = datetime.utcnow().isoformat()
            self.metrics["timestamp"] = datetime.utcnow().isoformat()
            
            # Update the repository with results
            await self.repository.update_context_result(
                context_id=context_id,
                status="completed",
                result=result
            )
            
            # Update tags if available
            if result and "tags" in result and isinstance(result["tags"], list):
                await self.repository.update_context_tags(
                    context_id=context_id,
                    tags=result["tags"]
                )
            
            logger.info(
                "Context processing completed",
                context_id=context_id,
                status="completed"
            )
            
        except Exception as e:
            error_message = str(e)
            retry_recommended = True
            
            # Extract retry recommendation if it's a ProcessingError
            if isinstance(e, ProcessingError):
                error_message = e.message
                retry_recommended = e.retry_recommended
                
            logger.error(
                "Failed to process context",
                context_id=context_id, 
                error=error_message,
                retry_recommended=retry_recommended,
                exc_info=True
            )
            
            # Update metrics
            self.metrics["processed_count"] += 1
            self.metrics["error_count"] += 1
            self.metrics["last_processed"] = datetime.utcnow().isoformat()
            self.metrics["timestamp"] = datetime.utcnow().isoformat()
            
            # Update context with error status
            error_info = {
                "message": error_message,
                "component": "worker_service",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.repository.update_context_status(
                context_id=context_id,
                status="failed",
                error=error_info
            )
            
            # Schedule retry if recommended
            if retry_recommended:
                # Get current retry count
                retry_count = await self.repository.get_retry_count(context_id) or 0
                retry_count += 1
                
                if retry_count <= self.settings.max_retries:
                    # Calculate next retry time using exponential backoff
                    retry_delay = self.settings.retry_delay * (2 ** (retry_count - 1))
                    next_retry = datetime.utcnow() + datetime.timedelta(seconds=retry_delay)
        
                    await self.repository.schedule_context_retry(
                        context_id=context_id,
                        retry_count=retry_count,
                        next_retry=next_retry
                    )
                    
                    logger.info(
                        "Scheduled context for retry",
                        context_id=context_id,
                        retry_count=retry_count,
                        next_retry=next_retry.isoformat()
                    )
    
    async def _process_batch(self):
        """Process a batch of pending contexts."""
        # Poll for a batch of pending contexts
        contexts = await self.repository.get_pending_contexts_batch(self.batch_size)
        
        if not contexts:
            # No pending contexts, sleep for poll interval
            await asyncio.sleep(self.settings.poll_interval)
            return
        
        context_ids = [context.get("_id", "unknown") for context in contexts]
        logger.info(
            "Processing context batch",
            batch_size=len(contexts)
        )
        
        try:
            # Update contexts to processing status
            for context_id in context_ids:
                await self.repository.update_context_status(
                    context_id=context_id,
                    status="processing"
                )
            
            # Process the contexts as a batch
            results = await self.processing_engine.process_batch(contexts)
        
            # Update each context with its result
            for i, context in enumerate(contexts):
                context_id = context.get("_id", "unknown")
                item_result = results.get("items", [])[i] if i < len(results.get("items", [])) else None
                
                if item_result and item_result.get("success", False):
                    # Successful processing
                await self.repository.update_context_result(
                        context_id=context_id,
                        status="completed",
                        result=item_result.get("result", {})
                    )
                    
                    # Update tags if available
                    result_data = item_result.get("result", {})
                    if result_data and "tags" in result_data and isinstance(result_data["tags"], list):
                        await self.repository.update_context_tags(
                            context_id=context_id,
                            tags=result_data["tags"]
                        )
                        
                    # Update metrics
                    self.metrics["processed_count"] += 1
                    self.metrics["success_count"] += 1
                else:
                    # Failed processing
                    error_message = item_result.get("error", "Unknown error") if item_result else "Batch processing error"
                    
                    error_info = {
                        "message": error_message,
                        "component": "worker_service",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    await self.repository.update_context_status(
                        context_id=context_id,
                        status="failed",
                        error=error_info
                    )
                    
                    # Update metrics
                    self.metrics["processed_count"] += 1
                    self.metrics["error_count"] += 1
            
            self.metrics["last_processed"] = datetime.utcnow().isoformat()
            self.metrics["timestamp"] = datetime.utcnow().isoformat()
            
            logger.info(
                "Batch processing completed",
                batch_size=len(contexts),
                successes=results.get("summary", {}).get("completed", 0),
                failures=results.get("summary", {}).get("failed", 0)
            )
            
        except Exception as e:
            logger.error(
                "Failed to process batch",
                batch_size=len(contexts),
                error=str(e),
                exc_info=True
        )
        
            # Update all contexts with error status
            for context_id in context_ids:
                error_info = {
                    "message": str(e),
                    "component": "worker_service",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            await self.repository.update_context_status(
                    context_id=context_id,
                    status="failed",
                    error=error_info
                )
            
            # Update metrics
            self.metrics["processed_count"] += len(contexts)
            self.metrics["error_count"] += len(contexts)
            self.metrics["last_processed"] = datetime.utcnow().isoformat()
            self.metrics["timestamp"] = datetime.utcnow().isoformat()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current worker service metrics.
        
        Returns:
            Dictionary of metrics
        """
        self.metrics["timestamp"] = datetime.utcnow().isoformat()
        return self.metrics 