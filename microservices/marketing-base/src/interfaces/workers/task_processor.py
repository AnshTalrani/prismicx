"""
Task processor worker for processing campaign tasks.

This module provides a worker for processing campaign tasks and monitoring
campaign status.
"""

import logging
import signal
import time
import asyncio
from typing import Dict, Any, Optional

from ...application.services.task_processor_service import TaskProcessorService
from ...application.services.campaign_service import CampaignService
from ...application.services.multi_tenant_batch_processor import MultiTenantBatchProcessor
from ...infrastructure.repositories.task_repository_adapter import TaskRepositoryAdapter
from ...infrastructure.repositories.campaign_repository import CampaignRepository
from ...infrastructure.repositories.multi_tenant_batch_repository import MultiTenantBatchRepository
from ...config.app_config import get_config

logger = logging.getLogger(__name__)


class TaskProcessor:
    """Worker for processing campaign tasks and monitoring campaign status."""

    def __init__(self):
        """Initialize the task processor worker."""
        self.task_processor_service = TaskProcessorService()
        self.task_repository = TaskRepositoryAdapter(service_id="marketing-worker")
        self.campaign_repository = CampaignRepository()
        self.multi_tenant_repository = MultiTenantBatchRepository()
        self.multi_tenant_processor = MultiTenantBatchProcessor(batch_repository=self.multi_tenant_repository)
        self.config = get_config()
        self.task_check_interval = getattr(self.config, 'task_check_interval', 30)  # seconds
        self.campaign_check_interval = getattr(self.config, 'campaign_check_interval', 60)  # seconds
        self.completion_check_interval = getattr(self.config, 'completion_check_interval', 120)  # seconds
        self.multi_tenant_check_interval = getattr(self.config, 'multi_tenant_check_interval', 45)  # seconds
        self.last_campaign_check = 0
        self.last_completion_check = 0
        self.last_multi_tenant_check = 0
        self.worker_id = getattr(self.config, 'worker_id', f"worker-{id(self)}")
        self.running = False
        self._setup_signal_handlers()
        
        logger.info(f"Task processor initialized with central task repository service", worker_id=self.worker_id)
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Received shutdown signal, stopping task processor", worker_id=self.worker_id)
        self.running = False
    
    async def process_tasks(self) -> Dict[str, int]:
        """
        Initialize campaigns from tasks in the central repository.
        
        Returns:
            Dictionary with counts of tasks processed
        """
        logger.info("Checking for campaign tasks", worker_id=self.worker_id)
        
        try:
            # Get pending tasks
            tasks = await self.task_repository.get_pending_campaign_tasks(limit=5)
            
            if not tasks:
                logger.debug("No pending tasks found", worker_id=self.worker_id)
                return {"processed": 0, "success": 0, "failed": 0}
            
            logger.info(
                f"Found {len(tasks)} pending tasks", 
                worker_id=self.worker_id, 
                task_count=len(tasks)
            )
            
            processed = 0
            success = 0
            failed = 0
            
            for task in tasks:
                task_id = task.get('_id')
                
                try:
                    # Process the task based on task type
                    result = await self.task_processor_service.process_campaign_task(task)
                    
                    # Check if processing was successful
                    if result and (
                        result.get('status') in ['scheduled', 'pending_processing', 'processing'] or 
                        result.get('success', False)
                    ):
                        success += 1
                        
                        # Mark task as completed in repository
                        await self.task_repository.mark_task_completed(task_id, result)
                        
                        logger.info(
                            f"Successfully processed task {task_id}", 
                            worker_id=self.worker_id,
                            task_id=task_id,
                            task_type=task.get('task_type', 'campaign')
                        )
                    else:
                        failed += 1
                        
                        # Mark task as failed in repository
                        error_message = result.get('error', 'Unknown error during processing')
                        await self.task_repository.mark_task_failed(task_id, error_message)
                        
                        logger.error(
                            f"Failed to process task {task_id}: {error_message}", 
                            worker_id=self.worker_id,
                            task_id=task_id,
                            task_type=task.get('task_type', 'campaign')
                        )
                    
                except Exception as e:
                    logger.error(
                        f"Error processing task {task_id}: {str(e)}", 
                        worker_id=self.worker_id,
                        task_id=task_id,
                        error=str(e)
                    )
                    
                    await self.task_repository.mark_task_failed(task_id, str(e))
                    failed += 1
                
                processed += 1
            
            return {"processed": processed, "success": success, "failed": failed}
            
        except Exception as e:
            logger.exception(
                f"Error in task processing: {str(e)}", 
                worker_id=self.worker_id,
                error=str(e)
            )
            
            return {"processed": 0, "success": 0, "failed": 0, "error": str(e)}
    
    async def process_scheduled_campaigns(self) -> Dict[str, int]:
        """
        Process scheduled campaigns due to run now.
        
        Returns:
            Dictionary with counts of campaigns processed
        """
        logger.info("Processing scheduled campaigns", worker_id=self.worker_id)
        
        try:
            # Process scheduled campaigns
            result = await self.task_processor_service.process_scheduled_campaigns()
            
            processed = result.get('processed', 0)
            
            if processed > 0:
                logger.info(
                    f"Processed {processed} scheduled campaigns",
                    worker_id=self.worker_id,
                    processed=processed,
                    success=result.get('success', 0),
                    failure=result.get('failure', 0)
                )
            else:
                logger.debug(
                    "No scheduled campaigns found to process",
                    worker_id=self.worker_id
                )
                
            return result
            
        except Exception as e:
            logger.exception(
                f"Error processing scheduled campaigns: {str(e)}",
                worker_id=self.worker_id,
                error=str(e)
            )
            
            return {"processed": 0, "success": 0, "failure": 0, "error": str(e)}
    
    async def check_completed_campaigns(self) -> Dict[str, int]:
        """
        Check for completed campaigns and update their tasks.
        
        Returns:
            Dictionary with counts of campaigns checked
        """
        logger.info("Checking for completed campaigns", worker_id=self.worker_id)
        
        try:
            # Get all completed campaigns that need task updates
            campaigns = await self.campaign_repository.list_completed_campaigns_needing_task_update(limit=10)
            
            if not campaigns:
                logger.debug("No completed campaigns found needing task updates", worker_id=self.worker_id)
                return {"checked": 0, "updated": 0, "failed": 0}
                
            logger.info(f"Found {len(campaigns)} completed campaigns to update", worker_id=self.worker_id)
            
            updated = 0
            failed = 0
            
            for campaign in campaigns:
                try:
                    # Update task in central repository
                    success = await self.task_processor_service.update_task_for_completed_campaign(campaign.id)
                    
                    if success:
                        # Mark campaign as task-updated
                        campaign.custom_attributes["task_updated"] = True
                        await self.campaign_repository.save(campaign)
                        updated += 1
                    else:
                        failed += 1
                
                except Exception as e:
                    logger.error(
                        f"Error updating task for campaign {campaign.id}: {str(e)}",
                        worker_id=self.worker_id, 
                        campaign_id=campaign.id,
                        error=str(e)
                    )
                    failed += 1
            
            if updated > 0:
                logger.info(
                    f"Updated {updated} tasks for completed campaigns",
                    worker_id=self.worker_id,
                    updated=updated,
                    failed=failed
                )
            
            return {"checked": len(campaigns), "updated": updated, "failed": failed}
            
        except Exception as e:
            logger.exception(
                f"Error checking completed campaigns: {str(e)}",
                worker_id=self.worker_id,
                error=str(e)
            )
            
            return {"checked": 0, "updated": 0, "failed": 0, "error": str(e)}
    
    async def process_multi_tenant_batches(self) -> Dict[str, int]:
        """
        Process pending multi-tenant campaign batches.
        
        Returns:
            Dictionary with counts of batches processed
        """
        logger.info("Processing multi-tenant campaign batches", worker_id=self.worker_id)
        
        try:
            # Process pending batches
            result = await self.multi_tenant_processor.process_pending_batches(limit=2)
            
            total = result.get('total', 0)
            
            if total > 0:
                logger.info(
                    f"Processed {total} multi-tenant batches",
                    worker_id=self.worker_id,
                    total=total,
                    success=result.get('success', 0),
                    failed=result.get('failed', 0)
                )
            else:
                logger.debug(
                    "No pending multi-tenant batches found",
                    worker_id=self.worker_id
                )
                
            return result
            
        except Exception as e:
            logger.exception(
                f"Error processing multi-tenant batches: {str(e)}",
                worker_id=self.worker_id,
                error=str(e)
            )
            
            return {"total": 0, "success": 0, "failed": 0, "error": str(e)}
    
    async def run(self):
        """Run the task processor loop."""
        logger.info(
            "Starting task processor",
            worker_id=self.worker_id,
            task_interval=self.task_check_interval,
            campaign_interval=self.campaign_check_interval,
            completion_interval=self.completion_check_interval,
            multi_tenant_interval=self.multi_tenant_check_interval
        )
        
        self.running = True
        
        while self.running:
            start_time = time.time()
            
            # Process tasks from central repository
            task_results = await self.process_tasks()
            
            if task_results.get("processed", 0) > 0:
                logger.info(
                    "Task processing results",
                    worker_id=self.worker_id,
                    processed=task_results.get("processed", 0),
                    success=task_results.get("success", 0),
                    failed=task_results.get("failed", 0)
                )
            
            # Check if it's time to process scheduled campaigns
            current_time = time.time()
            if current_time - self.last_campaign_check >= self.campaign_check_interval:
                await self.process_scheduled_campaigns()
                self.last_campaign_check = current_time
                
            # Check if it's time to check for completed campaigns
            if current_time - self.last_completion_check >= self.completion_check_interval:
                await self.check_completed_campaigns()
                self.last_completion_check = current_time
                
            # Check if it's time to process multi-tenant batches
            if current_time - self.last_multi_tenant_check >= self.multi_tenant_check_interval:
                await self.process_multi_tenant_batches()
                self.last_multi_tenant_check = current_time
            
            # Calculate sleep time
            elapsed = time.time() - start_time
            sleep_time = max(0, self.task_check_interval - elapsed)
            
            # Sleep until next interval
            if sleep_time > 0 and self.running:
                await asyncio.sleep(sleep_time)
                
        logger.info("Task processor stopped", worker_id=self.worker_id)


async def main():
    """Main entry point for the task processor worker."""
    processor = TaskProcessor()
    await processor.run()


if __name__ == "__main__":
    # Run the task processor
    asyncio.run(main()) 