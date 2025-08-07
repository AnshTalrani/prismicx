"""
Conversation Repository

This module provides database access operations for conversations,
extending the base repository with conversation-specific queries.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models.database import Conversation, Message, MessageDirection, MessageStatus
from .base import BaseRepository
from ..models.schemas import ConversationCreate, MessageCreate

class ConversationRepository(BaseRepository[Conversation, ConversationCreate, dict]):
    """Repository for conversation database operations."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize with database session."""
        super().__init__(Conversation, db_session)
    
    async def get_by_contact(
        self, 
        contact_id: UUID, 
        campaign_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Conversation]:
        """Retrieve conversations for a specific contact, optionally filtered by campaign."""
        query = select(Conversation).where(Conversation.contact_id == contact_id)
        
        if campaign_id:
            query = query.where(Conversation.campaign_id == campaign_id)
            
        query = query.order_by(Conversation.updated_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_active_conversation(
        self, 
        contact_id: UUID, 
        campaign_id: UUID
    ) -> Optional[Conversation]:
        """Retrieve an active conversation for a contact in a campaign."""
        result = await self.db.execute(
            select(Conversation).where(
                and_(
                    Conversation.contact_id == contact_id,
                    Conversation.campaign_id == campaign_id,
                    Conversation.status == "active"
                )
            )
        )
        return result.scalars().first()
    
    async def add_message(
        self, 
        conversation_id: UUID, 
        message_data: MessageCreate,
        direction: MessageDirection = MessageDirection.OUTBOUND,
        status: MessageStatus = MessageStatus.SENT
    ) -> Optional[Message]:
        """Add a message to a conversation."""
        conversation = await self.get(conversation_id)
        if not conversation:
            return None
            
        message = Message(
            conversation_id=conversation_id,
            direction=direction,
            status=status,
            content_type=message_data.content_type,
            content=message_data.content,
            metadata=message_data.metadata or {}
        )
        
        if direction == MessageDirection.OUTBOUND:
            message.sent_at = datetime.utcnow()
        
        self.db.add(message)
        
        # Update conversation's updated_at timestamp
        conversation.updated_at = datetime.utcnow()
        self.db.add(conversation)
        
        await self.db.commit()
        await self.db.refresh(message)
        return message
    
    async def get_messages(
        self, 
        conversation_id: UUID,
        limit: int = 100,
        offset: int = 0,
        include_system: bool = False
    ) -> List[Message]:
        """Retrieve messages for a conversation."""
        query = select(Message).where(Message.conversation_id == conversation_id)
        
        if not include_system:
            query = query.where(Message.direction != MessageDirection.SYSTEM)
            
        query = query.order_by(Message.created_at.asc())
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_conversation_metrics(
        self, 
        campaign_id: UUID,
        days: int = 30
    ) -> dict:
        """Get metrics for conversations in a campaign."""
        # Get total conversations
        total = await self.db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.campaign_id == campaign_id
            )
        )
        total = total.scalar_one()
        
        # Get active conversations
        active = await self.db.execute(
            select(func.count(Conversation.id)).where(
                and_(
                    Conversation.campaign_id == campaign_id,
                    Conversation.status == "active"
                )
            )
        )
        active = active.scalar_one()
        
        # Get completed conversations
        completed = await self.db.execute(
            select(func.count(Conversation.id)).where(
                and_(
                    Conversation.campaign_id == campaign_id,
                    Conversation.status == "completed"
                )
            )
        )
        completed = completed.scalar_one()
        
        # Get conversation trend (last N days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        trend = await self.db.execute(
            select(
                func.date_trunc('day', Conversation.created_at).label('date'),
                func.count(Conversation.id).label('count')
            ).where(
                and_(
                    Conversation.campaign_id == campaign_id,
                    Conversation.created_at >= start_date,
                    Conversation.created_at <= end_date
                )
            ).group_by('date').order_by('date')
        )
        
        trend_data = [{"date": row[0].isoformat(), "count": row[1]} for row in trend.all()]
        
        return {
            "total": total,
            "active": active,
            "completed": completed,
            "trend": trend_data
        }
