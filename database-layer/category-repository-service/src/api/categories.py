"""
Category API endpoints.

This module provides the FastAPI router for category management API endpoints.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Path

from ..config.settings import get_settings, Settings
from ..models.category import Category, CategoryCreate, Metrics
from ..repository.category_repository import CategoryRepository

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# Dependency to get repository instance
async def get_repository(settings: Settings = Depends(get_settings)) -> CategoryRepository:
    """
    Get category repository instance as a FastAPI dependency.
    
    Args:
        settings: Service settings
        
    Returns:
        CategoryRepository instance
    """
    repo = CategoryRepository(
        mongodb_uri=settings.mongodb_uri,
        database_name=settings.mongodb_database,
        categories_collection=settings.mongodb_categories_collection,
        factors_collection=settings.mongodb_factors_collection,
        campaigns_collection=settings.mongodb_campaigns_collection,
        batch_as_objects_collection=settings.mongodb_batch_as_objects_collection,
        entity_assignments_collection=settings.mongodb_entity_assignments_collection
    )
    await repo.connect()
    return repo


# API Key security
async def verify_api_key(
    x_api_key: str = Header(None),
    settings: Settings = Depends(get_settings)
):
    """
    Verify API key from header.
    
    Args:
        x_api_key: API key header
        settings: Service settings
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not settings.api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ======================
# Category API Endpoints
# ======================

@router.post("/api/v1/categories", response_model=Dict[str, str], dependencies=[Depends(verify_api_key)])
async def create_category(
    category: CategoryCreate,
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, str]:
    """
    Create a new category.
    
    Args:
        category: Category data to create
        repository: Category repository
        
    Returns:
        Dict with category ID
        
    Raises:
        HTTPException: If category creation fails
    """
    category_id = await repository.create_category(category)
    if category_id:
        return {"category_id": category_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to create category")


@router.get("/api/v1/categories/{category_id}", response_model=Dict[str, Any], dependencies=[Depends(verify_api_key)])
async def get_category(
    category_id: str = Path(..., description="Category ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, Any]:
    """
    Get a category by ID.
    
    Args:
        category_id: Category ID
        repository: Category repository
        
    Returns:
        Category document
        
    Raises:
        HTTPException: If category not found
    """
    category = await repository.get_category(category_id)
    if category:
        return category
    else:
        raise HTTPException(status_code=404, detail=f"Category {category_id} not found")


@router.put("/api/v1/categories/{category_id}", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def update_category(
    update_data: Dict[str, Any],
    category_id: str = Path(..., description="Category ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Update a category.
    
    Args:
        update_data: Category data to update
        category_id: Category ID
        repository: Category repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If category update fails
    """
    success = await repository.update_category(category_id, update_data)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Category {category_id} not found or update failed")


@router.delete("/api/v1/categories/{category_id}", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def delete_category(
    category_id: str = Path(..., description="Category ID"),
    cascade: bool = Query(False, description="Whether to delete all associated entities"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Delete a category.
    
    Args:
        category_id: Category ID
        cascade: Whether to delete all associated entities
        repository: Category repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If category deletion fails
    """
    success = await repository.delete_category(category_id, cascade)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Category {category_id} not found or deletion failed")


@router.get("/api/v1/categories", response_model=List[Dict[str, Any]], dependencies=[Depends(verify_api_key)])
async def get_categories_by_type(
    type: str = Query(..., description="Category type"),
    skip: int = Query(0, ge=0, description="Number of categories to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of categories to return"),
    repository: CategoryRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings)
) -> List[Dict[str, Any]]:
    """
    Get categories by type.
    
    Args:
        type: Category type
        skip: Number of categories to skip
        limit: Maximum number of categories to return
        repository: Category repository
        settings: Service settings
        
    Returns:
        List of category documents
    """
    categories = await repository.get_categories_by_type(
        category_type=type,
        skip=skip,
        limit=min(limit, settings.max_page_size)
    )
    return categories 