"""
Entity Assignment API endpoints.

This module provides the FastAPI router for entity assignment management API endpoints.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Path

from ..config.settings import get_settings, Settings
from ..models.category import EntityAssignment, EntityAssignmentCreate
from ..repository.category_repository import CategoryRepository
from .categories import get_repository, verify_api_key

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# ===========================
# Entity Assignment Endpoints
# ===========================

@router.post("/api/v1/assignments", response_model=Dict[str, str], dependencies=[Depends(verify_api_key)])
async def create_assignment(
    assignment: EntityAssignmentCreate,
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, str]:
    """
    Create a new entity assignment.
    
    Args:
        assignment: Entity assignment data to create
        repository: Category repository
        
    Returns:
        Dict with assignment ID
        
    Raises:
        HTTPException: If assignment creation fails
    """
    assignment_id = await repository.create_entity_assignment(assignment)
    if assignment_id:
        return {"assignment_id": assignment_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to create entity assignment")


@router.delete("/api/v1/assignments", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def delete_assignment(
    entity_type: str = Query(..., description="Entity type (e.g., 'user')"),
    entity_id: str = Query(..., description="Entity ID"),
    category_type: str = Query(..., description="Category type (e.g., 'factor', 'batch', 'campaign')"),
    item_id: str = Query(..., description="Item ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Delete an entity assignment.
    
    Args:
        entity_type: Entity type
        entity_id: Entity ID
        category_type: Category type
        item_id: Item ID
        repository: Category repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If assignment deletion fails
    """
    success = await repository.delete_entity_assignment(entity_type, entity_id, category_type, item_id)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Entity assignment not found or deletion failed")


@router.get("/api/v1/items/{category_type}/{item_id}/entities", response_model=List[Dict[str, Any]], dependencies=[Depends(verify_api_key)])
async def get_entities_by_item(
    category_type: str = Path(..., description="Category type (e.g., 'factor', 'batch', 'campaign')"),
    item_id: str = Path(..., description="Item ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    skip: int = Query(0, ge=0, description="Number of assignments to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of assignments to return"),
    repository: CategoryRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings)
) -> List[Dict[str, Any]]:
    """
    Get entities assigned to a specific item.
    
    Args:
        category_type: Category type
        item_id: Item ID
        entity_type: Optional entity type filter
        skip: Number of assignments to skip
        limit: Maximum number of assignments to return
        repository: Category repository
        settings: Service settings
        
    Returns:
        List of entity assignments
    """
    entities = await repository.get_entities_by_item(
        category_type=category_type,
        item_id=item_id,
        entity_type=entity_type,
        skip=skip,
        limit=min(limit, settings.max_page_size)
    )
    return entities


@router.get("/api/v1/entities/{entity_type}/{entity_id}/items", response_model=List[Dict[str, Any]], dependencies=[Depends(verify_api_key)])
async def get_items_by_entity(
    entity_type: str = Path(..., description="Entity type (e.g., 'user')"),
    entity_id: str = Path(..., description="Entity ID"),
    category_type: Optional[str] = Query(None, description="Filter by category type"),
    skip: int = Query(0, ge=0, description="Number of assignments to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of assignments to return"),
    repository: CategoryRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings)
) -> List[Dict[str, Any]]:
    """
    Get items assigned to a specific entity.
    
    Args:
        entity_type: Entity type
        entity_id: Entity ID
        category_type: Optional category type filter
        skip: Number of assignments to skip
        limit: Maximum number of assignments to return
        repository: Category repository
        settings: Service settings
        
    Returns:
        List of item assignments
    """
    items = await repository.get_items_by_entity(
        entity_type=entity_type,
        entity_id=entity_id,
        category_type=category_type,
        skip=skip,
        limit=min(limit, settings.max_page_size)
    )
    return items


@router.get("/api/v1/entities/{entity_type}/{entity_id}/details/{category_type}", response_model=List[Dict[str, Any]], dependencies=[Depends(verify_api_key)])
async def get_item_details_by_entity(
    entity_type: str = Path(..., description="Entity type (e.g., 'user')"),
    entity_id: str = Path(..., description="Entity ID"),
    category_type: str = Path(..., description="Category type (e.g., 'factor', 'batch', 'campaign')"),
    repository: CategoryRepository = Depends(get_repository)
) -> List[Dict[str, Any]]:
    """
    Get detailed item information for items assigned to an entity.
    
    Args:
        entity_type: Entity type
        entity_id: Entity ID
        category_type: Category type
        repository: Category repository
        
    Returns:
        List of item details
    """
    items = await repository.get_item_details_by_entity(
        entity_type=entity_type,
        entity_id=entity_id,
        category_type=category_type
    )
    return items


@router.get("/api/v1/assignments/check", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def check_assignment(
    entity_type: str = Query(..., description="Entity type (e.g., 'user')"),
    entity_id: str = Query(..., description="Entity ID"),
    category_type: str = Query(..., description="Category type (e.g., 'factor', 'batch', 'campaign')"),
    item_id: str = Query(..., description="Item ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Check if an entity is assigned to an item.
    
    Args:
        entity_type: Entity type
        entity_id: Entity ID
        category_type: Category type
        item_id: Item ID
        repository: Category repository
        
    Returns:
        Dict with assigned status
    """
    assigned = await repository.check_entity_assignment(
        entity_type=entity_type,
        entity_id=entity_id,
        category_type=category_type,
        item_id=item_id
    )
    return {"assigned": assigned} 