"""
Conversation Models Module

This module provides data models for conversation-related entities.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
from datetime import datetime


class StageData(BaseModel):
    """
    Model for stage-specific data within a conversation.
    """
    name: str
    order: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    requirements: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HistoryEntry(BaseModel):
    """
    Model for a conversation history entry.
    """
    timestamp: datetime
    event_type: str
    from_stage: Optional[str] = None
    to_stage: Optional[str] = None
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class ConversationState(BaseModel):
    """
    Model for a conversation state.
    """
    id: str
    campaign_id: str
    recipient_id: str
    status: str
    current_stage: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    stages: Dict[str, StageData] = Field(default_factory=dict)
    history: List[HistoryEntry] = Field(default_factory=list)
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationCreate(BaseModel):
    """
    Model for creating a new conversation state.
    """
    campaign_id: str
    recipient_id: str
    initial_stage: str
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationUpdate(BaseModel):
    """
    Model for updating an existing conversation state.
    """
    status: Optional[str] = None
    current_stage: Optional[str] = None
    stages: Optional[Dict[str, Union[StageData, Dict[str, Any]]]] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """
    Model for conversation response.
    """
    id: str
    campaign_id: str
    recipient_id: str
    status: str
    current_stage: str
    updated_at: Optional[datetime] = None
    message: str


class ConversationProgressResponse(BaseModel):
    """
    Model for conversation progression response.
    """
    id: str
    campaign_id: str
    recipient_id: str
    progressed: bool
    previous_stage: str
    current_stage: str
    status: str
    message: str


class StageRequirement(BaseModel):
    """
    Model for stage requirement.
    """
    type: str
    config: Dict[str, Any]
    description: Optional[str] = None


class StageDefinition(BaseModel):
    """
    Model for stage definition.
    """
    name: str
    display_name: str
    order: int
    description: Optional[str] = None
    requirements: List[StageRequirement] = Field(default_factory=list)
    timeout_seconds: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict) 