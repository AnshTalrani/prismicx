"""
Task models for the Task Repository Service.

This module defines the data models for tasks in the system.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status enum for tasks."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class TaskType(str, Enum):
    """Type enum for tasks."""
    GENERATIVE = "GENERATIVE"
    ANALYSIS = "ANALYSIS"
    COMMUNICATION = "COMMUNICATION"
    MARKETING = "MARKETING"


class TaskRequest(BaseModel):
    """Task request data model."""
    content: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    model_config = {"arbitrary_types_allowed": True}


class TaskTemplate(BaseModel):
    """Task template data model."""
    service_type: str
    template_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    model_config = {"arbitrary_types_allowed": True}


class TaskTags(BaseModel):
    """Task tags for categorization and filtering."""
    service: Optional[str] = None
    source: Optional[str] = None
    category: Optional[str] = None
    custom_tags: Optional[Dict[str, str]] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class TaskBase(BaseModel):
    """Base task model with common fields."""
    task_id: Optional[str] = None
    task_type: str
    status: TaskStatus = TaskStatus.PENDING
    priority: Optional[int] = 5  # 1-10, lower is higher priority
    tenant_id: Optional[str] = None
    processor_id: Optional[str] = None
    batch_id: Optional[str] = None
    request: Optional[TaskRequest] = None
    template: Optional[TaskTemplate] = None
    tags: Optional[TaskTags] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    model_config = {"arbitrary_types_allowed": True}


class TaskCreate(TaskBase):
    """Model for creating a new task."""
    request: TaskRequest
    template: TaskTemplate
    tags: TaskTags = Field(default_factory=TaskTags)


class TaskUpdate(BaseModel):
    """Model for updating an existing task."""
    status: Optional[TaskStatus] = None
    priority: Optional[int] = None
    processor_id: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = {"arbitrary_types_allowed": True}


class TaskInDB(TaskBase):
    """Model for tasks as stored in the database."""
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    processing_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = Field(default_factory=dict)
    error: Optional[str] = None


class Task(TaskInDB):
    """Complete task model with all fields."""
    pass 