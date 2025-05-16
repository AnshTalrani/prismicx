"""
Campaign Execution Model for batch processing and workflow execution.

This module defines models for tracking and managing the execution of
marketing campaigns, including batch processing, recipient journeys, and
individual message deliveries.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Set
import uuid

from .campaign import CampaignStatus, RecipientStatus


class BatchStatus(str, Enum):
    """Status of a campaign batch."""
    CREATED = "created"
    VALIDATING = "validating"
    VALIDATED = "validated"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    PAUSED = "paused"


class MessageDeliveryStatus(str, Enum):
    """Status of an individual message delivery."""
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    FAILED = "failed"
    BOUNCED = "bounced"
    REJECTED = "rejected"
    UNSUBSCRIBED = "unsubscribed"
    SPAM = "spam"


class JourneyStatus(str, Enum):
    """Status of a recipient's journey through a campaign workflow."""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    PAUSED = "paused"
    EXITED = "exited"  # Exited due to a condition or action


@dataclass
class MessageDelivery:
    """
    Represents a single message delivery to a recipient.
    
    Tracks the full lifecycle of a single message, from queuing to
    delivery and recipient engagement.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    batch_id: str
    journey_id: str
    recipient_id: str
    stage_id: str
    channel: str
    template_id: str
    
    # Status and tracking
    status: MessageDeliveryStatus = MessageDeliveryStatus.QUEUED
    tracking_id: Optional[str] = None
    
    # Message content
    subject: Optional[str] = None
    content_id: Optional[str] = None
    rendered_content: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    queued_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    
    # Error tracking
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Analytics data
    click_count: int = 0
    open_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_status(self, new_status: MessageDeliveryStatus) -> None:
        """
        Update the status of the message delivery.
        
        Args:
            new_status: The new status to set
        """
        self.status = new_status
        
        # Update appropriate timestamp based on status
        now = datetime.utcnow()
        if new_status == MessageDeliveryStatus.QUEUED:
            self.queued_at = now
        elif new_status == MessageDeliveryStatus.SENDING:
            self.processed_at = now
        elif new_status == MessageDeliveryStatus.SENT:
            self.sent_at = now
        elif new_status == MessageDeliveryStatus.DELIVERED:
            self.delivered_at = now
        elif new_status == MessageDeliveryStatus.OPENED:
            self.opened_at = now
            self.open_count += 1
        elif new_status == MessageDeliveryStatus.CLICKED:
            self.clicked_at = now
            self.click_count += 1
        elif new_status in (MessageDeliveryStatus.FAILED, MessageDeliveryStatus.BOUNCED, MessageDeliveryStatus.REJECTED):
            self.failed_at = now
    
    def record_error(self, error_message: str, error_code: Optional[str] = None) -> None:
        """
        Record an error that occurred during message delivery.
        
        Args:
            error_message: Description of the error
            error_code: Optional error code for categorization
        """
        self.error_message = error_message
        if error_code:
            self.error_code = error_code
        self.update_status(MessageDeliveryStatus.FAILED)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message delivery to dictionary format."""
        result = {
            "id": self.id,
            "batch_id": self.batch_id,
            "journey_id": self.journey_id,
            "recipient_id": self.recipient_id,
            "stage_id": self.stage_id,
            "channel": self.channel,
            "template_id": self.template_id,
            "status": self.status.value,
            "tracking_id": self.tracking_id,
            "subject": self.subject,
            "content_id": self.content_id,
            "created_at": self.created_at.isoformat(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "click_count": self.click_count,
            "open_count": self.open_count,
            "metadata": self.metadata,
        }
        
        # Add timestamps if they exist
        for field_name in [
            "queued_at", "processed_at", "sent_at", "delivered_at", 
            "opened_at", "clicked_at", "failed_at"
        ]:
            field_value = getattr(self, field_name)
            if field_value:
                result[field_name] = field_value.isoformat()
        
        # Add error information if it exists
        if self.error_message:
            result["error_message"] = self.error_message
        if self.error_code:
            result["error_code"] = self.error_code
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageDelivery':
        """Create a MessageDelivery from dictionary data."""
        instance = cls(
            id=data.get("id", str(uuid.uuid4())),
            batch_id=data["batch_id"],
            journey_id=data["journey_id"],
            recipient_id=data["recipient_id"],
            stage_id=data["stage_id"],
            channel=data["channel"],
            template_id=data["template_id"],
            status=MessageDeliveryStatus(data["status"]),
            tracking_id=data.get("tracking_id"),
            subject=data.get("subject"),
            content_id=data.get("content_id"),
            rendered_content=data.get("rendered_content"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            click_count=data.get("click_count", 0),
            open_count=data.get("open_count", 0),
            metadata=data.get("metadata", {}),
            error_message=data.get("error_message"),
            error_code=data.get("error_code"),
        )
        
        # Parse timestamps
        for field_name in [
            "created_at", "queued_at", "processed_at", "sent_at", "delivered_at", 
            "opened_at", "clicked_at", "failed_at"
        ]:
            if field_name in data and data[field_name]:
                setattr(instance, field_name, datetime.fromisoformat(data[field_name]))
                
        return instance


@dataclass
class StageExecution:
    """
    Represents a single stage execution for a recipient.
    
    Tracks the execution of a workflow stage for a specific recipient,
    including all attempts, outcomes, and associated messages.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    journey_id: str
    stage_id: str
    
    # Status tracking
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Stage result
    status: str = "pending"  # pending, success, failure, skipped
    next_stage_id: Optional[str] = None
    wait_until: Optional[datetime] = None
    
    # Messages sent in this stage
    message_ids: List[str] = field(default_factory=list)
    
    # Custom data produced during stage execution
    output_data: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, success: bool, next_stage_id: Optional[str] = None, output_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark the stage execution as complete.
        
        Args:
            success: Whether the stage completed successfully
            next_stage_id: The ID of the next stage to execute
            output_data: Any data produced by the stage
        """
        self.completed_at = datetime.utcnow()
        self.status = "success" if success else "failure"
        
        if next_stage_id:
            self.next_stage_id = next_stage_id
            
        if output_data:
            self.output_data.update(output_data)
    
    def add_message(self, message_id: str) -> None:
        """
        Associate a message with this stage execution.
        
        Args:
            message_id: The ID of the message to associate
        """
        if message_id not in self.message_ids:
            self.message_ids.append(message_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stage execution to dictionary format."""
        result = {
            "id": self.id,
            "journey_id": self.journey_id,
            "stage_id": self.stage_id,
            "started_at": self.started_at.isoformat(),
            "status": self.status,
            "next_stage_id": self.next_stage_id,
            "message_ids": self.message_ids,
            "output_data": self.output_data
        }
        
        if self.completed_at:
            result["completed_at"] = self.completed_at.isoformat()
            
        if self.wait_until:
            result["wait_until"] = self.wait_until.isoformat()
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StageExecution':
        """Create a StageExecution from dictionary data."""
        instance = cls(
            id=data.get("id", str(uuid.uuid4())),
            journey_id=data["journey_id"],
            stage_id=data["stage_id"],
            status=data.get("status", "pending"),
            next_stage_id=data.get("next_stage_id"),
            message_ids=data.get("message_ids", []),
            output_data=data.get("output_data", {})
        )
        
        # Parse timestamps
        if "started_at" in data:
            instance.started_at = datetime.fromisoformat(data["started_at"])
        
        if "completed_at" in data and data["completed_at"]:
            instance.completed_at = datetime.fromisoformat(data["completed_at"])
            
        if "wait_until" in data and data["wait_until"]:
            instance.wait_until = datetime.fromisoformat(data["wait_until"])
            
        return instance


@dataclass
class RecipientJourney:
    """
    Represents a recipient's journey through a campaign workflow.
    
    Tracks the full path of a recipient through all stages of a workflow,
    including the current state, history, and any personalized data.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    batch_id: str
    workflow_id: str
    recipient_id: str
    
    # Journey status
    status: JourneyStatus = JourneyStatus.ACTIVE
    current_stage_id: Optional[str] = None
    completed_stage_ids: Set[str] = field(default_factory=set)
    error_stage_id: Optional[str] = None
    
    # Timing information
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Stage executions
    stage_executions: List[StageExecution] = field(default_factory=list)
    
    # Custom data
    recipient_data: Dict[str, Any] = field(default_factory=dict)
    journey_data: Dict[str, Any] = field(default_factory=dict)
    
    def start(self, start_stage_id: str) -> None:
        """
        Start the journey at a specific stage.
        
        Args:
            start_stage_id: The ID of the starting stage
        """
        now = datetime.utcnow()
        self.started_at = now
        self.updated_at = now
        self.current_stage_id = start_stage_id
        self.status = JourneyStatus.ACTIVE
    
    def update_status(self, new_status: JourneyStatus, reason: Optional[str] = None) -> None:
        """
        Update the status of the journey.
        
        Args:
            new_status: The new status to set
            reason: Optional reason for the status change
        """
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        if reason:
            self.journey_data["status_reason"] = reason
            
        if new_status == JourneyStatus.COMPLETED:
            self.completed_at = self.updated_at
    
    def add_stage_execution(self, stage_execution: StageExecution) -> None:
        """
        Add a stage execution to the journey.
        
        Args:
            stage_execution: The stage execution to add
        """
        self.stage_executions.append(stage_execution)
        self.updated_at = datetime.utcnow()
        
        # Update current stage
        self.current_stage_id = stage_execution.stage_id
        
        # If the stage is complete, add it to completed stages
        if stage_execution.completed_at:
            self.completed_stage_ids.add(stage_execution.stage_id)
            
            # Update current stage to next stage if available
            if stage_execution.next_stage_id:
                self.current_stage_id = stage_execution.next_stage_id
            elif stage_execution.status == "failure":
                self.error_stage_id = stage_execution.stage_id
                self.update_status(JourneyStatus.FAILED)
            else:
                # If there's no next stage and it's successful, journey is complete
                self.update_status(JourneyStatus.COMPLETED)
    
    def get_current_stage_execution(self) -> Optional[StageExecution]:
        """
        Get the current stage execution, if any.
        
        Returns:
            The current stage execution or None
        """
        if not self.stage_executions:
            return None
            
        return next(
            (execution for execution in reversed(self.stage_executions) 
             if execution.stage_id == self.current_stage_id 
             and not execution.completed_at),
            None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert recipient journey to dictionary format."""
        result = {
            "id": self.id,
            "batch_id": self.batch_id,
            "workflow_id": self.workflow_id,
            "recipient_id": self.recipient_id,
            "status": self.status.value,
            "current_stage_id": self.current_stage_id,
            "completed_stage_ids": list(self.completed_stage_ids),
            "error_stage_id": self.error_stage_id,
            "created_at": self.created_at.isoformat(),
            "recipient_data": self.recipient_data,
            "journey_data": self.journey_data,
            "stage_executions": [se.to_dict() for se in self.stage_executions]
        }
        
        # Add timestamps if they exist
        for field_name in ["started_at", "updated_at", "completed_at"]:
            field_value = getattr(self, field_name)
            if field_value:
                result[field_name] = field_value.isoformat()
                
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecipientJourney':
        """Create a RecipientJourney from dictionary data."""
        instance = cls(
            id=data.get("id", str(uuid.uuid4())),
            batch_id=data["batch_id"],
            workflow_id=data["workflow_id"],
            recipient_id=data["recipient_id"],
            status=JourneyStatus(data["status"]),
            current_stage_id=data.get("current_stage_id"),
            error_stage_id=data.get("error_stage_id"),
            recipient_data=data.get("recipient_data", {}),
            journey_data=data.get("journey_data", {})
        )
        
        # Parse timestamps
        for field_name in ["created_at", "started_at", "updated_at", "completed_at"]:
            if field_name in data and data[field_name]:
                setattr(instance, field_name, datetime.fromisoformat(data[field_name]))
        
        # Parse completed stage IDs
        if "completed_stage_ids" in data:
            instance.completed_stage_ids = set(data["completed_stage_ids"])
            
        # Parse stage executions
        if "stage_executions" in data:
            instance.stage_executions = [
                StageExecution.from_dict(stage_data)
                for stage_data in data["stage_executions"]
            ]
            
        return instance


@dataclass
class CampaignBatch:
    """
    Represents a batch of recipients for a campaign workflow.
    
    A batch groups together a set of recipients processed together
    through a campaign workflow, allowing for monitoring and management
    of the execution as a unit.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    campaign_id: str
    workflow_id: str
    
    # Batch metadata
    name: str
    description: Optional[str] = None
    
    # Processing status
    status: BatchStatus = BatchStatus.CREATED
    total_recipients: int = 0
    processed_recipients: int = 0
    successful_recipients: int = 0
    failed_recipients: int = 0
    
    # Timing information
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Error tracking
    error_message: Optional[str] = None
    
    # Recipient journeys
    recipient_journeys: List[str] = field(default_factory=list)
    
    # Processing settings
    max_concurrent_recipients: int = 100
    throttle_rate: Optional[int] = None  # Messages per minute
    
    # Additional data
    tags: List[str] = field(default_factory=list)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def update_status(self, new_status: BatchStatus) -> None:
        """
        Update the status of the batch.
        
        Args:
            new_status: The new status to set
        """
        self.status = new_status
        
        # Update timing information based on status
        now = datetime.utcnow()
        
        if new_status == BatchStatus.PROCESSING and not self.started_at:
            self.started_at = now
            
        if new_status in (BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELED):
            self.completed_at = now
    
    def add_recipient_journey(self, journey_id: str) -> None:
        """
        Add a recipient journey to the batch.
        
        Args:
            journey_id: The ID of the journey to add
        """
        if journey_id not in self.recipient_journeys:
            self.recipient_journeys.append(journey_id)
            self.total_recipients = len(self.recipient_journeys)
    
    def update_recipient_counts(self, successful: int = 0, failed: int = 0) -> None:
        """
        Update the counts of recipients processed.
        
        Args:
            successful: Number of successful recipients to add
            failed: Number of failed recipients to add
        """
        self.processed_recipients += (successful + failed)
        self.successful_recipients += successful
        self.failed_recipients += failed
        
        # If all recipients have been processed, mark as complete
        if self.processed_recipients >= self.total_recipients and self.total_recipients > 0:
            if self.failed_recipients > 0:
                self.update_status(BatchStatus.COMPLETED)
            else:
                self.update_status(BatchStatus.COMPLETED)
    
    def record_error(self, error_message: str) -> None:
        """
        Record an error that occurred during batch processing.
        
        Args:
            error_message: Description of the error
        """
        self.error_message = error_message
        self.update_status(BatchStatus.FAILED)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the campaign batch to a dictionary."""
        result = {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "total_recipients": self.total_recipients,
            "processed_recipients": self.processed_recipients,
            "successful_recipients": self.successful_recipients,
            "failed_recipients": self.failed_recipients,
            "created_at": self.created_at.isoformat(),
            "error_message": self.error_message,
            "recipient_journeys": self.recipient_journeys,
            "max_concurrent_recipients": self.max_concurrent_recipients,
            "throttle_rate": self.throttle_rate,
            "tags": self.tags,
            "custom_attributes": self.custom_attributes
        }
        
        # Add timestamps if they exist
        if self.started_at:
            result["started_at"] = self.started_at.isoformat()
            
        if self.completed_at:
            result["completed_at"] = self.completed_at.isoformat()
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CampaignBatch':
        """Create a CampaignBatch from dictionary data."""
        instance = cls(
            id=data.get("id", str(uuid.uuid4())),
            campaign_id=data["campaign_id"],
            workflow_id=data["workflow_id"],
            name=data["name"],
            description=data.get("description"),
            status=BatchStatus(data["status"]),
            total_recipients=data.get("total_recipients", 0),
            processed_recipients=data.get("processed_recipients", 0),
            successful_recipients=data.get("successful_recipients", 0),
            failed_recipients=data.get("failed_recipients", 0),
            error_message=data.get("error_message"),
            recipient_journeys=data.get("recipient_journeys", []),
            max_concurrent_recipients=data.get("max_concurrent_recipients", 100),
            throttle_rate=data.get("throttle_rate"),
            tags=data.get("tags", []),
            custom_attributes=data.get("custom_attributes", {})
        )
        
        # Parse timestamps
        if "created_at" in data:
            instance.created_at = datetime.fromisoformat(data["created_at"])
            
        if "started_at" in data and data["started_at"]:
            instance.started_at = datetime.fromisoformat(data["started_at"])
            
        if "completed_at" in data and data["completed_at"]:
            instance.completed_at = datetime.fromisoformat(data["completed_at"])
            
        return instance 