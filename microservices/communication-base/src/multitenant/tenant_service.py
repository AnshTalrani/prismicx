"""
Tenant Service Module

This module provides a service for interacting with the tenant management service
to retrieve tenant information and metadata.
"""

import logging
import os
import json
from typing import Optional, Dict, Any, List
import httpx
from cachetools import TTLCache, cached

logger = logging.getLogger(__name__)

# Default TTL cache with 1000 items and 5-minute TTL
tenant_cache = TTLCache(maxsize=1000, ttl=300)


class TenantService:
    """
    Service for interacting with the tenant management service.
    
    This service provides methods to retrieve tenant information and metadata
    from the central tenant management service.
    """
    
    def __init__(self, base_url: Optional[str] = None, timeout: float = 5.0):
        """
        Initialize the tenant service.
        
        Args:
            base_url: Base URL of the tenant management service.
            timeout: Timeout for HTTP requests in seconds.
        """
        self.base_url = base_url or os.environ.get(
            "TENANT_MGMT_SERVICE_URL", 
            "http://tenant-mgmt-service:8000"
        )
        self.timeout = timeout
    
    async def get_tenant_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant information from the tenant management service.
        
        Args:
            tenant_id: The tenant ID to retrieve information for.
            
        Returns:
            Tenant information if found, None otherwise.
        """
        # Check cache first
        cached_info = self._get_cached_tenant_info(tenant_id)
        if cached_info:
            return cached_info
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/tenant-connection",
                    headers={"X-Tenant-ID": tenant_id}
                )
                
                if response.status_code == 200:
                    tenant_info = response.json()
                    # Cache the result
                    self._cache_tenant_info(tenant_id, tenant_info)
                    return tenant_info
                    
                if response.status_code == 404:
                    logger.warning(f"Tenant not found: {tenant_id}")
                    return None
                    
                logger.error(
                    f"Error from tenant service: {response.status_code} {response.text}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error connecting to tenant service: {str(e)}")
            return None
    
    async def list_tenants(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List tenants from the tenant management service.
        
        Args:
            limit: Maximum number of tenants to retrieve.
            offset: Offset for pagination.
            
        Returns:
            List of tenant information.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/tenants",
                    params={"limit": limit, "offset": offset}
                )
                
                if response.status_code == 200:
                    return response.json().get("items", [])
                    
                logger.error(
                    f"Error from tenant service: {response.status_code} {response.text}"
                )
                return []
                
        except Exception as e:
            logger.error(f"Error connecting to tenant service: {str(e)}")
            return []
    
    def _get_cached_tenant_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant information from cache.
        
        Args:
            tenant_id: The tenant ID to retrieve.
            
        Returns:
            Cached tenant information if found, None otherwise.
        """
        try:
            return tenant_cache.get(tenant_id)
        except Exception:
            return None
    
    def _cache_tenant_info(self, tenant_id: str, tenant_info: Dict[str, Any]) -> None:
        """
        Cache tenant information.
        
        Args:
            tenant_id: The tenant ID to cache.
            tenant_info: The tenant information to cache.
        """
        try:
            tenant_cache[tenant_id] = tenant_info
        except Exception as e:
            logger.warning(f"Failed to cache tenant info: {str(e)}")


# Singleton instance
_tenant_service: Optional[TenantService] = None


def get_tenant_service() -> TenantService:
    """
    Get the singleton tenant service instance.
    
    Returns:
        The tenant service instance.
    """
    global _tenant_service
    if _tenant_service is None:
        _tenant_service = TenantService()
    return _tenant_service 