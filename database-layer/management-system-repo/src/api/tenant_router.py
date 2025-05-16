"""
Tenant Router for Plugin Repository Service.

This module provides API endpoints for tenant-specific plugin operations,
including installation, configuration, and uninstallation.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, BackgroundTasks
from fastapi.responses import JSONResponse

from ..config.settings import get_settings, Settings
from ..repository.plugin_repository import PluginRepository
from ..repository.schema_manager import SchemaManager
from ..models.plugin_models import (
    TenantPlugin, Plugin, PluginVersion,
    PluginInstallRequest, PluginUpdateRequest, PluginConfigUpdateRequest
)

logger = logging.getLogger(__name__)

# Create API router
tenant_router = APIRouter(tags=["tenant-plugins"])

# Dependencies
async def get_plugin_repository(settings: Settings = Depends(get_settings)) -> PluginRepository:
    """Get plugin repository instance."""
    repo = PluginRepository(
        db_host=settings.db_host,
        db_port=settings.db_port,
        db_user=settings.db_user,
        db_password=settings.db_password,
        db_name=settings.db_name
    )
    await repo.initialize()
    try:
        yield repo
    finally:
        await repo.close()

async def get_schema_manager(settings: Settings = Depends(get_settings)) -> SchemaManager:
    """Get schema manager instance."""
    manager = SchemaManager(
        db_host=settings.db_host,
        db_port=settings.db_port,
        db_user=settings.db_user,
        db_password=settings.db_password,
        db_name=settings.db_name
    )
    await manager.initialize()
    try:
        yield manager
    finally:
        await manager.close()


# Background tasks
async def install_plugin_schema(
    tenant_id: str,
    plugin_id: str,
    plugin_type: str,
    schema_manager: SchemaManager
):
    """Background task to create schema for tenant plugin."""
    logger.info(f"Creating schema for tenant {tenant_id}, plugin {plugin_id}")
    success = await schema_manager.create_tenant_plugin_schema(
        tenant_id=tenant_id,
        plugin_id=plugin_id,
        plugin_type=plugin_type
    )
    
    if not success:
        logger.error(f"Failed to create schema for tenant {tenant_id}, plugin {plugin_id}")
        # Update tenant plugin status to error
        # This would require a repository reference, so in a real system
        # we would use a task queue to handle this properly


async def uninstall_plugin_schema(
    tenant_id: str,
    plugin_type: str,
    schema_manager: SchemaManager
):
    """Background task to drop schema for tenant plugin."""
    logger.info(f"Dropping schema for tenant {tenant_id}, plugin type {plugin_type}")
    success = await schema_manager.drop_tenant_plugin_schema(
        tenant_id=tenant_id,
        plugin_type=plugin_type
    )
    
    if not success:
        logger.error(f"Failed to drop schema for tenant {tenant_id}, plugin type {plugin_type}")


# Tenant plugin endpoints

@tenant_router.get("/tenants/{tenant_id}/plugins", response_model=Dict[str, Any])
async def list_tenant_plugins(
    tenant_id: str = Path(..., description="Tenant ID"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    status_filter: Optional[str] = Query(None, description="Filter by plugin status"),
    repo: PluginRepository = Depends(get_plugin_repository)
):
    """
    List plugins installed for a tenant.
    
    Returns a paginated list of plugins installed for the specified tenant.
    """
    try:
        tenant_plugins, total_count = await repo.get_tenant_plugins(
            tenant_id=tenant_id,
            offset=offset,
            limit=limit,
            status_filter=status_filter
        )
        
        return {
            "tenant_id": tenant_id,
            "items": tenant_plugins,
            "total": total_count,
            "offset": offset,
            "limit": limit,
            "filtered": bool(status_filter)
        }
    
    except Exception as e:
        logger.error(f"Error listing plugins for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tenant plugins"
        )


@tenant_router.get("/tenants/{tenant_id}/plugins/{plugin_id}", response_model=TenantPlugin)
async def get_tenant_plugin(
    tenant_id: str = Path(..., description="Tenant ID"),
    plugin_id: str = Path(..., description="Plugin ID"),
    repo: PluginRepository = Depends(get_plugin_repository)
):
    """
    Get details for a specific tenant plugin.
    
    Returns tenant-specific plugin data including configuration and status.
    """
    try:
        tenant_plugin = await repo.get_tenant_plugin(tenant_id, plugin_id)
        
        if not tenant_plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin {plugin_id} not found for tenant {tenant_id}"
            )
        
        return tenant_plugin
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error retrieving plugin {plugin_id} for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tenant plugin"
        )


@tenant_router.post("/tenants/{tenant_id}/plugins", response_model=TenantPlugin, status_code=status.HTTP_201_CREATED)
async def install_tenant_plugin(
    tenant_id: str = Path(..., description="Tenant ID"),
    install_request: PluginInstallRequest = None,
    background_tasks: BackgroundTasks = None,
    repo: PluginRepository = Depends(get_plugin_repository),
    schema_manager: SchemaManager = Depends(get_schema_manager)
):
    """
    Install a plugin for a tenant.
    
    Creates tenant-specific data for the specified plugin and initializes schema.
    """
    try:
        # Validate tenant ID
        if install_request.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID in request body must match URL parameter"
            )
        
        # Check if plugin exists
        plugin = await repo.get_plugin(install_request.plugin_id)
        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin with ID {install_request.plugin_id} not found"
            )
        
        # Determine version to install
        version_id = install_request.version_id
        if not version_id:
            # Get latest version
            versions, _ = await repo.get_plugin_versions(
                plugin_id=install_request.plugin_id,
                offset=0,
                limit=1
            )
            
            if not versions:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No versions found for plugin {install_request.plugin_id}"
                )
            
            # Find latest version
            latest_version = None
            for version in versions:
                if version.is_latest:
                    latest_version = version
                    break
            
            if not latest_version:
                latest_version = versions[0]  # Use first version if no latest flag
            
            version_id = latest_version.version_id
        
        # Create tenant plugin record
        tenant_plugin_data = TenantPlugin(
            tenant_id=tenant_id,
            plugin_id=install_request.plugin_id,
            version_id=version_id,
            status="installing",
            configurations=install_request.configurations,
            features_enabled=install_request.features_to_enable
        )
        
        tenant_plugin = await repo.install_tenant_plugin(tenant_plugin_data)
        
        # Schedule schema creation as background task
        background_tasks.add_task(
            install_plugin_schema,
            tenant_id=tenant_id,
            plugin_id=install_request.plugin_id,
            plugin_type=plugin.type,
            schema_manager=schema_manager
        )
        
        return tenant_plugin
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error installing plugin for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to install plugin for tenant"
        )


@tenant_router.put("/tenants/{tenant_id}/plugins/{plugin_id}", response_model=TenantPlugin)
async def update_tenant_plugin(
    tenant_id: str = Path(..., description="Tenant ID"),
    plugin_id: str = Path(..., description="Plugin ID"),
    update_request: PluginUpdateRequest = None,
    background_tasks: BackgroundTasks = None,
    repo: PluginRepository = Depends(get_plugin_repository),
    schema_manager: SchemaManager = Depends(get_schema_manager)
):
    """
    Update a tenant plugin.
    
    Updates tenant-specific plugin data, such as version or configuration.
    """
    try:
        # Validate tenant ID and plugin ID
        if update_request.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID in request body must match URL parameter"
            )
        
        if update_request.plugin_id != plugin_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plugin ID in request body must match URL parameter"
            )
        
        # Check if tenant plugin exists
        tenant_plugin = await repo.get_tenant_plugin(tenant_id, plugin_id)
        if not tenant_plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin {plugin_id} not found for tenant {tenant_id}"
            )
        
        # Get plugin type
        plugin = await repo.get_plugin(plugin_id)
        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin with ID {plugin_id} not found"
            )
        
        # Check if version exists
        if update_request.version_id:
            version = await repo.get_plugin_version(update_request.version_id)
            if not version:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Version {update_request.version_id} not found"
                )
            
            if version.plugin_id != plugin_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Version {update_request.version_id} does not belong to plugin {plugin_id}"
                )
        
        # Prepare update data
        update_data = {}
        if update_request.version_id:
            update_data["version_id"] = update_request.version_id
            update_data["status"] = "upgrading"
        
        if update_request.configurations:
            update_data["configurations"] = update_request.configurations
        
        if update_request.features_to_enable:
            update_data["features_enabled"] = update_request.features_to_enable
        
        # Update tenant plugin
        updated_plugin = await repo.update_tenant_plugin(tenant_id, plugin_id, update_data)
        
        # If version changed, schedule schema migration as background task
        if update_request.version_id and update_request.version_id != tenant_plugin.version_id:
            # Get current version
            current_version = await repo.get_plugin_version(tenant_plugin.version_id)
            # Get new version
            new_version = await repo.get_plugin_version(update_request.version_id)
            
            if current_version and new_version:
                background_tasks.add_task(
                    schema_manager.apply_schema_migration,
                    tenant_id=tenant_id,
                    plugin_id=plugin_id,
                    version_from=current_version.version,
                    version_to=new_version.version
                )
        
        return updated_plugin
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error updating plugin {plugin_id} for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tenant plugin"
        )


@tenant_router.put("/tenants/{tenant_id}/plugins/{plugin_id}/config", response_model=TenantPlugin)
async def update_tenant_plugin_config(
    tenant_id: str = Path(..., description="Tenant ID"),
    plugin_id: str = Path(..., description="Plugin ID"),
    config_request: PluginConfigUpdateRequest = None,
    repo: PluginRepository = Depends(get_plugin_repository)
):
    """
    Update tenant plugin configuration.
    
    Updates just the configuration for a tenant plugin.
    """
    try:
        # Check if tenant plugin exists
        tenant_plugin = await repo.get_tenant_plugin(tenant_id, plugin_id)
        if not tenant_plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin {plugin_id} not found for tenant {tenant_id}"
            )
        
        # Update tenant plugin configuration
        update_data = {"configurations": config_request.configurations}
        updated_plugin = await repo.update_tenant_plugin(tenant_id, plugin_id, update_data)
        
        return updated_plugin
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error updating config for plugin {plugin_id}, tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tenant plugin configuration"
        )


@tenant_router.delete("/tenants/{tenant_id}/plugins/{plugin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def uninstall_tenant_plugin(
    tenant_id: str = Path(..., description="Tenant ID"),
    plugin_id: str = Path(..., description="Plugin ID"),
    background_tasks: BackgroundTasks = None,
    repo: PluginRepository = Depends(get_plugin_repository),
    schema_manager: SchemaManager = Depends(get_schema_manager)
):
    """
    Uninstall a plugin for a tenant.
    
    Removes tenant-specific plugin data and drops schema.
    """
    try:
        # Check if tenant plugin exists
        tenant_plugin = await repo.get_tenant_plugin(tenant_id, plugin_id)
        if not tenant_plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin {plugin_id} not found for tenant {tenant_id}"
            )
        
        # Get plugin type
        plugin = await repo.get_plugin(plugin_id)
        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin with ID {plugin_id} not found"
            )
        
        # Uninstall tenant plugin
        success = await repo.uninstall_tenant_plugin(tenant_id, plugin_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to uninstall plugin"
            )
        
        # Schedule schema drop as background task
        background_tasks.add_task(
            uninstall_plugin_schema,
            tenant_id=tenant_id,
            plugin_type=plugin.type,
            schema_manager=schema_manager
        )
        
        return None
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error uninstalling plugin {plugin_id} for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to uninstall tenant plugin"
        ) 