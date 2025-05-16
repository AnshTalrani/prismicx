"""
Plugin Router for Plugin Repository Service.

This module provides API endpoints for plugin management, including
plugin registry, versioning, and schema migrations.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse

from ..config.settings import get_settings, Settings
from ..repository.plugin_repository import PluginRepository
from ..models.plugin_models import (
    Plugin, PluginVersion, SchemaMigration,
    PluginInstallRequest, PluginUpdateRequest
)

logger = logging.getLogger(__name__)

# Create API router
plugin_router = APIRouter(tags=["plugins"])

# Dependency to get plugin repository
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


# Plugin registry endpoints

@plugin_router.get("/plugins", response_model=Dict[str, Any])
async def list_plugins(
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    type_filter: Optional[str] = Query(None, description="Filter by plugin type"),
    status_filter: Optional[str] = Query(None, description="Filter by plugin status"),
    repo: PluginRepository = Depends(get_plugin_repository)
):
    """
    List available plugins with pagination and optional filters.
    
    Returns a paginated list of plugins with metadata.
    """
    try:
        plugins, total_count = await repo.get_plugins(
            offset=offset,
            limit=limit,
            type_filter=type_filter,
            status_filter=status_filter
        )
        
        return {
            "items": plugins,
            "total": total_count,
            "offset": offset,
            "limit": limit,
            "filtered": bool(type_filter or status_filter)
        }
    
    except Exception as e:
        logger.error(f"Error listing plugins: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plugins"
        )


@plugin_router.get("/plugins/{plugin_id}", response_model=Plugin)
async def get_plugin(
    plugin_id: str = Path(..., description="Plugin ID"),
    repo: PluginRepository = Depends(get_plugin_repository)
):
    """
    Get details for a specific plugin.
    
    Returns plugin metadata and information.
    """
    try:
        plugin = await repo.get_plugin(plugin_id)
        
        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin with ID {plugin_id} not found"
            )
        
        return plugin
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error retrieving plugin {plugin_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plugin"
        )


@plugin_router.post("/plugins", response_model=Plugin, status_code=status.HTTP_201_CREATED)
async def create_plugin(
    plugin_data: Plugin,
    repo: PluginRepository = Depends(get_plugin_repository)
):
    """
    Register a new plugin.
    
    Creates a new plugin in the registry with the provided metadata.
    """
    try:
        # Check if plugin ID already exists (if provided)
        if plugin_data.plugin_id:
            existing_plugin = await repo.get_plugin(plugin_data.plugin_id)
            if existing_plugin:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Plugin with ID {plugin_data.plugin_id} already exists"
                )
        
        # Create plugin
        created_plugin = await repo.create_plugin(plugin_data)
        return created_plugin
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error creating plugin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create plugin"
        )


@plugin_router.put("/plugins/{plugin_id}", response_model=Plugin)
async def update_plugin(
    plugin_id: str = Path(..., description="Plugin ID"),
    plugin_data: Dict[str, Any] = None,
    repo: PluginRepository = Depends(get_plugin_repository)
):
    """
    Update an existing plugin.
    
    Updates plugin metadata for the specified plugin.
    """
    try:
        # Check if plugin exists
        existing_plugin = await repo.get_plugin(plugin_id)
        if not existing_plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin with ID {plugin_id} not found"
            )
        
        # Update plugin
        updated_plugin = await repo.update_plugin(plugin_id, plugin_data)
        return updated_plugin
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error updating plugin {plugin_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update plugin"
        )


# Plugin version endpoints

@plugin_router.get("/plugins/{plugin_id}/versions", response_model=Dict[str, Any])
async def list_plugin_versions(
    plugin_id: str = Path(..., description="Plugin ID"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    repo: PluginRepository = Depends(get_plugin_repository)
):
    """
    List versions for a specific plugin.
    
    Returns a paginated list of versions for the specified plugin.
    """
    try:
        # Check if plugin exists
        plugin = await repo.get_plugin(plugin_id)
        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin with ID {plugin_id} not found"
            )
        
        # Get versions
        versions, total_count = await repo.get_plugin_versions(
            plugin_id=plugin_id,
            offset=offset,
            limit=limit
        )
        
        return {
            "plugin_id": plugin_id,
            "items": versions,
            "total": total_count,
            "offset": offset,
            "limit": limit
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error listing versions for plugin {plugin_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plugin versions"
        )


@plugin_router.get("/plugins/{plugin_id}/versions/{version_id}", response_model=PluginVersion)
async def get_plugin_version(
    plugin_id: str = Path(..., description="Plugin ID"),
    version_id: str = Path(..., description="Version ID"),
    repo: PluginRepository = Depends(get_plugin_repository)
):
    """
    Get details for a specific plugin version.
    
    Returns version metadata and information.
    """
    try:
        # Check if plugin exists
        plugin = await repo.get_plugin(plugin_id)
        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin with ID {plugin_id} not found"
            )
        
        # Get version
        version = await repo.get_plugin_version(version_id)
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version with ID {version_id} not found"
            )
        
        if version.plugin_id != plugin_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Version {version_id} does not belong to plugin {plugin_id}"
            )
        
        return version
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error retrieving version {version_id} for plugin {plugin_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plugin version"
        )


@plugin_router.post("/plugins/{plugin_id}/versions", response_model=PluginVersion, status_code=status.HTTP_201_CREATED)
async def create_plugin_version(
    plugin_id: str = Path(..., description="Plugin ID"),
    version_data: PluginVersion = None,
    repo: PluginRepository = Depends(get_plugin_repository)
):
    """
    Add a new version for a plugin.
    
    Creates a new version for the specified plugin.
    """
    try:
        # Check if plugin exists
        plugin = await repo.get_plugin(plugin_id)
        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin with ID {plugin_id} not found"
            )
        
        # Ensure plugin ID in version data matches path parameter
        if version_data.plugin_id and version_data.plugin_id != plugin_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plugin ID in version data must match URL parameter"
            )
        
        # Set plugin ID if not provided
        version_data.plugin_id = plugin_id
        
        # Create version
        created_version = await repo.create_plugin_version(version_data)
        return created_version
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error creating version for plugin {plugin_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create plugin version"
        )


# Schema migration endpoints

@plugin_router.get("/plugins/{plugin_id}/migrations", response_model=Dict[str, Any])
async def list_schema_migrations(
    plugin_id: str = Path(..., description="Plugin ID"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    repo: PluginRepository = Depends(get_plugin_repository)
):
    """
    List schema migrations for a plugin.
    
    Returns a paginated list of schema migrations for the specified plugin.
    """
    try:
        # Check if plugin exists
        plugin = await repo.get_plugin(plugin_id)
        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin with ID {plugin_id} not found"
            )
        
        # Get migrations
        migrations, total_count = await repo.get_schema_migrations(
            plugin_id=plugin_id,
            offset=offset,
            limit=limit
        )
        
        return {
            "plugin_id": plugin_id,
            "items": migrations,
            "total": total_count,
            "offset": offset,
            "limit": limit
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error listing migrations for plugin {plugin_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve schema migrations"
        )


@plugin_router.post("/plugins/{plugin_id}/migrations", response_model=SchemaMigration, status_code=status.HTTP_201_CREATED)
async def create_schema_migration(
    plugin_id: str = Path(..., description="Plugin ID"),
    migration_data: SchemaMigration = None,
    repo: PluginRepository = Depends(get_plugin_repository)
):
    """
    Create a new schema migration for a plugin.
    
    Registers a new schema migration for the specified plugin.
    """
    try:
        # Check if plugin exists
        plugin = await repo.get_plugin(plugin_id)
        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin with ID {plugin_id} not found"
            )
        
        # Ensure plugin ID in migration data matches path parameter
        if migration_data.plugin_id and migration_data.plugin_id != plugin_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plugin ID in migration data must match URL parameter"
            )
        
        # Set plugin ID if not provided
        migration_data.plugin_id = plugin_id
        
        # Create migration
        created_migration = await repo.create_schema_migration(migration_data)
        return created_migration
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error creating migration for plugin {plugin_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create schema migration"
        )