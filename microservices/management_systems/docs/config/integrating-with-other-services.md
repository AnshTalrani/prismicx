# Integrating with Other Microservices

This document provides guidance on how other microservices can integrate with the Management Systems configuration API.

## Overview

The Management Systems microservice provides a centralized configuration management system that can be used by other microservices to store and retrieve tenant-specific settings. By integrating with this system, other services can:

1. Store service-specific configuration in a consistent way
2. Retrieve tenant-specific settings
3. Take advantage of schema validation and caching
4. Access cross-tenant configuration data (with admin privileges)

## Integration Methods

### 1. HTTP Client Integration (Recommended)

The most common and recommended approach is to use an HTTP client to interact with the Management Systems API:

```python
# management_systems_client.py
import os
import logging
import httpx
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ManagementSystemsClient:
    """Client for interacting with Management Systems microservice."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        timeout: float = 10.0
    ):
        """Initialize the client."""
        self.base_url = base_url or os.getenv("MANAGEMENT_SYSTEMS_URL", "http://management-systems:8000")
        self.auth_token = auth_token
        self.timeout = timeout
        self.http_client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
    
    def _get_headers(self, tenant_id: Optional[str] = None):
        """Get request headers with authentication and optional tenant ID."""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        if tenant_id:
            headers["X-Tenant-ID"] = tenant_id
            
        return headers
    
    async def get_tenant_config(
        self,
        tenant_id: str,
        config_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get tenant-specific configuration.
        
        Args:
            tenant_id: Tenant identifier
            config_key: Configuration key
            
        Returns:
            Configuration value or None if not found
        """
        url = f"{self.base_url}/config/tenants/{tenant_id}/configs/{config_key}"
        headers = self._get_headers(tenant_id)
        
        try:
            response = await self.http_client.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get("config_value")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Config {config_key} not found for tenant {tenant_id}")
                return None
            logger.error(f"HTTP error retrieving config {config_key} for tenant {tenant_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving config {config_key} for tenant {tenant_id}: {str(e)}")
            return None
    
    async def set_tenant_config(
        self,
        tenant_id: str,
        config_key: str,
        config_value: Dict[str, Any]
    ) -> bool:
        """
        Set tenant-specific configuration.
        
        Args:
            tenant_id: Tenant identifier
            config_key: Configuration key
            config_value: Configuration value
            
        Returns:
            True if successful
        """
        url = f"{self.base_url}/config/tenants/{tenant_id}/configs/{config_key}"
        headers = self._get_headers(tenant_id)
        
        try:
            response = await self.http_client.put(
                url,
                headers=headers,
                json={"config_value": config_value}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error setting config {config_key} for tenant {tenant_id}: {str(e)}")
            return False
    
    async def get_config_for_all_tenants(
        self,
        config_key: str
    ) -> List[Dict[str, Any]]:
        """
        Get configuration for all tenants (admin only).
        
        Args:
            config_key: Configuration key
            
        Returns:
            List of configurations with tenant IDs
        """
        url = f"{self.base_url}/config/configs/{config_key}/all-tenants"
        headers = self._get_headers()
        
        try:
            response = await self.http_client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error retrieving config {config_key} for all tenants: {str(e)}")
            return []
```

### 2. Using the Client in Your Service

```python
# Example usage in another microservice
from management_systems_client import ManagementSystemsClient

async def initialize_service():
    # Create a client instance
    client = ManagementSystemsClient()
    
    try:
        # Get configuration values for specific tenant
        tenant_id = "tenant123"
        email_config = await client.get_tenant_config(tenant_id, "email_notifications")
        
        if email_config and email_config.get("enabled"):
            # Configure email service based on settings
            frequency = email_config.get("frequency", "daily")
            print(f"Email notifications enabled with frequency: {frequency}")
        else:
            print("Email notifications disabled")
        
        # Only for admin-level services:
        if is_admin_service():
            # Get configuration across all tenants
            all_configs = await client.get_config_for_all_tenants("feature_flags")
            
            # Count tenants with new UI enabled
            new_ui_enabled_count = sum(
                1 for config in all_configs 
                if config.get("config_value", {}).get("new_ui_enabled", False)
            )
            
            print(f"New UI enabled for {new_ui_enabled_count} tenants")
    finally:
        # Always close the client when done
        await client.close()
```

