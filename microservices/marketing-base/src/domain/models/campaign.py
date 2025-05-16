"""
Campaign Model for email marketing campaigns.

This module defines the Campaign and Recipient classes, which represent
email marketing campaigns and their recipients respectively.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import uuid

from .campaign_stage import CampaignStage


class CampaignStatus(str, Enum):
    """Enum representing possible statuses of a campaign."""
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    PAUSED = "PAUSED"


class RecipientStatus(str, Enum):
    """Enum representing possible statuses of email delivery to a recipient."""
    PENDING = "PENDING"
    SENT = "SENT"
    OPENED = "OPENED"
    CLICKED = "CLICKED"
    FAILED = "FAILED"
    BOUNCED = "BOUNCED"
    UNSUBSCRIBED = "UNSUBSCRIBED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


@dataclass
class Recipient:
    """
    Represents a recipient of an email campaign.
    
    This dataclass contains all the information needed to identify and track
    a recipient, including their email address, name, custom attributes,
    delivery status, and engagement timestamps.
    """
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    status: RecipientStatus = RecipientStatus.PENDING
    tracking_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    current_stage_index: int = 0
    stage_statuses: Dict[str, RecipientStatus] = field(default_factory=dict)
    stage_sent_times: Dict[str, datetime] = field(default_factory=dict)
    stage_response_times: Dict[str, datetime] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the recipient to a dictionary representation."""
        result = {
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "custom_attributes": self.custom_attributes,
            "status": self.status.value,
            "tracking_id": self.tracking_id,
            "current_stage_index": self.current_stage_index,
            "stage_statuses": {k: v.value for k, v in self.stage_statuses.items()},
            "stage_sent_times": {k: v.isoformat() for k, v in self.stage_sent_times.items() if v is not None},
            "stage_response_times": {k: v.isoformat() for k, v in self.stage_response_times.items() if v is not None}
        }
        
        # Add datetime fields only if they exist
        for field_name in ["sent_at", "opened_at", "clicked_at", "completed_at", "failed_at"]:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value.isoformat()
                
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Recipient':
        """Create a Recipient instance from a dictionary."""
        # Handle datetime fields
        datetime_fields = ["sent_at", "opened_at", "clicked_at", "completed_at", "failed_at"]
        for field in datetime_fields:
            if field in data and data[field] is not None:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field])
        
        # Handle status enum
        if "status" in data and isinstance(data["status"], str):
            data["status"] = RecipientStatus(data["status"])
            
        # Handle stage statuses
        stage_statuses = data.get("stage_statuses", {})
        if stage_statuses:
            data["stage_statuses"] = {
                k: RecipientStatus(v) if isinstance(v, str) else v 
                for k, v in stage_statuses.items()
            }
            
        # Handle stage times
        for time_field in ["stage_sent_times", "stage_response_times"]:
            if time_field in data:
                data[time_field] = {
                    k: datetime.fromisoformat(v) if isinstance(v, str) else v
                    for k, v in data[time_field].items()
                }
        
        return cls(
            email=data["email"],
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            custom_attributes=data.get("custom_attributes", {}),
            status=data.get("status", RecipientStatus.PENDING),
            tracking_id=data.get("tracking_id", str(uuid.uuid4())),
            sent_at=data.get("sent_at"),
            opened_at=data.get("opened_at"),
            clicked_at=data.get("clicked_at"),
            completed_at=data.get("completed_at"),
            failed_at=data.get("failed_at"),
            current_stage_index=data.get("current_stage_index", 0),
            stage_statuses=data.get("stage_statuses", {}),
            stage_sent_times=data.get("stage_sent_times", {}),
            stage_response_times=data.get("stage_response_times", {})
        )


@dataclass
class Campaign:
    """
    Represents an email marketing campaign.
    
    This dataclass contains all the information needed to define and track
    an email campaign, including campaign metadata, email content,
    recipient list, and tracking configuration.
    """
    name: str
    subject: str
    from_email: str
    recipients: List[Recipient] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    reply_to: Optional[str] = None
    template_id: Optional[str] = None
    template_html: Optional[str] = None
    template_text: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: CampaignStatus = CampaignStatus.DRAFT
    tags: List[str] = field(default_factory=list)
    track_opens: bool = True
    track_clicks: bool = True
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Multi-stage campaign fields
    stages: List[CampaignStage] = field(default_factory=list)
    current_stage_index: int = 0
    segment_id: Optional[str] = None
    product_data: Dict[str, Any] = field(default_factory=dict)
    workflow_config: Dict[str, Any] = field(default_factory=dict)
    ab_testing_config: Dict[str, Any] = field(default_factory=dict)
    analytics_config: Dict[str, Any] = field(default_factory=dict)
    batch_id: Optional[str] = None
    container_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the campaign to a dictionary representation."""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "subject": self.subject,
            "from_email": self.from_email,
            "reply_to": self.reply_to,
            "template_id": self.template_id,
            "template_html": self.template_html,
            "template_text": self.template_text,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "tags": self.tags,
            "track_opens": self.track_opens,
            "track_clicks": self.track_clicks,
            "custom_attributes": self.custom_attributes,
            "recipients": [r.to_dict() for r in self.recipients],
            
            # Multi-stage fields
            "current_stage_index": self.current_stage_index,
            "stages": [stage.to_dict() for stage in self.stages],
            "segment_id": self.segment_id,
            "product_data": self.product_data,
            "workflow_config": self.workflow_config,
            "ab_testing_config": self.ab_testing_config,
            "analytics_config": self.analytics_config,
            "batch_id": self.batch_id,
            "container_id": self.container_id
        }
        
        # Add optional datetime fields if they exist
        if self.scheduled_at:
            result["scheduled_at"] = self.scheduled_at.isoformat()
        if self.completed_at:
            result["completed_at"] = self.completed_at.isoformat()
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Campaign':
        """Create a Campaign instance from a dictionary."""
        # Process datetime fields
        for field in ["created_at", "scheduled_at", "completed_at"]:
            if field in data and data[field] is not None:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field])
        
        # Process status enum
        if "status" in data and isinstance(data["status"], str):
            data["status"] = CampaignStatus(data["status"])
            
        # Process recipients
        recipients = []
        if "recipients" in data:
            recipients = [Recipient.from_dict(r) for r in data["recipients"]]
            
        # Process stages
        stages = []
        if "stages" in data:
            from .campaign_stage import CampaignStage
            stages = [CampaignStage.from_dict(s) for s in data["stages"]]
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            description=data.get("description"),
            subject=data["subject"],
            from_email=data["from_email"],
            reply_to=data.get("reply_to"),
            template_id=data.get("template_id"),
            template_html=data.get("template_html"),
            template_text=data.get("template_text"),
            created_at=data.get("created_at", datetime.utcnow()),
            scheduled_at=data.get("scheduled_at"),
            completed_at=data.get("completed_at"),
            status=data.get("status", CampaignStatus.DRAFT),
            tags=data.get("tags", []),
            track_opens=data.get("track_opens", True),
            track_clicks=data.get("track_clicks", True),
            custom_attributes=data.get("custom_attributes", {}),
            recipients=recipients,
            
            # Multi-stage fields
            stages=stages,
            current_stage_index=data.get("current_stage_index", 0),
            segment_id=data.get("segment_id"),
            product_data=data.get("product_data", {}),
            workflow_config=data.get("workflow_config", {}),
            ab_testing_config=data.get("ab_testing_config", {}),
            analytics_config=data.get("analytics_config", {}),
            batch_id=data.get("batch_id"),
            container_id=data.get("container_id")
        ) 