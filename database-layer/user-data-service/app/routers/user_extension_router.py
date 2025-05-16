"""
User Extensions Router

This module defines the FastAPI router for the user extensions API endpoints.
It provides HTTP endpoints for managing user extensions.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
import logging

from app.services.user_extension_service import UserExtensionService
from app.models.user_extension import UserExtension, UserExtensionCreate, UserExtensionUpdate
from app.dependencies import get_tenant_aware_collection_sync, get_user_db_sync, get_user_extensions_collection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/extensions", tags=["extensions"])

def get_extension_service(
    request: Request,
    db = Depends(get_user_db_sync),
    collection = Depends(get_user_extensions_collection)
) -> UserExtensionService:
    """
    Dependency for getting the UserExtensionService instance with proper tenant context.
    
    Args:
        request: The incoming request
        db: MongoDB database instance
        collection: MongoDB collection for user extensions
        
    Returns:
        Initialized UserExtensionService
    """
    service = UserExtensionService(db=db, collection=collection)
    service.initialize(collection)
    return service

@router.get("/{user_id}", response_model=List[UserExtension])
async def get_extensions(
    user_id: str,
    request: Request,
    extension_type: Optional[str] = None,
    service: UserExtensionService = Depends(get_extension_service)
):
    """
    Get extensions for a specific user.
    
    Args:
        user_id: User identifier
        request: Request object
        extension_type: Optional filter by extension type
        service: UserExtensionService instance
        
    Returns:
        List of user extensions
    """
    # Get tenant ID from request
    tenant_id = request.state.tenant_id if hasattr(request.state, "tenant_id") else None
    
    if not tenant_id:
        logger.error("No tenant ID found in request")
        raise HTTPException(status_code=400, detail="Tenant ID is required")
    
    if extension_type:
        extensions = service.get_extensions_by_type(user_id, tenant_id, extension_type)
    else:
        extensions = service.get_extensions_by_user(user_id, tenant_id)
    
    if not extensions:
        return []
    
    return extensions

@router.post("/{user_id}", response_model=UserExtension)
async def create_extension(
    user_id: str,
    extension: UserExtensionCreate,
    request: Request,
    service: UserExtensionService = Depends(get_extension_service)
):
    """
    Create a new extension for a user.
    
    Args:
        user_id: User identifier
        extension: Extension data to create
        request: Request object
        service: UserExtensionService instance
        
    Returns:
        Created user extension
    """
    # Get tenant ID from request
    tenant_id = request.state.tenant_id if hasattr(request.state, "tenant_id") else None
    
    if not tenant_id:
        logger.error("No tenant ID found in request")
        raise HTTPException(status_code=400, detail="Tenant ID is required")
    
    # Create extension with the tenant ID
    result = service.create_extension(
        user_id=user_id,
        tenant_id=tenant_id,
        extension_type=extension.extension_type,
        metrics=extension.metrics,
        practicality=extension.practicality
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create extension")
    
    return result

@router.put("/{user_id}/{extension_id}", response_model=UserExtension)
async def update_extension(
    user_id: str,
    extension_id: str,
    extension_update: UserExtensionUpdate,
    request: Request,
    service: UserExtensionService = Depends(get_extension_service)
):
    """
    Update an existing extension for a user.
    
    Args:
        user_id: User identifier
        extension_id: Extension identifier
        extension_update: Extension data to update
        request: Request object
        service: UserExtensionService instance
        
    Returns:
        Updated user extension
    """
    # Get tenant ID from request
    tenant_id = request.state.tenant_id if hasattr(request.state, "tenant_id") else None
    
    if not tenant_id:
        logger.error("No tenant ID found in request")
        raise HTTPException(status_code=400, detail="Tenant ID is required")
    
    # Update extension with the tenant ID
    result = service.update_extension(
        user_id=user_id,
        tenant_id=tenant_id,
        extension_id=extension_id,
        update_data=extension_update.dict(exclude_unset=True)
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Extension not found or update failed")
    
    # Get the updated extension
    updated = service.get_extension_by_id(user_id, tenant_id, extension_id)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Failed to retrieve updated extension")
    
    return updated

@router.delete("/{user_id}/{extension_id}", response_model=Dict[str, bool])
async def delete_extension(
    user_id: str,
    extension_id: str,
    request: Request,
    service: UserExtensionService = Depends(get_extension_service)
):
    """
    Delete an extension for a user.
    
    Args:
        user_id: User identifier
        extension_id: Extension identifier
        request: Request object
        service: UserExtensionService instance
        
    Returns:
        Success status
    """
    # Get tenant ID from request
    tenant_id = request.state.tenant_id if hasattr(request.state, "tenant_id") else None
    
    if not tenant_id:
        logger.error("No tenant ID found in request")
        raise HTTPException(status_code=400, detail="Tenant ID is required")
    
    # Delete extension with the tenant ID
    result = service.delete_extension(user_id, tenant_id, extension_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Extension not found or delete failed")
    
    return {"success": True}

@router.get("", response_model=List[UserExtension])
async def get_all_extensions(
    request: Request,
    page: int = Query(1, gt=0),
    page_size: int = Query(20, gt=0, le=100),
    service: UserExtensionService = Depends(get_extension_service)
):
    """
    Get all extensions for the current tenant with pagination.
    
    Args:
        request: Request object
        page: Page number
        page_size: Number of items per page
        service: UserExtensionService instance
        
    Returns:
        List of user extensions for the tenant
    """
    # Get tenant ID from request
    tenant_id = request.state.tenant_id if hasattr(request.state, "tenant_id") else None
    
    if not tenant_id:
        logger.error("No tenant ID found in request")
        raise HTTPException(status_code=400, detail="Tenant ID is required")
    
    extensions = service.find_all_for_tenant(tenant_id, page, page_size)
    
    if not extensions:
        return []
    
    return extensions 