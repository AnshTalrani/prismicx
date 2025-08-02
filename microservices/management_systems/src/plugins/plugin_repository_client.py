"""
Plugin Repository Client for interacting with the Plugin Repository Service.

This client provides methods to interact with the Plugin Repository Service API.
"""
import os
import logging
import httpx
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class PluginRepositoryClient:
    """Client for interacting with Plugin Repository Service."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        timeout: float = 10.0
    ):
        """Initialize the plugin repository client.
        
        Args:
            base_url: Base URL of the Plugin Repository Service
            auth_token: Authentication token
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv("PLUGIN_REPO_URL", "http://plugin-repo-service:8080")
        self.auth_token = auth_token or os.getenv("PLUGIN_REPO_API_KEY", "")
        self.timeout = timeout
        self.http_client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
    
    def _get_headers(self, tenant_id: Optional[str] = None):
        """Get request headers with authentication and optional tenant ID.
        
        Args:
            tenant_id: Optional tenant ID to include in headers
            
        Returns:
            Dictionary of headers
        """
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        if tenant_id:
            headers["X-Tenant-ID"] = tenant_id
            
        return headers
    
    # Plugin operations
    async def get_plugins(
        self,
        offset: int = 0,
        limit: int = 100,
        type_filter: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get available plugins with pagination.
        
        Args:
            offset: Pagination offset
            limit: Pagination limit
            type_filter: Filter by plugin type
            status_filter: Filter by plugin status
            
        Returns:
            Tuple of plugins list and total count
        """
        url = f"{self.base_url}/api/v1/plugins"
        params = {
            "offset": offset,
            "limit": limit
        }
        
        if type_filter:
            params["type"] = type_filter
        if status_filter:
            params["status"] = status_filter
            
        headers = self._get_headers()
        
        try:
            response = await self.http_client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("items", []), data.get("total", 0)
        except Exception as e:
            logger.error(f"Error retrieving plugins: {str(e)}")
            return [], 0
    
    async def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific plugin by ID.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Plugin data or None if not found
        """
        url = f"{self.base_url}/api/v1/plugins/{plugin_id}"
        headers = self._get_headers()
        
        try:
            response = await self.http_client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Plugin {plugin_id} not found")
                return None
            logger.error(f"HTTP error retrieving plugin {plugin_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving plugin {plugin_id}: {str(e)}")
            return None
    
    async def create_plugin(self, plugin_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new plugin.
        
        Args:
            plugin_data: Plugin data to create
            
        Returns:
            Created plugin data or None if creation failed
        """
        url = f"{self.base_url}/api/v1/plugins"
        headers = self._get_headers()
        
        try:
            response = await self.http_client.post(url, headers=headers, json=plugin_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error creating plugin: {str(e)}")
            return None
    
    # Plugin version operations
    async def get_plugin_versions(
        self,
        plugin_id: str,
        offset: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get versions for a specific plugin.
        
        Args:
            plugin_id: Plugin identifier
            offset: Pagination offset
            limit: Pagination limit
            
        Returns:
            Tuple of versions list and total count
        """
        url = f"{self.base_url}/api/v1/plugins/{plugin_id}/versions"
        params = {
            "offset": offset,
            "limit": limit
        }
        headers = self._get_headers()
        
        try:
            response = await self.http_client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("items", []), data.get("total", 0)
        except Exception as e:
            logger.error(f"Error retrieving versions for plugin {plugin_id}: {str(e)}")
            return [], 0
    
    # Tenant plugin operations
    async def get_tenant_plugins(
        self,
        tenant_id: str,
        offset: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get plugins installed for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            offset: Pagination offset
            limit: Pagination limit
            status_filter: Filter by installation status
            
        Returns:
            Tuple of tenant plugins list and total count
        """
        url = f"{self.base_url}/api/v1/tenants/{tenant_id}/plugins"
        params = {
            "offset": offset,
            "limit": limit
        }
        
        if status_filter:
            params["status"] = status_filter
            
        headers = self._get_headers(tenant_id)
        
        try:
            response = await self.http_client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("items", []), data.get("total", 0)
        except Exception as e:
            logger.error(f"Error retrieving plugins for tenant {tenant_id}: {str(e)}")
            return [], 0
    
    async def get_tenant_plugin(
        self,
        tenant_id: str,
        plugin_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific tenant plugin.
        
        Args:
            tenant_id: Tenant identifier
            plugin_id: Plugin identifier
            
        Returns:
            Tenant plugin data or None if not found
        """
        url = f"{self.base_url}/api/v1/tenants/{tenant_id}/plugins/{plugin_id}"
        headers = self._get_headers(tenant_id)
        
        try:
            response = await self.http_client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Plugin {plugin_id} not found for tenant {tenant_id}")
                return None
            logger.error(f"HTTP error retrieving plugin {plugin_id} for tenant {tenant_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving plugin {plugin_id} for tenant {tenant_id}: {str(e)}")
            return None
    
    async def install_tenant_plugin(
        self,
        tenant_id: str,
        plugin_id: str,
        version_id: str,
        configurations: Optional[Dict[str, Any]] = None,
        features_enabled: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Install a plugin for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            plugin_id: Plugin identifier
            version_id: Version identifier
            configurations: Plugin configurations
            features_enabled: Enabled features
            
        Returns:
            Installed tenant plugin data or None if installation failed
        """
        url = f"{self.base_url}/api/v1/tenants/{tenant_id}/plugins"
        headers = self._get_headers(tenant_id)
        
        payload = {
            "tenant_id": tenant_id,
            "plugin_id": plugin_id,
            "version_id": version_id,
            "status": "installed",
            "configurations": configurations or {},
            "features_enabled": features_enabled or []
        }
        
        try:
            response = await self.http_client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error installing plugin {plugin_id} for tenant {tenant_id}: {str(e)}")
            return None
    
    async def update_tenant_plugin(
        self,
        tenant_id: str,
        plugin_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an installed tenant plugin.
        
        Args:
            tenant_id: Tenant identifier
            plugin_id: Plugin identifier
            update_data: Data to update
            
        Returns:
            Updated tenant plugin data or None if update failed
        """
        url = f"{self.base_url}/api/v1/tenants/{tenant_id}/plugins/{plugin_id}"
        headers = self._get_headers(tenant_id)
        
        try:
            response = await self.http_client.put(url, headers=headers, json=update_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error updating plugin {plugin_id} for tenant {tenant_id}: {str(e)}")
            return None
    
    async def uninstall_tenant_plugin(
        self,
        tenant_id: str,
        plugin_id: str
    ) -> bool:
        """Uninstall a plugin for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            plugin_id: Plugin identifier
            
        Returns:
            True if uninstallation was successful
        """
        url = f"{self.base_url}/api/v1/tenants/{tenant_id}/plugins/{plugin_id}"
        headers = self._get_headers(tenant_id)
        
        try:
            response = await self.http_client.delete(url, headers=headers)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error uninstalling plugin {plugin_id} for tenant {tenant_id}: {str(e)}")
            return False 