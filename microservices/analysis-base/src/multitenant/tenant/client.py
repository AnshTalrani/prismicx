"""
Tenant Management Service Client

This module provides a client for interacting with the Tenant Management Service.
Used to validate tenants and retrieve tenant information.
"""

import os
import structlog
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Configure structured logging
logger = structlog.get_logger(__name__)

# Cache expiration time for tenant info (10 minutes)
TENANT_CACHE_EXPIRY = timedelta(minutes=10)

class TenantClient:
    """
    Client for the Tenant Management Service.
    
    Provides methods to validate tenants and retrieve tenant information.
    Includes caching to reduce load on the Tenant Management Service.
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the tenant client.
        
        Args:
            base_url: Tenant Management Service URL (default from environment)
            api_key: API key for authentication (default from environment)
        """
        self.base_url = base_url or os.environ.get(
            "TENANT_MGMT_URL", "http://tenant-mgmt-service:8501"
        )
        self.api_key = api_key or os.environ.get("TENANT_MGMT_API_KEY", "")
        
        # Request timeout in seconds
        self.timeout = float(os.environ.get("TENANT_MGMT_TIMEOUT", "5.0"))
        
        # Initialize tenant cache
        self.tenant_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        logger.info(
            "Initialized tenant client",
            base_url=self.base_url
        )
    
    async def get_tenant_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant information.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Tenant information or None if not found
        """
        # Check cache first
        if tenant_id in self.tenant_cache:
            cache_time = self.cache_timestamps.get(tenant_id)
            if cache_time and datetime.now() - cache_time < TENANT_CACHE_EXPIRY:
                logger.debug(
                    "Using cached tenant info",
                    tenant_id=tenant_id
                )
                return self.tenant_cache[tenant_id]
        
        # Cache miss or expired, fetch from service
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {}
                if self.api_key:
                    headers["x-api-key"] = self.api_key
                
                response = await client.get(
                    f"{self.base_url}/api/v1/tenants/{tenant_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    tenant_info = response.json()
                    # Update cache
                    self.tenant_cache[tenant_id] = tenant_info
                    self.cache_timestamps[tenant_id] = datetime.now()
                    return tenant_info
                elif response.status_code == 404:
                    logger.warning(
                        "Tenant not found",
                        tenant_id=tenant_id
                    )
                    return None
                else:
                    logger.error(
                        "Failed to get tenant info",
                        tenant_id=tenant_id,
                        status_code=response.status_code,
                        error=response.text
                    )
                    return None
        except Exception as e:
            logger.error(
                "Error contacting tenant management service",
                tenant_id=tenant_id,
                error=str(e)
            )
            return None
    
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
    
    async def list_tenants(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List available tenants.
        
        Args:
            limit: Maximum number of tenants to retrieve
            offset: Pagination offset
            
        Returns:
            List of tenant information dictionaries
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {}
                if self.api_key:
                    headers["x-api-key"] = self.api_key
                
                response = await client.get(
                    f"{self.base_url}/api/v1/tenants",
                    params={"limit": limit, "offset": offset},
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json().get("tenants", [])
                else:
                    logger.error(
                        "Failed to list tenants",
                        status_code=response.status_code,
                        error=response.text
                    )
                    return []
        except Exception as e:
            logger.error(
                "Error contacting tenant management service for tenant list",
                error=str(e)
            )
            return []
    
    def clear_cache(self, tenant_id: Optional[str] = None):
        """
        Clear the tenant info cache.
        
        Args:
            tenant_id: Specific tenant to clear from cache, or None for all
        """
        if tenant_id:
            if tenant_id in self.tenant_cache:
                del self.tenant_cache[tenant_id]
                del self.cache_timestamps[tenant_id]
        else:
            self.tenant_cache.clear()
            self.cache_timestamps.clear()

# Global tenant client instance
tenant_client = TenantClient() 