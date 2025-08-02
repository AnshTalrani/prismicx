"""
Configuration service for managing tenant configurations.

This service provides a higher-level interface for accessing configuration data
using the ConfigDBClient to communicate with the database layer.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from functools import lru_cache

from ..clients.config_db_client import ConfigDBClient

logger = logging.getLogger(__name__)

class ConfigService:
    """Service for managing tenant configurations."""
    
    def __init__(self, config_db_client: ConfigDBClient):
        """
        Initialize the configuration service.
        
        Args:
            config_db_client: Client for interacting with the config_db
        """
        self.client = config_db_client
        logger.info("ConfigService initialized")
    
    async def get_tenant_config(
        self, 
        tenant_id: str, 
        config_key: str,
        default: Any = None
    ) -> Any:
        """
        Get configuration for a specific tenant with fallback to default.
        
        Args:
            tenant_id: Tenant ID
            config_key: Configuration key
            default: Default value if configuration is not found
            
        Returns:
            Configuration value or default if not found
        """
        result = await self.client.get_tenant_config(tenant_id, config_key)
        
        if result is None:
            return default
            
        return result.get("config_value", default)
    
    async def set_tenant_config(
        self,
        tenant_id: str,
        config_key: str,
        config_value: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Set configuration for a specific tenant.
        
        Args:
            tenant_id: Tenant ID
            config_key: Configuration key
            config_value: Configuration value
            metadata: Additional metadata
            user_id: User ID making the change
            
        Returns:
            True if successful, False otherwise
        """
        result = await self.client.set_tenant_config(
            tenant_id, config_key, config_value, metadata, user_id
        )
        
        return result is not None
    
    async def delete_tenant_config(self, tenant_id: str, config_key: str) -> bool:
        """
        Delete configuration for a specific tenant.
        
        Args:
            tenant_id: Tenant ID
            config_key: Configuration key
            
        Returns:
            True if deleted successfully, False otherwise
        """
        return await self.client.delete_tenant_config(tenant_id, config_key)
    
    async def get_tenant_configs(self, tenant_id: str, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all configurations for a specific tenant.
        
        Args:
            tenant_id: Tenant ID
            prefix: Optional prefix to filter configuration keys
            
        Returns:
            List of configurations
        """
        return await self.client.get_tenant_configs(tenant_id, prefix)
    
    async def get_config_for_all_tenants(self, config_key: str) -> List[Dict[str, Any]]:
        """
        Get configuration for all tenants.
        
        Args:
            config_key: Configuration key
            
        Returns:
            List of dictionaries containing tenant_id and config_value
        """
        tenant_configs = await self.client.get_config_for_all_tenants(config_key)
        
        # Convert the dictionary to a list format expected by existing code
        result = []
        for tenant_id, config_value in tenant_configs.items():
            result.append({
                "tenant_id": tenant_id,
                "config_value": config_value,
                "metadata": {}  # Metadata is not included in this API call
            })
        
        return result
    
    async def register_config_schema(
        self, 
        key: str, 
        schema: Dict[str, Any], 
        metadata: Dict[str, Any],
        required: bool,
        default_value: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Register a configuration schema.
        
        Args:
            key: Schema key
            schema: JSON schema for the configuration
            metadata: Additional metadata
            required: Whether this config is required
            default_value: Default value for the configuration
            
        Returns:
            True if successful, False otherwise
        """
        result = await self.client.set_config_schema(
            key, schema, metadata, required, default_value
        )
        
        return result is not None

@lru_cache()
def get_config_service() -> ConfigService:
    """
    Get a cached instance of the configuration service.
    
    Returns:
        ConfigService instance
    """
    base_url = os.getenv("MANAGEMENT_SYSTEM_REPO_URL", "http://management-system-repo:8080")
    api_key = os.getenv("MANAGEMENT_SYSTEM_REPO_API_KEY", "dev_api_key")
    
    config_db_client = ConfigDBClient(base_url, api_key)
    return ConfigService(config_db_client) 