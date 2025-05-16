"""
API endpoints for consultancy bot integration.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel

# Dependencies will be injected
from src.infrastructure.services.consultancy_bot_handler import ConsultancyBotHandler

router = APIRouter(prefix="/bot")

class BotRequest(BaseModel):
    """Model for consultancy bot requests."""
    text: str
    user_id: str
    session_id: str
    urgency: Optional[str] = "normal"

class BotNotification(BaseModel):
    """Model for consultancy bot notifications."""
    session_id: str
    user_id: str
    notification_type: str
    data: Optional[Dict[str, Any]] = None

class BotResponse(BaseModel):
    """Model for consultancy bot responses."""
    session_id: str
    user_id: str
    content: str = ""
    status: str
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class NotificationResponse(BaseModel):
    """Model for notification acknowledgments."""
    session_id: str
    status: str
    notification_type: Optional[str] = None
    error: Optional[str] = None

@router.post("/request", response_model=BotResponse)
async def handle_bot_request(
    request: BotRequest,
    bot_handler: ConsultancyBotHandler = Depends()
):
    """
    Handle request from consultancy bot.
    
    Args:
        request: Bot request data
        bot_handler: Injected bot handler service
        
    Returns:
        Response with generated content
    """
    try:
        result = await bot_handler.handle_request({
            "text": request.text,
            "user_id": request.user_id,
            "session_id": request.session_id,
            "urgency": request.urgency
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notification", response_model=NotificationResponse)
async def handle_bot_notification(
    notification: BotNotification,
    bot_handler: ConsultancyBotHandler = Depends()
):
    """
    Handle notification from consultancy bot.
    
    Args:
        notification: Bot notification data
        bot_handler: Injected bot handler service
        
    Returns:
        Acknowledgment response
    """
    try:
        result = await bot_handler.handle_notification({
            "session_id": notification.session_id,
            "user_id": notification.user_id,
            "notification_type": notification.notification_type,
            "data": notification.data
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 