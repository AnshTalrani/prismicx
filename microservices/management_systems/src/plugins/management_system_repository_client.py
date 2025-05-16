"""
Management System Repository Client for interacting with the Management System Repository Service.

This client provides methods to interact with the Management System Repository Service API.
"""
import os
import logging
import httpx
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class ManagementSystemRepositoryClient:
    """Client for interacting with Management System Repository Service."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        timeout: float = 10.0
    ):
        """Initialize the management system repository client.
        
        Args:
            base_url: Base URL of the Management System Repository Service
            auth_token: Authentication token
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv("SYSTEM_REPO_URL", "http://management-system-repo:8080")
        self.auth_token = auth_token or os.getenv("SYSTEM_REPO_API_KEY", "")
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
    
    # Management system operations
    async def get_systems(
        self,
        offset: int = 0,
        limit: int = 100,
        type_filter: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get available management systems with pagination.
        
        Args:
            offset: Pagination offset
            limit: Pagination limit
            type_filter: Filter by system type
            status_filter: Filter by system status
            
        Returns:
            Tuple of systems list and total count
        """
        url = f"{self.base_url}/api/v1/systems"
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
            logger.error(f"Error retrieving management systems: {str(e)}")
            return [], 0
    
    async def get_system(self, system_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific management system by ID.
        
        Args:
            system_id: System identifier
            
        Returns:
            System data or None if not found
        """
        url = f"{self.base_url}/api/v1/systems/{system_id}"
        headers = self._get_headers()
        
        try:
            response = await self.http_client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Management system {system_id} not found")
                return None
            logger.error(f"HTTP error retrieving management system {system_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving management system {system_id}: {str(e)}")
            return None
    
    async def create_system(self, system_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new management system.
        
        Args:
            system_data: System data to create
            
        Returns:
            Created system data or None if creation failed
        """
        url = f"{self.base_url}/api/v1/systems"
        headers = self._get_headers()
        
        try:
            response = await self.http_client.post(url, headers=headers, json=system_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error creating management system: {str(e)}")
            return None
    
    # Management system version operations
    async def get_system_versions(
        self,
        system_id: str,
        offset: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get versions for a specific management system.
        
        Args:
            system_id: System identifier
            offset: Pagination offset
            limit: Pagination limit
            
        Returns:
            Tuple of versions list and total count
        """
        url = f"{self.base_url}/api/v1/systems/{system_id}/versions"
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
            logger.error(f"Error retrieving versions for management system {system_id}: {str(e)}")
            return [], 0
    
    # Tenant management system operations
    async def get_tenant_systems(
        self,
        tenant_id: str,
        offset: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get management systems installed for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            offset: Pagination offset
            limit: Pagination limit
            status_filter: Filter by installation status
            
        Returns:
            Tuple of tenant systems list and total count
        """
        url = f"{self.base_url}/api/v1/tenants/{tenant_id}/systems"
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
            logger.error(f"Error retrieving management systems for tenant {tenant_id}: {str(e)}")
            return [], 0
    
    async def get_tenant_system(
        self,
        tenant_id: str,
        system_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific tenant management system.
        
        Args:
            tenant_id: Tenant identifier
            system_id: System identifier
            
        Returns:
            Tenant system data or None if not found
        """
        url = f"{self.base_url}/api/v1/tenants/{tenant_id}/systems/{system_id}"
        headers = self._get_headers(tenant_id)
        
        try:
            response = await self.http_client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Management system {system_id} not found for tenant {tenant_id}")
                return None
            logger.error(f"HTTP error retrieving management system {system_id} for tenant {tenant_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving management system {system_id} for tenant {tenant_id}: {str(e)}")
            return None
    
    async def install_tenant_system(
        self,
        tenant_id: str,
        system_id: str,
        version_id: str,
        features_enabled: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Install a management system for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            system_id: System identifier
            version_id: Version identifier
            features_enabled: List of enabled features
            
        Returns:
            Installation result or None if installation failed
        """
        url = f"{self.base_url}/api/v1/tenants/{tenant_id}/systems"
        headers = self._get_headers(tenant_id)
        
        data = {
            "system_id": system_id,
            "version_id": version_id
        }
        
        if features_enabled is not None:
            data["features_enabled"] = features_enabled
            
        try:
            response = await self.http_client.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error installing management system {system_id} for tenant {tenant_id}: {str(e)}")
            return None
    
    async def update_tenant_system(
        self,
        tenant_id: str,
        system_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a tenant's management system.
        
        Args:
            tenant_id: Tenant identifier
            system_id: System identifier
            update_data: Data to update
            
        Returns:
            Updated system data or None if update failed
        """
        url = f"{self.base_url}/api/v1/tenants/{tenant_id}/systems/{system_id}"
        headers = self._get_headers(tenant_id)
        
        try:
            response = await self.http_client.patch(url, headers=headers, json=update_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error updating management system {system_id} for tenant {tenant_id}: {str(e)}")
            return None
    
    async def uninstall_tenant_system(
        self,
        tenant_id: str,
        system_id: str
    ) -> bool:
        """Uninstall a management system from a tenant.
        
        Args:
            tenant_id: Tenant identifier
            system_id: System identifier
            
        Returns:
            True if uninstallation was successful, False otherwise
        """
        url = f"{self.base_url}/api/v1/tenants/{tenant_id}/systems/{system_id}"
        headers = self._get_headers(tenant_id)
        
        try:
            response = await self.http_client.delete(url, headers=headers)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error uninstalling management system {system_id} for tenant {tenant_id}: {str(e)}")
            return False 