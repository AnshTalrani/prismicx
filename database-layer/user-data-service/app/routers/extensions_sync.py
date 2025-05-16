"""
User Extensions Router (Sync Version)

API routes for managing user extensions with synchronous operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header, Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from ..services.user_extension_service import UserExtensionService
from ..models.user_extension import UserExtension
from ..dependencies import get_mongo_client_sync

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request and response validation
class ExtensionCreate(BaseModel):
    user_id: str = Field(..., description="User identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    extension_type: str = Field(..., description="Extension type")
    metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Extension metrics")
    practicality: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Extension practicality data")

class MetricsUpdate(BaseModel):
    metrics: Dict[str, Any] = Field(..., description="Extension metrics to update")

class PracticalityUpdate(BaseModel):
    practicality: Dict[str, Any] = Field(..., description="Extension practicality data to update")

class FactorAdd(BaseModel):
    name: str = Field(..., description="Factor name")
    value: float = Field(..., description="Factor value")
    weight: float = Field(..., description="Factor weight")

# Service dependency
def get_extension_service() -> UserExtensionService:
    """
    Get the user extension service.
    
    Returns:
        UserExtensionService instance
    """
    mongo_client = get_mongo_client_sync()
    service = UserExtensionService(mongo_client)
    service.initialize("user_data")
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
def get_extension(
    extension_id: str = Path(..., description="Extension identifier"),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Get a user extension by ID.
    
    Args:
        extension_id: Extension identifier
        extension_service: UserExtensionService instance
    
    Returns:
        User extension data
    """
    extension = extension_service.get_extension(extension_id)
    
    if not extension:
        raise HTTPException(status_code=404, detail=f"Extension not found with ID {extension_id}")
    
    return extension.model_dump()


