# Cross-Tenant Configuration API

This document provides detailed information about the cross-tenant configuration API endpoint, which allows administrators to access a specific configuration across all tenants.

## Overview

The cross-tenant configuration API provides a way to retrieve a specific configuration key for all tenants in the system. This is an administrative operation that requires elevated privileges.

## API Endpoint

**Endpoint:** `/config/configs/{config_key}/all-tenants`  
**Method:** GET  
**Auth Required:** Yes (Admin only)  

## Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| config_key | string | The configuration key to retrieve across all tenants |

## Request Headers

| Header | Description |
|--------|-------------|
| Authorization | Bearer token with admin privileges |

## Response

**Status Code:** 200 OK

```json
[
  {
    "tenant_id": "tenant1",
    "config_key": "email_notifications",
    "config_value": {
      "enabled": true,
      "frequency": "daily"
    },
    "metadata": {
      "description": "Email notification preferences"
    }
  },
  {
    "tenant_id": "tenant2",
    "config_key": "email_notifications",
    "config_value": {
      "enabled": false,
      "frequency": "weekly"
    },
    "metadata": {
      "description": "Email notification preferences"
    }
  }
]
```

## Error Responses

| Status Code | Description |
|-------------|-------------|
| 401 Unauthorized | Authentication token is missing or invalid |
| 403 Forbidden | User does not have admin privileges |
| 404 Not Found | Configuration key not found |
| 503 Service Unavailable | Configuration service unavailable |

## Code Samples

### cURL

```bash
curl -X GET \
  "http://management-systems:8000/config/configs/email_notifications/all-tenants" \
  -H "Authorization: Bearer admin_token_here"
```

### Python

```python
import httpx
import os
from typing import List, Dict, Any, Optional

async def get_config_for_all_tenants(
    config_key: str,
    admin_token: str
) -> List[Dict[str, Any]]:
    """
    Retrieve a specific configuration for all tenants.
    
    Args:
        config_key: The configuration key to retrieve
        admin_token: Admin authentication token
        
    Returns:
        List of configuration objects with tenant IDs
    """
    base_url = os.getenv("MANAGEMENT_SYSTEMS_URL", "http://management-systems:8000")
    url = f"{base_url}/config/configs/{config_key}/all-tenants"
    
    headers = {
        "Authorization": f"Bearer {admin_token}"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            print(f"Error: {str(e)}")
            return []
```

### JavaScript/TypeScript

```typescript
interface ConfigResponse {
  tenant_id: string;
  config_key: string;
  config_value: Record<string, any>;
  metadata: Record<string, any>;
}

async function getConfigForAllTenants(
  configKey: string,
  adminToken: string
): Promise<ConfigResponse[]> {
  const baseUrl = process.env.MANAGEMENT_SYSTEMS_URL || "http://management-systems:8000";
  const url = `${baseUrl}/config/configs/${configKey}/all-tenants`;
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${adminToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching cross-tenant config:', error);
    return [];
  }
}
```

## Use Cases

### 1. Administrative Dashboards

Build admin dashboards showing configuration adoption across tenants:

```python
async def configuration_adoption_dashboard(admin_token):
    # Get configurations across all tenants
    email_configs = await get_config_for_all_tenants("email_notifications", admin_token)
    
    # Calculate adoption metrics
    total_tenants = len(email_configs)
    enabled_count = sum(1 for config in email_configs 
                        if config.get("config_value", {}).get("enabled", False))
    
    adoption_rate = (enabled_count / total_tenants) * 100 if total_tenants > 0 else 0
    
    return {
        "total_tenants": total_tenants,
        "enabled_count": enabled_count,
        "adoption_rate": f"{adoption_rate:.1f}%",
        "tenant_details": email_configs
    }
```

### 2. Batch Configuration Updates

Identify tenants that need configuration updates:

```python
async def identify_tenants_for_update(admin_token):
    # Get feature flag settings for all tenants
    feature_flags = await get_config_for_all_tenants("feature_flags", admin_token)
    
    # Identify tenants with old flag values
    tenants_needing_update = []
    
    for config in feature_flags:
        tenant_id = config.get("tenant_id")
        flag_value = config.get("config_value", {}).get("new_feature_enabled")
        
        if flag_value is not True:
            tenants_needing_update.append(tenant_id)
    
    return tenants_needing_update
```

### 3. Configuration Compliance Checking

Verify that tenant configurations comply with required settings:

```python
async def check_configuration_compliance(admin_token):
    # Get security settings for all tenants
    security_configs = await get_config_for_all_tenants("security_settings", admin_token)
    
    # Check compliance
    compliance_issues = []
    
    for config in security_configs:
        tenant_id = config.get("tenant_id")
        settings = config.get("config_value", {})
        
        # Check required security settings
        if not settings.get("two_factor_required", False):
            compliance_issues.append({
                "tenant_id": tenant_id,
                "issue": "Two-factor authentication not required",
                "severity": "high"
            })
        
        if settings.get("password_expiry_days", 90) > 90:
            compliance_issues.append({
                "tenant_id": tenant_id,
                "issue": "Password expiry exceeds 90 days",
                "severity": "medium"
            })
    
    return compliance_issues
```

## Implementation Details

The cross-tenant configuration API is implemented in the `ConfigServicePlugin` class:

```python
async def get_config_for_all_tenants(self, config_key: str) -> List[Dict[str, Any]]:
    """Get a specific configuration for all tenants."""
    try:
        # Look for this config key across all tenants
        cursor = db_client.config_db.tenant_configs.find({"config_key": config_key})
        configs = await cursor.to_list(length=None)
        
        # Format the results to include just tenant_id and config_value
        result = []
        for config in configs:
            result.append({
                "tenant_id": config["tenant_id"],
                "config_value": config.get("config_value", {}),
                "metadata": config.get("metadata", {})
            })
        
        return result
    except Exception as e:
        logger.error(f"Error retrieving {config_key} configuration for all tenants: {str(e)}")
        return []
```

## Security Considerations

- This endpoint should only be accessible to users with administrative privileges
- The endpoint performs authorization checks before processing the request
- Access to this endpoint should be monitored and logged
- Consider rate limiting to prevent abuse

## Performance Considerations

- This endpoint queries across all tenants, which can be resource-intensive
- For systems with many tenants, consider pagination or streaming responses
- Caching results may be appropriate for frequently accessed configurations
- Avoid repeatedly calling this endpoint; cache results when appropriate 