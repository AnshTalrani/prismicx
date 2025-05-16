"""
Recipient status enumeration.

This module defines the possible statuses for an email recipient within a campaign.
"""

from enum import Enum, auto


class RecipientStatus(Enum):
    """Status of an email recipient in a marketing campaign."""
    
    PENDING = "pending"
    SENT = "sent"
    OPENED = "opened"
    CLICKED = "clicked"
    FAILED = "failed"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    
    def __str__(self) -> str:
        """Return the string representation of the status."""
        return self.value 