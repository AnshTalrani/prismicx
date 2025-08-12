"""Conversation model definitions."""
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

class ConversationStatus(str, Enum):
    """Conversation status enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class Conversation(BaseModel):
    """Conversation model."""
    id: UUID = Field(default_factory=uuid4)
    campaign_id: UUID
    contact_id: UUID
    status: ConversationStatus = ConversationStatus.ACTIVE
    context: Dict[str, Any] = Field(default_factory=dict)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True
