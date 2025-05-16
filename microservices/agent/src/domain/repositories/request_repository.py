"""Request repository interface module."""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.domain.entities.request import Request

class IRequestRepository(ABC):
    """
    Interface for request repository operations.
    
    This interface defines the contract for all request repository implementations
    across the application. It should be implemented by concrete repository classes
    in the infrastructure layer.
    """
    
    @abstractmethod
    async def save(self, request: Request) -> bool:
        """
        Save a request to the repository.
        
        Args:
            request: Request to save
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, request_id: str) -> Optional[Request]:
        """
        Get a request by ID.
        
        Args:
            request_id: Request identifier
            
        Returns:
            Request if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update(self, request: Request) -> bool:
        """
        Update an existing request.
        
        Args:
            request: Updated request
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    async def delete(self, request_id: str) -> bool:
        """
        Delete a request by ID.
        
        Args:
            request_id: Request identifier
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    async def list_by_user(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Request]:
        """
        List requests by user ID.
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of matching requests
        """
        pass
    
    @abstractmethod
    async def list_by_date_range(self, start_time: datetime, end_time: datetime, limit: int = 100) -> List[Request]:
        """
        List requests within a time range.
        
        Args:
            start_time: Start time
            end_time: End time
            limit: Maximum number of results
            
        Returns:
            List of matching requests
        """
        pass
    
    @abstractmethod
    async def search(self, query: str, filter_criteria: Dict[str, Any] = None, limit: int = 100) -> List[Request]:
        """
        Search requests by query and filter criteria.
        
        Args:
            query: Search query
            filter_criteria: Additional filter criteria
            limit: Maximum number of results
            
        Returns:
            List of matching requests
        """
        pass 