@router.get("/user/{user_id}", response_model=List[Dict[str, Any]])
def get_extensions_by_user(
    user_id: str = Path(..., description="User identifier"),
    tenant_id: Optional[str] = Query(None, description="Optional tenant ID filter"),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Get all extensions for a user.
    
    Args:
        user_id: User identifier
        tenant_id: Optional tenant ID filter
        extension_service: UserExtensionService instance
    
    Returns:
        List of user extension data
    """
    extensions = extension_service.get_extensions_by_user(user_id, tenant_id)
    
    return [ext.model_dump() for ext in extensions]


@router.post("/", response_model=Dict[str, Any])
def create_extension(
    extension_create: ExtensionCreate,
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Create a new user extension.
    
    Args:
        extension_create: Extension data to create
        extension_service: UserExtensionService instance
    
    Returns:
        Created extension data with ID
    """
    # Create a UserExtension instance from the input data
    extension = UserExtension(
        user_id=extension_create.user_id,
        tenant_id=extension_create.tenant_id,
        extension_type=extension_create.extension_type,
        metrics=extension_create.metrics,
        practicality=extension_create.practicality
    )
    
    # Create the extension in the database
    extension_id = extension_service.create_extension(extension)
    
    if not extension_id:
        raise HTTPException(status_code=500, detail="Failed to create extension")
    
    # Set the ID and return the extension
    extension.id = extension_id
    return extension.model_dump()


@router.put("/extension/{extension_id}/metrics", response_model=Dict[str, Any])
def update_metrics(
    metrics_update: MetricsUpdate,
    extension_id: str = Path(..., description="Extension identifier"),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Update metrics for a user extension.
    
    Args:
        metrics_update: Metrics data to update
        extension_id: Extension identifier
        extension_service: UserExtensionService instance
    
    Returns:
        Success status
    """
    success = extension_service.update_metrics(
        extension_id=extension_id,
        metrics=metrics_update.metrics
    )
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Extension not found with ID {extension_id} or update failed")
    
    return {"status": "success", "message": f"Updated metrics for extension {extension_id}"}


@router.put("/extension/{extension_id}/practicality", response_model=Dict[str, Any])
def update_practicality(
    practicality_update: PracticalityUpdate,
    extension_id: str = Path(..., description="Extension identifier"),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Update practicality data for a user extension.
    
    Args:
        practicality_update: Practicality data to update
        extension_id: Extension identifier
        extension_service: UserExtensionService instance
    
    Returns:
        Success status
    """
    success = extension_service.update_practicality(
        extension_id=extension_id,
        practicality=practicality_update.practicality
    )
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Extension not found with ID {extension_id} or update failed")
    
    return {"status": "success", "message": f"Updated practicality for extension {extension_id}"}


@router.post("/extension/{extension_id}/factor", response_model=Dict[str, Any])
def add_factor(
    factor_add: FactorAdd,
    extension_id: str = Path(..., description="Extension identifier"),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Add a factor to the practicality of a user extension.
    
    Args:
        factor_add: Factor data to add
        extension_id: Extension identifier
        extension_service: UserExtensionService instance
    
    Returns:
        Success status
    """
    factor = {
        "name": factor_add.name,
        "value": factor_add.value,
        "weight": factor_add.weight
    }
    
    success = extension_service.add_factor(
        extension_id=extension_id,
        factor=factor
    )
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Extension not found with ID {extension_id} or update failed")
    
    return {"status": "success", "message": f"Added factor to extension {extension_id}"}


@router.delete("/extension/{extension_id}/factor/{factor_id}")
def remove_factor(
    extension_id: str = Path(..., description="Extension identifier"),
    factor_id: str = Path(..., description="Factor ID"),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Remove a factor from the practicality of a user extension.
    
    Args:
        extension_id: Extension identifier
        factor_id: Factor ID
        extension_service: UserExtensionService instance
    
    Returns:
        Success status
    """
    success = extension_service.remove_factor(
        extension_id=extension_id,
        factor_id=factor_id
    )
    
    if not success:
        raise HTTPException(
            status_code=404, 
            detail=f"Extension not found with ID {extension_id} or factor not found with ID {factor_id}"
        )
    
    return {"status": "success", "message": f"Removed factor {factor_id} from extension {extension_id}"}


@router.delete("/extension/{extension_id}")
def delete_extension(
    extension_id: str = Path(..., description="Extension identifier"),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Delete a user extension.
    
    Args:
        extension_id: Extension identifier
        extension_service: UserExtensionService instance
    
    Returns:
        Deletion status
    """
    success = extension_service.delete_extension(extension_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Extension not found with ID {extension_id}")
    
    return {"status": "success", "message": f"Extension {extension_id} deleted"}


@router.get("/type/{extension_type}", response_model=List[Dict[str, Any]])
def get_extensions_by_type(
    extension_type: str = Path(..., description="Extension type"),
    tenant_id: Optional[str] = Query(None, description="Optional tenant ID filter"),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Get all extensions of a specific type.
    
    Args:
        extension_type: Extension type
        tenant_id: Optional tenant ID filter
        extension_service: UserExtensionService instance
    
    Returns:
        List of extension data
    """
    extensions = extension_service.get_extensions_by_type(
        extension_type=extension_type,
        tenant_id=tenant_id
    )
    
    return [ext.model_dump() for ext in extensions]


@router.get("/tenants", response_model=List[str])
def get_all_tenants(
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Get all tenant IDs that have user extensions.
    
    Args:
        extension_service: UserExtensionService instance
    
    Returns:
        List of tenant IDs
    """
    tenants = extension_service.get_all_tenants()
    
    return tenants


@router.get("/tenant/{tenant_id}/extensions", response_model=List[Dict[str, Any]])
def find_all_for_tenant(
    tenant_id: str = Path(..., description="Tenant identifier"),
    extension_service: UserExtensionService = Depends(get_extension_service)
):
    """
    Find all extensions for a tenant.
    
    Args:
        tenant_id: Tenant identifier
        extension_service: UserExtensionService instance
    
    Returns:
        List of extension data
    """
    extensions = extension_service.find_all_for_tenant(tenant_id)
    
    return [ext.model_dump() for ext in extensions] 