"""
Response models for API endpoints.

These models define the data structures for API responses.
"""
from typing import Dict, List, Any, Optional, Generic, TypeVar, Type
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar('T')

class SuccessResponse(BaseModel):
    """Simple success response."""
    
    success: bool = True
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    """Error response."""
    
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None

class PaginatedResponse(GenericModel, Generic[T]):
    """Paginated response for lists of items."""
    
    items: List[T]
    total: int
    offset: int
    limit: int 