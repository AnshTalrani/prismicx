"""
Batch As Object API endpoints.

This module provides the FastAPI router for batch as object management API endpoints.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Path

from ..config.settings import get_settings, Settings
from ..models.category import BatchAsObject, BatchAsObjectCreate, Metrics, MetricsUpdate
from ..repository.category_repository import CategoryRepository
from .categories import get_repository, verify_api_key

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# ======================
# Batch As Object API Endpoints
# ======================

@router.post("/api/v1/batch-as-objects", response_model=Dict[str, str], dependencies=[Depends(verify_api_key)])
async def create_batch_as_object(
    batch_as_object: BatchAsObjectCreate,
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, str]:
    """
    Create a new batch as object.
    
    Args:
        batch_as_object: Batch as object data to create
        repository: Category repository
        
    Returns:
        Dict with batch as object ID
        
    Raises:
        HTTPException: If batch as object creation fails
    """
    bao_id = await repository.create_batch_as_object(batch_as_object)
    if bao_id:
        return {"bao_id": bao_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to create batch as object")


@router.get("/api/v1/batch-as-objects/{bao_id}", response_model=Dict[str, Any], dependencies=[Depends(verify_api_key)])
async def get_batch_as_object(
    bao_id: str = Path(..., description="Batch as object ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, Any]:
    """
    Get a batch as object by ID.
    
    Args:
        bao_id: Batch as object ID
        repository: Category repository
        
    Returns:
        Batch as object document
        
    Raises:
        HTTPException: If batch as object not found
    """
    batch_as_object = await repository.get_batch_as_object(bao_id)
    if batch_as_object:
        return batch_as_object
    else:
        raise HTTPException(status_code=404, detail=f"Batch as object {bao_id} not found")


@router.put("/api/v1/batch-as-objects/{bao_id}", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def update_batch_as_object(
    update_data: Dict[str, Any],
    bao_id: str = Path(..., description="Batch as object ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Update a batch as object.
    
    Args:
        update_data: Batch as object data to update
        bao_id: Batch as object ID
        repository: Category repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If batch as object update fails
    """
    success = await repository.update_batch_as_object(bao_id, update_data)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Batch as object {bao_id} not found or update failed")


@router.delete("/api/v1/batch-as-objects/{bao_id}", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def delete_batch_as_object(
    bao_id: str = Path(..., description="Batch as object ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Delete a batch as object.
    
    Args:
        bao_id: Batch as object ID
        repository: Category repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If batch as object deletion fails
    """
    success = await repository.delete_batch_as_object(bao_id)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Batch as object {bao_id} not found or deletion failed")


@router.get("/api/v1/categories/{category_id}/batch-as-objects", response_model=List[Dict[str, Any]], dependencies=[Depends(verify_api_key)])
async def get_batch_as_objects_by_category(
    category_id: str = Path(..., description="Category ID"),
    skip: int = Query(0, ge=0, description="Number of batch as objects to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of batch as objects to return"),
    repository: CategoryRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings)
) -> List[Dict[str, Any]]:
    """
    Get batch as objects by category.
    
    Args:
        category_id: Category ID
        skip: Number of batch as objects to skip
        limit: Maximum number of batch as objects to return
        repository: Category repository
        settings: Service settings
        
    Returns:
        List of batch as object documents
    """
    batch_as_objects = await repository.get_batch_as_objects_by_category(
        category_id=category_id,
        skip=skip,
        limit=min(limit, settings.max_page_size)
    )
    return batch_as_objects


@router.put("/api/v1/batch-as-objects/{bao_id}/metrics", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def update_batch_as_object_metrics(
    metrics: MetricsUpdate,
    bao_id: str = Path(..., description="Batch as object ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Update batch as object metrics.
    
    Args:
        metrics: Metrics data to update
        bao_id: Batch as object ID
        repository: Category repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If metrics update fails
    """
    success = await repository.update_batch_as_object_metrics(bao_id, metrics.metrics)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Batch as object {bao_id} not found or metrics update failed") 