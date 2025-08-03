"""
Chatbot Service for PrismicX Dashboard
"""

import httpx
import structlog
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models.dashboard_models import (
    ChatRequest, ChatResponse, ChatSession, ChatMessage, 
    BotType, ChatMessageType
)

logger = structlog.get_logger(__name__)


class ChatbotService:
    def __init__(self, communication_base_url: str = "http://localhost:8003", api_key: str = "dev_api_key"):
        self.communication_base_url = communication_base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        # In-memory storage for demo (in production, use Redis or database)
        self.sessions: Dict[str, ChatSession] = {}
        self.messages: Dict[str, List[ChatMessage]] = {}
    
    async def get_communication_health(self) -> Dict[str, Any]:
        """Get communication base health status"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.communication_base_url}/health",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("Failed to get communication base health", error=str(e))
            return {"status": "error", "message": str(e)}
    
    def create_session(self, bot_type: BotType, user_id: Optional[str] = None) -> ChatSession:
        """Create a new chat session"""
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            bot_type=bot_type,
            context={"created_via": "dashboard"}
        )
        self.sessions[session_id] = session
        self.messages[session_id] = []
        
        # Add welcome message
        welcome_message = self._get_welcome_message(bot_type)
        self.add_message(session_id, ChatMessageType.BOT, welcome_message, bot_type)
        
        logger.info("Created new chat session", session_id=session_id, bot_type=bot_type)
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get existing chat session"""
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, message_type: ChatMessageType, 
                   content: str, bot_type: Optional[BotType] = None) -> ChatMessage:
        """Add message to session"""
        message = ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            message_type=message_type,
            content=content,
            bot_type=bot_type
        )
        
        if session_id not in self.messages:
            self.messages[session_id] = []
        
        self.messages[session_id].append(message)
        
        # Update session timestamp
        if session_id in self.sessions:
            self.sessions[session_id].updated_at = datetime.utcnow()
        
        return message
    
    def get_messages(self, session_id: str) -> List[ChatMessage]:
        """Get all messages for a session"""
        return self.messages.get(session_id, [])
    
    async def send_message(self, request: ChatRequest) -> ChatResponse:
        """Send message to chatbot and get response"""
        try:
            # Get or create session
            session = None
            if request.session_id:
                session = self.get_session(request.session_id)
            
            if not session:
                session = self.create_session(request.bot_type)
            
            # Add user message
            self.add_message(session.session_id, ChatMessageType.USER, request.message)
            
            # Get bot response (try communication base, fallback to mock)
            bot_response = await self._get_bot_response(request, session)
            
            # Add bot response message
            self.add_message(session.session_id, ChatMessageType.BOT, bot_response, request.bot_type)
            
            return ChatResponse(
                session_id=session.session_id,
                message=bot_response,
                bot_type=request.bot_type,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Failed to send message to chatbot", error=str(e))
            # Return error response
            return ChatResponse(
                session_id=request.session_id or "error",
                message="I'm sorry, I'm having trouble processing your request right now. Please try again.",
                bot_type=request.bot_type,
                timestamp=datetime.utcnow(),
                metadata={"error": str(e)}
            )
    
    async def _get_bot_response(self, request: ChatRequest, session: ChatSession) -> str:
        """Get response from communication base or generate mock response"""
        try:
            # Try to get response from communication base
            async with httpx.AsyncClient() as client:
                payload = {
                    "message": request.message,
                    "bot_type": request.bot_type.value,
                    "context": {
                        **request.context,
                        "session_id": session.session_id,
                        "user_id": session.user_id
                    }
                }
                
                response = await client.post(
                    f"{self.communication_base_url}/api/v1/conversations",
                    headers=self.headers,
                    json=payload,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "I received your message.")
                else:
                    logger.warning("Communication base returned non-200", status=response.status_code)
                    return self._get_mock_response(request.message, request.bot_type)
                    
        except Exception as e:
            logger.warning("Failed to get response from communication base, using mock", error=str(e))
            return self._get_mock_response(request.message, request.bot_type)
    
    def _get_mock_response(self, message: str, bot_type: BotType) -> str:
        """Generate mock bot response based on bot type and message"""
        message_lower = message.lower()
        
        if bot_type == BotType.SUPPORT:
            if any(word in message_lower for word in ["help", "problem", "issue", "error"]):
                return "I understand you're experiencing an issue. Let me help you troubleshoot this. Can you provide more details about what you're trying to do?"
            elif any(word in message_lower for word in ["thank", "thanks"]):
                return "You're welcome! Is there anything else I can help you with today?"
            else:
                return "I'm here to help with any technical support questions you might have. What can I assist you with?"
        
        elif bot_type == BotType.SALES:
            if any(word in message_lower for word in ["price", "cost", "pricing", "quote"]):
                return "I'd be happy to discuss pricing with you. Our solutions are tailored to your specific needs. Can you tell me more about your requirements?"
            elif any(word in message_lower for word in ["demo", "trial", "test"]):
                return "Great! I can set up a personalized demo for you. What's the best time for a 30-minute call this week?"
            elif any(word in message_lower for word in ["feature", "capability", "function"]):
                return "Our platform offers comprehensive CRM, sales automation, and analytics capabilities. Which specific features are you most interested in?"
            else:
                return "Hello! I'm here to help you discover how our platform can boost your sales performance. What brings you here today?"
        
        elif bot_type == BotType.CONSULTANCY:
            if any(word in message_lower for word in ["strategy", "plan", "approach"]):
                return "Strategic planning is crucial for success. Based on your industry and goals, I can recommend best practices. What's your current biggest challenge?"
            elif any(word in message_lower for word in ["optimize", "improve", "better"]):
                return "Optimization is key to growth. I can analyze your current processes and suggest improvements. What area would you like to focus on first?"
            else:
                return "I'm here to provide strategic guidance and consulting insights. How can I help you achieve your business objectives?"
        
        return "I received your message. How can I assist you further?"
    
    def _get_welcome_message(self, bot_type: BotType) -> str:
        """Get welcome message based on bot type"""
        if bot_type == BotType.SUPPORT:
            return "Hello! I'm your support assistant. I'm here to help you with any technical questions or issues you might have."
        elif bot_type == BotType.SALES:
            return "Hi there! I'm your sales assistant. I'm excited to show you how our platform can help grow your business. What would you like to know?"
        elif bot_type == BotType.CONSULTANCY:
            return "Welcome! I'm your strategic consultant. I'm here to provide insights and recommendations to help optimize your business processes."
        return "Hello! How can I help you today?"
    
    def get_active_sessions(self) -> List[ChatSession]:
        """Get all active chat sessions"""
        return [session for session in self.sessions.values() if session.is_active]
    
    def close_session(self, session_id: str) -> bool:
        """Close a chat session"""
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False
            logger.info("Closed chat session", session_id=session_id)
            return True
        return False
