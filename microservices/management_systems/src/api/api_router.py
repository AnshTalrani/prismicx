"""
Management API router for handling HTTP requests.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Path, Query, status
from typing import List, Dict, Any, Optional

from ..services.management_service import (
    management_service, 
    ManagementServiceError,
    TemplateNotFoundError,
    SystemNotFoundError,
    InstanceNotFoundError
)
from ..models.management_system import (
    ManagementSystem,
    SystemInstance,
    DataItem,
    DataView
)
from ..common.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["management"])

@router.get("/systems", response_model=List[ManagementSystem])
async def get_systems():
    """Get all available management systems."""
    try:
        return await management_service.get_management_systems()
    except ManagementServiceError as e:
        logger.error(f"Error fetching systems: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve management systems"
        )

@router.get("/systems/{system_id}", response_model=ManagementSystem)
async def get_system(system_id: str = Path(..., description="System ID")):
    """Get details for a specific management system."""
    try:
        system = await management_service.get_management_system(system_id)
        if not system:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"System {system_id} not found"
            )
        return system
    except ManagementServiceError as e:
        logger.error(f"Error fetching system {system_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system {system_id}"
        )

@router.post("/systems/template/{template_id}", response_model=ManagementSystem)
async def create_system_from_template(
    template_id: str = Path(..., description="Template ID"),
    custom_data: Dict[str, Any] = {}
):
    """Create a new management system from a template."""
    try:
        system = await management_service.create_system_from_template(template_id, custom_data)
        if not system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create system from template {template_id}"
            )
        return system
    except TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )
    except ManagementServiceError as e:
        logger.error(f"Error creating system from template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create system from template {template_id}"
        )

@router.post("/systems", response_model=ManagementSystem)
async def create_system(system_data: Dict[str, Any]):
    """Create a new management system."""
    try:
        system = await management_service.create_management_system(system_data)
        if not system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create management system"
            )
        return system
    except ManagementServiceError as e:
        logger.error(f"Error creating system: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create management system"
        )

@router.put("/systems/{system_id}", response_model=bool)
async def update_system(
    system_id: str = Path(..., description="System ID"),
    updates: Dict[str, Any] = {}
):
    """Update a management system."""
    try:
        success = await management_service.update_management_system(system_id, updates)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"System {system_id} not found or not updated"
            )
        return success
    except ManagementServiceError as e:
        logger.error(f"Error updating system {system_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update system {system_id}"
        )

@router.delete("/systems/{system_id}", response_model=bool)
async def delete_system(system_id: str = Path(..., description="System ID")):
    """Delete a management system."""
    try:
        success = await management_service.delete_management_system(system_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"System {system_id} not found or not deleted"
            )
        return success
    except ManagementServiceError as e:
        logger.error(f"Error deleting system {system_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete system {system_id}"
        )

@router.get("/tenant/{tenant_id}/systems", response_model=List[SystemInstance])
async def get_tenant_systems(
    tenant_id: str = Path(..., description="Tenant ID")
):
    """Get all management systems for a tenant."""
    try:
        return await management_service.get_tenant_systems(tenant_id)
    except ManagementServiceError as e:
        logger.error(f"Error fetching systems for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve systems for tenant {tenant_id}"
        )

@router.get("/tenant/{tenant_id}/systems/{instance_id}", response_model=SystemInstance)
async def get_tenant_system(
    tenant_id: str = Path(..., description="Tenant ID"),
    instance_id: str = Path(..., description="Instance ID")
):
    """Get a specific system instance for a tenant."""
    try:
        instance = await management_service.get_system_instance(tenant_id, instance_id)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"System instance {instance_id} not found for tenant {tenant_id}"
            )
        return instance
    except ManagementServiceError as e:
        logger.error(f"Error fetching system {instance_id} for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system {instance_id} for tenant {tenant_id}"
        )

@router.post("/tenant/{tenant_id}/systems", response_model=SystemInstance)
async def create_tenant_system(
    tenant_id: str = Path(..., description="Tenant ID"),
    system_id: str = Query(..., description="System ID to instantiate"),
    name: str = Query(..., description="Instance name"),
    settings: Dict[str, Any] = {}
):
    """Create a new system instance for a tenant."""
    try:
        instance = await management_service.create_system_instance(tenant_id, system_id, name, settings)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create system instance for tenant {tenant_id}"
            )
        return instance
    except SystemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System {system_id} not found"
        )
    except ManagementServiceError as e:
        logger.error(f"Error creating system instance for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create system instance for tenant {tenant_id}"
        )

@router.put("/tenant/{tenant_id}/systems/{instance_id}", response_model=bool)
async def update_tenant_system(
    tenant_id: str = Path(..., description="Tenant ID"),
    instance_id: str = Path(..., description="Instance ID"),
    updates: Dict[str, Any] = {}
):
    """Update a system instance for a tenant."""
    try:
        success = await management_service.update_system_instance(tenant_id, instance_id, updates)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"System instance {instance_id} not found for tenant {tenant_id} or not updated"
            )
        return success
    except ManagementServiceError as e:
        logger.error(f"Error updating system {instance_id} for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update system {instance_id} for tenant {tenant_id}"
        )

@router.delete("/tenant/{tenant_id}/systems/{instance_id}", response_model=bool)
async def delete_tenant_system(
    tenant_id: str = Path(..., description="Tenant ID"),
    instance_id: str = Path(..., description="Instance ID")
):
    """Delete a system instance for a tenant."""
    try:
        success = await management_service.delete_system_instance(tenant_id, instance_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"System instance {instance_id} not found for tenant {tenant_id} or not deleted"
            )
        return success
    except ManagementServiceError as e:
        logger.error(f"Error deleting system {instance_id} for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete system {instance_id} for tenant {tenant_id}"
        )

@router.get("/tenant/{tenant_id}/systems/{instance_id}/data", response_model=Dict[str, Any])
async def get_tenant_system_data(
    tenant_id: str = Path(..., description="Tenant ID"),
    instance_id: str = Path(..., description="Instance ID"),
    view_id: Optional[str] = Query(None, description="View ID to use"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    filters: Optional[Dict[str, Any]] = None
):
    """Get data for a system instance."""
    try:
        data = await management_service.get_system_data(
            tenant_id, 
            instance_id, 
            view_id=view_id, 
            filters=filters, 
            page=page, 
            page_size=page_size
        )
        return data
    except InstanceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System instance {instance_id} not found for tenant {tenant_id}"
        )
    except SystemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System definition not found for instance {instance_id}"
        )
    except ManagementServiceError as e:
        logger.error(f"Error retrieving data for system {instance_id} of tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve data for system {instance_id} of tenant {tenant_id}"
        )

# ... Other data management endpoints (create, update, delete) with similar error handling ... 