"""Workflow model definitions."""
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

class WorkflowStatus(str, Enum):
    """Workflow status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowStepType(str, Enum):
    """Workflow step type enumeration."""
    MESSAGE = "message"
    INPUT = "input"
    DECISION = "decision"
    ACTION = "action"

class WorkflowStep(BaseModel):
    """Workflow step model."""
    step_id: str
    step_type: WorkflowStepType
    name: Optional[str] = None
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    next_steps: List[Dict[str, str]] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True

class Workflow(BaseModel):
    """Workflow model."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.DRAFT
    steps: List[WorkflowStep] = Field(default_factory=list)
    start_step: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
