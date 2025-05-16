"""
User Extensions Router

API routes for managing user extensions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header, Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from ..services.user_extension_service import UserExtensionService
from ..models.user_extension import UserExtension
from ..database import get_mongo_client

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request and response validation
class ExtensionCreate(BaseModel):
    user_id: str = Field(..., description="User identifier")
    extension_type: str = Field(..., description="Extension type")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Extension metrics")
    practicality: Optional[Dict[str, Any]] = Field(None, description="Extension practicality data")

class MetricsUpdate(BaseModel):
    metrics: Dict[str, Any] = Field(..., description="Extension metrics to update")

class PracticalityUpdate(BaseModel):
    practicality: Dict[str, Any] = Field(..., description="Extension practicality data to update")

class FactorAdd(BaseModel):
    name: str = Field(..., description="Factor name")
    value: float = Field(..., description="Factor value")
    weight: float = Field(..., description="Factor weight")

# Service dependency
async def get_extension_service() -> UserExtensionService:
    """
    Get the user extension service.
    
    Returns:
        UserExtensionService instance
    """
    mongo_client = await get_mongo_client()
    service = UserExtensionService(mongo_client)
    await service.initialize(mongo_client)
    return service


# Tenant ID extraction from header
def get_tenant_id(x_tenant_id: str = Header(..., description="Tenant identifier")) -> str:
    """
    Extract tenant ID from header.
    
    Args:
        x_tenant_id: Tenant identifier header
    
    Returns:
        Tenant ID
    """
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required")
    return x_tenant_id


# Routes
@router.get("/extension/{extension_id}", response_model=Dict[str, Any])
async def get_extension(
    extension_id: str = Path(..., description="Extension identifier"),
    tenant_id: str = Depends(get_tenant_id),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Get a user extension by ID.
    
    Args:
        extension_id: Extension identifier
        tenant_id: Tenant identifier
        extension_service: UserExtensionService instance
    
    Returns:
        User extension data
    """
    extension = await extension_service.get_extension(extension_id, tenant_id)
    
    if not extension:
        raise HTTPException(status_code=404, detail=f"Extension not found with ID {extension_id}")
    
    return extension.to_dict()


