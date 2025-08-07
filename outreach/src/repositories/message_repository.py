"""
Message Repository

This module provides database access operations for messages,
extending the base repository with message-specific queries.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.database import Message, MessageDirection, MessageStatus
from src.repositories.base import BaseRepository
from src.models.schemas import MessageCreate

class MessageRepository(BaseRepository[Message, MessageCreate, dict]):
    """Repository for message database operations."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize with database session."""
        super().__init__(Message, db_session)
    
    async def get_conversation_messages(
        self, 
        conversation_id: UUID,
        limit: int = 100,
        offset: int = 0,
        include_system: bool = False
    ) -> List[Message]:
        """Retrieve messages for a conversation with pagination."""
        query = select(Message).where(Message.conversation_id == conversation_id)
        
        if not include_system:
            query = query.where(Message.direction != MessageDirection.SYSTEM)
            
        query = query.order_by(Message.created_at.asc())
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_undelivered_messages(
        self,
        conversation_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[Message]:
        """Retrieve undelivered messages, optionally filtered by conversation."""
        query = select(Message).where(
            and_(
                Message.status == MessageStatus.QUEUED,
                Message.direction == MessageDirection.OUTBOUND
            )
        )
        
        if conversation_id:
            query = query.where(Message.conversation_id == conversation_id)
            
        query = query.order_by(Message.created_at.asc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def mark_as_delivered(self, message_id: UUID) -> Optional[Message]:
        """Mark a message as delivered."""
        message = await self.get(message_id)
        if not message:
            return None
            
        message.status = MessageStatus.DELIVERED
        message.delivered_at = datetime.utcnow()
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message
    
    async def mark_as_read(self, message_id: UUID) -> Optional[Message]:
        """Mark a message as read."""
        message = await self.get(message_id)
        if not message:
            return None
            
        message.status = MessageStatus.READ
        message.read_at = datetime.utcnow()
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message
    
    async def get_message_metrics(
        self,
        conversation_id: UUID,
        time_window: int = 30  # days
    ) -> Dict[str, Any]:
        """Get message metrics for a conversation."""
        # Calculate time window
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_window)
        
        # Total message count
        total = await self.db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id
            )
        )
        total = total.scalar_one() or 0
        
        # Messages by direction
        by_direction = await self.db.execute(
            select(
                Message.direction,
                func.count(Message.id).label('count')
            )
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.created_at >= start_date,
                    Message.created_at <= end_date
                )
            )
            .group_by(Message.direction)
        )
        
        # Response time metrics
        avg_response_time = await self._calculate_avg_response_time(conversation_id, start_date, end_date)
        
        return {
            "total_messages": total,
            "messages_by_direction": {r[0]: r[1] for r in by_direction.all()},
            "avg_response_time_seconds": avg_response_time,
            "time_window_days": time_window
        }
    
    async def _calculate_avg_response_time(
        self,
        conversation_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[float]:
        """Calculate average response time for messages in a conversation."""
        # This is a simplified implementation - a production system might use
        # window functions or more sophisticated querying
        
        # Get all messages in time window ordered by creation time
        messages = await self.db.execute(
            select(Message)
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.created_at >= start_date,
                    Message.created_at <= end_date,
                    Message.direction.in_([MessageDirection.INBOUND, MessageDirection.OUTBOUND])
                )
            )
            .order_by(Message.created_at.asc())
        )
        
        messages = messages.scalars().all()
        
        if not messages:
            return None
            
        response_times = []
        last_inbound = None
        
        for msg in messages:
            if msg.direction == MessageDirection.INBOUND:
                last_inbound = msg.created_at
            elif msg.direction == MessageDirection.OUTBOUND and last_inbound:
                response_time = (msg.created_at - last_inbound).total_seconds()
                if response_time > 0:  # Sanity check
                    response_times.append(response_time)
                last_inbound = None  # Reset to avoid counting multiple responses
        
        return sum(response_times) / len(response_times) if response_times else None
