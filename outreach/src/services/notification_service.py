"""
Notification Service

Handles sending notifications for various events in the outreach system.
"""
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
from enum import Enum

class NotificationType(Enum):
    """Types of notifications that can be sent."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    SLACK = "slack"
    WEBHOOK = "webhook"

class NotificationPriority(Enum):
    """Priority levels for notifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationService:
    """Service for sending notifications."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with configuration."""
        self.config = config or {}
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        recipient: Union[str, List[str]],
        subject: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Send a notification to the specified recipient(s).
        
        Args:
            notification_type: Type of notification to send
            recipient: Email address, phone number, or user ID(s)
            subject: Notification subject
            message: Notification content
            priority: Priority level
            metadata: Additional data for the notification
            
        Returns:
            bool: True if the notification was sent successfully
        """
        # In a real implementation, this would integrate with notification providers
        # For now, just log the notification
        print(f"Sending {notification_type.value.upper()} notification to {recipient}:")
        print(f"Subject: {subject}")
        print(f"Message: {message}")
        print(f"Priority: {priority.value}")
        if metadata:
            print(f"Metadata: {metadata}")
            
        return True
    
    async def send_campaign_notification(
        self,
        campaign_id: UUID,
        notification_type: NotificationType,
        recipient: Union[str, List[str]],
        subject: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        campaign_metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Send a notification related to a specific campaign.
        
        Args:
            campaign_id: ID of the related campaign
            notification_type: Type of notification to send
            recipient: Email address, phone number, or user ID(s)
            subject: Notification subject
            message: Notification content
            priority: Priority level
            campaign_metadata: Additional campaign-specific data
            
        Returns:
            bool: True if the notification was sent successfully
        """
        metadata = {
            'campaign_id': str(campaign_id),
            'notification_type': 'campaign_update',
            **(campaign_metadata or {})
        }
        
        return await self.send_notification(
            notification_type=notification_type,
            recipient=recipient,
            subject=f"[Campaign {campaign_id[:8]}] {subject}",
            message=message,
            priority=priority,
            metadata=metadata
        )
    
    async def send_system_alert(
        self,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.HIGH,
        context: Dict[str, Any] = None
    ) -> bool:
        """
        Send a system alert to administrators.
        
        Args:
            title: Alert title
            message: Detailed alert message
            priority: Alert priority
            context: Additional context data
            
        Returns:
            bool: True if the alert was sent successfully
        """
        # In a real implementation, this would notify system administrators
        print(f"SYSTEM ALERT [{priority.value.upper()}]: {title}")
        print(f"Message: {message}")
        if context:
            print(f"Context: {context}")
            
        return True
