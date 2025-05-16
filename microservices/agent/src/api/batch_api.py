"""
Batch API endpoints for the Agent microservice.

This module provides API endpoints for managing and monitoring batch operations
using the 2x2 matrix model:
- Processing methods: INDIVIDUAL (one-by-one) vs BATCH (all together)
- Data sources: USERS (from user-data-service) vs CATEGORIES (from category repository)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

from src.application.services.batch_processor import BatchProcessor
from src.domain.value_objects.batch_type import BatchType, ProcessingMethod, DataSourceType
from src.domain.entities.request import BatchRequest
from src.api.dependencies import get_batch_processor

# Create router
router = APIRouter(prefix="/api/batch", tags=["batch"])

# Enums for API
class ProcessingMethodEnum(str, Enum):
    """Processing method options for the API."""
    BATCH = "batch"
    INDIVIDUAL = "individual"

class DataSourceTypeEnum(str, Enum):
    """Data source type options for the API."""
    USERS = "users"
    CATEGORIES = "categories"

# Models for API
class BatchItemRequest(BaseModel):
    """Request model for batch processing."""
    source: str = Field(..., description="Source of the batch request")
    template_id: str = Field(..., description="ID of the template to use for processing")
    items: List[Dict[str, Any]] = Field(..., description="List of items to process")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the batch")

class BatchResponse(BaseModel):
    """Response model for batch processing."""
    batch_id: str = Field(..., description="ID of the created batch")
    status: str = Field(..., description="Status of the batch")

class MatrixBatchRequest(BaseModel):
    """Request model for 2x2 matrix batch processing."""
    source: str = Field(..., description="Source of the batch request")
    template_id: str = Field(..., description="ID of the template to use for processing")
    items: List[Dict[str, Any]] = Field(..., description="List of items to process")
    processing_method: ProcessingMethodEnum = Field(default=ProcessingMethodEnum.INDIVIDUAL, description="Processing method to use")
    data_source_type: DataSourceTypeEnum = Field(..., description="Type of data source")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the batch")

# Endpoints
@router.post("/matrix", response_model=BatchResponse)
async def create_matrix_batch(
    request: MatrixBatchRequest,
    batch_processor: BatchProcessor = Depends(get_batch_processor)
):
    """
    Create a batch using the 2x2 matrix model.
    
    This is the preferred way to create batches, explicitly specifying both
    the processing method and data source type.
    
    Args:
        request: Batch configuration with explicit matrix dimensions
        batch_processor: BatchProcessor service
        
    Returns:
        Batch ID and initial status
    """
    # Convert enum values to actual enums
    processing_method = ProcessingMethod.from_string(request.processing_method.value)
    data_source_type = DataSourceType.from_string(request.data_source_type.value)
    
    # Create a batch request using the flexible factory method
    batch_request = BatchRequest.create_from_components(
        source=request.source,
        template_id=request.template_id,
        items=request.items,
        processing_method=processing_method,
        data_source_type=data_source_type,
        batch_metadata=request.metadata
    )
    
    # Process the batch
    result = await batch_processor.request_service.process_batch(batch_request)
    
    return {
        "batch_id": batch_request.id,
        "status": result.get("status", "created")
    }

@router.post("/user_batch", response_model=BatchResponse)
async def create_user_batch(
    request: BatchItemRequest,
    process_individually: bool = Query(True, description="Whether to process users individually"),
    batch_processor: BatchProcessor = Depends(get_batch_processor)
):
    """
    Create a batch for processing users.
    
    Args:
        request: Batch items to process (users)
        process_individually: Whether to process users individually or as a group
        batch_processor: BatchProcessor service
        
    Returns:
        Batch ID and initial status
    """
    # Create batch request
    batch_request = BatchRequest.create_user_batch(
        source=request.source,
        template_id=request.template_id,
        users=request.items,
        process_individually=process_individually,
        batch_metadata=request.metadata
    )
    
    # Process via the request service
    result = await batch_processor.request_service.process_batch(batch_request)
    
    return {
        "batch_id": batch_request.id,
        "status": result.get("status", "created")
    }

@router.post("/category_batch", response_model=BatchResponse)
async def create_category_batch(
    request: BatchItemRequest,
    process_individually: bool = Query(False, description="Whether to process categories individually"),
    batch_processor: BatchProcessor = Depends(get_batch_processor)
):
    """
    Create a batch for processing categories.
    
    Args:
        request: Batch items to process (categories)
        process_individually: Whether to process categories individually or as a group
        batch_processor: BatchProcessor service
        
    Returns:
        Batch ID and initial status
    """
    # Create batch request
    batch_request = BatchRequest.create_category_batch(
        source=request.source,
        template_id=request.template_id,
        categories=request.items,
        process_individually=process_individually,
        batch_metadata=request.metadata
    )
    
    # Process via the request service
    result = await batch_processor.request_service.process_batch(batch_request)
    
    return {
        "batch_id": batch_request.id,
        "status": result.get("status", "created")
    }

@router.get("/status/{batch_id}", response_model=Dict[str, Any])
async def get_batch_status(
    batch_id: str = Path(..., description="Batch ID"),
    batch_processor: BatchProcessor = Depends(get_batch_processor)
):
    """
    Get the status of a batch.
    
    Args:
        batch_id: Batch ID
        batch_processor: BatchProcessor service
        
    Returns:
        Batch status information
    """
    status = await batch_processor.get_batch_status(batch_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
        
    return status 