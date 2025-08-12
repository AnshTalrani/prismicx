"""Analytics model definitions."""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

class CampaignMetrics(BaseModel):
    """Campaign metrics model."""
    campaign_id: UUID
    total_recipients: int = 0
    messages_sent: int = 0
    responses_received: int = 0
    response_rate: float = 0.0
    positive_responses: int = 0
    conversion_rate: float = 0.0
    avg_response_time: Optional[timedelta] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ConversationMetrics(BaseModel):
    """Conversation metrics model."""
    conversation_id: UUID
    message_count: int = 0
    duration: Optional[timedelta] = None
    sentiment_score: float = 0.0
    key_topics: List[str] = Field(default_factory=list)
    outcome: Optional[str] = None
