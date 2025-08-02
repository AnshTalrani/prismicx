"""Communication service interface for notifying users and systems."""
from typing import Dict, Any, Optional, List, Protocol, Union
from enum import Enum

from src.domain.entities.user import User

class NotificationLevel(str, Enum):
    """Notification importance levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

class NotificationType(str, Enum):
    """Types of notifications."""
    REQUEST_STATUS = "request_status"
    BATCH_STATUS = "batch_status"
    SYSTEM = "system"
    ERROR = "error"
    SECURITY = "security"
    USER = "user"

class ICommunicationService(Protocol):
    """Interface for communication service."""
    
    async def notify_user(self, 
                         user_id: str, 
                         message: str,
                         title: Optional[str] = None,
                         notification_type: NotificationType = NotificationType.USER,
                         level: NotificationLevel = NotificationLevel.INFO,
                         data: Optional[Dict[str, Any]] = None,
                         channels: Optional[List[str]] = None) -> bool:
        """
        Send notification to a user.
        
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
        ...
    
    async def notify_request_status(self, 
                                  request_id: str, 
                                  user_id: str,
                                  status: str,
                                  progress: Optional[Union[int, float]] = None,
                                  message: Optional[str] = None,
                                  data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send notification about request status update.
        
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
        ...
    
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
        Send notification about batch status update.
        
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
        ...
    
    async def notify_error(self, 
                         source: str, 
                         error_code: str,
                         message: str,
                         user_id: Optional[str] = None,
                         context: Optional[Dict[str, Any]] = None,
                         details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send error notification.
        
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
        ...
    
    async def is_notification_enabled(self, 
                                    user_id: str, 
                                    notification_type: NotificationType) -> bool:
        """
        Check if notification type is enabled for user.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
            
        Returns:
            True if notifications are enabled
        """
        ...
    
    async def notify_completion(self, 
                               user_id: str, 
                               request_id: str, 
                               result: Dict[str, Any]) -> bool:
        """
        Notify a user of request completion.
        
        Args:
            user_id: User to notify
            request_id: ID of the completed request
            result: Request result data
            
        Returns:
            Success status
        """
        ...
    
    async def notify_error(self, 
                          user_id: str, 
                          request_id: str, 
                          error: str, 
                          details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Notify a user of an error.
        
        Args:
            user_id: User to notify
            request_id: ID of the failed request
            error: Error message
            details: Additional error details
            
        Returns:
            Success status
        """
        ...
    
    async def send_batch_completion(self, 
                                   user_id: str, 
                                   batch_id: str, 
                                   summary: Dict[str, Any]) -> bool:
        """
        Notify a user of batch completion.
        
        Args:
            user_id: User to notify
            batch_id: ID of the completed batch
            summary: Batch processing summary
            
        Returns:
            Success status
        """
        ...
    
    async def broadcast_event(self, 
                             event_type: str, 
                             event_data: Dict[str, Any], 
                             channels: Optional[List[str]] = None) -> bool:
        """
        Broadcast an event to subscribers.
        
        Args:
            event_type: Type of event
            event_data: Event data
            channels: Channels to broadcast to (if None, broadcast to all)
            
        Returns:
            Success status
        """
        ...
    
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
        ... 