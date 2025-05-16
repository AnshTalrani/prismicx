"""
Tenant repository implementation.

This module provides an implementation of the tenant repository interface
that interacts with the tenant management service.
"""

import logging
import httpx
from typing import Dict, List, Optional, Any

from .tenant_repository import TenantRepository
from ...config.app_config import get_config

# Import the common database client
from database_layer.common.database_client import get_tenant_info, get_tenant_connection

logger = logging.getLogger(__name__)


class TenantRepositoryImpl(TenantRepository):
    """
    Implementation of the tenant repository interface.
    
    This implementation uses the common database client to interact with
    the tenant management service.
    """
    
    def __init__(self):
        """Initialize the tenant repository implementation."""
        self.config = get_config()
        self.tenant_mgmt_url = self.config.tenant_management_url
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 300  # Cache TTL in seconds
        
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a tenant by ID.
        
        Args:
            tenant_id: The ID of the tenant.
            
        Returns:
            The tenant information, or None if not found.
        """
        # Check cache first
        if tenant_id in self.cache:
            logger.debug(f"Tenant {tenant_id} found in cache")
            return self.cache[tenant_id]
        
        try:
            # Use the common database client to get tenant info
            tenant_info = await get_tenant_info(tenant_id)
            
            if tenant_info:
                # Cache the result
                self.cache[tenant_id] = tenant_info
                logger.debug(f"Tenant {tenant_id} retrieved from tenant management service")
                return tenant_info
            else:
                logger.warning(f"Tenant {tenant_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error getting tenant {tenant_id}: {str(e)}")
            return None
    
    async def get_all_tenants(self) -> List[Dict[str, Any]]:
        """
        Get all tenants.
        
        Returns:
            A list of all tenants.
        """
        try:
            # Direct API call to tenant management service
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.tenant_mgmt_url}/api/v1/tenants")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting all tenants: {str(e)}")
            return []
    
    async def get_tenant_schema(self, tenant_id: str) -> Optional[str]:
        """
        Get the database schema name for a tenant.
        
        Args:
            tenant_id: The ID of the tenant.
            
        Returns:
            The schema name, or None if the tenant does not exist.
        """
        tenant = await self.get_tenant_by_id(tenant_id)
        if tenant and "schema_name" in tenant:
            return tenant["schema_name"]
        return None
            
    async def get_tenant_connection(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get database connection information for a tenant.
        
        Args:
            tenant_id: The ID of the tenant.
            
        Returns:
            Database connection information, or None if the tenant does not exist.
        """
        try:
            # Use the common database client to get connection info
            connection_info = await get_tenant_connection(tenant_id)
            return connection_info
        except Exception as e:
            logger.error(f"Error getting connection for tenant {tenant_id}: {str(e)}")
            return None 