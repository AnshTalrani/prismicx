"""
Campaign Models Module

This module provides data models for campaign-related entities.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID


class Recipient(BaseModel):
    """
    Model for a campaign recipient.
    """
    id: str
    contact_info: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class ContentElement(BaseModel):
    """
    Model for a campaign content element.
    """
    type: str
    content: Any
    metadata: Optional[Dict[str, Any]] = None


class CampaignContent(BaseModel):
    """
    Model for campaign content.
    """
    elements: List[ContentElement]
    template_id: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class CampaignCreate(BaseModel):
    """
    Model for creating a new campaign.
    """
    name: str
    type: str
    content: CampaignContent
    recipients: List[Recipient]
    scheduled_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class CampaignUpdate(BaseModel):
    """
    Model for updating an existing campaign.
    """
    name: Optional[str] = None
    status: Optional[str] = None
    content: Optional[CampaignContent] = None
    recipients: Optional[List[Recipient]] = None
    scheduled_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class Campaign(BaseModel):
    """
    Model for a complete campaign.
    """
    id: str
    name: str
    type: str
    status: str
    content: CampaignContent
    recipients: List[Recipient]
    created_at: datetime
    updated_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CampaignResponse(BaseModel):
    """
    Model for campaign response.
    """
    id: str
    name: str
    type: str
    status: str
    scheduled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    message: str


class CampaignMetrics(BaseModel):
    """
    Model for campaign metrics.
    """
    campaign_id: str
    total_recipients: int
    conversation_counts: Dict[str, int]
    stage_counts: Dict[str, int]
    completion_rate: float
    average_time_to_complete: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict) 