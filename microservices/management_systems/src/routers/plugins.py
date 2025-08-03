"""
Plugin router for managing business system plugins.

This router provides endpoints for interacting with plugins.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict, Any, Optional

from ..services.plugin_service import PluginService, PluginNotFoundError, PluginServiceError
from ..models.plugin_models import (
    Plugin, 
    PluginVersion, 
    TenantPlugin, 
    PluginInstallRequest,
    PluginUpdateRequest
)
from ..models.responses import PaginatedResponse, SuccessResponse
from ..common.auth import get_current_user, CurrentUser as User

router = APIRouter(prefix="/plugins", tags=["plugins"])

# Dependency to get the plugin service
async def get_plugin_service() -> PluginService:
    """Get plugin service instance."""
    service = PluginService()
    try:
        yield service
    finally:
        await service.close()

@router.get("/", response_model=PaginatedResponse[Plugin])
async def get_plugins(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    system_type: Optional[str] = Query(None, description="Filter by system type"),
    status: Optional[str] = Query(None, description="Filter by plugin status"),
    current_user: User = Depends(get_current_user),
    service: PluginService = Depends(get_plugin_service)
):
    """
    Get available plugins with pagination.
    
    Returns a paginated list of all available business system plugins.
    """
    plugins, total = await service.get_available_plugins(
        offset=offset,
        limit=limit,
        system_type=system_type,
        status_filter=status
    )
    
    return {
        "items": plugins,
        "total": total,
        "offset": offset,
        "limit": limit
    }

@router.get("/{plugin_id}", response_model=Plugin)
async def get_plugin(
    plugin_id: str = Path(..., description="Plugin identifier"),
    current_user: User = Depends(get_current_user),
    service: PluginService = Depends(get_plugin_service)
):
    """
    Get a specific plugin by ID.
    
    Returns details about a specific business system plugin.
    """
    try:
        return await service.get_plugin(plugin_id)
    except PluginNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{plugin_id}/versions", response_model=PaginatedResponse[PluginVersion])
async def get_plugin_versions(
    plugin_id: str = Path(..., description="Plugin identifier"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    service: PluginService = Depends(get_plugin_service)
):
    """
    Get versions for a specific plugin.
    
    Returns a paginated list of versions for a business system plugin.
    """
    try:
        versions, total = await service.get_plugin_versions(
            plugin_id=plugin_id,
            offset=offset,
            limit=limit
        )
        
        return {
            "items": versions,
            "total": total,
            "offset": offset,
            "limit": limit
        }
    except PluginNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/tenant/{tenant_id}", response_model=PaginatedResponse[TenantPlugin])
async def get_tenant_plugins(
    tenant_id: str = Path(..., description="Tenant identifier"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by installation status"),
    current_user: User = Depends(get_current_user),
    service: PluginService = Depends(get_plugin_service)
):
    """
    Get plugins installed for a tenant.
    
    Returns a paginated list of business system plugins installed for a specific tenant.
    """
    plugins, total = await service.get_tenant_plugins(
        tenant_id=tenant_id,
        offset=offset,
        limit=limit,
        status_filter=status
    )
    
    return {
        "items": plugins,
        "total": total,
        "offset": offset,
        "limit": limit
    }

@router.get("/tenant/{tenant_id}/{plugin_id}", response_model=TenantPlugin)
async def get_tenant_plugin(
    tenant_id: str = Path(..., description="Tenant identifier"),
    plugin_id: str = Path(..., description="Plugin identifier"),
    current_user: User = Depends(get_current_user),
    service: PluginService = Depends(get_plugin_service)
):
    """
    Get a specific tenant plugin.
    
    Returns details about a specific business system plugin installed for a tenant.
    """
    try:
        return await service.get_tenant_plugin(tenant_id, plugin_id)
    except PluginNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/tenant/{tenant_id}/install", response_model=TenantPlugin)
async def install_plugin(
    tenant_id: str = Path(..., description="Tenant identifier"),
    request: PluginInstallRequest = ...,
    current_user: User = Depends(get_current_user),
    service: PluginService = Depends(get_plugin_service)
):
    """
    Install a plugin for a tenant.
    
    Installs a business system plugin for a specific tenant.
    """
    try:
        return await service.install_plugin(tenant_id, request)
    except PluginServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/tenant/{tenant_id}/{plugin_id}", response_model=TenantPlugin)
async def update_tenant_plugin(
    tenant_id: str = Path(..., description="Tenant identifier"),
    plugin_id: str = Path(..., description="Plugin identifier"),
    request: PluginUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    service: PluginService = Depends(get_plugin_service)
):
    """
    Update an installed tenant plugin.
    
    Updates a business system plugin installed for a specific tenant.
    """
    try:
        return await service.update_tenant_plugin(tenant_id, plugin_id, request)
    except PluginNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PluginServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/tenant/{tenant_id}/{plugin_id}", response_model=SuccessResponse)
async def uninstall_plugin(
    tenant_id: str = Path(..., description="Tenant identifier"),
    plugin_id: str = Path(..., description="Plugin identifier"),
    current_user: User = Depends(get_current_user),
    service: PluginService = Depends(get_plugin_service)
):
    """
    Uninstall a plugin for a tenant.
    
    Uninstalls a business system plugin for a specific tenant.
    """
    try:
        await service.uninstall_plugin(tenant_id, plugin_id)
        return {"success": True, "message": f"Plugin {plugin_id} uninstalled successfully"}
    except PluginNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PluginServiceError as e:
        raise HTTPException(status_code=400, detail=str(e)) 