"""Logging implementation of the communication service."""
import logging
from typing import Dict, Any, Optional, List, Union

from src.application.interfaces.communication_service import ICommunicationService, NotificationLevel, NotificationType
from src.domain.entities.user import User

logger = logging.getLogger(__name__)

class LoggingCommunicationService(ICommunicationService):
    """
    Implementation of communication service that logs notifications.
    
    This is a simple implementation that logs notifications instead of sending
    them to external systems. Useful for development and testing.
    """
    
    async def notify_user(self, 
                         user_id: str, 
                         message: str,
                         title: Optional[str] = None,
                         notification_type: NotificationType = NotificationType.USER,
                         level: NotificationLevel = NotificationLevel.INFO,
                         data: Optional[Dict[str, Any]] = None,
                         channels: Optional[List[str]] = None) -> bool:
        """
        Log a notification for a user.
        
        Args:
            user_id: Target user ID
            message: Notification message
            title: Optional notification title
            notification_type: Type of notification
            level: Importance level
            data: Optional additional data
            channels: Optional list of notification channels
            
        Returns:
            Success status of notification
        """
        title_str = f" - {title}" if title else ""
        
        log_message = f"NOTIFICATION [{level.value}]{title_str}: {message} (User: {user_id}, Type: {notification_type.value})"
        
        if level == NotificationLevel.ERROR:
            logger.error(log_message)
        elif level == NotificationLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
            
        if data:
            logger.debug(f"Notification data: {data}")
            
        return True
    
    async def notify_request_status(self, 
                                  request_id: str, 
                                  user_id: str,
                                  status: str,
                                  progress: Optional[Union[int, float]] = None,
                                  message: Optional[str] = None,
                                  data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log a notification about request status update.
        
        Args:
            request_id: Request ID
            user_id: User ID
            status: New status
            progress: Optional progress percentage (0-100)
            message: Optional status message
            data: Optional additional data
            
        Returns:
            Success status of notification
        """
        progress_str = f" ({progress}%)" if progress is not None else ""
        msg = message or f"Request {request_id} status updated to {status}{progress_str}"
        
        return await self.notify_user(
            user_id=user_id,
            message=msg,
            title=f"Request {status.capitalize()}",
            notification_type=NotificationType.REQUEST_STATUS,
            level=NotificationLevel.INFO,
            data=data
        )
    
    async def notify_batch_status(self, 
                                batch_id: str, 
                                user_id: str,
                                status: str,
                                progress: Optional[Union[int, float]] = None,
                                completed: Optional[int] = None,
                                total: Optional[int] = None,
                                message: Optional[str] = None,
                                data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log a notification about batch status update.
        
        Args:
            batch_id: Batch ID
            user_id: User ID
            status: New status
            progress: Optional progress percentage (0-100)
            completed: Optional count of completed items
            total: Optional total items count
            message: Optional status message
            data: Optional additional data
            
        Returns:
            Success status of notification
        """
        progress_str = f" ({progress}%)" if progress is not None else ""
        completion_str = f" ({completed}/{total} items)" if completed is not None and total is not None else ""
        
        msg = message or f"Batch {batch_id} status updated to {status}{progress_str}{completion_str}"
        
        return await self.notify_user(
            user_id=user_id,
            message=msg,
            title=f"Batch {status.capitalize()}",
            notification_type=NotificationType.BATCH_STATUS,
            level=NotificationLevel.INFO,
            data=data
        )
    
    async def notify_error(self, 
                         source: str, 
                         error_code: str,
                         message: str,
                         user_id: Optional[str] = None,
                         context: Optional[Dict[str, Any]] = None,
                         details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log an error notification.
        
        Args:
            source: Source of error
            error_code: Error code
            message: Error message
            user_id: Optional user ID if user-specific
            context: Optional error context
            details: Optional error details
            
        Returns:
            Success status of notification
        """
        logger.error(f"ERROR [{error_code}] from {source}: {message}")
        
        if context:
            logger.debug(f"Error context: {context}")
            
        if details:
            logger.debug(f"Error details: {details}")
            
        # If user_id is provided, also send a user notification
        if user_id:
            return await self.notify_user(
                user_id=user_id,
                message=message,
                title=f"Error {error_code}",
                notification_type=NotificationType.ERROR,
                level=NotificationLevel.ERROR,
                data={"source": source, "error_code": error_code}
            )
            
        return True
    
    async def is_notification_enabled(self, 
                                    user_id: str, 
                                    notification_type: NotificationType) -> bool:
        """
        Check if notification type is enabled for user.
        In this implementation, all notifications are enabled.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
            
        Returns:
            True if notifications are enabled
        """
        logger.debug(f"Checking if {notification_type.value} notifications are enabled for user {user_id}")
        return True
    
    async def notify_completion(self,
                              user_id: str,
                              request_id: str,
                              result: Dict[str, Any]) -> bool:
        """
        Notify user of request completion.
        
        Args:
            user_id: User to notify
            request_id: Request ID
            result: Request result
            
        Returns:
            Success status of notification
        """
        # Extract result summary if available
        summary = result.get("summary", "Request completed successfully")
        
        return await self.notify_request_status(
            request_id=request_id,
            user_id=user_id,
            status="completed",
            message=summary,
            data={"result": result}
        )
    
    async def broadcast_event(self, 
                             event_type: str, 
                             event_data: Dict[str, Any], 
                             channels: Optional[List[str]] = None) -> bool:
        """
        Log an event broadcast.
        
        Args:
            event_type: Type of event
            event_data: Event data
            channels: Channels to broadcast to
            
        Returns:
            Success status
        """
        channels_str = f" to channels: {channels}" if channels else " to all channels"
        logger.info(f"EVENT BROADCAST: {event_type}{channels_str}")
        logger.debug(f"Event data: {event_data}")
        return True

    async def notify_queued(
        self,
        user: User,
        request_id: str,
        result: Dict[str, Any]
    ) -> bool:
        """
        Notify user that their request has been queued for processing.
        
        Args:
            user: User to notify
            request_id: Request ID
            result: Queue result information
            
        Returns:
            Success status
        """
        try:
            # Log the notification
            self.logger.info(
                f"Notifying user {user.id} that request {request_id} "
                f"has been queued for {result.get('metadata', {}).get('service_type', 'unknown')} service"
            )
            
            # In a real implementation, this would send an email, push notification, etc.
            # For now, we just log it
            
            return True
        except Exception as e:
            self.logger.error(f"Error notifying user {user.id} of queued request {request_id}: {str(e)}")
            return False 