@router.get("/user/{user_id}", response_model=List[Dict[str, Any]])
async def get_extensions_by_user(
    user_id: str = Path(..., description="User identifier"),
    tenant_id: str = Depends(get_tenant_id),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Get all extensions for a user.
    
    Args:
        user_id: User identifier
        tenant_id: Tenant identifier
        extension_service: UserExtensionService instance
    
    Returns:
        List of user extension data
    """
    extensions = await extension_service.get_extensions_by_user(user_id, tenant_id)
    
    return [ext.to_dict() for ext in extensions]


@router.post("/", response_model=Dict[str, Any])
async def create_extension(
    extension_create: ExtensionCreate,
    tenant_id: str = Depends(get_tenant_id),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Create a new user extension.
    
    Args:
        extension_create: Extension data to create
        tenant_id: Tenant identifier
        extension_service: UserExtensionService instance
    
    Returns:
        Created extension data
    """
    extension = await extension_service.create_extension(
        user_id=extension_create.user_id,
        tenant_id=tenant_id,
        extension_type=extension_create.extension_type,
        metrics=extension_create.metrics,
        practicality=extension_create.practicality
    )
    
    return extension.to_dict()


@router.put("/extension/{extension_id}/metrics", response_model=Dict[str, Any])
async def update_metrics(
    metrics_update: MetricsUpdate,
    extension_id: str = Path(..., description="Extension identifier"),
    tenant_id: str = Depends(get_tenant_id),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Update metrics for a user extension.
    
    Args:
        metrics_update: Metrics data to update
        extension_id: Extension identifier
        tenant_id: Tenant identifier
        extension_service: UserExtensionService instance
    
    Returns:
        Updated extension data
    """
    extension = await extension_service.update_metrics(
        extension_id=extension_id,
        tenant_id=tenant_id,
        metrics=metrics_update.metrics
    )
    
    if not extension:
        raise HTTPException(status_code=404, detail=f"Extension not found with ID {extension_id}")
    
    return extension.to_dict()


@router.put("/extension/{extension_id}/practicality", response_model=Dict[str, Any])
async def update_practicality(
    practicality_update: PracticalityUpdate,
    extension_id: str = Path(..., description="Extension identifier"),
    tenant_id: str = Depends(get_tenant_id),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Update practicality data for a user extension.
    
    Args:
        practicality_update: Practicality data to update
        extension_id: Extension identifier
        tenant_id: Tenant identifier
        extension_service: UserExtensionService instance
    
    Returns:
        Updated extension data
    """
    extension = await extension_service.update_practicality(
        extension_id=extension_id,
        tenant_id=tenant_id,
        practicality=practicality_update.practicality
    )
    
    if not extension:
        raise HTTPException(status_code=404, detail=f"Extension not found with ID {extension_id}")
    
    return extension.to_dict()


@router.post("/extension/{extension_id}/factor", response_model=Dict[str, Any])
async def add_factor(
    factor_add: FactorAdd,
    extension_id: str = Path(..., description="Extension identifier"),
    tenant_id: str = Depends(get_tenant_id),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Add a factor to the practicality of a user extension.
    
    Args:
        factor_add: Factor data to add
        extension_id: Extension identifier
        tenant_id: Tenant identifier
        extension_service: UserExtensionService instance
    
    Returns:
        Updated extension data
    """
    factor = {
        "name": factor_add.name,
        "value": factor_add.value,
        "weight": factor_add.weight
    }
    
    extension = await extension_service.add_factor(
        extension_id=extension_id,
        tenant_id=tenant_id,
        factor=factor
    )
    
    if not extension:
        raise HTTPException(status_code=404, detail=f"Extension not found with ID {extension_id}")
    
    return extension.to_dict()


@router.delete("/extension/{extension_id}/factor/{factor_name}")
async def remove_factor(
    extension_id: str = Path(..., description="Extension identifier"),
    factor_name: str = Path(..., description="Factor name"),
    tenant_id: str = Depends(get_tenant_id),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Remove a factor from the practicality of a user extension.
    
    Args:
        extension_id: Extension identifier
        factor_name: Factor name
        tenant_id: Tenant identifier
        extension_service: UserExtensionService instance
    
    Returns:
        Updated extension data
    """
    extension = await extension_service.remove_factor(
        extension_id=extension_id,
        tenant_id=tenant_id,
        factor_name=factor_name
    )
    
    if not extension:
        raise HTTPException(status_code=404, detail=f"Extension not found with ID {extension_id} or factor not found with name {factor_name}")
    
    return extension.to_dict()


@router.delete("/extension/{extension_id}")
async def delete_extension(
    extension_id: str = Path(..., description="Extension identifier"),
    tenant_id: str = Depends(get_tenant_id),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Delete a user extension.
    
    Args:
        extension_id: Extension identifier
        tenant_id: Tenant identifier
        extension_service: UserExtensionService instance
    
    Returns:
        Deletion status
    """
    success = await extension_service.delete_extension(extension_id, tenant_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Extension not found with ID {extension_id}")
    
    return {"status": "success", "message": f"Extension {extension_id} deleted"}


@router.get("/type/{extension_type}", response_model=List[Dict[str, Any]])
async def get_extensions_by_type(
    extension_type: str = Path(..., description="Extension type"),
    page: int = Query(1, description="Page number"),
    page_size: int = Query(20, description="Page size"),
    tenant_id: str = Depends(get_tenant_id),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Get all extensions of a specific type.
    
    Args:
        extension_type: Extension type
        page: Page number
        page_size: Page size
        tenant_id: Tenant identifier
        extension_service: UserExtensionService instance
    
    Returns:
        List of extension data
    """
    extensions = await extension_service.get_extensions_by_type(
        extension_type=extension_type,
        tenant_id=tenant_id,
        page=page,
        page_size=page_size
    )
    
    return [ext.to_dict() for ext in extensions]


@router.get("/tenants", response_model=List[str])
async def get_all_tenants(
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Get all tenant IDs that have user extensions.
    
    Args:
        extension_service: UserExtensionService instance
    
    Returns:
        List of tenant IDs
    """
    tenants = await extension_service.get_all_tenants()
    
    return tenants


@router.get("/tenant/{tenant_id}/extensions", response_model=List[Dict[str, Any]])
async def find_all_for_tenant(
    tenant_id: str = Path(..., description="Tenant identifier"),
    page: int = Query(1, description="Page number"),
    page_size: int = Query(20, description="Page size"),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Find all extensions for a tenant.
    
    Args:
        tenant_id: Tenant identifier
        page: Page number
        page_size: Page size
        extension_service: UserExtensionService instance
    
    Returns:
        List of extension data
    """
    extensions = await extension_service.find_all_for_tenant(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size
    )
    
    return [ext.to_dict() for ext in extensions] 