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
                # Process feedback: forward to request_service for storage/analysis if available
                try:
                    await self.request_service.process_notification(
                        notification_type="feedback",
                        user_id=user_id,
                        session_id=session_id,
                        data=notification_data,
                    )
                except AttributeError:
                    # Fallback if request_service lacks the helper
                    logger.info("Storing feedback via generic log", extra={"data": notification_data})
                pass
            elif notification_type == "cancellation":
                # Process cancellation: attempt to cancel ongoing batch or request if IDs provided
                cancel_target = notification_data.get("target_request_id") or notification_data.get("batch_id")
                if cancel_target:
                    try:
                        # Prefer dedicated cancel method when available
                        if hasattr(self.request_service, "cancel_request"):
                            await self.request_service.cancel_request(cancel_target)
                        elif hasattr(self.request_service, "batch_processor") and hasattr(self.request_service.batch_processor, "cancel_batch"):
                            await self.request_service.batch_processor.cancel_batch(cancel_target)  # type: ignore[attr-defined]
                        else:
                            logger.warning("No cancellation mechanism available in request_service")
                    except Exception as exc:
                        logger.error("Error cancelling target", error=str(exc))
                pass
            elif notification_type == "user_context":
                # Store/update user context in context manager if available
                context_data = notification_data.get("context") or notification_data
                if hasattr(self.request_service, "context_manager"):
                    try:
                        await self.request_service.context_manager.set_user_context(user_id, context_data)  # type: ignore[attr-defined]
                    except Exception as exc:
                        logger.error("Failed saving user context", error=str(exc))
                else:
                    logger.info("Context manager not available; dropping user context", extra={"user_id": user_id})
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