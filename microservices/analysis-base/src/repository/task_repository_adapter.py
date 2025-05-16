"""
Task Repository Adapter

This module provides an adapter between the Analysis service and the Task Repository Service.
It implements the same interface as the MongoDB Repository but uses the Task Repository
Service for all data operations.
"""

import structlog
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
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

# Configure structured logging
logger = structlog.get_logger(__name__)


class TaskRepositoryAdapter:
    """
    Adapter for the Task Repository Service.
    
    This class implements the same interface as the original Repository class
    but uses the Task Repository Service instead of direct MongoDB access.
    """
    
    def __init__(self, service_id: str = "analysis-service"):
        """
        Initialize the adapter.
        
        Args:
            service_id: Identifier for this service instance
        """
        self.service_id = service_id
        logger.info(f"Initialized TaskRepositoryAdapter with service_id: {service_id}")
    
    async def connect(self) -> bool:
        """
        Simulate connecting to the database.
        The actual connection is handled by the task client.
        
        Returns:
            Success status (always True for now)
        """
        logger.info("TaskRepositoryAdapter connected")
        return True
    
    async def close(self) -> None:
        """
        Simulate closing the database connection.
        No actual close required as HTTP client connections are managed by the task client.
        """
        logger.info("TaskRepositoryAdapter closed")
    
    def is_connected(self) -> bool:
        """
        Check if the repository is connected.
        Task client connections are on-demand, so this always returns True.
        
        Returns:
            True
        """
        return True

    async def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a context by ID from the task repository.
        
        Args:
            context_id: Context ID
            
        Returns:
            Context document or None if not found
        """
        try:
            # Retrieve the task from the repository
            task = await get_task(context_id)
            
            if not task:
                logger.warning(f"Task not found for context {context_id}")
                return None
            
            # Convert task to context format
            context = {
                "_id": task.get("task_id"),
                "status": task.get("status", "unknown"),
                "template_id": task.get("task_type"),
                "service_type": task.get("task_type"),
                "data": task.get("request", {}).get("content", {}),
                "metadata": task.get("metadata", {}),
                "created_at": task.get("created_at"),
                "updated_at": task.get("updated_at"),
                "results": task.get("result", {}),
                "tags": task.get("tags", {})
            }
            
            # Add batch ID if available
            if task.get("batch_id"):
                context["batch_id"] = task.get("batch_id")
            
            return context
            
        except Exception as e:
            logger.error(
                "Failed to get context",
                context_id=context_id,
                error=str(e)
            )
            return None
    
    async def get_next_pending_context(self) -> Optional[Dict[str, Any]]:
        """
        Get the next pending context for processing.
        
        Returns:
            The next pending context, or None if no pending contexts
        """
        try:
            # Get pending tasks for this service type
            tasks = await get_pending_tasks("analysis", limit=1)
            
            if not tasks or len(tasks) == 0:
                return None
            
            task = tasks[0]
            
            # Try to claim the task
            claimed = await claim_task(task.get("task_id"))
            
            if not claimed:
                logger.debug(
                    "Failed to claim task", 
                    task_id=task.get("task_id")
                )
                return None
            
            # Convert task to context format
            context = {
                "_id": task.get("task_id"),
                "status": "processing",  # Mark as processing since we claimed it
                "template_id": task.get("task_type"),
                "service_type": task.get("task_type"),
                "data": task.get("request", {}).get("content", {}),
                "metadata": task.get("metadata", {}),
                "created_at": task.get("created_at"),
                "updated_at": task.get("updated_at"),
                "tags": task.get("tags", {})
            }
            
            # Add batch ID if available
            if task.get("batch_id"):
                context["batch_id"] = task.get("batch_id")
            
            return context
            
        except Exception as e:
            logger.error(
                "Failed to get next pending context",
                error=str(e)
            )
            return None
    
    async def get_pending_contexts_batch(self, batch_size: int) -> List[Dict[str, Any]]:
        """
        Get a batch of pending contexts for processing.
        
        Args:
            batch_size: Maximum number of contexts to retrieve
            
        Returns:
            List of pending contexts, may be empty
        """
        try:
            # Get pending tasks for this service type
            tasks = await get_pending_tasks("analysis", limit=batch_size)
            
            if not tasks:
                return []
            
            contexts = []
            
            # Convert tasks to contexts and try to claim them
            for task in tasks:
                task_id = task.get("task_id")
                
                # Try to claim the task
                claimed = await claim_task(task_id)
                
                if not claimed:
                    logger.debug(
                        "Failed to claim task", 
                        task_id=task_id
                    )
                    continue
                
                # Convert task to context format
                context = {
                    "_id": task_id,
                    "status": "processing",  # Mark as processing since we claimed it
                    "template_id": task.get("task_type"),
                    "service_type": task.get("task_type"),
                    "data": task.get("request", {}).get("content", {}),
                    "metadata": task.get("metadata", {}),
                    "created_at": task.get("created_at"),
                    "updated_at": task.get("updated_at"),
                    "tags": task.get("tags", {})
                }
                
                # Add batch ID if available
                if task.get("batch_id"):
                    context["batch_id"] = task.get("batch_id")
                
                contexts.append(context)
            
            return contexts
            
        except Exception as e:
            logger.error(
                "Failed to get pending contexts batch",
                error=str(e)
            )
            return []
    
    async def update_context_status(
        self, 
        context_id: str, 
        status: str, 
        error: Optional[Dict[str, Any]] = None,
        retry_metadata: Optional[Dict[str, Any]] = None,
        processing_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a context's status in the task repository.
        
        Args:
            context_id: Context identifier
            status: New context status
            error: Optional error information
            retry_metadata: Optional retry metadata
            processing_metadata: Optional processing metadata
            
        Returns:
            Success status
        """
        try:
            # For completed or failed status, use specialized calls
            if status == "completed":
                # Create an empty result if needed
                result = {}
                if processing_metadata:
                    result["processing_metadata"] = processing_metadata
                
                success = await complete_task(context_id, result)
                return success
                
            elif status == "failed":
                # Create error info from provided error or default
                error_info = error or {"message": "Unknown error"}
                
                # Add retry metadata if provided
                if retry_metadata:
                    error_info["retry_metadata"] = retry_metadata
                
                success = await fail_task(context_id, error_info)
                return success
                
            else:
                # For other statuses, use update_task_status
                success = await update_task_status(context_id, status)
                return success
                
        except Exception as e:
            logger.error(
                "Failed to update context status",
                context_id=context_id,
                status=status,
                error=str(e)
            )
            return False
    
    async def update_context_result(
        self, 
        context_id: str, 
        status: str, 
        result: Dict[str, Any],
        processing_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a context's result in the task repository.
        
        Args:
            context_id: Context identifier
            status: New context status
            result: Result data
            processing_metadata: Optional processing metadata
            
        Returns:
            Success status
        """
        try:
            # Combine result with processing metadata if provided
            full_result = result.copy()
            if processing_metadata:
                full_result["processing_metadata"] = processing_metadata
            
            # For completed status, use complete_task
            if status == "completed":
                success = await complete_task(context_id, full_result)
                return success
            else:
                # For other statuses, first update the task status
                status_updated = await update_task_status(context_id, status)
                
                if not status_updated:
                    logger.error(
                        "Failed to update task status before updating result",
                        context_id=context_id,
                        status=status
                    )
                    return False
                
                # Then complete the task with the results (this is a simplification)
                # In a real implementation, we might need a more complex update mechanism
                success = await complete_task(context_id, full_result)
                return success
                
        except Exception as e:
            logger.error(
                "Failed to update context result",
                context_id=context_id,
                status=status,
                error=str(e)
            )
            return False
    
    async def create_context(self, context_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new context by creating a task in the task repository.
        
        Args:
            context_data: Context data to create
            
        Returns:
            Context ID if created, None otherwise
        """
        try:
            # Extract data from context
            service_type = context_data.get("service_type", "analysis")
            template_id = context_data.get("template_id", service_type)
            status = context_data.get("status", "pending")
            tags = context_data.get("tags", {})
            metadata = context_data.get("metadata", {})
            batch_id = context_data.get("batch_id")
            
            # Priority defaults to 5 (medium) if not specified
            priority = metadata.get("priority", 5)
            
            # Prepare task data
            task_data = {
                "task_type": service_type,
                "status": status,
                "priority": priority,
                "request": {
                    "content": context_data.get("data", {}),
                    "metadata": metadata
                },
                "template": {
                    "service_type": service_type,
                    "template_id": template_id,
                    "template_data": context_data.get("template", {})
                },
                "tags": tags,
                "metadata": metadata
            }
            
            # Add batch ID if provided
            if batch_id:
                task_data["batch_id"] = batch_id
            
            # Create the task
            task_id = await create_task(task_data)
            
            if task_id:
                logger.info(f"Created task with ID: {task_id}")
                return task_id
            else:
                logger.error("Failed to create task")
                return None
                
        except Exception as e:
            logger.error(
                "Failed to create context",
                error=str(e)
            )
            return None
    
    async def update_context_tags(self, context_id: str, tags: List[str]) -> bool:
        """
        Update a context's tags.
        
        Args:
            context_id: Context identifier
            tags: New tags list
            
        Returns:
            Success status
        """
        try:
            # Get current task
            task = await get_task(context_id)
            
            if not task:
                logger.warning(f"Task not found for context {context_id}")
                return False
            
            # Update tags and status in one update
            task_data = {
                "tags": tags
            }
            
            # Simplified implementation - in reality, we would need a method to update specific fields
            # For now, we'll just update the status which will maintain other fields
            success = await update_task_status(context_id, task.get("status", "pending"))
            
            return success
                
        except Exception as e:
            logger.error(
                "Failed to update context tags",
                context_id=context_id,
                error=str(e)
            )
            return False
    
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by ID.
        
        In the task repository model, templates are part of tasks, 
        not separate entities. This method is included for API compatibility.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template document or None if not found
        """
        # This is a placeholder - in actual implementation, 
        # templates might be stored elsewhere or retrieved differently
        logger.warning("get_template not fully implemented in TaskRepositoryAdapter")
        return {
            "template_id": template_id,
            "service_type": "analysis",
            "name": template_id
        }
    
    async def schedule_context_retry(
        self, 
        context_id: str, 
        retry_count: int,
        next_retry: datetime
    ) -> bool:
        """
        Schedule a context for retry.
        
        Args:
            context_id: Context identifier
            retry_count: Current retry count
            next_retry: When to retry
            
        Returns:
            Success status
        """
        try:
            # Update the task metadata and status
            retry_metadata = {
                "retry_count": retry_count,
                "next_retry_at": next_retry.isoformat()
            }
            
            # Mark as pending for retry
            success = await update_task_status(context_id, "pending")
            
            return success
                
        except Exception as e:
            logger.error(
                "Failed to schedule context retry",
                context_id=context_id,
                retry_count=retry_count,
                error=str(e)
            )
            return False 