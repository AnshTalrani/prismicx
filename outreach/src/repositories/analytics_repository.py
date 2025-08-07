"""
Analytics Repository

This module provides database access operations for analytics data,
extending the base repository with analytics-specific queries.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models.database import Campaign, Conversation, Message, MessageStatus
from .base import BaseRepository

class AnalyticsRepository(BaseRepository):
    """Repository for analytics database operations."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize with database session."""
        super().__init__(Campaign, db_session)  # Using Campaign as base model
    
    async def get_campaign_metrics(
        self, 
        campaign_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Get metrics for a specific campaign."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
            
        # Get conversation count
        conversations_result = await self.db.execute(
            select(func.count(Conversation.id)).where(
                and_(
                    Conversation.campaign_id == campaign_id,
                    Conversation.created_at >= start_date,
                    Conversation.created_at <= end_date
                )
            )
        )
        conversation_count = conversations_result.scalar()
        
        # Get message count
        messages_result = await self.db.execute(
            select(func.count(Message.id)).join(Conversation).where(
                and_(
                    Conversation.campaign_id == campaign_id,
                    Message.created_at >= start_date,
                    Message.created_at <= end_date
                )
            )
        )
        message_count = messages_result.scalar()
        
        # Get delivery rate
        delivered_messages_result = await self.db.execute(
            select(func.count(Message.id)).join(Conversation).where(
                and_(
                    Conversation.campaign_id == campaign_id,
                    Message.status == MessageStatus.DELIVERED,
                    Message.created_at >= start_date,
                    Message.created_at <= end_date
                )
            )
        )
        delivered_count = delivered_messages_result.scalar()
        
        delivery_rate = (delivered_count / message_count * 100) if message_count > 0 else 0
        
        return {
            "campaign_id": campaign_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "metrics": {
                "conversation_count": conversation_count,
                "message_count": message_count,
                "delivered_messages": delivered_count,
                "delivery_rate": round(delivery_rate, 2)
            }
        }
    
    async def get_conversation_analytics(
        self,
        conversation_id: UUID
    ) -> Dict:
        """Get analytics for a specific conversation."""
        # Get conversation details
        conversation_result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = conversation_result.scalars().first()
        
        if not conversation:
            return {}
        
        # Get message statistics
        messages_result = await self.db.execute(
            select(Message).where(Message.conversation_id == conversation_id)
        )
        messages = messages_result.scalars().all()
        
        inbound_count = sum(1 for msg in messages if msg.direction == "inbound")
        outbound_count = sum(1 for msg in messages if msg.direction == "outbound")
        
        # Calculate response times
        response_times = []
        last_inbound = None
        
        for msg in sorted(messages, key=lambda x: x.created_at):
            if msg.direction == "inbound":
                last_inbound = msg.created_at
            elif msg.direction == "outbound" and last_inbound:
                response_time = (msg.created_at - last_inbound).total_seconds()
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "conversation_id": conversation_id,
            "campaign_id": conversation.campaign_id,
            "contact_id": conversation.contact_id,
            "status": conversation.status,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "analytics": {
                "total_messages": len(messages),
                "inbound_messages": inbound_count,
                "outbound_messages": outbound_count,
                "avg_response_time_seconds": round(avg_response_time, 2),
                "message_status_breakdown": {
                    status.value: sum(1 for msg in messages if msg.status == status)
                    for status in MessageStatus
                }
            }
        }
    
    async def get_performance_metrics(
        self,
        days: int = 30
    ) -> Dict:
        """Get overall system performance metrics."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total campaigns
        campaigns_result = await self.db.execute(
            select(func.count(Campaign.id)).where(Campaign.created_at >= start_date)
        )
        total_campaigns = campaigns_result.scalar()
        
        # Active campaigns
        active_campaigns_result = await self.db.execute(
            select(func.count(Campaign.id)).where(
                and_(
                    Campaign.status == "active",
                    Campaign.created_at >= start_date
                )
            )
        )
        active_campaigns = active_campaigns_result.scalar()
        
        # Total conversations
        conversations_result = await self.db.execute(
            select(func.count(Conversation.id)).where(Conversation.created_at >= start_date)
        )
        total_conversations = conversations_result.scalar()
        
        # Total messages
        messages_result = await self.db.execute(
            select(func.count(Message.id)).where(Message.created_at >= start_date)
        )
        total_messages = messages_result.scalar()
        
        return {
            "period_days": days,
            "metrics": {
                "total_campaigns": total_campaigns,
                "active_campaigns": active_campaigns,
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "avg_messages_per_conversation": round(total_messages / total_conversations, 2) if total_conversations > 0 else 0
            }
        } 