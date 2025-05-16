"""
Task Repository Adapter

This module provides an adapter between the Context Manager and the Task Repository Service
in the database layer. It allows the Context Manager to use the centralized Task Repository Service
instead of a local MongoDB instance.

Previously, context storage was handled by MongoContextRepository with direct MongoDB access.
This adapter replaces that implementation with calls to the database layer's task-repo-service.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

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

from src.utils.id_utils import generate_request_id

logger = logging.getLogger(__name__)


class TaskRepositoryAdapter:
    """
    Adapter that connects the agent microservice to the Task Repository Service in the database layer.
    
    This adapter implements the same interface as the previous MongoContextRepository,
    but instead of directly using MongoDB, it uses the centralized Task Repository Service
    through the task client library. This promotes a more maintainable microservice architecture
    with a single source of truth for task data.
    """
    
    def __init__(self, service_id: str = "agent"):
        """
        Initialize the adapter.
        
        Args:
            service_id: Identifier for this service instance
        """
        self.service_id = service_id
        logger.info(f"Initialized TaskRepositoryAdapter with service_id: {service_id}")
    
    async def save(self, context_id: str, context: Dict[str, Any]) -> bool:
        """
        Save or update a context by creating or updating a task in the task repository.
        
        Args:
            context_id: Unique context identifier
            context: Context data to save
            
        Returns:
            Success status
        """
        try:
            # Extract relevant fields from the context
            request_data = context.get("request", {})
            template_data = context.get("template", {})
            status = context.get("status", "pending")
            tags = context.get("tags", {})
            service_type = template_data.get("service_type")
            priority = context.get("priority", 5)
            
            if not service_type:
                logger.error(f"Missing service_type in context {context_id}")
                return False
            
            # Prepare task data
            task_data = {
                "task_id": context_id,
                "task_type": service_type,
                "status": status,
                "priority": priority,
                "request": {
                    "content": request_data,
                    "metadata": request_data.get("metadata", {})
                },
                "template": {
                    "service_type": service_type,
                    "template_data": template_data
                },
                "tags": tags,
                "metadata": context.get("metadata", {}),
                "batch_id": context.get("parent_id")
            }
            
            # If this is a new task (pending status), create it
            if status == "pending" and not await get_task(context_id):
                task_id = await create_task(task_data)
                if task_id:
                    logger.info(f"Created task with ID: {task_id}")
                    return True
                else:
                    logger.error(f"Failed to create task for context {context_id}")
                    return False
            
            # For other statuses, we're updating the task
            if status == "completed":
                # For completed tasks, we need to include results
                result = context.get("results", {})
                success = await complete_task(context_id, result)
                if success:
                    logger.info(f"Marked task {context_id} as completed")
                    return True
                else:
                    logger.error(f"Failed to mark task {context_id} as completed")
                    return False
            elif status == "failed":
                # For failed tasks, we need to include error information
                error_info = context.get("results", {}).get("error", "Unknown error")
                success = await fail_task(context_id, error_info)
                if success:
                    logger.info(f"Marked task {context_id} as failed")
                    return True
                else:
                    logger.error(f"Failed to mark task {context_id} as failed")
                    return False
            else:
                # For other status updates, use update_task_status
                success = await update_task_status(context_id, status)
                if success:
                    logger.info(f"Updated task {context_id} status to {status}")
                    return True
                else:
                    logger.warning(f"Failed to update task {context_id} status to {status}")
                    return False
                
        except Exception as e:
            logger.error(f"Error saving context {context_id} to task repository: {str(e)}")
            return False
    
    async def get(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a context by retrieving the corresponding task from the repository.
        
        Args:
            context_id: Context identifier
            
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
                "priority": task.get("priority", 5),
                "request": task.get("request", {}).get("content", {}),
                "template": task.get("template", {}).get("template_data", {}),
                "tags": task.get("tags", {}),
                "metadata": task.get("metadata", {}),
                "created_at": task.get("created_at"),
                "updated_at": task.get("updated_at"),
                "results": task.get("result", {})
            }
            
            # Add parent ID if available
            if task.get("batch_id"):
                context["parent_id"] = task.get("batch_id")
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting context {context_id} from task repository: {str(e)}")
            return None
    
    async def delete(self, context_id: str) -> bool:
        """
        Delete a context by deleting the corresponding task.
        
        Args:
            context_id: Context identifier
            
        Returns:
            Success status
        """
        try:
            # The task repository client doesn't directly support deletion
            # Mark the task as "deleted" status instead
            success = await update_task_status(context_id, "deleted")
            if success:
                logger.info(f"Marked task {context_id} as deleted")
                return True
            else:
                logger.warning(f"Failed to mark task {context_id} as deleted")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting context {context_id}: {str(e)}")
            return False
    
    async def update_field(self, context_id: str, field: str, value: Any) -> bool:
        """
        Update a specific field in a context.
        
        Args:
            context_id: Context identifier
            field: Field name to update
            value: New value
            
        Returns:
            Success status
        """
        try:
            # For status updates, we have specialized handling
            if field == "status":
                success = await update_task_status(context_id, value)
                if success:
                    logger.info(f"Updated task {context_id} status to {value}")
                    return True
                else:
                    logger.warning(f"Failed to update task {context_id} status to {value}")
                    return False
            else:
                # For other fields, we need to get the task, update it, and save it back
                context = await self.get(context_id)
                if not context:
                    logger.warning(f"Context {context_id} not found for field update")
                    return False
                
                # Update the field
                if '.' in field:
                    # Handle nested fields like 'request.priority'
                    parts = field.split('.')
                    current = context
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = value
                else:
                    context[field] = value
                
                # Save the updated context
                return await self.save(context_id, context)
                
        except Exception as e:
            logger.error(f"Error updating field {field} for context {context_id}: {str(e)}")
            return False
    
    async def find_by_status(self, status: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find contexts by status by retrieving tasks with the specified status.
        
        Args:
            status: Status to filter by
            limit: Maximum number of results
            
        Returns:
            List of matching contexts
        """
        try:
            if status == "pending":
                # For pending tasks, we can use get_pending_tasks
                tasks = await get_pending_tasks(limit=limit)
                
                # Convert tasks to contexts
                contexts = []
                for task in tasks:
                    # Extract task data into context format
                    context = {
                        "_id": task.get("task_id") or task.get("_id"),
                        "status": task.get("status", "unknown"),
                        "priority": task.get("priority", 5),
                        "request": task.get("request", {}).get("content", {}),
                        "template": task.get("template", {}).get("template_data", {}),
                        "tags": task.get("tags", {}),
                        "metadata": task.get("metadata", {}),
                        "created_at": task.get("created_at"),
                        "updated_at": task.get("updated_at"),
                        "results": task.get("result", {})
                    }
                    contexts.append(context)
                
                return contexts
            else:
                # Other status queries are not directly supported by the client
                # This would need to be added to the task repository service
                logger.warning(f"Finding contexts by status '{status}' not directly supported")
                return []
                
        except Exception as e:
            logger.error(f"Error finding contexts by status {status}: {str(e)}")
            return []
    
    async def find_by_user(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find contexts by user ID.
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            
        Returns:
            List of matching contexts
        """
        try:
            # This would need to be implemented in the task repository service
            logger.warning(f"Finding contexts by user ID not directly supported")
            return []
                
        except Exception as e:
            logger.error(f"Error finding contexts for user {user_id}: {str(e)}")
            return []
    
    async def save_batch_context(self, batch_id: str, context: Dict[str, Any]) -> bool:
        """
        Save a batch context.
        
        Args:
            batch_id: Batch identifier
            context: Batch context data
            
        Returns:
            Success status
        """
        try:
            # Create a special task to represent the batch
            task_data = {
                "task_id": batch_id,
                "task_type": "BATCH",
                "status": context.get("status", "pending"),
                "priority": context.get("priority", 5),
                "metadata": {
                    "is_batch": True,
                    "batch_data": context
                }
            }
            
            task_id = await create_task(task_data)
            if task_id:
                logger.info(f"Created batch task with ID: {batch_id}")
                return True
            else:
                logger.error(f"Failed to create batch task for batch {batch_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving batch context {batch_id}: {str(e)}")
            return False
    
    async def get_batch_context(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a batch context.
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Batch context or None if not found
        """
        try:
            # Retrieve the batch task
            task = await get_task(batch_id)
            
            if not task or not task.get("metadata", {}).get("is_batch"):
                logger.warning(f"Batch task not found for batch {batch_id}")
                return None
            
            # Extract the batch context from the metadata
            return task.get("metadata", {}).get("batch_data", {})
                
        except Exception as e:
            logger.error(f"Error getting batch context {batch_id}: {str(e)}")
            return None
    
    async def delete_old_contexts(self, days: int = 30) -> int:
        """
        Delete old contexts.
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of deleted contexts
        """
        try:
            # The task repository should handle cleanup automatically
            # This method is included for compatibility with the repository interface
            logger.info(f"Context cleanup is handled by the task repository service")
            return 0
                
        except Exception as e:
            logger.error(f"Error in context cleanup: {str(e)}")
            return 0 