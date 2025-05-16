"""
Factor API endpoints.

This module provides the FastAPI router for factor management API endpoints.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Path

from ..config.settings import get_settings, Settings
from ..models.category import Factor, FactorCreate, Metrics, MetricsUpdate
from ..repository.category_repository import CategoryRepository
from .categories import get_repository, verify_api_key

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# ======================
# Factor API Endpoints
# ======================

@router.post("/api/v1/factors", response_model=Dict[str, str], dependencies=[Depends(verify_api_key)])
async def create_factor(
    factor: FactorCreate,
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, str]:
    """
    Create a new factor.
    
    Args:
        factor: Factor data to create
        repository: Category repository
        
    Returns:
        Dict with factor ID
        
    Raises:
        HTTPException: If factor creation fails
    """
    factor_id = await repository.create_factor(factor)
    if factor_id:
        return {"factor_id": factor_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to create factor")


@router.get("/api/v1/factors/{factor_id}", response_model=Dict[str, Any], dependencies=[Depends(verify_api_key)])
async def get_factor(
    factor_id: str = Path(..., description="Factor ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, Any]:
    """
    Get a factor by ID.
    
    Args:
        factor_id: Factor ID
        repository: Category repository
        
    Returns:
        Factor document
        
    Raises:
        HTTPException: If factor not found
    """
    factor = await repository.get_factor(factor_id)
    if factor:
        return factor
    else:
        raise HTTPException(status_code=404, detail=f"Factor {factor_id} not found")


@router.put("/api/v1/factors/{factor_id}", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def update_factor(
    update_data: Dict[str, Any],
    factor_id: str = Path(..., description="Factor ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Update a factor.
    
    Args:
        update_data: Factor data to update
        factor_id: Factor ID
        repository: Category repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If factor update fails
    """
    success = await repository.update_factor(factor_id, update_data)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Factor {factor_id} not found or update failed")


@router.delete("/api/v1/factors/{factor_id}", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def delete_factor(
    factor_id: str = Path(..., description="Factor ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Delete a factor.
    
    Args:
        factor_id: Factor ID
        repository: Category repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If factor deletion fails
    """
    success = await repository.delete_factor(factor_id)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Factor {factor_id} not found or deletion failed")


@router.get("/api/v1/categories/{category_id}/factors", response_model=List[Dict[str, Any]], dependencies=[Depends(verify_api_key)])
async def get_factors_by_category(
    category_id: str = Path(..., description="Category ID"),
    skip: int = Query(0, ge=0, description="Number of factors to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of factors to return"),
    repository: CategoryRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings)
) -> List[Dict[str, Any]]:
    """
    Get factors by category.
    
    Args:
        category_id: Category ID
        skip: Number of factors to skip
        limit: Maximum number of factors to return
        repository: Category repository
        settings: Service settings
        
    Returns:
        List of factor documents
    """
    factors = await repository.get_factors_by_category(
        category_id=category_id,
        skip=skip,
        limit=min(limit, settings.max_page_size)
    )
    return factors


@router.put("/api/v1/factors/{factor_id}/metrics", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def update_factor_metrics(
    metrics: MetricsUpdate,
    factor_id: str = Path(..., description="Factor ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Update factor metrics.
    
    Args:
        metrics: Metrics data to update
        factor_id: Factor ID
        repository: Category repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If metrics update fails
    """
    success = await repository.update_factor_metrics(factor_id, metrics.metrics)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Factor {factor_id} not found or metrics update failed") 