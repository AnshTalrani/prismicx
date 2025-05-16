"""
Task Processor Worker.

This module provides a worker for processing campaign tasks from a queue,
monitoring campaign status, and updating results back to the central repository.
"""

import asyncio
import logging
import signal
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List

from ...domain.models.campaign import Campaign, CampaignStatus
from ...domain.models.campaign_task import CampaignTask, TaskStatus
from ...infrastructure.repositories.campaign_repository import CampaignRepository
from ...infrastructure.repositories.task_repository_adapter import TaskRepositoryAdapter
from ...infrastructure.queue.queue_client import QueueClient
from ...infrastructure.tenant.tenant_context import TenantContext
from ..services.campaign_service import CampaignService

logger = logging.getLogger(__name__)


class TaskProcessor:
    """
    Worker for processing campaign tasks and monitoring campaign status.
    
    This processor pulls tasks from a queue, processes them based on their type,
    and updates the task status in the central repository.
    """
    
    def __init__(
        self,
        task_repository: Optional[TaskRepositoryAdapter] = None,
        campaign_repository: Optional[CampaignRepository] = None,
        campaign_service: Optional[CampaignService] = None,
        queue_client: Optional[QueueClient] = None
    ):
        """
        Initialize the task processor.
        
        Args:
            task_repository: Repository for campaign task operations
            campaign_repository: Repository for campaign operations
            campaign_service: Service for campaign operations
            queue_client: Client for queue operations
        """
        self.task_repository = task_repository or TaskRepositoryAdapter(service_id="marketing-processor")
        self.campaign_repository = campaign_repository or CampaignRepository()
        self.campaign_service = campaign_service or CampaignService()
        self.queue_client = queue_client or QueueClient()
        self.running = False
        self.tasks = []
        self._shutdown_event = asyncio.Event()
        
        logger.info("Task processor initialized with central task repository service")
        
    async def close(self):
        """Close resources used by the processor."""
        try:
            # Close repositories and services
            if self.task_repository:
                await self.task_repository.close()
                
            if self.campaign_repository:
                await self.campaign_repository.close()
                
            if self.queue_client:
                await self.queue_client.close()
                
            # Cancel running tasks
            for task in self.tasks:
                if not task.done():
                    task.cancel()
                    
            logger.info("Closed task processor resources")
        except Exception as e:
            logger.error(f"Error closing task processor resources: {str(e)}")
    
    async def start(self, poll_interval: int = 5):
        """
        Start the task processor.
        
        Args:
            poll_interval: Interval in seconds between polling the queue
        """
        self.running = True
        self._setup_signal_handlers()
        
        logger.info(f"Task processor starting with poll interval of {poll_interval} seconds")
        
        try:
            # Start the main processing loop
            self.tasks.append(
                asyncio.create_task(self._process_tasks_loop(poll_interval))
            )
            
            # Start the campaign status monitoring loop
            self.tasks.append(
                asyncio.create_task(self._monitor_campaigns_loop(poll_interval * 2))
            )
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
        except asyncio.CancelledError:
            logger.info("Task processor received cancellation")
            
        except Exception as e:
            logger.error(f"Error in task processor: {str(e)}")
            logger.error(traceback.format_exc())
            
        finally:
            self.running = False
            await self.close()
            logger.info("Task processor has stopped")
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        loop = asyncio.get_running_loop()
        
        # Add signal handlers for graceful shutdown
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig, lambda s=sig: asyncio.create_task(self._shutdown(sig))
            )
        
        logger.info("Signal handlers set up for graceful shutdown")
    
    async def _shutdown(self, sig):
        """
        Handle shutdown signal.
        
        Args:
            sig: Signal that triggered the shutdown
        """
        logger.info(f"Received exit signal {sig.name}, shutting down...")
        self.running = False
        self._shutdown_event.set()
    
    async def _process_tasks_loop(self, poll_interval: int):
        """
        Main processing loop for tasks.
        
        Args:
            poll_interval: Interval in seconds between polling the queue
        """
        logger.info("Task processing loop started")
        
        while self.running:
            try:
                # Get tasks from the queue
                tasks = await self.queue_client.receive_tasks(max_count=10)
                
                if tasks:
                    logger.info(f"Retrieved {len(tasks)} tasks from queue")
                    
                    # Process each task
                    await asyncio.gather(
                        *[self._process_task(task) for task in tasks],
                        return_exceptions=True
                    )
                    
                # Wait for the next poll interval
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error in task processing loop: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Slow down if there's an error
                await asyncio.sleep(poll_interval * 2)
    
    async def _monitor_campaigns_loop(self, poll_interval: int):
        """
        Loop for monitoring campaign status.
        
        Args:
            poll_interval: Interval in seconds between monitoring checks
        """
        logger.info("Campaign monitoring loop started")
        
        while self.running:
            try:
                # Get active campaigns that need status monitoring
                active_campaigns = await self.campaign_repository.get_active_campaigns(limit=20)
                
                if active_campaigns:
                    logger.info(f"Monitoring {len(active_campaigns)} active campaigns")
                    
                    # Process each campaign
                    await asyncio.gather(
                        *[self._monitor_campaign(campaign) for campaign in active_campaigns],
                        return_exceptions=True
                    )
                    
                # Wait for the next poll interval
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error in campaign monitoring loop: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Slow down if there's an error
                await asyncio.sleep(poll_interval * 2)
    
    async def _process_task(self, task: CampaignTask):
        """
        Process a single campaign task.
        
        Args:
            task: The task to process
        """
        if not task or not task.id:
            logger.error("Received invalid task, skipping")
            return
            
        logger.info(f"Processing task {task.id} of type {task.task_type}")
        
        try:
            # Update task status to PROCESSING
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.utcnow()
            await self.task_repository.update_task(task)
            
            # Set tenant context if provided
            if task.tenant_id:
                TenantContext.set_tenant_id(task.tenant_id)
                
            # Process the task based on its type
            if task.task_type == "SEND_CAMPAIGN":
                await self._process_send_campaign(task)
                
            elif task.task_type == "CANCEL_CAMPAIGN":
                await self._process_cancel_campaign(task)
                
            else:
                logger.warning(f"Unknown task type: {task.task_type}")
                task.status = TaskStatus.FAILED
                task.error_message = f"Unknown task type: {task.task_type}"
                
            # Update task completion
            task.completed_at = datetime.utcnow()
            await self.task_repository.update_task(task)
            
            logger.info(f"Task {task.id} processed with status {task.status}")
            
        except Exception as e:
            logger.error(f"Error processing task {task.id}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Update task with error status
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            
            try:
                await self.task_repository.update_task(task)
            except Exception as inner_e:
                logger.error(f"Failed to update task status: {str(inner_e)}")
                
        finally:
            # Clear tenant context
            TenantContext.clear()
    
    async def _process_send_campaign(self, task: CampaignTask):
        """
        Process a send campaign task.
        
        Args:
            task: The task to process
        """
        logger.info(f"Processing send campaign task for campaign {task.campaign_id}")
        
        # Get payload from task
        payload = task.payload or {}
        campaign_id = task.campaign_id or payload.get("campaign_id")
        
        if not campaign_id:
            task.status = TaskStatus.FAILED
            task.error_message = "No campaign ID provided"
            return
            
        # Get campaign
        campaign = await self.campaign_repository.get_by_id(campaign_id)
        
        if not campaign:
            task.status = TaskStatus.FAILED
            task.error_message = f"Campaign {campaign_id} not found"
            return
            
        # Send the campaign
        try:
            success = await self.campaign_service.send_campaign(campaign_id)
            
            if success:
                task.status = TaskStatus.COMPLETED
                logger.info(f"Successfully sent campaign {campaign_id}")
            else:
                task.status = TaskStatus.FAILED
                task.error_message = "Failed to send campaign"
                logger.error(f"Failed to send campaign {campaign_id}")
                
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            logger.error(f"Error sending campaign {campaign_id}: {str(e)}")
    
    async def _process_cancel_campaign(self, task: CampaignTask):
        """
        Process a cancel campaign task.
        
        Args:
            task: The task to process
        """
        logger.info(f"Processing cancel campaign task for campaign {task.campaign_id}")
        
        # Get payload from task
        payload = task.payload or {}
        campaign_id = task.campaign_id or payload.get("campaign_id")
        
        if not campaign_id:
            task.status = TaskStatus.FAILED
            task.error_message = "No campaign ID provided"
            return
            
        # Get campaign
        campaign = await self.campaign_repository.get_by_id(campaign_id)
        
        if not campaign:
            task.status = TaskStatus.FAILED
            task.error_message = f"Campaign {campaign_id} not found"
            return
            
        # Cancel the campaign
        try:
            success = await self.campaign_service.cancel_campaign(campaign_id)
            
            if success:
                task.status = TaskStatus.COMPLETED
                logger.info(f"Successfully cancelled campaign {campaign_id}")
            else:
                task.status = TaskStatus.FAILED
                task.error_message = "Failed to cancel campaign"
                logger.error(f"Failed to cancel campaign {campaign_id}")
                
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            logger.error(f"Error cancelling campaign {campaign_id}: {str(e)}")
    
    async def _monitor_campaign(self, campaign: Campaign):
        """
        Monitor the status of a campaign and update if needed.
        
        Args:
            campaign: The campaign to monitor
        """
        if not campaign or not campaign.id:
            logger.error("Received invalid campaign for monitoring, skipping")
            return
            
        logger.debug(f"Monitoring campaign {campaign.id} with status {campaign.status}")
        
        try:
            # Set tenant context if available
            if hasattr(campaign, 'tenant_id') and campaign.tenant_id:
                TenantContext.set_tenant_id(campaign.tenant_id)
            elif campaign.custom_attributes and 'tenant_id' in campaign.custom_attributes:
                TenantContext.set_tenant_id(campaign.custom_attributes['tenant_id'])
                
            # Get current campaign status from service
            current_status = await self.campaign_service.get_campaign_status(campaign.id)
            
            # Check if status has changed
            if current_status != campaign.status:
                logger.info(f"Campaign {campaign.id} status changed from {campaign.status} to {current_status}")
                
                # Update campaign status
                campaign.status = current_status
                campaign.updated_at = datetime.utcnow()
                
                # If campaign is complete, update completion time
                if current_status in [CampaignStatus.COMPLETED, CampaignStatus.FAILED, CampaignStatus.CANCELLED]:
                    campaign.completed_at = datetime.utcnow()
                    
                    # Get campaign statistics
                    stats = await self.campaign_service.get_campaign_statistics(campaign.id)
                    campaign.metrics = stats
                    
                    # If this is a multi-tenant batch campaign, update the batch
                    if campaign.custom_attributes and 'multi_tenant_batch_id' in campaign.custom_attributes:
                        await self._update_batch_status(campaign)
                
                # Save campaign changes
                await self.campaign_repository.update(campaign)
                
        except Exception as e:
            logger.error(f"Error monitoring campaign {campaign.id}: {str(e)}")
            
        finally:
            # Clear tenant context
            TenantContext.clear()
    
    async def _update_batch_status(self, campaign: Campaign):
        """
        Update the status of a multi-tenant batch based on campaign status.
        
        Args:
            campaign: The campaign whose status has been updated
        """
        if not campaign or not campaign.custom_attributes:
            return
            
        batch_id = campaign.custom_attributes.get('multi_tenant_batch_id')
        tenant_id = campaign.custom_attributes.get('tenant_id')
        
        if not batch_id or not tenant_id:
            logger.debug(f"Campaign {campaign.id} is not part of a multi-tenant batch")
            return
            
        logger.info(f"Updating batch {batch_id} for tenant {tenant_id} based on campaign {campaign.id}")
        
        try:
            # Create tenant result based on campaign status
            tenant_status = "COMPLETED"
            if campaign.status == CampaignStatus.FAILED:
                tenant_status = "FAILED"
            elif campaign.status == CampaignStatus.CANCELLED:
                tenant_status = "CANCELLED"
                
            # Get metrics
            processed_count = campaign.metrics.get("processed", 0)
            success_count = campaign.metrics.get("success", 0)
            error_count = campaign.metrics.get("failed", 0)
            
            # Create tenant result data
            tenant_result = {
                "tenant_id": tenant_id,
                "campaign_id": campaign.id,
                "status": tenant_status,
                "processed_count": processed_count,
                "success_count": success_count,
                "error_count": error_count,
                "completed_at": datetime.utcnow().isoformat(),
                "error_message": campaign.last_error if campaign.status == CampaignStatus.FAILED else None
            }
            
            # Update batch with tenant result
            from ...infrastructure.repositories.multi_tenant_batch_repository import MultiTenantBatchRepository
            batch_repo = MultiTenantBatchRepository()
            
            try:
                await batch_repo.update_tenant_result(batch_id, tenant_id, tenant_result)
                logger.info(f"Updated batch {batch_id} with tenant {tenant_id} result")
            finally:
                await batch_repo.close()
                
        except Exception as e:
            logger.error(f"Error updating batch status: {str(e)}") 