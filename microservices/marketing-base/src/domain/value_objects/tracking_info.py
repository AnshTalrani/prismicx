"""
Tracking information value object.

This module defines a value object for email tracking information.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class TrackingInfo:
    """Value object containing tracking information for email recipients."""
    
    tracking_id: str
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    bounce_at: Optional[datetime] = None
    unsubscribe_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def to_dict(self):
        """Convert tracking info to a dictionary."""
        return {
            "tracking_id": self.tracking_id,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at else None,
            "bounce_at": self.bounce_at.isoformat() if self.bounce_at else None,
            "unsubscribe_at": self.unsubscribe_at.isoformat() if self.unsubscribe_at else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent
        }
    
    @staticmethod
    def from_dict(data):
        """Create a TrackingInfo instance from a dictionary."""
        return TrackingInfo(
            tracking_id=data.get("tracking_id"),
            sent_at=datetime.fromisoformat(data["sent_at"]) if data.get("sent_at") else None,
            opened_at=datetime.fromisoformat(data["opened_at"]) if data.get("opened_at") else None,
            clicked_at=datetime.fromisoformat(data["clicked_at"]) if data.get("clicked_at") else None,
            bounce_at=datetime.fromisoformat(data["bounce_at"]) if data.get("bounce_at") else None,
            unsubscribe_at=datetime.fromisoformat(data["unsubscribe_at"]) if data.get("unsubscribe_at") else None,
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent")
        ) 