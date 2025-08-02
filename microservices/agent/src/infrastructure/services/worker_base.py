"""Base worker class for service clients.

Provides the foundation for service-specific workers that process
contexts directly from the repository.
"""
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.infrastructure.repositories.task_repository_adapter import TaskRepositoryAdapter

logger = logging.getLogger(__name__)

class ClientWorker:
    """Base worker class for service clients."""
    
    def __init__(
        self,
        service_type: str,
        repository: TaskRepositoryAdapter,
        poll_interval: float = 1.0,
        batch_size: int = 5
    ):
        """
        Initialize client worker.
        
        Args:
            service_type: Type of service this worker handles
            repository: Task repository adapter for context access
            poll_interval: Time between polling for new contexts (seconds)
            batch_size: Maximum number of contexts to retrieve at once
        """
        self.service_type = service_type
        self.repository = repository
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.worker_id = f"{service_type}_worker_{uuid.uuid4().hex[:8]}"
        self.running = False
        self.task = None
        self.logger = logging.getLogger(f"{__name__}.{service_type}Worker")
        
    async def start(self):
        """Start the worker processing loop."""
        if self.running:
            self.logger.warning(f"Worker {self.worker_id} already running")
            return
            
        self.running = True
        self.task = asyncio.create_task(self._process_loop())
        self.logger.info(f"Started {self.service_type} worker {self.worker_id}")
        
    async def stop(self):
        """Stop the worker processing loop."""
        if not self.running:
            return
            
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.logger.info(f"Stopped {self.service_type} worker {self.worker_id}")
        
    async def _process_loop(self):
        """Main processing loop for polling and handling contexts."""
        self.logger.info(f"Worker {self.worker_id} starting processing loop")
        
        while self.running:
            try:
                # Find pending contexts for this service type
                contexts = await self._find_pending_contexts()
                
                if not contexts:
                    # No pending contexts, wait before checking again
                    await asyncio.sleep(self.poll_interval)
                    continue
                    
                # Process each context
                for context in contexts:
                    await self._process_context(context)
                    
            except Exception as e:
                self.logger.error(f"Error in {self.service_type} worker loop: {str(e)}")
                # Wait before retrying
                await asyncio.sleep(self.poll_interval)
    
    async def _find_pending_contexts(self) -> List[Dict[str, Any]]:
        """Find pending contexts for this worker's service type."""
        try:
            # Get pending contexts from the repository
            pending_contexts = await self.repository.find_by_status("pending", limit=self.batch_size)
            
            # Filter for contexts that match this worker's service type
            matching_contexts = []
            for context in pending_contexts:
                service_type_from_template = context.get("template", {}).get("service_type")
                service_type_from_tags = context.get("tags", {}).get("service")
                
                if (service_type_from_template == self.service_type or 
                        service_type_from_tags == self.service_type):
                    matching_contexts.append(context)
            
            return matching_contexts
            
        except Exception as e:
            self.logger.error(f"Error finding pending contexts: {str(e)}")
            return []
                
    async def _process_context(self, context: Dict[str, Any]):
        """Process a single context."""
        context_id = context["_id"]
        
        # Try to claim this context
        claimed = await self._claim_context(context_id)
        if not claimed:
            # Another worker claimed it first
            self.logger.debug(f"Context {context_id} already claimed by another worker")
            return
            
        self.logger.info(f"Worker {self.worker_id} processing context {context_id}")
        
        try:
            # Process the context (to be implemented by subclasses)
            result = await self.process(context)
            
            # Update context with result and mark as completed
            context["status"] = "completed" if result.get("success", False) else "failed"
            context["results"] = result
            context["processed_by"] = self.worker_id
            context["completed_at"] = datetime.utcnow().isoformat()
            
            # Save the updated context
            await self.repository.save(context_id, context)
            
            self.logger.info(f"Completed processing context {context_id}")
            
        except Exception as e:
            self.logger.error(f"Error processing context {context_id}: {str(e)}")
            
            # Get the current context again in case it changed
            current_context = await self.repository.get(context_id)
            if current_context:
                # Update status to failed and add error info
                current_context["status"] = "failed"
                current_context["results"] = {
                    "error": {
                        "message": str(e),
                        "worker_id": self.worker_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
                # Save the updated context
                await self.repository.save(context_id, current_context)
    
    async def _claim_context(self, context_id: str) -> bool:
        """Atomically claim a context for processing."""
        try:
            # Get the current context
            context = await self.repository.get(context_id)
            if not context or context.get("status") != "pending":
                return False
                
            # Update the context status to processing
            context["status"] = "processing"
            context["claimed_by"] = self.worker_id
            context["claimed_at"] = datetime.utcnow().isoformat()
            
            # Save the updated context
            success = await self.repository.save(context_id, context)
            return success
            
        except Exception as e:
            self.logger.error(f"Error claiming context {context_id}: {str(e)}")
            return False
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a context. To be implemented by subclasses.
        
        Args:
            context: Context to process
            
        Returns:
            Processing result
        """
        raise NotImplementedError("Subclasses must implement process method") 