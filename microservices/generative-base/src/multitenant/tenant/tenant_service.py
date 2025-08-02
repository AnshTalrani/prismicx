"""
Tenant Service Client Module

This module provides a client for the tenant management service.
It allows retrieving tenant information and connection details.
"""

import logging
import os
from typing import Optional, Dict, Any
import httpx
from httpx import AsyncClient, Response

logger = logging.getLogger(__name__)

# Default tenant management service URL
DEFAULT_TENANT_MGT_URL = "http://tenant-mgmt-service:8000"


class TenantServiceClient:
    """
    Client for the tenant management service.
    
    This class provides methods to retrieve tenant information and
    connection details from the tenant management service.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the tenant service client.
        
        Args:
            base_url: The base URL of the tenant management service.
                Defaults to the value from environment or a default URL.
        """
        self.base_url = base_url or os.environ.get("TENANT_MGT_URL", DEFAULT_TENANT_MGT_URL)
        logger.debug(f"Initialized tenant service client with URL: {self.base_url}")
    
    async def get_tenant_connection_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get connection information for a tenant.
        
        Args:
            tenant_id: The ID of the tenant.
            
        Returns:
            The tenant connection information or None if not found.
        """
        try:
            async with AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/tenant-connection",
                    headers={"X-Tenant-ID": tenant_id},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    return response.json()
                
                logger.error(
                    f"Failed to get tenant connection info for {tenant_id}: "
                    f"Status {response.status_code}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error getting tenant connection info: {str(e)}")
            return None
    
    async def get_tenant_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a tenant.
        
        Args:
            tenant_id: The ID of the tenant.
            
        Returns:
            The tenant information or None if not found.
        """
        try:
            async with AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/tenants/{tenant_id}",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    return response.json()
                
                logger.error(
                    f"Failed to get tenant info for {tenant_id}: "
                    f"Status {response.status_code}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error getting tenant info: {str(e)}")
            return None 