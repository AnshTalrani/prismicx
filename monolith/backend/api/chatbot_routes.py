"""
Chatbot API Routes for PrismicX Monolith
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import structlog

from ..services.chatbot_service import ChatbotService
from ..models.dashboard_models import (
    ChatRequest, ChatResponse, ChatSession, ChatMessage,
    BotType, APIResponse
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

# Dependency to get chatbot service
def get_chatbot_service() -> ChatbotService:
    return ChatbotService()


@router.get("/health")
async def chatbot_health():
    """Chatbot health check"""
    return {"status": "healthy", "service": "chatbot"}


@router.post("/chat", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Send message to chatbot"""
    try:
        response = await chatbot_service.send_message(request)
        return response
    except Exception as e:
        logger.error("Failed to send message to chatbot", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process chat message")


@router.post("/sessions", response_model=ChatSession)
async def create_session(
    bot_type: BotType,
    user_id: str = None,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Create new chat session"""
    try:
        session = chatbot_service.create_session(bot_type, user_id)
        return session
    except Exception as e:
        logger.error("Failed to create chat session", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create chat session")


@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_session(
    session_id: str,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Get chat session"""
    try:
        session = chatbot_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get chat session", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve chat session")


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_session_messages(
    session_id: str,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Get messages for a chat session"""
    try:
        messages = chatbot_service.get_messages(session_id)
        return messages
    except Exception as e:
        logger.error("Failed to get session messages", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve session messages")


@router.get("/sessions", response_model=List[ChatSession])
async def get_active_sessions(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Get all active chat sessions"""
    try:
        sessions = chatbot_service.get_active_sessions()
        return sessions
    except Exception as e:
        logger.error("Failed to get active sessions", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve active sessions")


@router.delete("/sessions/{session_id}")
async def close_session(
    session_id: str,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Close a chat session"""
    try:
        success = chatbot_service.close_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return APIResponse(
            success=True,
            message="Session closed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to close session", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to close session")


@router.get("/communication-status")
async def get_communication_status(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Get communication base status"""
    try:
        status = await chatbot_service.get_communication_health()
        return APIResponse(
            success=True,
            message="Communication status retrieved successfully",
            data=status
        )
    except Exception as e:
        logger.error("Failed to get communication status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve communication status")
