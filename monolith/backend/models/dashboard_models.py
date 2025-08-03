"""
Dashboard Models for PrismicX Monolith
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ChatMessageType(str, Enum):
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"


class BotType(str, Enum):
    SUPPORT = "support"
    SALES = "sales"
    CONSULTANCY = "consultancy"


class ChatMessage(BaseModel):
    id: str
    session_id: str
    message_type: ChatMessageType
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    bot_type: Optional[BotType] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatSession(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    bot_type: BotType
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    context: Dict[str, Any] = Field(default_factory=dict)


class DashboardStats(BaseModel):
    total_customers: int
    active_opportunities: int
    completed_tasks: int
    pending_tasks: int
    total_revenue: float
    monthly_revenue: float
    conversion_rate: float
    recent_activities: List[Dict[str, Any]]


class CustomerSummary(BaseModel):
    customer_id: str
    name: str
    email: Optional[str]
    status: str
    total_value: float
    last_interaction: Optional[datetime]
    opportunities_count: int


class OpportunitySummary(BaseModel):
    opportunity_id: str
    customer_id: str
    customer_name: str
    title: str
    value: Optional[float]
    stage: str
    probability: Optional[float]
    expected_close_date: Optional[datetime]


class TaskSummary(BaseModel):
    task_id: str
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    priority: str
    status: str
    assigned_to: Optional[str]
    related_to_type: str
    related_to_id: str


class ActivityFeed(BaseModel):
    activity_id: str
    activity_type: str
    title: str
    description: str
    timestamp: datetime
    user: Optional[str]
    related_entity_type: Optional[str]
    related_entity_id: Optional[str]


class CampaignRequest(BaseModel):
    name: str
    message: str
    recipients: List[str]
    campaign_type: str = "general"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CampaignResponse(BaseModel):
    campaign_id: str
    status: str
    message: str
    created_at: datetime


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    bot_type: BotType = BotType.SUPPORT
    context: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    session_id: str
    message: str
    bot_type: BotType
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
