"""
Configuration service plugin for managing tenant configurations.

This plugin acts as a client to the database-layer's management-system-repo service.
It coordinates configuration management while delegating actual database operations to the appropriate services.
"""

import logging
import os
from typing import Dict, Any, Optional, List
import httpx
from pathlib import Path
from datetime import datetime

from .base import PluginBase
from .interfaces.config_service_plugin import ConfigServicePlugin

logger = logging.getLogger(__name__)

class ConfigServicePlugin(PluginBase):
    """Plugin for managing tenant configurations using database-layer services."""
    
    def __init__(self, plugin_id: str = "config_service"):
        """Initialize the configuration service plugin."""
        super().__init__(plugin_id)
        self.management_system_repo_url = os.getenv(
            "MANAGEMENT_SYSTEM_REPO_URL", 
            "http://management-system-repo:8080"
        )
        self.management_system_repo_api_key = os.getenv(
            "MANAGEMENT_SYSTEM_REPO_API_KEY",
            "dev_api_key"
        )
        self.http_client = None
        
    async def initialize(self) -> None:
        """Initialize HTTP client for service communication."""
        try:
            self.http_client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
                headers={
                    "Authorization": f"Bearer {self.management_system_repo_api_key}",
                    "Content-Type": "application/json"
                }
            )
            logger.info("Configuration service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize configuration service: {str(e)}")
            raise
            
    async def start(self) -> None:
        """Start the configuration service."""
        logger.info("Configuration service started")
        
    async def stop(self) -> None:
        """Stop the configuration service and cleanup connections."""
        if self.http_client:
            await self.http_client.aclose()
        logger.info("Configuration service stopped")
        
    async def get_tenant_config(
        self,
        tenant_id: str,
        config_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get tenant-specific configuration using config service."""
        try:
            response = await self.http_client.get(
                f"{self.management_system_repo_url}/api/v1/tenants/{tenant_id}/configs/{config_key}"
            )
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            result = response.json()
            return result.get("config_value", {})
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
        user_id: str = None
    ) -> bool:
        """Set tenant-specific configuration using config service."""
        try:
            url = f"{self.management_system_repo_url}/api/v1/tenants/{tenant_id}/configs/{config_key}"
            if user_id:
                url += f"?user_id={user_id}"
                
            payload = {
                "config_value": config_value,
                "metadata": {}  # Can be extended with more metadata if needed
            }
            
            response = await self.http_client.put(url, json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error setting config {config_key} for tenant {tenant_id}: {str(e)}")
            return False
            
    async def get_tenant_configs(
        self,
        tenant_id: str
    ) -> List[Dict[str, Any]]:
        """Get all configurations for a tenant using config service."""
        try:
            response = await self.http_client.get(
                f"{self.management_system_repo_url}/api/v1/tenants/{tenant_id}/configs"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error retrieving configs for tenant {tenant_id}: {str(e)}")
            return []

    async def get_config_for_all_tenants(self, config_key: str) -> List[Dict[str, Any]]:
        """Get a specific configuration for all tenants."""
        try:
            response = await self.http_client.get(
                f"{self.management_system_repo_url}/api/v1/configs/{config_key}/all-tenants"
            )
            response.raise_for_status()
            
            # Convert the response to the expected format
            result = []
            tenant_configs = response.json()
            
            for tenant_id, config_value in tenant_configs.items():
                result.append({
                    "tenant_id": tenant_id,
                    "config_value": config_value,
                    "metadata": {}  # Metadata is not included in this API call
                })
            
            return result
        except Exception as e:
            logger.error(f"Error retrieving {config_key} configuration for all tenants: {str(e)}")
            return []
    
    async def register_config_schema(
        self, 
        key: str, 
        schema: Dict[str, Any], 
        metadata: Dict[str, Any],
        required: bool,
        default_value: Optional[Dict[str, Any]]
    ) -> bool:
        """Register a configuration schema."""
        try:
            payload = {
                "schema": schema,
                "metadata": metadata,
                "required": required,
                "default_value": default_value
            }
            
            response = await self.http_client.put(
                f"{self.management_system_repo_url}/api/v1/schemas/{key}",
                json=payload
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error registering config schema {key}: {str(e)}")
            return False 