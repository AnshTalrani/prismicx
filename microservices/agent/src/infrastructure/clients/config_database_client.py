"""
Client for interacting with the configuration database service in the database layer.

This client makes API calls to the management-system-repo service to access
configuration data stored in the config_db MongoDB database.
"""

import httpx
import os
import logging
import json
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ConfigDatabaseClient:
    """Client for the configuration database service."""
    
    def __init__(self, base_url=None, timeout=10.0, api_key=None):
        """
        Initialize the config database client.
        
        Args:
            base_url: Base URL of the management-system-repo service
            timeout: Request timeout in seconds
            api_key: Optional API key for authentication
        """
        # Update to point to management-system-repo service
        self.base_url = base_url or os.getenv("CONFIG_DB_URL", "http://management-system-repo:8080")
        self.timeout = timeout
        self.api_key = api_key or os.getenv("CONFIG_DB_API_KEY", "dev_api_key")
        self.http_client = httpx.AsyncClient(timeout=self.timeout)
        logger.info(f"ConfigDatabaseClient initialized with URL: {self.base_url}")
        
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
        
    def _get_headers(self):
        """Get request headers with authentication."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        return headers
        
    async def get_config_for_all_tenants(self, config_key: str) -> Dict[str, Any]:
        """
        Get configuration for all tenants at once.
        
        This optimized method returns a mapping of tenant_id -> config_value
        for all tenants that have the requested configuration key.
        
        Args:
            config_key: Configuration key
            
        Returns:
            Dictionary mapping tenant_id -> config_value
        """
        try:
            url = f"{self.base_url}/api/v1/configs/{config_key}/all-tenants"
            response = await self.http_client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error retrieving config for all tenants, key {config_key}: {str(e)}")
            return {}
    
    async def get_tenant_config(self, tenant_id: str, config_key: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific tenant.
        
        Args:
            tenant_id: Tenant ID
            config_key: Configuration key
            
        Returns:
            Configuration for the tenant
        """
        try:
            url = f"{self.base_url}/api/v1/tenants/{tenant_id}/configs/{config_key}"
            response = await self.http_client.get(url, headers=self._get_headers())
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error retrieving config: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving config for tenant {tenant_id}, key {config_key}: {str(e)}")
            return None
            
    async def set_tenant_config(self, tenant_id: str, config_key: str, config_value: Dict[str, Any]) -> bool:
        """
        Set configuration for a specific tenant.
        
        Args:
            tenant_id: Tenant ID
            config_key: Configuration key
            config_value: Configuration value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/api/v1/tenants/{tenant_id}/configs/{config_key}"
            response = await self.http_client.put(
                url, 
                headers=self._get_headers(),
                json=config_value
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error setting config for tenant {tenant_id}, key {config_key}: {str(e)}")
            return False
            
    async def get_feature_types(self) -> List[str]:
        """
        Get all available feature types.
        
        Returns:
            List of feature types
        """
        try:
            url = f"{self.base_url}/api/v1/feature-types"
            response = await self.http_client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error retrieving feature types: {str(e)}")
            return []
    
    async def get_frequency_groups(self, feature_type: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get frequency groups for a specific feature type.
        
        Args:
            feature_type: Feature type
            
        Returns:
            Dictionary mapping frequency groups to user lists
        """
        try:
            url = f"{self.base_url}/api/v1/features/{feature_type}/frequency-groups"
            response = await self.http_client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error retrieving frequency groups for {feature_type}: {str(e)}")
            return {}
    
    async def get_frequency_group_users(
        self, 
        feature_type: str, 
        frequency: str, 
        time_key: str
    ) -> List[Dict[str, Any]]:
        """
        Get users for a specific frequency group.
        
        Args:
            feature_type: Feature type
            frequency: Frequency (daily, weekly, monthly)
            time_key: Time key
            
        Returns:
            List of users with their preferences
        """
        try:
            url = f"{self.base_url}/api/v1/features/{feature_type}/frequency-groups/{frequency}/{time_key}/users"
            response = await self.http_client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error retrieving users for {feature_type} {frequency}:{time_key}: {str(e)}")
            return []
    
    async def get_user_preferences(self, user_id: str, feature_type: str) -> Optional[Dict[str, Any]]:
        """
        Get user preferences for a specific feature type.
        
        Args:
            user_id: User ID
            feature_type: Feature type
            
        Returns:
            User preferences
        """
        try:
            url = f"{self.base_url}/api/v1/users/{user_id}/preferences/{feature_type}"
            response = await self.http_client.get(url, headers=self._get_headers())
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error retrieving user preferences: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving preferences for user {user_id}, feature {feature_type}: {str(e)}")
            return None
    
    async def get_user_tenant(self, user_id: str) -> Optional[str]:
        """
        Get the tenant ID for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Tenant ID
        """
        try:
            url = f"{self.base_url}/api/v1/users/{user_id}/tenant"
            response = await self.http_client.get(url, headers=self._get_headers())
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            result = response.json()
            return result.get("tenant_id")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error retrieving user tenant: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving tenant for user {user_id}: {str(e)}")
            return None 