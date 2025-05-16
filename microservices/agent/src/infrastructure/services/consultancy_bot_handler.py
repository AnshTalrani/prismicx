"""
Handler for consultancy bot integration.
"""
import logging
from typing import Dict, Any, Optional

from src.utils.id_utils import generate_request_id

from src.application.interfaces.request_service import IRequestService

logger = logging.getLogger(__name__)

class ConsultancyBotHandler:
    """
    Handler for consultancy bot integration.
    
    This service handles requests and notifications from the consultancy bot
    and routes them to the appropriate services.
    """
    
    def __init__(self, request_service: IRequestService, user_repository=None):
        """
        Initialize the bot handler.
        
        Args:
            request_service: Service for processing requests
            user_repository: Repository for user data validation
        """
        self.request_service = request_service
        self.user_repository = user_repository
        logger.info("Initialized ConsultancyBotHandler")
    
    async def handle_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle request from consultancy bot.
        
        Args:
            data: Request data
            
        Returns:
            Response with generated content
        """
        try:
            # Extract request data
            text = data.get("text", "")
            user_id = data.get("user_id")
            session_id = data.get("session_id")
            urgency = data.get("urgency", "normal")
            
            if not text:
                return {
                    "session_id": session_id,
                    "user_id": user_id,
                    "status": "error",
                    "error": "No text provided"
                }
            
            # Validate user if user_repository is available
            if self.user_repository and user_id:
                user_exists = await self.user_repository.validate_user_exists(user_id)
                if not user_exists:
                    logger.warning(f"User {user_id} does not exist in system_users database")
                    return {
                        "session_id": session_id,
                        "user_id": user_id,
                        "status": "error",
                        "error": "User does not exist"
                    }
            
            # Use ID utilities to generate a standardized request ID
            request_id = generate_request_id(source=f"bot_{session_id}")
            
            # Process request
            logger.info(f"Processing bot request: {text[:100]}...")
            result = await self.request_service.process_request(
                text=text,
                user_id=user_id,
                request_id=request_id,
                metadata={
                    "source": "consultancy_bot",
                    "session_id": session_id,
                    "urgency": urgency
                }
            )
            
            # Extract content from result
            content = result.get("content", "")
            if not content and "results" in result:
                content = result["results"].get("message", "")
            
            # Prepare response
            response = {
                "session_id": session_id,
                "user_id": user_id,
                "content": content,
                "status": "success",
                "metadata": {
                    "request_id": request_id,
                    "purpose_id": result.get("purpose_id")
                }
            }
            
            logger.info(f"Bot request {request_id} processed successfully")
            return response
            
        except Exception as e:
            logger.exception(f"Error processing bot request: {str(e)}")
            return {
                "session_id": data.get("session_id"),
                "user_id": data.get("user_id"),
                "status": "error",
                "error": f"Failed to process request: {str(e)}"
            }
    
    async def handle_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle notification from consultancy bot.
        
        Args:
            data: Notification data
            
        Returns:
            Acknowledgment response
        """
        try:
            # Extract notification data
            session_id = data.get("session_id")
            user_id = data.get("user_id")
            notification_type = data.get("notification_type")
            notification_data = data.get("data", {})
            
            # Validate user if user_repository is available and this is user-specific notification
            if self.user_repository and user_id:
                user_exists = await self.user_repository.validate_user_exists(user_id)
                if not user_exists:
                    logger.warning(f"User {user_id} does not exist in system_users database")
                    return {
                        "session_id": session_id,
                        "status": "error",
                        "notification_type": notification_type,
                        "error": "User does not exist"
                    }
            
            logger.info(f"Received bot notification: {notification_type} for session {session_id}")
            
            # Process notification based on type
            if notification_type == "feedback":
                # TODO: Process feedback
                pass
            elif notification_type == "cancellation":
                # TODO: Process cancellation
                pass
            elif notification_type == "user_context":
                # TODO: Store user context
                pass
            
            # Return acknowledgment
            return {
                "session_id": session_id,
                "status": "success",
                "notification_type": notification_type
            }
            
        except Exception as e:
            logger.exception(f"Error processing bot notification: {str(e)}")
            return {
                "session_id": data.get("session_id"),
                "status": "error",
                "notification_type": data.get("notification_type"),
                "error": f"Failed to process notification: {str(e)}"
            } 