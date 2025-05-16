from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

class ConfigServicePlugin(ABC):
    @abstractmethod
    async def get_tenant_configs(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get all configurations for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            List of configuration objects
        """
        pass
    
    @abstractmethod
    async def get_config_for_all_tenants(self, config_key: str) -> List[Dict[str, Any]]:
        """
        Get a specific configuration for all tenants.
        
        Args:
            config_key: Configuration key to retrieve
            
        Returns:
            List of dictionaries, each containing tenant_id and config_value
        """
        pass
    
    @abstractmethod
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
            key: Configuration key
            schema: JSON schema for the configuration
            metadata: Additional metadata
            required: Whether this config is required
            default_value: Default value for the configuration
            
        Returns:
            True if successful
        """
        pass 