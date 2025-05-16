"""
Campaign API schemas.

This module defines the request and response schemas for campaign API endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, EmailStr

from ....domain.models.campaign import Campaign
from ....domain.enums.campaign_status import CampaignStatus
from ....domain.enums.recipient_status import RecipientStatus


class RecipientBase(BaseModel):
    """Base schema for recipient data."""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


class RecipientCreate(RecipientBase):
    """Schema for creating a recipient."""
    pass


class RecipientResponse(RecipientBase):
    """Schema for recipient response."""
    tracking_id: str
    status: str
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None


class CampaignBase(BaseModel):
    """Base schema with common campaign fields."""
    name: str
    subject: str
    from_email: EmailStr
    description: Optional[str] = None
    reply_to: Optional[EmailStr] = None
    tags: List[str] = Field(default_factory=list)
    track_opens: bool = True
    track_clicks: bool = True
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


class CampaignCreate(CampaignBase):
    """Schema for creating a campaign."""
    template_id: Optional[str] = None
    template_html: Optional[str] = None
    template_text: Optional[str] = None
    recipients: List[RecipientCreate] = Field(default_factory=list)
    scheduled_at: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration."""
        extra = "forbid"


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign."""
    name: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    from_email: Optional[EmailStr] = None
    reply_to: Optional[EmailStr] = None
    template_id: Optional[str] = None
    template_html: Optional[str] = None
    template_text: Optional[str] = None
    tags: Optional[List[str]] = None
    track_opens: Optional[bool] = None
    track_clicks: Optional[bool] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    recipients: Optional[List[RecipientCreate]] = None
    
    class Config:
        """Pydantic configuration."""
        extra = "forbid"


class CampaignSchedule(BaseModel):
    """Schema for scheduling a campaign."""
    scheduled_at: datetime


class CampaignResponse(CampaignBase):
    """Schema for campaign response."""
    id: str
    template_id: Optional[str] = None
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str
    recipients_count: int
    pending_count: int
    sent_count: int
    opened_count: int
    clicked_count: int
    failed_count: int
    bounced_count: int
    unsubscribed_count: int

    @classmethod
    def from_campaign(cls, campaign: Campaign) -> 'CampaignResponse':
        """Create a response model from a campaign entity."""
        # Count recipients by status
        pending_count = 0
        sent_count = 0
        opened_count = 0
        clicked_count = 0
        failed_count = 0
        bounced_count = 0
        unsubscribed_count = 0
        
        for recipient in campaign.recipients:
            status = recipient.status
            if status == RecipientStatus.PENDING:
                pending_count += 1
            elif status == RecipientStatus.SENT:
                sent_count += 1
            elif status == RecipientStatus.OPENED:
                opened_count += 1
            elif status == RecipientStatus.CLICKED:
                clicked_count += 1
            elif status == RecipientStatus.FAILED:
                failed_count += 1
            elif status == RecipientStatus.BOUNCED:
                bounced_count += 1
            elif status == RecipientStatus.UNSUBSCRIBED:
                unsubscribed_count += 1
        
        return cls(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            subject=campaign.subject,
            from_email=campaign.from_email,
            reply_to=campaign.reply_to,
            template_id=campaign.template_id,
            created_at=campaign.created_at,
            scheduled_at=campaign.scheduled_at,
            completed_at=campaign.completed_at,
            status=campaign.status.value,
            recipients_count=len(campaign.recipients),
            pending_count=pending_count,
            sent_count=sent_count,
            opened_count=opened_count,
            clicked_count=clicked_count,
            failed_count=failed_count,
            bounced_count=bounced_count,
            unsubscribed_count=unsubscribed_count,
            tags=campaign.tags,
            track_opens=campaign.track_opens,
            track_clicks=campaign.track_clicks,
            custom_attributes=campaign.custom_attributes
        )


class CampaignDetailResponse(CampaignResponse):
    """Schema for detailed campaign response including recipients."""
    recipients: List[RecipientResponse] = Field(default_factory=list)
    template_html: Optional[str] = None
    template_text: Optional[str] = None


class CampaignListResponse(BaseModel):
    """Schema for list of campaigns response."""
    items: List[CampaignResponse]
    total: int
    page: int
    size: int
    pages: int


class CampaignStatisticsResponse(BaseModel):
    """Schema for campaign statistics response."""
    campaign_id: str
    name: str
    status: str
    total_recipients: int
    sent_count: int
    open_count: int
    click_count: int
    bounce_count: int
    unsubscribe_count: int
    failed_count: int
    open_rate: float
    click_rate: float
    bounce_rate: float
    unsubscribe_rate: float
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None 