## Configuration Naming Conventions

When creating configuration keys for your microservice, follow these conventions:

1. **Prefix with Service Name**: Use your service name as a prefix, e.g., `user-service.email_settings`
2. **Use Namespaces**: Group related configurations under a common namespace
3. **Follow JSON Schema**: Define a JSON schema for your configuration structure

Example:

```python
# Define a configuration schema for your service
schema = {
    "key": "reporting-service.export_settings",
    "schema": {
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "enum": ["csv", "pdf", "excel"]
            },
            "include_headers": {"type": "boolean"},
            "max_rows": {"type": "integer", "minimum": 100, "maximum": 10000}
        },
        "required": ["format"]
    },
    "metadata": {
        "description": "Report export settings",
        "category": "reporting"
    },
    "required": false,
    "default_value": {
        "format": "csv",
        "include_headers": true,
        "max_rows": 1000
    }
}

# Register the schema
async def register_schema():
    client = ManagementSystemsClient(auth_token=admin_token)
    try:
        await client.register_config_schema(
            schema["key"],
            schema["schema"],
            schema["metadata"],
            schema["required"],
            schema["default_value"]
        )
    finally:
        await client.close()
```

## Best Practices for Integration

1. **Create a Dedicated Client**: Implement a client class specifically for integration
2. **Handle Connection Failures**: Implement proper error handling and retries
3. **Use Caching**: Cache configuration values to reduce API calls
4. **Respect Tenant Context**: Always include tenant context in API requests
5. **Validate Input**: Ensure data sent to the API meets schema requirements
6. **Close HTTP Clients**: Always close HTTP clients when done
7. **Follow Naming Conventions**: Use consistent naming for configuration keys
8. **Document Configuration Keys**: Document your service's configuration keys

## Example: Full Integration Pattern

Here's a complete example of how to integrate the Management Systems configuration with another service:

```python
# In your service's core module
from management_systems_client import ManagementSystemsClient
from functools import lru_cache
import os

# Singleton client
_client = None

async def get_client():
    """Get or create the Management Systems client."""
    global _client
    if _client is None:
        auth_token = os.getenv("MANAGEMENT_SYSTEMS_TOKEN")
        _client = ManagementSystemsClient(auth_token=auth_token)
    return _client

@lru_cache(maxsize=100)
async def get_cached_config(tenant_id, config_key):
    """
    Get cached configuration value.
    
    This function caches results in memory to reduce API calls.
    """
    client = await get_client()
    return await client.get_tenant_config(tenant_id, config_key)

async def shutdown():
    """Close the client during application shutdown."""
    global _client
    if _client:
        await _client.close()
        _client = None
```

## Cross-Service Configuration Access

The `/config/configs/{config_key}/all-tenants` endpoint is particularly useful for:

1. **Analytics Services**: Analyze configuration patterns across tenants
2. **Reporting Services**: Generate reports on tenant configurations
3. **Admin Dashboards**: Provide visibility into tenant settings
4. **Global Updates**: Identify tenants needing configuration updates

Example: Generating a tenant configuration report:

```python
async def generate_config_adoption_report(config_key):
    """Generate a report on configuration adoption across tenants."""
    client = await get_client()
    configs = await client.get_config_for_all_tenants(config_key)
    
    # Process configurations to generate report
    total_tenants = len(configs)
    configured_tenants = sum(1 for config in configs if config.get("config_value"))
    
    return {
        "config_key": config_key,
        "total_tenants": total_tenants,
        "configured_tenants": configured_tenants,
        "adoption_rate": configured_tenants / total_tenants if total_tenants > 0 else 0,
        "details": configs
    }
``` 