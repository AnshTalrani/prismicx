"""In-memory implementation of request repository."""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import copy

from src.domain.repositories.request_repository import IRequestRepository
from src.domain.entities.request import Request
from src.utils.id_utils import generate_request_id

logger = logging.getLogger(__name__)

class InMemoryRequestRepository(IRequestRepository):
    """
    In-memory implementation of the request repository.
    
    This implementation stores requests in memory and is suitable for
    development, testing, and prototype environments.
    """
    
    def __init__(self):
        """Initialize the in-memory repository."""
        self.requests: Dict[str, Request] = {}
        logger.info("In-memory request repository initialized")
    
    async def save(self, request: Request) -> bool:
        """
        Save a request to the repository.
        
        Args:
            request: Request to save
            
        Returns:
            Success status
        """
        try:
            if not request.request_id:
                request.request_id = generate_request_id(source="repository")
                
            self.requests[request.request_id] = copy.deepcopy(request)
            logger.debug(f"Saved request {request.request_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving request: {str(e)}")
            return False
    
    async def get_by_id(self, request_id: str) -> Optional[Request]:
        """
        Get a request by ID.
        
        Args:
            request_id: Request identifier
            
        Returns:
            Request if found, None otherwise
        """
        if request_id not in self.requests:
            logger.debug(f"Request {request_id} not found")
            return None
        
        return copy.deepcopy(self.requests[request_id])
    
    async def update(self, request: Request) -> bool:
        """
        Update an existing request.
        
        Args:
            request: Updated request
            
        Returns:
            Success status
        """
        if request.request_id not in self.requests:
            logger.warning(f"Cannot update non-existent request {request.request_id}")
            return False
        
        try:
            self.requests[request.request_id] = copy.deepcopy(request)
            logger.debug(f"Updated request {request.request_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating request: {str(e)}")
            return False
    
    async def delete(self, request_id: str) -> bool:
        """
        Delete a request by ID.
        
        Args:
            request_id: Request identifier
            
        Returns:
            Success status
        """
        if request_id not in self.requests:
            logger.warning(f"Cannot delete non-existent request {request_id}")
            return False
        
        try:
            del self.requests[request_id]
            logger.debug(f"Deleted request {request_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting request: {str(e)}")
            return False
    
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
        user_requests = [
            req for req in self.requests.values()
            if req.user_id == user_id
        ]
        
        # Apply pagination
        paginated = user_requests[offset:offset+limit]
        return copy.deepcopy(paginated)
    
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
        filtered_requests = [
            req for req in self.requests.values()
            if start_time <= req.created_at <= end_time
        ]
        
        # Apply limit
        limited = filtered_requests[:limit]
        return copy.deepcopy(limited)
    
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
        filter_criteria = filter_criteria or {}
        
        # Simple implementation - search in request properties
        results = []
        for req in self.requests.values():
            req_dict = req.to_dict() if hasattr(req, 'to_dict') else req.__dict__
            
            # Search in string values
            matches_query = any(
                query.lower() in str(value).lower()
                for key, value in req_dict.items()
                if isinstance(value, (str, int, float, bool))
            )
            
            # Apply additional filter criteria
            matches_criteria = all(
                key in req_dict and req_dict[key] == value
                for key, value in filter_criteria.items()
            )
            
            if matches_query and matches_criteria:
                results.append(req)
                
            if len(results) >= limit:
                break
                
        return copy.deepcopy(results) 