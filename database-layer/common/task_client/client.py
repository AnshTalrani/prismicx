"""
Task Client for interacting with the task repository service.

This module provides a client for interacting with the task repository service,
which is responsible for creating and managing tasks. The client provides methods
for creating, retrieving, claiming, completing, and failing tasks.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional, Union
import httpx

logger = logging.getLogger(__name__)

class TaskClient:
    """
    Client for interacting with the task repository service.
    
    Provides methods for creating, retrieving, claiming, completing, and failing tasks.
    """
    
    def __init__(self, service_url: str, api_key: str, service_id: str):
        """
        Initialize the task client.
        
        Args:
            service_url: URL of the task repository service
            api_key: API key for authenticating with the service
            service_id: ID of the service using the client
        """
        self.service_url = service_url.rstrip("/") + "/api/v1"
        self.api_key = api_key
        self.service_id = service_id
        self.client = httpx.AsyncClient(
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "x-service-id": service_id
            },
            timeout=30.0
        )
        logger.info(f"Initialized task client for service {service_id} with URL {service_url}")
    
    async def create_task(self, task_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new task in the repository.
        
        Args:
            task_data: Task data, including type, priority, and content
            
        Returns:
            Task ID if created, None otherwise
        """
        try:
            response = await self.client.post(
                f"{self.service_url}/tasks",
                json=task_data
            )
            
            if response.status_code == 201:
                task_id = response.json().get("task_id")
                logger.info(f"Created task {task_id}")
                return task_id
            else:
                logger.error(f"Failed to create task: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return None
    
    async def get_pending_tasks(self, task_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get pending tasks from the repository.
        
        Args:
            task_type: Optional task type to filter by
            limit: Maximum number of tasks to retrieve
            
        Returns:
            List of pending tasks
        """
        try:
            params = {"limit": limit}
            if task_type:
                params["task_type"] = task_type
                
            response = await self.client.get(
                f"{self.service_url}/tasks/pending",
                params=params
            )
            
            if response.status_code == 200:
                tasks = response.json().get("tasks", [])
                logger.info(f"Retrieved {len(tasks)} pending tasks")
                return tasks
            else:
                logger.error(f"Failed to get pending tasks: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error getting pending tasks: {str(e)}")
            return []
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task by ID from the repository.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            Task data if found, None otherwise
        """
        try:
            response = await self.client.get(
                f"{self.service_url}/tasks/{task_id}"
            )
            
            if response.status_code == 200:
                task = response.json()
                logger.info(f"Retrieved task {task_id}")
                return task
            elif response.status_code == 404:
                logger.warning(f"Task {task_id} not found")
                return None
            else:
                logger.error(f"Failed to get task {task_id}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {str(e)}")
            return None
    
    async def claim_task(self, task_id: str) -> bool:
        """
        Claim a task for processing.
        
        Args:
            task_id: ID of the task to claim
            
        Returns:
            Success status
        """
        try:
            response = await self.client.post(
                f"{self.service_url}/tasks/{task_id}/claim",
                json={"service_id": self.service_id}
            )
            
            if response.status_code == 200:
                logger.info(f"Claimed task {task_id}")
                return True
            else:
                logger.error(f"Failed to claim task {task_id}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error claiming task {task_id}: {str(e)}")
            return False
    
    async def complete_task(self, task_id: str, result: Dict[str, Any]) -> bool:
        """
        Mark a task as completed with result.
        
        Args:
            task_id: ID of the task to complete
            result: Task result data
            
        Returns:
            Success status
        """
        try:
            response = await self.client.post(
                f"{self.service_url}/tasks/{task_id}/complete",
                json={"result": result}
            )
            
            if response.status_code == 200:
                logger.info(f"Completed task {task_id}")
                return True
            else:
                logger.error(f"Failed to complete task {task_id}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error completing task {task_id}: {str(e)}")
            return False
    
    async def fail_task(self, task_id: str, error: Union[str, Dict[str, Any]]) -> bool:
        """
        Mark a task as failed with error.
        
        Args:
            task_id: ID of the task to fail
            error: Error information (string or dict)
            
        Returns:
            Success status
        """
        try:
            error_data = error if isinstance(error, dict) else {"message": str(error)}
            response = await self.client.post(
                f"{self.service_url}/tasks/{task_id}/fail",
                json={"error": error_data}
            )
            
            if response.status_code == 200:
                logger.info(f"Failed task {task_id}")
                return True
            else:
                logger.error(f"Failed to mark task {task_id} as failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error failing task {task_id}: {str(e)}")
            return False
            
    async def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update the status of a task.
        
        Args:
            task_id: ID of the task to update
            status: New status for the task
            
        Returns:
            Success status
        """
        try:
            response = await self.client.patch(
                f"{self.service_url}/tasks/{task_id}/status",
                json={"status": status}
            )
            
            if response.status_code == 200:
                logger.info(f"Updated task {task_id} status to {status}")
                return True
            else:
                logger.error(f"Failed to update task {task_id} status: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error updating task {task_id} status: {str(e)}")
            return False

# Initialize client instance with environment variables
service_url = os.environ.get("TASK_SERVICE_URL", "http://task-repository-service:8000")
api_key = os.environ.get("TASK_SERVICE_API_KEY", "default-api-key")
service_id = os.environ.get("SERVICE_ID", "default-service")

client = TaskClient(service_url, api_key, service_id)

# Provide module-level functions that use the client instance
async def create_task(task_data: Dict[str, Any]) -> Optional[str]:
    return await client.create_task(task_data)

async def get_pending_tasks(task_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    return await client.get_pending_tasks(task_type, limit)

async def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    return await client.get_task(task_id)
    
async def claim_task(task_id: str) -> bool:
    return await client.claim_task(task_id)

async def complete_task(task_id: str, result: Dict[str, Any]) -> bool:
    return await client.complete_task(task_id, result)

async def fail_task(task_id: str, error: Union[str, Dict[str, Any]]) -> bool:
    return await client.fail_task(task_id, error)
    
async def update_task_status(task_id: str, status: str) -> bool:
    return await client.update_task_status(task_id, status) 