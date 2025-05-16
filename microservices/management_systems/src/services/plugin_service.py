"""
Plugin service for managing business system plugins.

This service provides methods for interacting with the Plugin Repository Service.
"""
import logging
from typing import Dict, List, Any, Optional, Tuple

from ..plugins.plugin_repository_client import PluginRepositoryClient
from ..models.plugin_models import (
    Plugin, 
    PluginVersion, 
    TenantPlugin, 
    SchemaMigration,
    PluginInstallRequest,
    PluginUpdateRequest
)
from ..cache.redis_cache import cache

logger = logging.getLogger(__name__)

class PluginServiceError(Exception):
    """Base exception for plugin service errors."""
    pass

class PluginNotFoundError(PluginServiceError):
    """Exception raised when a plugin is not found."""
    pass

class PluginService:
    """Service for plugin management using the Plugin Repository Service."""
    
    def __init__(self):
        """Initialize the plugin service."""
        self.client = PluginRepositoryClient()
    
    async def close(self):
        """Close the client."""
        await self.client.close()
    
    async def get_available_plugins(
        self,
        offset: int = 0,
        limit: int = 100,
        system_type: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> Tuple[List[Plugin], int]:
        """
        Get available plugins with pagination.
        
        Args:
            offset: Pagination offset
            limit: Pagination limit
            system_type: Filter by system type
            status_filter: Filter by plugin status
            
        Returns:
            Tuple of plugins list and total count
        """
        # Check cache first
        cache_key = f"plugins:available:{system_type or 'all'}:{status_filter or 'all'}:{offset}:{limit}"
        cached = await cache.get(cache_key)
        if cached:
            return cached.get("items", []), cached.get("total", 0)
        
        # Get data from plugin repository
        plugin_data, total = await self.client.get_plugins(
            offset=offset,
            limit=limit,
            type_filter=system_type,
            status_filter=status_filter
        )
        
        # Convert to model objects
        plugins = [Plugin(**data) for data in plugin_data]
        
        # Cache the results
        await cache.set(cache_key, {"items": plugin_data, "total": total}, 3600)
        
        return plugins, total
    
    async def get_plugin(self, plugin_id: str) -> Plugin:
        """
        Get a specific plugin by ID.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Plugin details
            
        Raises:
            PluginNotFoundError: If plugin is not found
        """
        # Check cache first
        cache_key = f"plugins:{plugin_id}"
        cached = await cache.get(cache_key)
        if cached:
            return Plugin(**cached)
        
        # Get data from plugin repository
        plugin_data = await self.client.get_plugin(plugin_id)
        
        if not plugin_data:
            raise PluginNotFoundError(f"Plugin {plugin_id} not found")
        
        # Cache the results
        await cache.set(cache_key, plugin_data, 3600)
        
        return Plugin(**plugin_data)
    
    async def get_plugin_versions(
        self,
        plugin_id: str,
        offset: int = 0,
        limit: int = 100
    ) -> Tuple[List[PluginVersion], int]:
        """
        Get versions for a specific plugin.
        
        Args:
            plugin_id: Plugin identifier
            offset: Pagination offset
            limit: Pagination limit
            
        Returns:
            Tuple of versions list and total count
        """
        # Check cache first
        cache_key = f"plugins:{plugin_id}:versions:{offset}:{limit}"
        cached = await cache.get(cache_key)
        if cached:
            return cached.get("items", []), cached.get("total", 0)
        
        # Get data from plugin repository
        version_data, total = await self.client.get_plugin_versions(
            plugin_id=plugin_id,
            offset=offset,
            limit=limit
        )
        
        # Convert to model objects
        versions = [PluginVersion(**data) for data in version_data]
        
        # Cache the results
        await cache.set(cache_key, {"items": version_data, "total": total}, 3600)
        
        return versions, total
    
    async def get_tenant_plugins(
        self,
        tenant_id: str,
        offset: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None
    ) -> Tuple[List[TenantPlugin], int]:
        """
        Get plugins installed for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            offset: Pagination offset
            limit: Pagination limit
            status_filter: Filter by installation status
            
        Returns:
            Tuple of tenant plugins list and total count
        """
        # Check cache first
        cache_key = f"plugins:tenant:{tenant_id}:{status_filter or 'all'}:{offset}:{limit}"
        cached = await cache.get(cache_key)
        if cached:
            return cached.get("items", []), cached.get("total", 0)
        
        # Get data from plugin repository
        plugin_data, total = await self.client.get_tenant_plugins(
            tenant_id=tenant_id,
            offset=offset,
            limit=limit,
            status_filter=status_filter
        )
        
        # Convert to model objects
        tenant_plugins = [TenantPlugin(**data) for data in plugin_data]
        
        # Cache the results
        await cache.set(cache_key, {"items": plugin_data, "total": total}, 3600)
        
        return tenant_plugins, total
    
    async def get_tenant_plugin(
        self,
        tenant_id: str,
        plugin_id: str
    ) -> TenantPlugin:
        """
        Get a specific tenant plugin.
        
        Args:
            tenant_id: Tenant identifier
            plugin_id: Plugin identifier
            
        Returns:
            Tenant plugin details
            
        Raises:
            PluginNotFoundError: If plugin is not found for tenant
        """
        # Check cache first
        cache_key = f"plugins:tenant:{tenant_id}:{plugin_id}"
        cached = await cache.get(cache_key)
        if cached:
            return TenantPlugin(**cached)
        
        # Get data from plugin repository
        plugin_data = await self.client.get_tenant_plugin(
            tenant_id=tenant_id,
            plugin_id=plugin_id
        )
        
        if not plugin_data:
            raise PluginNotFoundError(f"Plugin {plugin_id} not found for tenant {tenant_id}")
        
        # Cache the results
        await cache.set(cache_key, plugin_data, 3600)
        
        return TenantPlugin(**plugin_data)
    
    async def install_plugin(
        self,
        tenant_id: str,
        request: PluginInstallRequest
    ) -> TenantPlugin:
        """
        Install a plugin for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            request: Installation request
            
        Returns:
            Installed tenant plugin
            
        Raises:
            PluginServiceError: If installation fails
        """
        result = await self.client.install_tenant_plugin(
            tenant_id=tenant_id,
            plugin_id=request.plugin_id,
            version_id=request.version_id,
            configurations=request.configurations,
            features_enabled=request.features_enabled
        )
        
        if not result:
            raise PluginServiceError(f"Failed to install plugin {request.plugin_id} for tenant {tenant_id}")
        
        # Invalidate cache
        await cache.delete_pattern(f"plugins:tenant:{tenant_id}*")
        
        return TenantPlugin(**result)
    
    async def update_tenant_plugin(
        self,
        tenant_id: str,
        plugin_id: str,
        request: PluginUpdateRequest
    ) -> TenantPlugin:
        """
        Update an installed tenant plugin.
        
        Args:
            tenant_id: Tenant identifier
            plugin_id: Plugin identifier
            request: Update request
            
        Returns:
            Updated tenant plugin
            
        Raises:
            PluginNotFoundError: If plugin is not found for tenant
            PluginServiceError: If update fails
        """
        # Create update data dictionary with only non-None values
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            # If no update data, just return current plugin
            return await self.get_tenant_plugin(tenant_id, plugin_id)
        
        result = await self.client.update_tenant_plugin(
            tenant_id=tenant_id,
            plugin_id=plugin_id,
            update_data=update_data
        )
        
        if not result:
            # Check if plugin exists
            try:
                await self.get_tenant_plugin(tenant_id, plugin_id)
                # If we get here, plugin exists but update failed
                raise PluginServiceError(f"Failed to update plugin {plugin_id} for tenant {tenant_id}")
            except PluginNotFoundError:
                # Re-raise the not found error
                raise
        
        # Invalidate cache
        await cache.delete_pattern(f"plugins:tenant:{tenant_id}*")
        
        return TenantPlugin(**result)
    
    async def uninstall_plugin(
        self,
        tenant_id: str,
        plugin_id: str
    ) -> bool:
        """
        Uninstall a plugin for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            plugin_id: Plugin identifier
            
        Returns:
            True if uninstallation was successful
            
        Raises:
            PluginNotFoundError: If plugin is not found for tenant
            PluginServiceError: If uninstallation fails
        """
        # Check if plugin exists
        try:
            await self.get_tenant_plugin(tenant_id, plugin_id)
        except PluginNotFoundError:
            # Re-raise the not found error
            raise
        
        result = await self.client.uninstall_tenant_plugin(
            tenant_id=tenant_id,
            plugin_id=plugin_id
        )
        
        if not result:
            raise PluginServiceError(f"Failed to uninstall plugin {plugin_id} for tenant {tenant_id}")
        
        # Invalidate cache
        await cache.delete_pattern(f"plugins:tenant:{tenant_id}*")
        
        return True 