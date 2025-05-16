"""
Tenant Management Service Client.

Client for interacting with the Tenant Management Service to retrieve tenant information.
"""
import logging
import json
from typing import Dict, Any, Optional, List
import httpx
from functools import lru_cache

from src.postgres_migration.config.postgres_config import TENANT_MGMT_URL, TENANT_MGMT_TIMEOUT_MS

logger = logging.getLogger(__name__)

class TenantManagementClient:
    """Client for interacting with the Tenant Management Service."""
    
    def __init__(self, base_url: str = TENANT_MGMT_URL, timeout_ms: int = TENANT_MGMT_TIMEOUT_MS):
        """
        Initialize the tenant management client.
        
        Args:
            base_url: Base URL for the tenant management service
            timeout_ms: Request timeout in milliseconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout_ms / 1000.0  # Convert to seconds
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Content-Type": "application/json"}
        )
        logger.info(f"Initialized Tenant Management Client with URL: {base_url}")
    
    async def get_tenant_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant information by ID.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Tenant information or None if not found
        """
        try:
            response = await self.client.get(f"/api/v1/tenants/{tenant_id}")
            
            if response.status_code == 200:
                tenant_info = response.json()
                logger.debug(f"Retrieved tenant info for {tenant_id}")
                return tenant_info
            elif response.status_code == 404:
                logger.warning(f"Tenant {tenant_id} not found")
                return None
            else:
                logger.error(f"Error retrieving tenant {tenant_id}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error connecting to tenant management service: {str(e)}")
            return None
    
    @lru_cache(maxsize=100)
    async def get_tenant_connection_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant database connection information (cached).
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Connection information or None if not found
        """
        try:
            response = await self.client.get(
                f"/api/v1/tenant-connection",
                headers={"X-Tenant-ID": tenant_id}
            )
            
            if response.status_code == 200:
                connection_info = response.json()
                logger.debug(f"Retrieved connection info for {tenant_id}")
                return connection_info
            else:
                logger.error(f"Error retrieving connection for {tenant_id}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting tenant connection info: {str(e)}")
            return None
    
    async def list_tenants(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all available tenants.
        
        Args:
            limit: Maximum number of tenants to retrieve
            offset: Pagination offset
            
        Returns:
            List of tenant information dictionaries
        """
        try:
            response = await self.client.get(
                f"/api/v1/tenants",
                params={"limit": limit, "offset": offset}
            )
            
            if response.status_code == 200:
                tenants = response.json().get("tenants", [])
                logger.debug(f"Retrieved {len(tenants)} tenants")
                return tenants
            else:
                logger.error(f"Error listing tenants: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error listing tenants: {str(e)}")
            return []
    
    async def validate_tenant(self, tenant_id: str) -> bool:
        """
        Validate if a tenant exists and is active.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            True if tenant exists and is active, False otherwise
        """
        tenant_info = await self.get_tenant_info(tenant_id)
        if not tenant_info:
            return False
        
        # Check if tenant is active
        return tenant_info.get("status") == "active"
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("Closed Tenant Management Client")

# Create a singleton instance
client = TenantManagementClient()

# Module-level functions
async def get_tenant_info(tenant_id: str) -> Optional[Dict[str, Any]]:
    """Get tenant information by ID."""
    return await client.get_tenant_info(tenant_id)

async def get_tenant_connection_info(tenant_id: str) -> Optional[Dict[str, Any]]:
    """Get tenant database connection information (cached)."""
    return await client.get_tenant_connection_info(tenant_id)

async def list_tenants(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """List all available tenants."""
    return await client.list_tenants(limit, offset)

async def validate_tenant(tenant_id: str) -> bool:
    """Validate if a tenant exists and is active."""
    return await client.validate_tenant(tenant_id) 