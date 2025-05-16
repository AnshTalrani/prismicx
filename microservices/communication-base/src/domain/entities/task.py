"""
Task Entity Module

This module defines the Task domain entity and related enumerations for the
communication-base service.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Any, Optional


class TaskStatus(Enum):
    """
    Enumeration of possible task statuses in the system.
    """
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELED = auto()
    SCHEDULED = auto()


class TaskPriority(Enum):
    """
    Enumeration of possible task priorities in the system.
    """
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass
class Task:
    """
    Domain entity representing a task in the communication-base service.
    
    A task is a unit of work that needs to be processed by the system.
    It can represent various types of communication jobs such as sending
    an email, SMS, push notification, or other communication tasks.
    """
    id: str
    type: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    tenant_id: Optional[str] = None
    title: str = ""
    description: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    worker_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    scheduled_for: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """
        Validate and initialize the Task object after creation.
        
        Sets default timestamps if not provided and validates required fields.
        """
        # Set default values for timestamps if not provided
        if not self.created_at:
            self.created_at = datetime.utcnow()
        
        if not self.updated_at:
            self.updated_at = self.created_at
        
        # Ensure data and result are dictionaries
        if self.data is None:
            self.data = {}
            
        if self.result is None:
            self.result = {}
            
        if self.tags is None:
            self.tags = []
    
    def update_status(self, new_status: TaskStatus) -> None:
        """
        Update the task status and related timestamps.
        
        Args:
            new_status: The new status to set for the task
        """
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # Update timestamps based on status changes
        if new_status == TaskStatus.IN_PROGRESS and not self.started_at:
            self.started_at = self.updated_at
            
        if new_status in (TaskStatus.COMPLETED, TaskStatus.FAILED) and not self.completed_at:
            self.completed_at = self.updated_at
    
    def add_result(self, result: Dict[str, Any]) -> None:
        """
        Add or update the task result.
        
        Args:
            result: The result data to set
        """
        self.result = result
        self.updated_at = datetime.utcnow()
    
    def set_error(self, error: str) -> None:
        """
        Set an error message for the task.
        
        Args:
            error: The error message to set
        """
        self.error = error
        self.updated_at = datetime.utcnow()
    
    def assign_worker(self, worker_id: str) -> None:
        """
        Assign a worker to this task.
        
        Args:
            worker_id: The ID of the worker to assign
        """
        self.worker_id = worker_id
        self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the task if it doesn't already exist.
        
        Args:
            tag: The tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the task if it exists.
        
        Args:
            tag: The tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()
    
    def is_due(self) -> bool:
        """
        Check if a scheduled task is due for execution.
        
        Returns:
            bool: True if the task is scheduled and the scheduled time has passed
        """
        if self.status != TaskStatus.SCHEDULED:
            return False
            
        if not self.scheduled_for:
            return False
            
        return datetime.utcnow() >= self.scheduled_for
    
    def has_parent(self) -> bool:
        """
        Check if this task has a parent task.
        
        Returns:
            bool: True if the task has a parent task ID
        """
        return self.parent_task_id is not None
    
    def mark_completed(self, result: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark the task as completed and set its result if provided.
        
        Args:
            result: Optional result data to set
        """
        if result:
            self.result = result
            
        self.update_status(TaskStatus.COMPLETED)
    
    def mark_failed(self, error: Optional[str] = None) -> None:
        """
        Mark the task as failed and set an error message if provided.
        
        Args:
            error: Optional error message to set
        """
        if error:
            self.error = error
            
        self.update_status(TaskStatus.FAILED)
    
    def schedule(self, scheduled_time: datetime) -> None:
        """
        Schedule the task for execution at a specific time.
        
        Args:
            scheduled_time: The time at which the task should be executed
        """
        self.scheduled_for = scheduled_time
        self.update_status(TaskStatus.SCHEDULED)
        self.updated_at = datetime.utcnow() 