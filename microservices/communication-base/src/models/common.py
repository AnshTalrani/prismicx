"""
Common Models Module

This module provides common data models used across the communication-base service.
"""

from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime


class SuccessResponse(BaseModel):
    """
    Standard success response model.
    """
    message: str
    timestamp: datetime = datetime.utcnow()
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """
    Standard error response model.
    """
    error: str
    timestamp: datetime = datetime.utcnow()
    details: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel):
    """
    Standard paginated response model.
    """
    total: int
    page: int
    page_size: int
    items: List[Any]
    next_page: Optional[int] = None
    previous_page: Optional[int] = None


class HealthStatus(BaseModel):
    """
    Health status model for health check endpoints.
    """
    status: str
    timestamp: datetime = datetime.utcnow()
    service: str
    version: str
    environment: str
    dependencies: Dict[str, Any] = {}
    system: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[float] = None 