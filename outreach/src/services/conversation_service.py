"""
Conversation Service

This module provides comprehensive conversation management functionality,
including real-time messaging, WebSocket support, and conversation state management.
"""

import asyncio
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.logging_config import get_logger, LoggerMixin
from ..models.schemas import (
    ConversationCreate, ConversationResponse,
    MessageCreate, MessageResponse
)
from ..repositories.conversation_repository import ConversationRepository
from ..repositories.message_repository import MessageRepository

class MockConversationRepository:
    """Mock conversation repository for testing."""
    
    async def create_conversation(self, conversation_data: ConversationCreate) -> ConversationResponse:
        """Mock create conversation."""
        from uuid import uuid4
        from datetime import datetime
        
        return ConversationResponse(
            id=uuid4(),
            campaign_id=conversation_data.campaign_id,
            contact_id=conversation_data.contact_id,
            status="active",
            current_workflow_state=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            messages=[],
            metadata=conversation_data.metadata or {}
        )
    
    async def get_conversation(self, conversation_id: UUID) -> Optional[ConversationResponse]:
        """Mock get conversation."""
        return None
    
    async def list_conversations(self, skip: int = 0, limit: int = 100, campaign_id: Optional[UUID] = None, contact_id: Optional[UUID] = None, status_filter: Optional[str] = None) -> List[ConversationResponse]:
        """Mock list conversations."""
        return []
    
    async def add_message(self, conversation_id: UUID, message_data: MessageCreate, direction: str = "outbound", status: str = "sent") -> Optional[MessageResponse]:
        """Mock add message."""
        from uuid import uuid4
        from datetime import datetime
        
        return MessageResponse(
            id=uuid4(),
            content=message_data.content,
            content_type=message_data.content_type,
            direction=direction,
            status=status,
            created_at=datetime.utcnow(),
            sent_at=datetime.utcnow() if direction == "outbound" else None,
            delivered_at=None,
            read_at=None
        )

class MockMessageRepository:
    """Mock message repository for testing."""
    
    async def create_message(self, message_data: MessageCreate) -> MessageResponse:
        """Mock create message."""
        from uuid import uuid4
        from datetime import datetime
        
        return MessageResponse(
            id=uuid4(),
            content=message_data.content,
            content_type=message_data.content_type,
            direction="outbound",
            status="sent",
            created_at=datetime.utcnow(),
            sent_at=datetime.utcnow(),
            delivered_at=None,
            read_at=None
        )
    
    async def get_message(self, message_id: UUID) -> Optional[MessageResponse]:
        """Mock get message."""
        return None
    
    async def list_messages(self, conversation_id: UUID, skip: int = 0, limit: int = 100) -> List[MessageResponse]:
        """Mock list messages."""
        return []

logger = get_logger(__name__)


