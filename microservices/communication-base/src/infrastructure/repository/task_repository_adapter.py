"""
Task Repository Adapter Module

This module provides an adapter for the central task repository service.
It connects the communication-base microservice to the centralized task management system.
"""

import logging
import json
import aiohttp
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

import structlog

from ...config.settings import get_settings
from ..tenant.tenant_context import TenantContext

logger = structlog.get_logger(__name__)


class TaskRepositoryAdapter:
    """
    Adapter for the task repository service.
    
    This class provides methods to interact with the central task repository
    service for task management operations.
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
        self.processor_id = f"communication-{settings.service_name}"
        
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
    
    async def get_pending_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get pending tasks from the repository.
        
        Args:
            limit: Maximum number of tasks to retrieve.
            
        Returns:
            List of pending task data.
        """
        await self._ensure_client_session()
        
        tenant_id = TenantContext.get_current_tenant()
        
        try:
            params = {
                "task_type": "COMMUNICATION",
                "service_tag": get_settings().service_name,
                "limit": limit
            }
            
            if tenant_id:
                params["tenant_id"] = tenant_id
            
            async with self.client_session.get(
                f"{self.base_url}/tasks/pending",
                params=params
            ) as response:
                if response.status == 200:
                    tasks = await response.json()
                    return tasks
                else:
                    error_text = await response.text()
                    logger.error(
                        "Failed to get pending tasks",
                        status=response.status,
                        error=error_text
                    )
                    return []
        except Exception as e:
            logger.error("Error retrieving pending tasks", error=str(e))
            return []
    
    async def create_task(self, task_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new task in the repository.
        
        Args:
            task_data: Task data to create.
            
        Returns:
            Task ID if successful, None otherwise.
        """
        await self._ensure_client_session()
        
        try:
            async with self.client_session.post(
                f"{self.base_url}/tasks",
                json=task_data
            ) as response:
                if response.status == 201:
                    result = await response.json()
                    task_id = result.get("task_id")
                    logger.info("Created task", task_id=task_id)
                    return task_id
                else:
                    error_text = await response.text()
                    logger.error(
                        "Failed to create task",
                        status=response.status,
                        error=error_text
                    )
                    return None
        except Exception as e:
            logger.error("Error creating task", error=str(e))
            return None
    
    async def claim_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Claim a task for processing.
        
        Args:
            task_id: Task ID to claim.
            
        Returns:
            Claimed task data if successful, None otherwise.
        """
        await self._ensure_client_session()
        
        tenant_id = TenantContext.get_current_tenant()
        
        try:
            data = {
                "processor_id": self.processor_id
            }
            
            if tenant_id:
                data["tenant_id"] = tenant_id
            
            async with self.client_session.post(
                f"{self.base_url}/tasks/{task_id}/claim",
                json=data
            ) as response:
                if response.status == 200:
                    task = await response.json()
                    return task
                else:
                    error_text = await response.text()
                    logger.error(
                        "Failed to claim task",
                        task_id=task_id,
                        status=response.status,
                        error=error_text
                    )
                    return None
        except Exception as e:
            logger.error("Error claiming task", task_id=task_id, error=str(e))
            return None
    
    async def mark_task_completed(self, task_id: str, results: Dict[str, Any]) -> bool:
        """
        Mark a task as completed with results.
        
        Args:
            task_id: Task ID to update.
            results: Task processing results.
            
        Returns:
            True if successful, False otherwise.
        """
        await self._ensure_client_session()
        
        try:
            data = {
                "results": results,
                "processor_id": self.processor_id
            }
            
            async with self.client_session.post(
                f"{self.base_url}/tasks/{task_id}/complete",
                json=data
            ) as response:
                if response.status == 200:
                    return True
                else:
                    error_text = await response.text()
                    logger.error(
                        "Failed to mark task as completed",
                        task_id=task_id,
                        status=response.status,
                        error=error_text
                    )
                    return False
        except Exception as e:
            logger.error("Error marking task as completed", task_id=task_id, error=str(e))
            return False
    
    async def mark_task_failed(self, task_id: str, error: str) -> bool:
        """
        Mark a task as failed with error information.
        
        Args:
            task_id: Task ID to update.
            error: Error message.
            
        Returns:
            True if successful, False otherwise.
        """
        await self._ensure_client_session()
        
        try:
            data = {
                "error": error,
                "processor_id": self.processor_id
            }
            
            async with self.client_session.post(
                f"{self.base_url}/tasks/{task_id}/fail",
                json=data
            ) as response:
                if response.status == 200:
                    return True
                else:
                    error_text = await response.text()
                    logger.error(
                        "Failed to mark task as failed",
                        task_id=task_id,
                        status=response.status,
                        error=error_text
                    )
                    return False
        except Exception as e:
            logger.error("Error marking task as failed", task_id=task_id, error=str(e))
            return False
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID to retrieve.
            
        Returns:
            Task data if found, None otherwise.
        """
        await self._ensure_client_session()
        
        try:
            async with self.client_session.get(
                f"{self.base_url}/tasks/{task_id}"
            ) as response:
                if response.status == 200:
                    task = await response.json()
                    return task
                else:
                    error_text = await response.text()
                    logger.error(
                        "Failed to get task",
                        task_id=task_id,
                        status=response.status,
                        error=error_text
                    )
                    return None
        except Exception as e:
            logger.error("Error retrieving task", task_id=task_id, error=str(e))
            return None 