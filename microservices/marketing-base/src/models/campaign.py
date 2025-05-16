"""
Campaign data models.

This module provides data models for email marketing campaigns.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class CampaignStatus(Enum):
    """Status of a campaign."""
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class RecipientStatus(Enum):
    """Status of an email delivery to a recipient."""
    PENDING = "PENDING"
    SENT = "SENT"
    OPENED = "OPENED"
    CLICKED = "CLICKED"
    FAILED = "FAILED"
    BOUNCED = "BOUNCED"
    UNSUBSCRIBED = "UNSUBSCRIBED"


@dataclass
class Recipient:
    """Recipient of an email campaign."""
    email: str
    first_name: str = ""
    last_name: str = ""
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    status: RecipientStatus = RecipientStatus.PENDING
    tracking_id: str = field(default_factory=lambda: str(uuid4()))
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None
    unsubscribed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert recipient to a dictionary for JSON serialization."""
        return {
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "custom_attributes": self.custom_attributes,
            "status": self.status.name if self.status else None,
            "tracking_id": self.tracking_id,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "bounced_at": self.bounced_at.isoformat() if self.bounced_at else None,
            "unsubscribed_at": self.unsubscribed_at.isoformat() if self.unsubscribed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Recipient':
        """Create a recipient from a dictionary."""
        recipient = cls(
            email=data.get("email", ""),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            custom_attributes=data.get("custom_attributes", {}),
            tracking_id=data.get("tracking_id", str(uuid4()))
        )

        # Parse status
        status_str = data.get("status")
        if status_str:
            try:
                recipient.status = RecipientStatus[status_str]
            except KeyError:
                logger.warning(f"Invalid recipient status: {status_str}")
                recipient.status = RecipientStatus.PENDING

        # Parse timestamps
        for field_name in ["sent_at", "opened_at", "clicked_at", "failed_at", 
                          "bounced_at", "unsubscribed_at"]:
            timestamp = data.get(field_name)
            if timestamp:
                try:
                    setattr(recipient, field_name, datetime.fromisoformat(timestamp))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid timestamp for {field_name}: {timestamp}")

        return recipient


@dataclass
class Campaign:
    """Email marketing campaign."""
    id: str
    name: str
    subject: str
    from_email: str
    template_html: str
    template_text: Optional[str] = None
    reply_to: Optional[str] = None
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: CampaignStatus = CampaignStatus.DRAFT
    recipients: List[Recipient] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    track_opens: bool = True
    track_clicks: bool = True
    custom_attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert campaign to a dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "subject": self.subject,
            "from_email": self.from_email,
            "reply_to": self.reply_to,
            "template_html": self.template_html,
            "template_text": self.template_text,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.name if self.status else None,
            "recipients": [r.to_dict() for r in self.recipients],
            "tags": self.tags,
            "track_opens": self.track_opens,
            "track_clicks": self.track_clicks,
            "custom_attributes": self.custom_attributes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Campaign':
        """Create a campaign from a dictionary."""
        # Parse recipients
        recipients = []
        for r_data in data.get("recipients", []):
            recipients.append(Recipient.from_dict(r_data))

        # Parse status
        status_str = data.get("status")
        status = None
        if status_str:
            try:
                status = CampaignStatus[status_str]
            except KeyError:
                logger.warning(f"Invalid campaign status: {status_str}")
                status = CampaignStatus.DRAFT

        # Parse timestamps
        created_at = None
        updated_at = None
        scheduled_at = None
        completed_at = None

        for field_name, var_name in [
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("scheduled_at", "scheduled_at"),
            ("completed_at", "completed_at")
        ]:
            timestamp = data.get(field_name)
            if timestamp:
                try:
                    locals()[var_name] = datetime.fromisoformat(timestamp)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid timestamp for {field_name}: {timestamp}")

        # Create campaign
        campaign = cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            subject=data.get("subject", ""),
            from_email=data.get("from_email", ""),
            reply_to=data.get("reply_to"),
            template_html=data.get("template_html", ""),
            template_text=data.get("template_text"),
            description=data.get("description", ""),
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at or datetime.utcnow(),
            scheduled_at=scheduled_at,
            completed_at=completed_at,
            status=status or CampaignStatus.DRAFT,
            recipients=recipients,
            tags=data.get("tags", []),
            track_opens=data.get("track_opens", True),
            track_clicks=data.get("track_clicks", True),
            custom_attributes=data.get("custom_attributes", {})
        )

        return campaign 