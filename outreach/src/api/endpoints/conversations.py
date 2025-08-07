"""
Conversation API endpoints.

This module handles real-time conversation interactions,
including message sending, receiving, and conversation state management.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from ...models.schemas import (
    ConversationCreate, ConversationResponse,
    MessageCreate, MessageResponse
)
from ...services.conversation_service import ConversationService
from ...config.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_conversation_service() -> ConversationService:
    """Dependency to get conversation service."""
    # In a real implementation, this would get the service from app state
    return ConversationService()


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation: ConversationCreate,
    service: ConversationService = Depends(get_conversation_service)
):
    """Start a new conversation."""
    try:
        logger.info(f"Creating conversation for campaign: {conversation.campaign_id}")
        created_conversation = await service.create_conversation(conversation)
        logger.info(f"Conversation created successfully: {created_conversation.id}")
        return created_conversation
    except Exception as e:
        logger.error(f"Failed to create conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )


@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = Query(0, ge=0, description="Number of conversations to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of conversations to return"),
    campaign_id: Optional[UUID] = Query(None, description="Filter by campaign ID"),
    contact_id: Optional[UUID] = Query(None, description="Filter by contact ID"),
    status_filter: Optional[str] = Query(None, description="Filter by conversation status"),
    service: ConversationService = Depends(get_conversation_service)
):
    """List all conversations with optional filtering."""
    try:
        logger.info(f"Listing conversations: skip={skip}, limit={limit}")
        conversations = await service.list_conversations(
            skip=skip,
            limit=limit,
            campaign_id=campaign_id,
            contact_id=contact_id,
            status_filter=status_filter
        )
        logger.info(f"Retrieved {len(conversations)} conversations")
        return conversations
    except Exception as e:
        logger.error(f"Failed to list conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list conversations: {str(e)}"
        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service)
):
    """Get a specific conversation by ID."""
    try:
        logger.info(f"Getting conversation: {conversation_id}")
        conversation = await service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: UUID,
    message: MessageCreate,
    service: ConversationService = Depends(get_conversation_service)
):
    """Send a message in a conversation."""
    try:
        logger.info(f"Sending message in conversation: {conversation_id}")
        sent_message = await service.send_message(conversation_id, message)
        if not sent_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        logger.info(f"Message sent successfully: {sent_message.id}")
        return sent_message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send message in conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    skip: int = Query(0, ge=0, description="Number of messages to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of messages to return"),
    service: ConversationService = Depends(get_conversation_service)
):
    """Get conversation history."""
    try:
        logger.info(f"Getting messages for conversation: {conversation_id}")
        messages = await service.get_conversation_messages(
            conversation_id,
            skip=skip,
            limit=limit
        )
        if messages is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        logger.info(f"Retrieved {len(messages)} messages")
        return messages
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages for conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation messages: {str(e)}"
        )


@router.post("/{conversation_id}/end", response_model=ConversationResponse)
async def end_conversation(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service)
):
    """End a conversation."""
    try:
        logger.info(f"Ending conversation: {conversation_id}")
        conversation = await service.end_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        logger.info(f"Conversation ended successfully: {conversation_id}")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end conversation: {str(e)}"
        )


@router.get("/{conversation_id}/state")
async def get_conversation_state(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service)
):
    """Get conversation state and workflow information."""
    try:
        logger.info(f"Getting state for conversation: {conversation_id}")
        state = await service.get_conversation_state(conversation_id)
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return state
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get state for conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation state: {str(e)}"
        )


@router.put("/{conversation_id}/state")
async def update_conversation_state(
    conversation_id: UUID,
    state_update: dict,
    service: ConversationService = Depends(get_conversation_service)
):
    """Update conversation state."""
    try:
        logger.info(f"Updating state for conversation: {conversation_id}")
        updated_state = await service.update_conversation_state(conversation_id, state_update)
        if not updated_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        logger.info(f"Conversation state updated successfully: {conversation_id}")
        return updated_state
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update state for conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update conversation state: {str(e)}"
        )


# WebSocket endpoint for real-time conversation
@router.websocket("/{conversation_id}/ws")
async def websocket_conversation(
    websocket: WebSocket,
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service)
):
    """WebSocket endpoint for real-time conversation."""
    await websocket.accept()
    logger.info(f"WebSocket connection established for conversation: {conversation_id}")
    
    try:
        # Register the WebSocket connection
        await service.register_websocket_connection(conversation_id, websocket)
        
        # Send initial conversation state
        conversation_state = await service.get_conversation_state(conversation_id)
        if conversation_state:
            await websocket.send_json({
                "type": "conversation_state",
                "data": conversation_state
            })
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == "message":
                    # Handle incoming message
                    message_data = data.get("data", {})
                    message = MessageCreate(**message_data)
                    
                    # Process message through conversation service
                    processed_message = await service.process_realtime_message(
                        conversation_id, message, websocket
                    )
                    
                    # Send response back to client
                    await websocket.send_json({
                        "type": "message_response",
                        "data": processed_message.dict() if processed_message else None
                    })
                
                elif message_type == "typing":
                    # Handle typing indicators
                    await service.handle_typing_indicator(conversation_id, data.get("data", {}))
                
                elif message_type == "ping":
                    # Handle ping/pong for connection health
                    await websocket.send_json({"type": "pong"})
                
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": f"Unknown message type: {message_type}"}
                    })
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for conversation: {conversation_id}")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket handler: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Internal server error"}
                })
    
    except Exception as e:
        logger.error(f"WebSocket error for conversation {conversation_id}: {str(e)}")
    finally:
        # Cleanup WebSocket connection
        await service.unregister_websocket_connection(conversation_id, websocket)
        logger.info(f"WebSocket connection closed for conversation: {conversation_id}")


# Analytics endpoints for conversations
@router.get("/{conversation_id}/analytics")
async def get_conversation_analytics(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service)
):
    """Get conversation analytics and insights."""
    try:
        logger.info(f"Getting analytics for conversation: {conversation_id}")
        analytics = await service.get_conversation_analytics(conversation_id)
        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics for conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation analytics: {str(e)}"
        )


@router.post("/{conversation_id}/transcribe")
async def transcribe_audio_message(
    conversation_id: UUID,
    audio_data: bytes,
    service: ConversationService = Depends(get_conversation_service)
):
    """Transcribe audio message in conversation."""
    try:
        logger.info(f"Transcribing audio for conversation: {conversation_id}")
        transcription = await service.transcribe_audio_message(conversation_id, audio_data)
        if not transcription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return transcription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to transcribe audio for conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transcribe audio: {str(e)}"
        )
