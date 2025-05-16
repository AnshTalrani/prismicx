"""
Campaign status enumeration.

This module defines the possible statuses for an email marketing campaign.
"""

from enum import Enum, auto


class CampaignStatus(Enum):
    """Status of a marketing campaign."""
    
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    
    def __str__(self) -> str:
        """Return the string representation of the status."""
        return self.value 