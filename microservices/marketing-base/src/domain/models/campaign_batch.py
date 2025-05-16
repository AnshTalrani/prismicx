"""
Campaign Batch Model for organizing and processing groups of recipients.

This module defines the CampaignBatch class which represents a grouping of recipients
within a campaign workflow, allowing for organized processing, tracking, and monitoring
of recipient communications across all campaign stages.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
import uuid

from .campaign import Recipient, CampaignStatus


class BatchStatus(str, Enum):
    """Enum representing the status of a campaign batch."""
    CREATED = "created"
    VALIDATING = "validating"
    QUEUED = "queued"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchPriority(str, Enum):
    """Enum representing the priority levels for batch processing."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class StageProgress:
    """Tracks the progress of a batch through a specific campaign stage."""
    stage_id: str
    status: str = "pending"  # pending, in_progress, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    pending_count: int = 0
    skip_count: int = 0
    error_details: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stage progress to a dictionary."""
        return {
            "stage_id": self.stage_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "pending_count": self.pending_count,
            "skip_count": self.skip_count,
            "error_details": self.error_details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StageProgress':
        """Create a StageProgress instance from a dictionary."""
        progress = cls(
            stage_id=data["stage_id"],
            status=data.get("status", "pending"),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            pending_count=data.get("pending_count", 0),
            skip_count=data.get("skip_count", 0),
            error_details=data.get("error_details", [])
        )
        
        if data.get("started_at"):
            progress.started_at = datetime.fromisoformat(data["started_at"])
        
        if data.get("completed_at"):
            progress.completed_at = datetime.fromisoformat(data["completed_at"])
        
        return progress


@dataclass
class CampaignBatch:
    """
    Represents a batch of recipients to be processed through a workflow campaign.
    
    A batch groups recipients together for processing and tracking purposes,
    allowing for more efficient handling of communications and better monitoring.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    campaign_id: str
    name: str
    description: Optional[str] = None
    
    # Batch metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    status: BatchStatus = BatchStatus.CREATED
    priority: BatchPriority = BatchPriority.MEDIUM
    
    # Recipients and processing
    recipients: List[Recipient] = field(default_factory=list)
    total_recipient_count: int = 0
    current_stage_id: Optional[str] = None
    stage_progress: List[StageProgress] = field(default_factory=list)
    
    # Error tracking
    error_count: int = 0
    last_error: Optional[str] = None
    max_retries: int = 3
    retry_count: int = 0
    
    # Additional data
    tags: List[str] = field(default_factory=list)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize derived values after object creation."""
        if not self.total_recipient_count and self.recipients:
            self.total_recipient_count = len(self.recipients)
    
    def add_recipient(self, recipient: Recipient) -> None:
        """
        Add a recipient to the batch.
        
        Args:
            recipient: The recipient to add
        """
        self.recipients.append(recipient)
        self.total_recipient_count = len(self.recipients)
        self.updated_at = datetime.utcnow()
    
    def add_recipients(self, recipients: List[Recipient]) -> None:
        """
        Add multiple recipients to the batch.
        
        Args:
            recipients: The list of recipients to add
        """
        self.recipients.extend(recipients)
        self.total_recipient_count = len(self.recipients)
        self.updated_at = datetime.utcnow()
    
    def update_status(self, status: BatchStatus) -> None:
        """
        Update the status of the batch.
        
        Args:
            status: The new status
        """
        self.status = status
        self.updated_at = datetime.utcnow()
    
    def update_stage_progress(self, stage_id: str, **kwargs) -> None:
        """
        Update the progress of a specific stage.
        
        Args:
            stage_id: The ID of the stage to update
            **kwargs: The stage progress fields to update
        """
        # Find the existing progress for this stage
        stage_progress = next((p for p in self.stage_progress if p.stage_id == stage_id), None)
        
        # If no progress exists for this stage, create a new one
        if not stage_progress:
            stage_progress = StageProgress(stage_id=stage_id)
            self.stage_progress.append(stage_progress)
        
        # Update the progress fields
        for key, value in kwargs.items():
            if hasattr(stage_progress, key):
                setattr(stage_progress, key, value)
        
        self.updated_at = datetime.utcnow()
    
    def move_to_next_stage(self, next_stage_id: str) -> None:
        """
        Move the batch to the next stage in the workflow.
        
        Args:
            next_stage_id: The ID of the next stage
        """
        # Update the current stage ID
        self.current_stage_id = next_stage_id
        
        # Initialize progress for the new stage if it doesn't exist
        if not any(p.stage_id == next_stage_id for p in self.stage_progress):
            self.stage_progress.append(StageProgress(
                stage_id=next_stage_id,
                status="pending",
                pending_count=self.total_recipient_count
            ))
        
        self.updated_at = datetime.utcnow()
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the batch progress across all stages.
        
        Returns:
            A dictionary with progress summary information
        """
        total_stages = len(self.stage_progress)
        completed_stages = sum(1 for p in self.stage_progress if p.status == "completed")
        failed_stages = sum(1 for p in self.stage_progress if p.status == "failed")
        
        total_success = sum(p.success_count for p in self.stage_progress)
        total_failure = sum(p.failure_count for p in self.stage_progress)
        
        return {
            "total_stages": total_stages,
            "completed_stages": completed_stages,
            "failed_stages": failed_stages,
            "progress_percentage": (completed_stages / total_stages * 100) if total_stages > 0 else 0,
            "total_success": total_success,
            "total_failure": total_failure,
            "success_rate": (total_success / (total_success + total_failure) * 100) 
                           if (total_success + total_failure) > 0 else 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the campaign batch to a dictionary."""
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "status": self.status.value,
            "priority": self.priority.value,
            "recipients": [recipient.to_dict() for recipient in self.recipients],
            "total_recipient_count": self.total_recipient_count,
            "current_stage_id": self.current_stage_id,
            "stage_progress": [progress.to_dict() for progress in self.stage_progress],
            "error_count": self.error_count,
            "last_error": self.last_error,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "tags": self.tags,
            "custom_attributes": self.custom_attributes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CampaignBatch':
        """Create a CampaignBatch instance from a dictionary."""
        # Create the batch without complex attributes
        batch = cls(
            id=data.get("id", str(uuid.uuid4())),
            campaign_id=data["campaign_id"],
            name=data["name"],
            description=data.get("description"),
            created_by=data.get("created_by"),
            status=BatchStatus(data.get("status", "created")),
            priority=BatchPriority(data.get("priority", "medium")),
            total_recipient_count=data.get("total_recipient_count", 0),
            current_stage_id=data.get("current_stage_id"),
            error_count=data.get("error_count", 0),
            last_error=data.get("last_error"),
            max_retries=data.get("max_retries", 3),
            retry_count=data.get("retry_count", 0),
            tags=data.get("tags", []),
            custom_attributes=data.get("custom_attributes", {})
        )
        
        # Convert timestamps
        if "created_at" in data:
            batch.created_at = datetime.fromisoformat(data["created_at"])
        
        if "updated_at" in data:
            batch.updated_at = datetime.fromisoformat(data["updated_at"])
        
        # Parse recipients
        if "recipients" in data:
            batch.recipients = [
                Recipient.from_dict(recipient_data)
                for recipient_data in data["recipients"]
            ]
        
        # Parse stage progress
        if "stage_progress" in data:
            batch.stage_progress = [
                StageProgress.from_dict(progress_data)
                for progress_data in data["stage_progress"]
            ]
        
        return batch 