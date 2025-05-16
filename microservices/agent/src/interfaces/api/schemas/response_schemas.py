"""Response schemas for the API interface."""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ResponseStatus(str, Enum):
    """Enum for response status values."""
    
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    PENDING = "pending"


class ErrorSchema(BaseModel):
    """Schema for error details."""
    
    error_type: str = Field(
        ...,
        description="Type of error that occurred"
    )
    message: str = Field(
        ...,
        description="Error message"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )


class ResponseSchema(BaseModel):
    """Schema for API response data."""
    
    status: ResponseStatus = Field(
        ...,
        description="Status of the request processing"
    )
    message: str = Field(
        ...,
        description="Human-readable response message"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Response data"
    )
    error: Optional[ErrorSchema] = Field(
        None,
        description="Error details if status is failure"
    )
    request_id: Optional[str] = Field(
        None,
        description="Original request ID for tracking"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Successfully processed etsy_listing request",
                "data": {
                    "listing_id": "12345",
                    "title": "Handmade Wooden Bowl - Reclaimed Oak",
                    "description": "Beautiful handcrafted wooden bowl made from reclaimed oak. Perfect for serving salads or as a decorative piece.",
                    "price": 45.99,
                    "images": ["https://example.com/image1.jpg"]
                },
                "request_id": "req_abc123"
            }
        }


class BatchItemResultSchema(BaseModel):
    """Schema for individual batch item result."""
    
    item_id: str = Field(
        ...,
        description="ID of the processed item"
    )
    status: ResponseStatus = Field(
        ...,
        description="Status of the item processing"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Item result data"
    )
    error: Optional[ErrorSchema] = Field(
        None,
        description="Error details if item processing failed"
    )


class BatchResponseSchema(BaseModel):
    """Schema for batch processing response."""
    
    status: ResponseStatus = Field(
        ...,
        description="Overall status of the batch processing"
    )
    message: str = Field(
        ...,
        description="Human-readable response message"
    )
    results: List[BatchItemResultSchema] = Field(
        default_factory=list,
        description="Results for successfully processed items"
    )
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary statistics of batch processing"
    )
    errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Errors that occurred during batch processing"
    )
    batch_id: Optional[str] = Field(
        None,
        description="Original batch ID for tracking"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": "partial",
                "message": "Partially processed batch. 2 succeeded, 1 failed.",
                "results": [
                    {
                        "item_id": "item_001",
                        "status": "success",
                        "data": {
                            "listing_id": "12345",
                            "title": "Handmade Wooden Bowl - Reclaimed Oak"
                        }
                    },
                    {
                        "item_id": "item_002",
                        "status": "success",
                        "data": {
                            "listing_id": "12346",
                            "title": "Ceramic Mug - Hand Painted"
                        }
                    }
                ],
                "summary": {
                    "total_items": 3,
                    "success_count": 2,
                    "error_count": 1,
                    "success_rate": 0.67
                },
                "errors": [
                    {
                        "item_id": "item_003",
                        "error_type": "VALIDATION_ERROR",
                        "message": "Missing required field: price"
                    }
                ],
                "batch_id": "batch_xyz789"
            }
        } 