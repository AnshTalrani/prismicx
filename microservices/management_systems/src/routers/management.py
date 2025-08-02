"""
API router for business management systems.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..services.management_service import management_service
from ..models.management_system import (
    ManagementSystem,
    SystemInstance,
    SystemType,
    DataField,
    DataView
)
from ..data.system_templates import get_system_template, get_all_system_templates

router = APIRouter(prefix="/api/v1/management", tags=["management"])

# Request/Response models
class SystemInstanceCreate(BaseModel):
    """Request model for creating a system instance."""
    system_id: str
    name: str
    settings: Dict[str, Any] = {}

class SystemInstanceUpdate(BaseModel):
    """Request model for updating a system instance."""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None
    custom_fields: Optional[List[DataField]] = None
    custom_views: Optional[List[DataView]] = None

class SystemCreate(BaseModel):
    """Request model for creating a management system."""
    system_id: str
    name: str
    type: SystemType
    description: Optional[str] = None
    version: str = "1.0.0"
    tenant_collection: str
    data_fields: List[Dict[str, Any]]
    data_views: List[Dict[str, Any]]
    custom_actions: Optional[List[Dict[str, Any]]] = None

class SystemTemplateCustomization(BaseModel):
    """Request model for customizing a system template."""
    system_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tenant_collection: Optional[str] = None
    custom_fields: Optional[List[Dict[str, Any]]] = None
    custom_views: Optional[List[Dict[str, Any]]] = None

class DataItemCreate(BaseModel):
    """Request model for creating a data item."""
    data: Dict[str, Any]

class DataItemUpdate(BaseModel):
    """Request model for updating a data item."""
    updates: Dict[str, Any]

class FilterParams(BaseModel):
    """Request model for filtering data."""
    filters: Dict[str, Any] = {}

class BulkImportRequest(BaseModel):
    """Request model for bulk importing data."""
    items: List[Dict[str, Any]]

# Routes for system templates
@router.get("/templates", response_model=List[Dict[str, Any]])
async def get_system_templates():
    """Get all available system templates."""
    return get_all_system_templates()

@router.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_template(template_id: str = Path(..., description="Template identifier")):
    """Get a specific system template."""
    template = get_system_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.post("/templates/{template_id}", response_model=ManagementSystem)
async def create_from_template(
    template_id: str,
    customization: SystemTemplateCustomization = None,
    custom_data: Dict[str, Any] = None
):
    """Create a new management system from a template."""
    if customization:
        custom_data = customization.dict(exclude_unset=True)
    system = await management_service.create_system_from_template(template_id, custom_data)
    if not system:
        raise HTTPException(status_code=400, detail="Failed to create system from template")
    return system

# Routes for management systems
@router.get("/systems", response_model=List[ManagementSystem])
async def get_systems():
    """Get all available management systems."""
    return await management_service.get_management_systems()

@router.post("/systems", response_model=ManagementSystem)
async def create_system(system: SystemCreate):
    """Create a new management system."""
    created = await management_service.create_management_system(system.dict())
    if not created:
        raise HTTPException(status_code=400, detail="Failed to create management system")
    return created

@router.get("/systems/{system_id}", response_model=ManagementSystem)
async def get_system(system_id: str = Path(..., description="System identifier")):
    """Get a specific management system."""
    system = await management_service.get_management_system(system_id)
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    return system

@router.patch("/systems/{system_id}", response_model=bool)
async def update_system(
    updates: Dict[str, Any],
    system_id: str = Path(..., description="System identifier")
):
    """Update a management system."""
    success = await management_service.update_management_system(system_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="System not found")
    return success

@router.delete("/systems/{system_id}", response_model=bool)
async def delete_system(system_id: str = Path(..., description="System identifier")):
    """Delete a management system."""
    success = await management_service.delete_management_system(system_id)
    if not success:
        raise HTTPException(status_code=404, detail="System not found or has active instances")
    return success

# Routes for tenant system instances
@router.get("/tenants/{tenant_id}/systems", response_model=List[SystemInstance])
async def get_tenant_systems(tenant_id: str = Path(..., description="Tenant identifier")):
    """Get all system instances for a tenant."""
    return await management_service.get_tenant_systems(tenant_id)

@router.post("/tenants/{tenant_id}/systems", response_model=SystemInstance)
async def create_system_instance(
    instance: SystemInstanceCreate,
    tenant_id: str = Path(..., description="Tenant identifier")
):
    """Create a new system instance for a tenant."""
    created = await management_service.create_system_instance(
        tenant_id=tenant_id,
        system_id=instance.system_id,
        name=instance.name,
        settings=instance.settings
    )
    if not created:
        raise HTTPException(status_code=400, detail="Failed to create system instance")
    return created

@router.get("/tenants/{tenant_id}/systems/{instance_id}", response_model=SystemInstance)
async def get_system_instance(
    tenant_id: str = Path(..., description="Tenant identifier"),
    instance_id: str = Path(..., description="System instance identifier")
):
    """Get a specific system instance."""
    instance = await management_service.get_system_instance(tenant_id, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="System instance not found")
    return instance

@router.patch("/tenants/{tenant_id}/systems/{instance_id}", response_model=bool)
async def update_system_instance(
    updates: SystemInstanceUpdate,
    tenant_id: str = Path(..., description="Tenant identifier"),
    instance_id: str = Path(..., description="System instance identifier")
):
    """Update a system instance."""
    success = await management_service.update_system_instance(
        tenant_id=tenant_id,
        instance_id=instance_id,
        updates=updates.dict(exclude_unset=True)
    )
    if not success:
        raise HTTPException(status_code=404, detail="System instance not found")
    return success

@router.delete("/tenants/{tenant_id}/systems/{instance_id}", response_model=bool)
async def delete_system_instance(
    tenant_id: str = Path(..., description="Tenant identifier"),
    instance_id: str = Path(..., description="System instance identifier")
):
    """Delete a system instance."""
    success = await management_service.delete_system_instance(tenant_id, instance_id)
    if not success:
        raise HTTPException(status_code=404, detail="System instance not found")
    return success

# Routes for system data
@router.get("/tenants/{tenant_id}/systems/{instance_id}/data")
async def get_data(
    tenant_id: str = Path(..., description="Tenant identifier"),
    instance_id: str = Path(..., description="System instance identifier"),
    view_id: Optional[str] = Query(None, description="View identifier"),
    page: int = Query(1, description="Page number", ge=1),
    page_size: int = Query(50, description="Items per page", ge=1, le=100)
):
    """Get data for a system instance."""
    return await management_service.get_system_data(
        tenant_id=tenant_id,
        instance_id=instance_id,
        view_id=view_id,
        page=page,
        page_size=page_size
    )

@router.post("/tenants/{tenant_id}/systems/{instance_id}/data/filter")
async def filter_data(
    filter_params: FilterParams,
    tenant_id: str = Path(..., description="Tenant identifier"),
    instance_id: str = Path(..., description="System instance identifier"),
    view_id: Optional[str] = Query(None, description="View identifier"),
    page: int = Query(1, description="Page number", ge=1),
    page_size: int = Query(50, description="Items per page", ge=1, le=100)
):
    """Filter data for a system instance."""
    return await management_service.get_system_data(
        tenant_id=tenant_id,
        instance_id=instance_id,
        view_id=view_id,
        filters=filter_params.filters,
        page=page,
        page_size=page_size
    )

@router.post("/tenants/{tenant_id}/systems/{instance_id}/data", status_code=201)
async def create_item(
    item: DataItemCreate,
    tenant_id: str = Path(..., description="Tenant identifier"),
    instance_id: str = Path(..., description="System instance identifier")
):
    """Create a new data item."""
    created = await management_service.create_data_item(
        tenant_id=tenant_id,
        instance_id=instance_id,
        data=item.data
    )
    if not created:
        raise HTTPException(status_code=400, detail="Failed to create data item")
    return created

@router.post("/tenants/{tenant_id}/systems/{instance_id}/data/bulk-import")
async def bulk_import(
    import_data: BulkImportRequest,
    tenant_id: str = Path(..., description="Tenant identifier"),
    instance_id: str = Path(..., description="System instance identifier")
):
    """Bulk import data items."""
    result = await management_service.bulk_import_data(
        tenant_id=tenant_id,
        instance_id=instance_id,
        items=import_data.items
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Import failed"))
    return result

@router.patch("/tenants/{tenant_id}/systems/{instance_id}/data/{item_id}", response_model=bool)
async def update_item(
    updates: DataItemUpdate,
    tenant_id: str = Path(..., description="Tenant identifier"),
    instance_id: str = Path(..., description="System instance identifier"),
    item_id: str = Path(..., description="Item identifier")
):
    """Update a data item."""
    success = await management_service.update_data_item(
        tenant_id=tenant_id,
        instance_id=instance_id,
        item_id=item_id,
        updates=updates.updates
    )
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return success

@router.delete("/tenants/{tenant_id}/systems/{instance_id}/data/{item_id}", response_model=bool)
async def delete_item(
    tenant_id: str = Path(..., description="Tenant identifier"),
    instance_id: str = Path(..., description="System instance identifier"),
    item_id: str = Path(..., description="Item identifier")
):
    """Delete a data item."""
    success = await management_service.delete_data_item(
        tenant_id=tenant_id,
        instance_id=instance_id,
        item_id=item_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return success 