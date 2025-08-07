"""
API Request/Response Schemas

This module contains Pydantic models for API request/response validation
and serialization/deserialization.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator

# Common base schemas
class BaseSchema(BaseModel):
    """Base schema with common fields and configuration."""
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
        orm_mode = True
        use_enum_values = True
        extra = "ignore"

# Request/Response schemas for Campaigns
class CampaignCreate(BaseSchema):
    """Schema for creating a new campaign."""
    name: str = Field(..., max_length=255, description="Name of the campaign")
    description: Optional[str] = Field(None, description="Description of the campaign")
    campaign_type: str = Field(..., description="Type of campaign")
    workflow_id: Optional[UUID] = Field(None, description="ID of the workflow to use")
    start_date: Optional[datetime] = Field(None, description="When the campaign should start")
    end_date: Optional[datetime] = Field(None, description="When the campaign should end")
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional metadata")

class CampaignUpdate(BaseSchema):
    """Schema for updating an existing campaign."""
    name: Optional[str] = Field(None, max_length=255, description="Updated name")
    description: Optional[str] = Field(None, description="Updated description")
    status: Optional[str] = Field(None, description="Updated status")
    metadata: Optional[Dict] = Field(None, description="Updated metadata")

class CampaignResponse(CampaignCreate):
    """Schema for campaign responses."""
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

# Request/Response schemas for Conversations
class MessageCreate(BaseSchema):
    """Schema for creating a new message."""
    content: str = Field(..., description="Message content")
    content_type: str = Field("text/plain", description="MIME type of the content")
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional metadata")

class MessageResponse(MessageCreate):
    """Schema for message responses."""
    id: UUID
    direction: str
    status: str
    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]

class ConversationCreate(BaseSchema):
    """Schema for creating a new conversation."""
    campaign_id: UUID = Field(..., description="ID of the associated campaign")
    contact_id: UUID = Field(..., description="ID of the contact")
    initial_message: Optional[MessageCreate] = Field(None, description="Optional initial message")
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional metadata")

class ConversationResponse(BaseSchema):
    """Schema for conversation responses."""
    id: UUID
    campaign_id: UUID
    contact_id: UUID
    status: str
    current_workflow_state: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []
    metadata: Dict = {}

# Workflow schemas
class WorkflowNode(BaseModel):
    """Schema for a workflow node in a decision tree."""
    id: str
    type: str  # message, decision, action, etc.
    content: Optional[Dict]
    next_nodes: Optional[Dict[str, str]]  # key: condition, value: next_node_id

class WorkflowDefinition(BaseModel):
    """Schema for a complete workflow definition."""
    name: str
    description: Optional[str]
    version: str = "1.0"
    start_node_id: str
    nodes: Dict[str, WorkflowNode]  # node_id -> node_definition

class WorkflowCreate(BaseSchema):
    """Schema for creating a workflow."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    definition: WorkflowDefinition
    is_active: bool = True

class WorkflowResponse(WorkflowCreate):
    """Schema for workflow responses."""
    id: UUID
    version: int
    created_at: datetime
    updated_at: datetime
