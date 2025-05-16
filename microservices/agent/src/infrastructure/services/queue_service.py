"""Interface for queue service."""
from typing import Dict, Any, Optional, List, Callable, Awaitable
from datetime import datetime, timedelta
from abc import ABC, abstractmethod


class IQueueService(ABC):
    """Interface for queue service."""
    
    @abstractmethod
    async def send_message(
        self,
        queue_name: str,
        message: Dict[str, Any],
        delay_seconds: Optional[int] = None,
        message_attributes: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Send a message to a queue.
        
        Args:
            queue_name: Name of the queue
            message: Message to send
            delay_seconds: Optional delay before processing
            message_attributes: Optional message attributes
            
        Returns:
            Message ID
        """
        pass
    
    @abstractmethod
    async def receive_messages(
        self,
        queue_name: str,
        max_messages: int = 1,
        wait_time_seconds: int = 0,
        visibility_timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Receive messages from a queue.
        
        Args:
            queue_name: Name of the queue
            max_messages: Maximum number of messages to receive
            wait_time_seconds: Time to wait for messages
            visibility_timeout: Optional visibility timeout
            
        Returns:
            List of received messages
        """
        pass
    
    @abstractmethod
    async def delete_message(
        self,
        queue_name: str,
        receipt_handle: str
    ) -> None:
        """
        Delete a message from a queue.
        
        Args:
            queue_name: Name of the queue
            receipt_handle: Message receipt handle
        """
        pass
    
    @abstractmethod
    async def change_message_visibility(
        self,
        queue_name: str,
        receipt_handle: str,
        visibility_timeout: int
    ) -> None:
        """
        Change message visibility timeout.
        
        Args:
            queue_name: Name of the queue
            receipt_handle: Message receipt handle
            visibility_timeout: New visibility timeout in seconds
        """
        pass
    
    @abstractmethod
    async def create_queue(
        self,
        queue_name: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new queue.
        
        Args:
            queue_name: Name of the queue
            attributes: Optional queue attributes
            
        Returns:
            Queue URL
        """
        pass
    
    @abstractmethod
    async def delete_queue(
        self,
        queue_name: str
    ) -> None:
        """
        Delete a queue.
        
        Args:
            queue_name: Name of the queue
        """
        pass
    
    @abstractmethod
    async def get_queue_attributes(
        self,
        queue_name: str,
        attribute_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get queue attributes.
        
        Args:
            queue_name: Name of the queue
            attribute_names: Optional list of attributes to get
            
        Returns:
            Queue attributes
        """
        pass
    
    @abstractmethod
    async def set_queue_attributes(
        self,
        queue_name: str,
        attributes: Dict[str, Any]
    ) -> None:
        """
        Set queue attributes.
        
        Args:
            queue_name: Name of the queue
            attributes: Attributes to set
        """
        pass
    
    @abstractmethod
    async def purge_queue(
        self,
        queue_name: str
    ) -> None:
        """
        Purge all messages from a queue.
        
        Args:
            queue_name: Name of the queue
        """
        pass
    
    @abstractmethod
    async def get_queue_url(
        self,
        queue_name: str
    ) -> str:
        """
        Get queue URL.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            Queue URL
        """
        pass
    
    @abstractmethod
    async def list_queues(
        self,
        prefix: Optional[str] = None
    ) -> List[str]:
        """
        List queues.
        
        Args:
            prefix: Optional prefix to filter by
            
        Returns:
            List of queue names
        """
        pass
    
    @abstractmethod
    async def start_consuming(
        self,
        queue_name: str,
        handler: Callable[[Dict[str, Any]], Awaitable[None]],
        max_messages: int = 1,
        wait_time_seconds: int = 20,
        visibility_timeout: Optional[int] = None
    ) -> None:
        """
        Start consuming messages from a queue.
        
        Args:
            queue_name: Name of the queue
            handler: Async handler function for messages
            max_messages: Maximum number of messages to receive per batch
            wait_time_seconds: Time to wait for messages
            visibility_timeout: Optional visibility timeout
        """
        pass
    
    @abstractmethod
    async def stop_consuming(
        self,
        queue_name: str
    ) -> None:
        """
        Stop consuming messages from a queue.
        
        Args:
            queue_name: Name of the queue
        """
        pass 