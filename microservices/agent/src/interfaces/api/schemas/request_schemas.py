"""Request schemas for the API interface."""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator


class RequestSchema(BaseModel):
    """Schema for incoming request data."""
    
    text: Optional[str] = Field(
        None, 
        description="Request text to analyze and process"
    )
    purpose_id: Optional[str] = Field(
        None, 
        description="Known purpose identifier"
    )
    user_id: Optional[str] = Field(
        None, 
        description="User identifier for context and tracking"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional structured data for the request"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Request metadata and context"
    )
    
    @validator('text', 'purpose_id', always=True)
    def check_text_or_purpose(cls, v, values):
        """Validate that either text or purpose_id is provided."""
        if not values.get('text') and not values.get('purpose_id') and not values.get('data'):
            raise ValueError("Either text, purpose_id, or data must be provided")
        return v


class BatchRequestItemSchema(BaseModel):
    """Schema for an individual item in a batch request."""
    
    item_id: str = Field(
        ..., 
        description="Unique identifier for the batch item"
    )
    data: Dict[str, Any] = Field(
        ...,
        description="Item data to process"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Item-specific metadata"
    )


class BatchRequestSchema(BaseModel):
    """Schema for batch request data."""
    
    source: str = Field(
        ...,
        description="Source system or user initiating the batch"
    )
    template_id: str = Field(
        ...,
        description="Template identifier to use for processing"
    )
    items: List[BatchRequestItemSchema] = Field(
        ...,
        description="List of items to process in the batch",
        min_items=1
    )
    batch_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata for the entire batch"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "source": "management_system",
                "template_id": "etsy_listing",
                "items": [
                    {
                        "item_id": "item_001",
                        "data": {
                            "product_name": "Handmade Wooden Bowl",
                            "description": "Beautiful handcrafted wooden bowl made from reclaimed oak.",
                            "price": 45.99
                        },
                        "metadata": {
                            "priority": "high"
                        }
                    }
                ],
                "batch_metadata": {
                    "request_source": "scheduled_task",
                    "user_id": "admin"
                }
            }
        } 