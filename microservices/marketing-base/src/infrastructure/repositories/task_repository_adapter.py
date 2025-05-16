"""
Task Repository Adapter

This module provides an adapter between the Marketing microservice and the Task Repository Service.
It implements the same interface as the original TaskRepository but uses the Task Repository
Service for all operations through the common task client library.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

# Import the task client library
from database_layer.common.task_client import (
    create_task,
    get_pending_tasks,
    claim_task,
    complete_task,
    fail_task,
    get_task,
    update_task_status
)

logger = logging.getLogger(__name__)


class TaskRepositoryAdapter:
    """
    Adapter for the Task Repository Service.
    
    This class implements the same interface as the original TaskRepository class
    but uses the Task Repository Service instead of direct MongoDB access.
    """
    
    def __init__(self, service_id: str = "marketing-service"):
        """
        Initialize the adapter.
        
        Args:
            service_id: Identifier for this service instance
        """
        self.service_id = service_id
        logger.info(f"Initialized TaskRepositoryAdapter with service_id: {service_id}")
    
    async def get_pending_campaign_tasks(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get pending campaign tasks from the central repository.
        
        Args:
            limit: Maximum number of tasks to retrieve
            
        Returns:
            List of task documents
        """
        try:
            # Get pending tasks for campaign task type
            tasks = await get_pending_tasks("campaign", limit=limit)
            
            if not tasks:
                return []
            
            claimed_tasks = []
            
            # Try to claim each task
            for task in tasks:
                task_id = task.get("task_id")
                
                # Claim the task
                claimed = await claim_task(task_id)
                
                if claimed:
                    logger.info(f"Claimed task {task_id}")
                    claimed_tasks.append(task)
                else:
                    logger.warning(f"Failed to claim task {task_id}")
            
            logger.info(f"Retrieved and claimed {len(claimed_tasks)} pending campaign tasks")
            return claimed_tasks
            
        except Exception as e:
            logger.error(f"Error getting pending campaign tasks: {str(e)}")
            return []
    
    async def mark_task_completed(self, task_id: str, result: Dict[str, Any]) -> bool:
        """
        Mark a task as completed with results.
        
        Args:
            task_id: ID of the task
            result: Result data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = await complete_task(task_id, result)
            
            if success:
                logger.info(f"Marked task {task_id} as completed")
            else:
                logger.warning(f"Failed to mark task {task_id} as completed")
                
            return success
            
        except Exception as e:
            logger.error(f"Error marking task {task_id} as completed: {str(e)}")
            return False
    
    async def mark_task_failed(self, task_id: str, error: str) -> bool:
        """
        Mark a task as failed with error information.
        
        Args:
            task_id: ID of the task
            error: Error message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = await fail_task(task_id, error)
            
            if success:
                logger.error(f"Marked task {task_id} as failed: {error}")
            else:
                logger.warning(f"Failed to mark task {task_id} as failed")
                
            return success
            
        except Exception as e:
            logger.error(f"Error marking task {task_id} as failed: {str(e)}")
            return False
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a task with new data.
        
        Args:
            task_id: ID of the task
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # If updates include status change, use the dedicated method
            if "status" in updates:
                success = await update_task_status(task_id, updates["status"])
                
                # Remove status from updates if we have other fields to update
                status_only = len(updates) == 1
                if not status_only:
                    updates_copy = updates.copy()
                    del updates_copy["status"]
                    
                    # TODO: Currently task client doesn't support partial updates
                    # This would require extending the client API
                    logger.warning(f"Partial updates not supported: {updates_copy}")
                
                return success
            else:
                # TODO: Implement partial update support in task client
                logger.warning(f"Partial updates not supported: {updates}")
                return False
            
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {str(e)}")
            return False
    
    async def close(self) -> None:
        """Close the repository connection."""
        # No action needed as HTTP client connections are managed by the task client
        logger.info("Closing TaskRepositoryAdapter") 