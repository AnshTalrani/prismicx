"""Campaign model definitions."""
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

class CampaignStatus(str, Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class CampaignType(str, Enum):
    """Campaign type enumeration."""
    EMAIL = "email"
    SMS = "sms"
    VOICE = "voice"
    MIXED = "mixed"

class Campaign(BaseModel):
    """Campaign model."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    status: CampaignStatus = CampaignStatus.DRAFT
    type: CampaignType = CampaignType.EMAIL
    workflow_id: Optional[UUID] = None
    contact_list_id: Optional[UUID] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
