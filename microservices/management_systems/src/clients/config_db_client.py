"""
Configuration database client for interacting with the config_db in the database layer.

This client provides methods for accessing the configuration database API exposed
by the management-system-repo service in the database layer.
"""

import logging
import os
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigDBClient:
    """Client for interacting with the config_db in the database layer."""
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the config DB client.
        
        Args:
            base_url: Base URL for the management-system-repo service
            api_key: API key for authentication
        """
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.http_client = None
    
    async def initialize(self):
        """Initialize the HTTP client for making API requests."""
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            headers=self.headers
        )
        logger.info(f"ConfigDBClient initialized with base URL: {self.base_url}")
    
    async def close(self):
        """Close the HTTP client."""
        if self.http_client:
            await self.http_client.aclose()
            logger.info("ConfigDBClient HTTP client closed")
    
    async def get_tenant_config(self, tenant_id: str, config_key: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific tenant.
        
        Args:
            tenant_id: Tenant ID
            config_key: Configuration key
            
        Returns:
            Configuration value or None if not found
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/tenants/{tenant_id}/configs/{config_key}"
            response = await self.http_client.get(url)
            
            if response.status_code == 404:
                logger.debug(f"Config {config_key} not found for tenant {tenant_id}")
                return None
                
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error retrieving config {config_key} for tenant {tenant_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving config {config_key} for tenant {tenant_id}: {str(e)}")
            return None
    
    async def set_tenant_config(
        self,
        tenant_id: str,
        config_key: str,
        config_value: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Set configuration for a specific tenant.
        
        Args:
            tenant_id: Tenant ID
            config_key: Configuration key
            config_value: Configuration value
            metadata: Additional metadata
            user_id: User ID making the change
            
        Returns:
            Updated configuration or None if failed
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/tenants/{tenant_id}/configs/{config_key}"
            
            if user_id:
                url += f"?user_id={user_id}"
            
            payload = {
                "config_value": config_value,
                "metadata": metadata or {}
            }
            
            response = await self.http_client.put(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error setting config {config_key} for tenant {tenant_id}: {str(e)}")
            return None
    
    async def delete_tenant_config(self, tenant_id: str, config_key: str) -> bool:
        """
        Delete configuration for a specific tenant.
        
        Args:
            tenant_id: Tenant ID
            config_key: Configuration key
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/tenants/{tenant_id}/configs/{config_key}"
            response = await self.http_client.delete(url)
            
            if response.status_code == 404:
                logger.debug(f"Config {config_key} not found for tenant {tenant_id}")
                return False
                
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error deleting config {config_key} for tenant {tenant_id}: {str(e)}")
            return False
    
    async def get_tenant_configs(self, tenant_id: str, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all configurations for a specific tenant.
        
        Args:
            tenant_id: Tenant ID
            prefix: Optional prefix to filter configuration keys
            
        Returns:
            List of configurations
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/tenants/{tenant_id}/configs"
            
            if prefix:
                url += f"?prefix={prefix}"
                
            response = await self.http_client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error retrieving configs for tenant {tenant_id}: {str(e)}")
            return []
    
    async def get_config_for_all_tenants(self, config_key: str) -> Dict[str, Dict[str, Any]]:
        """
        Get configuration for all tenants at once.
        
        Args:
            config_key: Configuration key
            
        Returns:
            Dictionary mapping tenant IDs to their configuration values
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/configs/{config_key}/all-tenants"
            response = await self.http_client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error retrieving config {config_key} for all tenants: {str(e)}")
            return {}
    
    async def get_config_schema(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration schema for a specific key.
        
        Args:
            key: Schema key
            
        Returns:
            Configuration schema or None if not found
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/schemas/{key}"
            response = await self.http_client.get(url)
            
            if response.status_code == 404:
                logger.debug(f"Schema for key {key} not found")
                return None
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error retrieving schema for key {key}: {str(e)}")
            return None
    
    async def set_config_schema(
        self,
        key: str,
        schema: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        required: bool = False,
        default_value: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Set or update configuration schema.
        
        Args:
            key: Schema key
            schema: JSON schema for the configuration
            metadata: Additional metadata
            required: Whether this config is required
            default_value: Default value for the configuration
            
        Returns:
            Updated schema or None if failed
        """
        if not self.http_client:
            await self.initialize()
            
        try:
            url = f"{self.base_url}/api/v1/schemas/{key}"
            
            payload = {
                "schema": schema,
                "metadata": metadata or {},
                "required": required
            }
            
            if default_value is not None:
                payload["default_value"] = default_value
                
            response = await self.http_client.put(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error setting schema for key {key}: {str(e)}")
            return None 