class ConversationService(LoggerMixin):
    """Service for managing conversations and real-time messaging."""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        """Initialize the conversation service."""
        self.db_session = db_session
        self.conversation_repository = None
        self.message_repository = None
        self.websocket_connections: Dict[UUID, List[WebSocket]] = {}
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the service."""
        try:
            self.logger.info("Initializing Conversation Service...")
            if self.db_session:
                self.conversation_repository = ConversationRepository(self.db_session)
                self.message_repository = MessageRepository(self.db_session)
            else:
                # Create mock repositories for testing
                self.conversation_repository = MockConversationRepository()
                self.message_repository = MockMessageRepository()
            self.is_initialized = True
            self.logger.info("Conversation Service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Conversation Service: {str(e)}")
            raise
    
    async def create_conversation(self, conversation_data: ConversationCreate) -> ConversationResponse:
        """Create a new conversation."""
        try:
            self.logger.info(f"Creating conversation for campaign: {conversation_data.campaign_id}")
            
            # Validate campaign exists
            # This would typically check against campaign repository
            
            # Create conversation
            conversation = await self.conversation_repository.create_conversation(conversation_data)
            
            # Send initial message if provided
            if conversation_data.initial_message:
                await self.send_message(conversation.id, conversation_data.initial_message)
            
            self.logger.info(f"Conversation created successfully: {conversation.id}")
            return conversation
            
        except Exception as e:
            self.logger.error(f"Failed to create conversation: {str(e)}")
            raise
    
    async def get_conversation(self, conversation_id: UUID) -> Optional[ConversationResponse]:
        """Get a conversation by ID."""
        try:
            self.logger.info(f"Getting conversation: {conversation_id}")
            conversation = await self.conversation_repository.get_conversation(conversation_id)
            return conversation
        except Exception as e:
            self.logger.error(f"Failed to get conversation {conversation_id}: {str(e)}")
            raise
    
    async def list_conversations(
        self,
        skip: int = 0,
        limit: int = 100,
        campaign_id: Optional[UUID] = None,
        contact_id: Optional[UUID] = None,
        status_filter: Optional[str] = None
    ) -> List[ConversationResponse]:
        """List conversations with optional filtering."""
        try:
            self.logger.info(f"Listing conversations: skip={skip}, limit={limit}")
            conversations = await self.conversation_repository.list_conversations(
                skip=skip,
                limit=limit,
                campaign_id=campaign_id,
                contact_id=contact_id,
                status_filter=status_filter
            )
            return conversations
        except Exception as e:
            self.logger.error(f"Failed to list conversations: {str(e)}")
            raise
    
    async def send_message(
        self, 
        conversation_id: UUID, 
        message_data: MessageCreate
    ) -> Optional[MessageResponse]:
        """Send a message in a conversation."""
        try:
            self.logger.info(f"Sending message in conversation: {conversation_id}")
            
            # Validate conversation exists
            conversation = await self.conversation_repository.get_conversation(conversation_id)
            if not conversation:
                return None
            
            # Create message
            message = await self.message_repository.create_message(conversation_id, message_data)
            
            # Broadcast to WebSocket connections
            await self._broadcast_message(conversation_id, message)
            
            # Update conversation state if needed
            await self._update_conversation_state(conversation_id, message)
            
            self.logger.info(f"Message sent successfully: {message.id}")
            return message
            
        except Exception as e:
            self.logger.error(f"Failed to send message in conversation {conversation_id}: {str(e)}")
            raise
    
    async def get_conversation_messages(
        self, 
        conversation_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> Optional[List[MessageResponse]]:
        """Get conversation messages."""
        try:
            self.logger.info(f"Getting messages for conversation: {conversation_id}")
            
            # Validate conversation exists
            conversation = await self.conversation_repository.get_conversation(conversation_id)
            if not conversation:
                return None
            
            messages = await self.message_repository.get_conversation_messages(
                conversation_id, skip=skip, limit=limit
            )
            return messages
            
        except Exception as e:
            self.logger.error(f"Failed to get messages for conversation {conversation_id}: {str(e)}")
            raise
    
    async def end_conversation(self, conversation_id: UUID) -> Optional[ConversationResponse]:
        """End a conversation."""
        try:
            self.logger.info(f"Ending conversation: {conversation_id}")
            
            # Get conversation
            conversation = await self.conversation_repository.get_conversation(conversation_id)
            if not conversation:
                return None
            
            # Update conversation status
            updated_conversation = await self.conversation_repository.update_conversation_status(
                conversation_id, "ended"
            )
            
            # Close WebSocket connections
            await self._close_websocket_connections(conversation_id)
            
            self.logger.info(f"Conversation ended successfully: {conversation_id}")
            return updated_conversation
            
        except Exception as e:
            self.logger.error(f"Failed to end conversation {conversation_id}: {str(e)}")
            raise
    
    async def get_conversation_state(self, conversation_id: UUID) -> Optional[Dict[str, Any]]:
        """Get conversation state and workflow information."""
        try:
            self.logger.info(f"Getting state for conversation: {conversation_id}")
            
            # Get conversation
            conversation = await self.conversation_repository.get_conversation(conversation_id)
            if not conversation:
                return None
            
            # Get workflow state
            workflow_state = await self.conversation_repository.get_conversation_workflow_state(
                conversation_id
            )
            
            return {
                "conversation_id": conversation_id,
                "status": conversation.status,
                "current_workflow_state": conversation.current_workflow_state,
                "workflow_state": workflow_state,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get state for conversation {conversation_id}: {str(e)}")
            raise
    
    async def update_conversation_state(
        self, 
        conversation_id: UUID, 
        state_update: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update conversation state."""
        try:
            self.logger.info(f"Updating state for conversation: {conversation_id}")
            
            # Get conversation
            conversation = await self.conversation_repository.get_conversation(conversation_id)
            if not conversation:
                return None
            
            # Update workflow state
            updated_state = await self.conversation_repository.update_conversation_workflow_state(
                conversation_id, state_update
            )
            
            # Broadcast state update to WebSocket connections
            await self._broadcast_state_update(conversation_id, updated_state)
            
            self.logger.info(f"Conversation state updated successfully: {conversation_id}")
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Failed to update state for conversation {conversation_id}: {str(e)}")
            raise
    
    # WebSocket management methods
    async def register_websocket_connection(
        self, 
        conversation_id: UUID, 
        websocket: WebSocket
    ):
        """Register a WebSocket connection for a conversation."""
        try:
            if conversation_id not in self.websocket_connections:
                self.websocket_connections[conversation_id] = []
            
            self.websocket_connections[conversation_id].append(websocket)
            self.logger.info(f"WebSocket connection registered for conversation: {conversation_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to register WebSocket connection: {str(e)}")
            raise
    
    async def unregister_websocket_connection(
        self, 
        conversation_id: UUID, 
        websocket: WebSocket
    ):
        """Unregister a WebSocket connection."""
        try:
            if conversation_id in self.websocket_connections:
                if websocket in self.websocket_connections[conversation_id]:
                    self.websocket_connections[conversation_id].remove(websocket)
                
                # Remove conversation if no connections
                if not self.websocket_connections[conversation_id]:
                    del self.websocket_connections[conversation_id]
            
            self.logger.info(f"WebSocket connection unregistered for conversation: {conversation_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to unregister WebSocket connection: {str(e)}")
            raise
    
    async def _broadcast_message(self, conversation_id: UUID, message: MessageResponse):
        """Broadcast message to all WebSocket connections for a conversation."""
        try:
            if conversation_id in self.websocket_connections:
                message_data = {
                    "type": "message",
                    "data": message.dict()
                }
                
                # Send to all connections
                for websocket in self.websocket_connections[conversation_id]:
                    try:
                        await websocket.send_json(message_data)
                    except Exception as e:
                        self.logger.error(f"Failed to send message to WebSocket: {str(e)}")
                        # Remove failed connection
                        await self.unregister_websocket_connection(conversation_id, websocket)
            
        except Exception as e:
            self.logger.error(f"Failed to broadcast message: {str(e)}")
    
    async def _broadcast_state_update(self, conversation_id: UUID, state: Dict[str, Any]):
        """Broadcast state update to all WebSocket connections for a conversation."""
        try:
            if conversation_id in self.websocket_connections:
                state_data = {
                    "type": "state_update",
                    "data": state
                }
                
                # Send to all connections
                for websocket in self.websocket_connections[conversation_id]:
                    try:
                        await websocket.send_json(state_data)
                    except Exception as e:
                        self.logger.error(f"Failed to send state update to WebSocket: {str(e)}")
                        # Remove failed connection
                        await self.unregister_websocket_connection(conversation_id, websocket)
            
        except Exception as e:
            self.logger.error(f"Failed to broadcast state update: {str(e)}")
    
    async def _close_websocket_connections(self, conversation_id: UUID):
        """Close all WebSocket connections for a conversation."""
        try:
            if conversation_id in self.websocket_connections:
                for websocket in self.websocket_connections[conversation_id]:
                    try:
                        await websocket.close()
                    except Exception as e:
                        self.logger.error(f"Failed to close WebSocket: {str(e)}")
                
                del self.websocket_connections[conversation_id]
            
        except Exception as e:
            self.logger.error(f"Failed to close WebSocket connections: {str(e)}")
    
    async def _update_conversation_state(self, conversation_id: UUID, message: MessageResponse):
        """Update conversation state based on message."""
        try:
            # This would typically involve:
            # 1. Analyzing message content
            # 2. Updating workflow state
            # 3. Triggering next workflow step
            
            # For now, just log the update
            self.logger.info(f"Updated conversation state for message: {message.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to update conversation state: {str(e)}")
    
    # Real-time message processing
    async def process_realtime_message(
        self, 
        conversation_id: UUID, 
        message: MessageCreate, 
        websocket: WebSocket
    ) -> Optional[MessageResponse]:
        """Process a real-time message from WebSocket."""
        try:
            self.logger.info(f"Processing real-time message in conversation: {conversation_id}")
            
            # Send message
            sent_message = await self.send_message(conversation_id, message)
            
            # Process with AI if needed
            if message.content_type == "text/plain":
                ai_response = await self._generate_ai_response(conversation_id, message.content)
                if ai_response:
                    await self.send_message(conversation_id, ai_response)
            
            return sent_message
            
        except Exception as e:
            self.logger.error(f"Failed to process real-time message: {str(e)}")
            raise
    
    async def _generate_ai_response(
        self, 
        conversation_id: UUID, 
        user_message: str
    ) -> Optional[MessageCreate]:
        """Generate AI response for user message."""
        try:
            # This would typically involve:
            # 1. Getting conversation context
            # 2. Using LLM to generate response
            # 3. Creating message object
            
            # For now, return a simple response
            ai_response = MessageCreate(
                content=f"AI response to: {user_message}",
                content_type="text/plain"
            )
            
            return ai_response
            
        except Exception as e:
            self.logger.error(f"Failed to generate AI response: {str(e)}")
            return None
    
    async def handle_typing_indicator(self, conversation_id: UUID, data: Dict[str, Any]):
        """Handle typing indicators."""
        try:
            if conversation_id in self.websocket_connections:
                typing_data = {
                    "type": "typing",
                    "data": data
                }
                
                # Broadcast typing indicator
                for websocket in self.websocket_connections[conversation_id]:
                    try:
                        await websocket.send_json(typing_data)
                    except Exception as e:
                        self.logger.error(f"Failed to send typing indicator: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle typing indicator: {str(e)}")
    
    # Audio transcription
    async def transcribe_audio_message(
        self, 
        conversation_id: UUID, 
        audio_data: bytes
    ) -> Optional[Dict[str, Any]]:
        """Transcribe audio message in conversation."""
        try:
            self.logger.info(f"Transcribing audio for conversation: {conversation_id}")
            
            # Validate conversation exists
            conversation = await self.conversation_repository.get_conversation(conversation_id)
            if not conversation:
                return None
            
            # This would typically involve:
            # 1. Using ASR model to transcribe audio
            # 2. Creating text message from transcription
            # 3. Processing the transcribed message
            
            # For now, return mock transcription
            transcription = {
                "conversation_id": conversation_id,
                "transcription": "Mock transcription of audio message",
                "confidence": 0.95,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return transcription
            
        except Exception as e:
            self.logger.error(f"Failed to transcribe audio for conversation {conversation_id}: {str(e)}")
            raise
    
    # Analytics
    async def get_conversation_analytics(self, conversation_id: UUID) -> Optional[Dict[str, Any]]:
        """Get conversation analytics and insights."""
        try:
            self.logger.info(f"Getting analytics for conversation: {conversation_id}")
            
            # Get conversation
            conversation = await self.conversation_repository.get_conversation(conversation_id)
            if not conversation:
                return None
            
            # Get conversation analytics
            analytics = await self.conversation_repository.get_conversation_analytics(conversation_id)
            
            return {
                "conversation_id": conversation_id,
                "status": conversation.status,
                "analytics": analytics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get analytics for conversation {conversation_id}: {str(e)}")
            raise
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            self.logger.info("Cleaning up Conversation Service...")
            
            # Close all WebSocket connections
            for conversation_id in list(self.websocket_connections.keys()):
                await self._close_websocket_connections(conversation_id)
            
            # Cleanup repositories
            await self.conversation_repository.cleanup()
            await self.message_repository.cleanup()
            
            self.logger.info("Conversation Service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}") 