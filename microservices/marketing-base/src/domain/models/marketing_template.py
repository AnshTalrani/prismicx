"""
Marketing template model.

This module defines the domain model for marketing templates.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List


class MarketingTemplate:
    """
    Domain model for a marketing template.
    
    A marketing template represents personalized content generated
    for a specific user based on campaign analysis.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        user_id: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        personalization_data: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Initialize a marketing template.
        
        Args:
            id: Unique identifier for the template.
            campaign_id: ID of the associated campaign.
            user_id: ID of the user for which the template is personalized.
            content: The template content.
            metadata: Additional metadata for the template.
            personalization_data: Data used to personalize the template.
            created_at: Timestamp when the template was created.
            updated_at: Timestamp when the template was last updated.
        """
        self.id = id or str(uuid.uuid4())
        self.campaign_id = campaign_id
        self.user_id = user_id
        self.content = content or ""
        self.metadata = metadata or {}
        self.personalization_data = personalization_data or {}
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at
    
    def add_personalization_data(self, key: str, value: Any) -> None:
        """
        Add personalization data to the template.
        
        Args:
            key: The data key.
            value: The data value.
        """
        self.personalization_data[key] = value
        self.updated_at = datetime.utcnow()
    
    def update_content(self, content: str) -> None:
        """
        Update the template content.
        
        Args:
            content: The new content.
        """
        self.content = content
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the template to a dictionary.
        
        Returns:
            A dictionary representation of the template.
        """
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "user_id": self.user_id,
            "content": self.content,
            "metadata": self.metadata,
            "personalization_data": self.personalization_data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketingTemplate":
        """
        Create a template from a dictionary.
        
        Args:
            data: A dictionary representation of a template.
            
        Returns:
            A new MarketingTemplate instance.
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
            
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
            
        return cls(
            id=data.get("id"),
            campaign_id=data.get("campaign_id"),
            user_id=data.get("user_id"),
            content=data.get("content"),
            metadata=data.get("metadata"),
            personalization_data=data.get("personalization_data"),
            created_at=created_at,
            updated_at=updated_at,
        ) 