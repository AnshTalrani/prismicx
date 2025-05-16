"""
Recipient model.

This module defines the recipient model for email marketing campaigns.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Any

from ..enums.recipient_status import RecipientStatus
from ..value_objects.tracking_info import TrackingInfo


@dataclass
class Recipient:
    """
    Represents an email recipient in a marketing campaign.
    
    Contains recipient information, status, and tracking data.
    """
    
    email: str
    tracking_id: str
    status: RecipientStatus = RecipientStatus.PENDING
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    
    @property
    def full_name(self) -> str:
        """Get the recipient's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return ""
    
    @property
    def tracking_info(self) -> TrackingInfo:
        """Get tracking information as a value object."""
        return TrackingInfo(
            tracking_id=self.tracking_id,
            sent_at=self.sent_at,
            opened_at=self.opened_at,
            clicked_at=self.clicked_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the recipient to a dictionary.
        
        Returns:
            Dictionary representation of the recipient.
        """
        return {
            "email": self.email,
            "tracking_id": self.tracking_id,
            "status": self.status.value,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "custom_attributes": self.custom_attributes,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Recipient':
        """
        Create a recipient from a dictionary.
        
        Args:
            data: Dictionary representation of a recipient.
            
        Returns:
            Recipient instance.
        """
        # Convert status string to enum
        status = data.get("status", RecipientStatus.PENDING.value)
        if isinstance(status, str):
            status = RecipientStatus(status)
        
        # Parse datetime strings to datetime objects
        sent_at = data.get("sent_at")
        if sent_at and isinstance(sent_at, str):
            sent_at = datetime.fromisoformat(sent_at)
            
        opened_at = data.get("opened_at")
        if opened_at and isinstance(opened_at, str):
            opened_at = datetime.fromisoformat(opened_at)
            
        clicked_at = data.get("clicked_at")
        if clicked_at and isinstance(clicked_at, str):
            clicked_at = datetime.fromisoformat(clicked_at)
        
        return cls(
            email=data["email"],
            tracking_id=data.get("tracking_id", ""),
            status=status,
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            custom_attributes=data.get("custom_attributes", {}),
            sent_at=sent_at,
            opened_at=opened_at,
            clicked_at=clicked_at
        ) 