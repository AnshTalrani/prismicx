"""
Task Repository Adapter Module

This module provides an adapter for the central task repository service.
It connects the generative-base microservice to the centralized task management system
and implements the Repository interface directly.
"""

import logging
import json
import aiohttp
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone

import structlog

from ...common.config import get_settings
from ...repository.repository import Repository  # Import the Repository interface
from ...multitenant import TenantContext
from ..mapper.task_mapper import TaskMapper  # Import the mapper for task-context conversion

logger = structlog.get_logger(__name__)


class TaskRepositoryAdapter(Repository):  # Implement Repository directly
    """
    Adapter for the task repository service.
    
    This class provides methods to interact with the central task repository
    service for task management operations. It directly implements the Repository
    interface.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the task repository adapter.
        
        Args:
            base_url: Base URL for the task repository service API.
                      If None, uses the configuration.
        """
        settings = get_settings()
        self.base_url = base_url or settings.task_repo_url
        self.client_session = None
        self.processor_id = f"generative-{settings.service_type}"
        
        logger.info("Task repository adapter initialized", base_url=self.base_url)
    
    async def _ensure_client_session(self):
        """Ensure aiohttp client session is initialized."""
        if self.client_session is None:
            self.client_session = aiohttp.ClientSession(
                headers={"Content-Type": "application/json"}
            )
    
    async def close(self):
        """Close the HTTP client session."""
        if self.client_session:
            await self.client_session.close()
            self.client_session = None
            logger.info("Task repository adapter client session closed")
    
    def is_connected(self) -> bool:
        """
        Check if the repository is connected.
        
        Returns:
            True as the task repository connects on demand.
        """
        return True
    
    async def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a context by ID.
        
        Args:
            context_id: Context ID
            
        Returns:
            Context document or None if not found
        """
        task = await self.get_task(context_id)
        if task:
            return TaskMapper.task_to_context(task)
        return None
    
    async def get_next_pending_context(self) -> Optional[Dict[str, Any]]:
        """
        Get the next pending context for processing.
        
        Returns:
            The next pending context, or None if no pending contexts
        """
        # Get a batch of 1 pending task
        tasks = await self.get_pending_tasks(limit=1)
        if tasks and len(tasks) > 0:
            # Claim the task
            task = await self.claim_task(tasks[0]["task_id"])
            if task:
                return TaskMapper.task_to_context(task)
        return None
    
    async def get_pending_contexts_batch(self, batch_size: int) -> List[Dict[str, Any]]:
        """
        Get a batch of pending contexts.
        
        Args:
            batch_size: Maximum number of contexts to retrieve
            
        Returns:
            List of pending contexts
        """
        contexts = []
        
        # Get pending tasks
        tasks = await self.get_pending_tasks(limit=batch_size)
        
        # Claim and convert each task
        for task in tasks:
            claimed_task = await self.claim_task(task["task_id"])
            if claimed_task:
                context = TaskMapper.task_to_context(claimed_task)
                contexts.append(context)
        
        return contexts
    
    async def update_context(self, context_id: str, update: Dict[str, Any]) -> bool:
        """
        Update a context document.
        
        Args:
            context_id: Context ID
            update: Update operations
            
        Returns:
            True if successful, False otherwise
        """
        # Extract the set operations
        if "$set" in update:
            set_data = update["$set"]
            
            # Handle status updates specifically
            if "status" in set_data:
                status = set_data["status"]
                if status == "completed":
                    # For completed status, include results
                    result = set_data.get("results", {})
                    return await self.mark_task_completed(context_id, result)
                elif status == "failed":
                    # For failed status, include error information
                    errors = set_data.get("errors", [])
                    error_msg = "Unknown error"
                    if errors and len(errors) > 0:
                        error_msg = errors[0].get("error", "Unknown error")
                    return await self.mark_task_failed(context_id, error_msg)
                else:
                    # For other statuses, use update task status
                    return await self.update_task_status(context_id, status)
        
        # For other updates (shouldn't normally happen with current patterns)
        logger.warning("Complex update operation not fully supported", context_id=context_id)
        return False

    async def update_context_status(
        self, 
        context_id: str, 
        status: str, 
        error: Optional[Dict[str, Any]] = None,
        retry_metadata: Optional[Dict[str, Any]] = None,
        processing_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a context's status.
        
        Args:
            context_id: Context ID
            status: New status value
            error: Error information (for failed status)
            retry_metadata: Retry metadata (for retryable errors)
            processing_metadata: Additional processing metadata
            
        Returns:
            True if successful, False otherwise
        """
        if status == "completed":
            # Completed contexts need results
            results = processing_metadata or {}
            return await self.mark_task_completed(context_id, results)
        elif status == "failed":
            # Failed contexts need error information
            error_msg = str(error) if error else "Unknown error"
            return await self.mark_task_failed(context_id, error_msg)
        return await self.update_task_status(context_id, status)
    
    async def update_context_result(
        self, 
        context_id: str, 
        status: str, 
        result: Dict[str, Any],
        processing_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a context with processing results.
        
        Args:
            context_id: Context ID
            status: New status value
            result: Processing result data
            processing_metadata: Additional processing metadata
            
        Returns:
            True if successful, False otherwise
        """
        # Add processing metadata to results if available
        if processing_metadata:
            result["processing_metadata"] = processing_metadata
        
        if status == "completed":
            return await self.mark_task_completed(context_id, result)
        elif status == "failed":
            error_msg = result.get("error", "Unknown error")
            return await self.mark_task_failed(context_id, error_msg)
        return await self.update_task_status(context_id, status)
    
    async def create_context(self, context_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new context.
        
        Args:
            context_data: Context data to create
            
        Returns:
            Context ID if successful, None otherwise
        """
        # Convert context to task
        task = TaskMapper.context_to_task(context_data)
        
        # Create task
        task_id = await self.create_task(task)
        return task_id 

    # Add other repository interface methods as needed
    
    # Keep existing task repository specific methods
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID"""
        await self._ensure_client_session()
        
        try:
            url = f"{self.base_url}/api/v1/tasks/{task_id}"
            async with self.client_session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    logger.debug(f"Task {task_id} not found")
                    return None
                else:
                    logger.error(f"Error getting task {task_id}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {str(e)}")
            return None
    
    async def get_pending_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending tasks"""
        await self._ensure_client_session()
        
        try:
            url = f"{self.base_url}/api/v1/tasks/pending"
            params = {
                "processor_type": "generative",
                "limit": limit
            }
            
            async with self.client_session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error getting pending tasks: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting pending tasks: {str(e)}")
            return []
    
    async def claim_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Claim a task for processing"""
        await self._ensure_client_session()
        
        try:
            url = f"{self.base_url}/api/v1/tasks/{task_id}/claim"
            data = {
                "processor_id": self.processor_id
            }
            
            async with self.client_session.post(url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error claiming task {task_id}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error claiming task {task_id}: {str(e)}")
            return None
    
    async def create_task(self, task_data: Dict[str, Any]) -> Optional[str]:
        """Create a new task"""
        await self._ensure_client_session()
        
        try:
            url = f"{self.base_url}/api/v1/tasks"
            
            async with self.client_session.post(url, json=task_data) as response:
                if response.status == 201:
                    result = await response.json()
                    return result.get("task_id")
                else:
                    logger.error(f"Error creating task: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return None
    
    async def mark_task_completed(self, task_id: str, result: Dict[str, Any]) -> bool:
        """Mark a task as completed with result"""
        await self._ensure_client_session()
        
        try:
            url = f"{self.base_url}/api/v1/tasks/{task_id}/complete"
            data = {
                "processor_id": self.processor_id,
                "result": result
            }
            
            async with self.client_session.post(url, json=data) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Error completing task {task_id}: {str(e)}")
            return False
    
    async def mark_task_failed(self, task_id: str, error: str) -> bool:
        """Mark a task as failed with error"""
        await self._ensure_client_session()
        
        try:
            url = f"{self.base_url}/api/v1/tasks/{task_id}/fail"
            data = {
                "processor_id": self.processor_id,
                "error": error
            }
            
            async with self.client_session.post(url, json=data) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Error failing task {task_id}: {str(e)}")
            return False
    
    async def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        await self._ensure_client_session()
        
        try:
            url = f"{self.base_url}/api/v1/tasks/{task_id}/status"
            data = {
                "processor_id": self.processor_id,
                "status": status
            }
            
            async with self.client_session.post(url, json=data) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Error updating task status {task_id}: {str(e)}")
            return False 