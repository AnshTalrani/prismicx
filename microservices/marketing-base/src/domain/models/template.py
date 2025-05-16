"""
Template model.

This module defines the template model for email marketing.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class Template:
    """
    Represents an email template for marketing campaigns.
    
    Contains template content, metadata, and settings.
    """
    
    name: str
    html_content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text_content: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the template to a dictionary.
        
        Returns:
            Dictionary representation of the template.
        """
        return {
            "id": self.id,
            "name": self.name,
            "html_content": self.html_content,
            "text_content": self.text_content,
            "subject": self.subject,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": self.tags,
            "custom_attributes": self.custom_attributes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        """
        Create a template from a dictionary.
        
        Args:
            data: Dictionary representation of a template.
            
        Returns:
            Template instance.
        """
        # Parse datetime strings to datetime objects
        created_at = data.get("created_at", datetime.utcnow())
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
            
        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            html_content=data["html_content"],
            text_content=data.get("text_content"),
            subject=data.get("subject"),
            description=data.get("description"),
            created_at=created_at,
            updated_at=updated_at,
            tags=data.get("tags", []),
            custom_attributes=data.get("custom_attributes", {})
        ) 