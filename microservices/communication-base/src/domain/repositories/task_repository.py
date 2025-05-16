"""
Task Repository Interface Module

This module defines the abstract interface for task repositories,
providing methods for CRUD operations on Task entities.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from ..entities.task import Task, TaskStatus, TaskPriority


class TaskRepository(ABC):
    """
    Abstract interface for task repositories.
    
    This interface defines the required methods for interacting with
    task storage, regardless of the specific implementation details.
    """
    
    @abstractmethod
    async def create(self, task: Task) -> Task:
        """
        Create a new task in the repository.
        
        Args:
            task: The task to create
            
        Returns:
            The created task with any repository-assigned fields (like ID)
            
        Raises:
            RepositoryError: If there's an issue with the repository operation
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, task_id: str, tenant_id: Optional[str] = None) -> Optional[Task]:
        """
        Retrieve a task by its ID.
        
        Args:
            task_id: The ID of the task to retrieve
            tenant_id: Optional tenant ID for multi-tenancy support
            
        Returns:
            The task if found, otherwise None
            
        Raises:
            RepositoryError: If there's an issue with the repository operation
        """
        pass
    
    @abstractmethod
    async def update(self, task: Task) -> Task:
        """
        Update an existing task in the repository.
        
        Args:
            task: The task with updated fields
            
        Returns:
            The updated task
            
        Raises:
            RepositoryError: If there's an issue with the repository operation
            NotFoundError: If the task doesn't exist
        """
        pass
    
    @abstractmethod
    async def delete(self, task_id: str, tenant_id: Optional[str] = None) -> bool:
        """
        Delete a task from the repository.
        
        Args:
            task_id: The ID of the task to delete
            tenant_id: Optional tenant ID for multi-tenancy support
            
        Returns:
            True if the task was deleted, False if it didn't exist
            
        Raises:
            RepositoryError: If there's an issue with the repository operation
        """
        pass
    
    @abstractmethod
    async def list(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[Union[TaskStatus, List[TaskStatus]]] = None,
        type_filter: Optional[Union[str, List[str]]] = None,
        priority: Optional[Union[TaskPriority, List[TaskPriority]]] = None,
        tags: Optional[List[str]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        scheduled_after: Optional[datetime] = None,
        scheduled_before: Optional[datetime] = None,
        worker_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[Task]:
        """
        List tasks with optional filtering criteria.
        
        Args:
            tenant_id: Filter by tenant ID
            status: Filter by task status or list of statuses
            type_filter: Filter by task type or list of types
            priority: Filter by task priority or list of priorities
            tags: Filter by one or more tags (tasks must have all specified tags)
            created_after: Filter tasks created after this datetime
            created_before: Filter tasks created before this datetime
            scheduled_after: Filter tasks scheduled after this datetime
            scheduled_before: Filter tasks scheduled before this datetime
            worker_id: Filter by assigned worker ID
            parent_task_id: Filter by parent task ID
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip for pagination
            sort_by: Field to sort by
            sort_order: Sort order ("asc" or "desc")
            
        Returns:
            List of tasks matching the criteria
            
        Raises:
            RepositoryError: If there's an issue with the repository operation
            ValueError: If invalid filter parameters are provided
        """
        pass
    
    @abstractmethod
    async def count(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[Union[TaskStatus, List[TaskStatus]]] = None,
        type_filter: Optional[Union[str, List[str]]] = None,
        priority: Optional[Union[TaskPriority, List[TaskPriority]]] = None,
        tags: Optional[List[str]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        scheduled_after: Optional[datetime] = None,
        scheduled_before: Optional[datetime] = None,
        worker_id: Optional[str] = None,
        parent_task_id: Optional[str] = None
    ) -> int:
        """
        Count tasks with optional filtering criteria.
        
        Args:
            tenant_id: Filter by tenant ID
            status: Filter by task status or list of statuses
            type_filter: Filter by task type or list of types
            priority: Filter by task priority or list of priorities
            tags: Filter by one or more tags (tasks must have all specified tags)
            created_after: Filter tasks created after this datetime
            created_before: Filter tasks created before this datetime
            scheduled_after: Filter tasks scheduled after this datetime
            scheduled_before: Filter tasks scheduled before this datetime
            worker_id: Filter by assigned worker ID
            parent_task_id: Filter by parent task ID
            
        Returns:
            The count of tasks matching the criteria
            
        Raises:
            RepositoryError: If there's an issue with the repository operation
            ValueError: If invalid filter parameters are provided
        """
        pass
    
    @abstractmethod
    async def get_next_scheduled(
        self,
        tenant_id: Optional[str] = None,
        type_filter: Optional[Union[str, List[str]]] = None,
        limit: int = 10
    ) -> List[Task]:
        """
        Get the next scheduled tasks sorted by scheduled time (ascending).
        
        Args:
            tenant_id: Optional tenant ID filter
            type_filter: Optional task type filter
            limit: Maximum number of tasks to return
            
        Returns:
            List of scheduled tasks
            
        Raises:
            RepositoryError: If there's an issue with the repository operation
        """
        pass
    
    @abstractmethod
    async def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        tenant_id: Optional[str] = None,
        error: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> Optional[Task]:
        """
        Update the status of a task.
        
        Args:
            task_id: The ID of the task to update
            status: The new status
            tenant_id: Optional tenant ID for multi-tenancy support
            error: Optional error message (for failed tasks)
            result: Optional result data (for completed tasks)
            
        Returns:
            The updated task, or None if not found
            
        Raises:
            RepositoryError: If there's an issue with the repository operation
        """
        pass
    
    @abstractmethod
    async def assign_worker(
        self, 
        task_id: str, 
        worker_id: str,
        tenant_id: Optional[str] = None
    ) -> Optional[Task]:
        """
        Assign a worker to a task.
        
        Args:
            task_id: The ID of the task to update
            worker_id: The ID of the worker to assign
            tenant_id: Optional tenant ID for multi-tenancy support
            
        Returns:
            The updated task, or None if not found
            
        Raises:
            RepositoryError: If there's an issue with the repository operation
        """
        pass 