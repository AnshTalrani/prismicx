# Tenant Configuration Management

This document explains how tenant configurations are structured, stored, and accessed in the Management Systems microservice.

## Overview

The tenant configuration management system provides a flexible way to store and retrieve tenant-specific configuration settings. Configurations are organized by tenant and configuration key, with JSON schema validation to ensure data integrity.

## Configuration Storage

Tenant configurations are stored in the following locations:

### 1. MongoDB Config Database

The primary storage for tenant configurations is in the MongoDB configuration database:

- **Collection:** `tenant_configs`
- **Connection:** Accessed via `db_client.config_db`
- **Schema:** Defined by the `TenantConfig` model

### 2. Redis Cache

For performance optimization, configurations are cached in Redis:

- **Cache Keys:** `tenant:{tenant_id}:config:{config_key}`
- **TTL:** Typically 300 seconds (5 minutes)
- **Invalidation:** Cache entries are cleared on configuration updates

## Data Model

### TenantConfig Model

```python
class TenantConfig(BaseModel):
    """Configuration model for tenant-specific settings."""
    
    tenant_id: str
    config_key: str
    config_value: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
```

### ConfigSchema Model

```python
class ConfigSchema(BaseModel):
    """Schema definition for configuration keys."""
    
    key: str
    schema: Dict[str, Any]
    metadata: Dict[str, Any]
    required: bool
    default_value: Optional[Dict[str, Any]]
```

## Example Configuration

A typical tenant configuration document would look like:

```json
{
  "tenant_id": "tenant123",
  "config_key": "email_notifications",
  "config_value": {
    "enabled": true,
    "frequency": "daily",
    "recipients": ["admin@example.com"]
  },
  "metadata": {
    "description": "Email notification preferences",
    "category": "notifications"
  },
  "created_at": "2023-10-01T12:00:00Z",
  "updated_at": "2023-10-15T09:30:00Z",
  "created_by": "system",
  "updated_by": "admin"
}
```

## Configuration Keys

Configuration keys are organized into categories. Common configuration keys include:

| Config Key | Purpose | Example Value |
|------------|---------|--------------|
| `email_notifications` | Email notification settings | `{"enabled": true, "frequency": "daily"}` |
| `system_preferences` | UI and system preferences | `{"theme": "dark", "language": "en-US"}` |
| `integration_settings` | External integration settings | `{"api_key": "xxx", "endpoint": "https://api.example.com"}` |
| `workflow_config` | Workflow automation settings | `{"auto_approval": true, "stages": ["draft", "review", "approved"]}` |

## Accessing Configurations

### 1. Using the API

Configurations can be accessed through the REST API as documented in the [Configuration API](../api/configuration.md) documentation.

### 2. Using the Configuration Service

Services within the microservice can use the `ConfigServicePlugin`:

```python
from ..plugins.plugin_manager import get_plugin_manager

async def get_tenant_config(tenant_id, config_key):
    plugin_manager = get_plugin_manager()
    config_service = plugin_manager.get_plugin("config_service")
    
    if config_service:
        return await config_service.get_tenant_config(tenant_id, config_key)
    return None
```

### 3. Direct Database Access (Not Recommended)

In rare cases, direct database access may be used:

```python
from ..common.db_client_wrapper import db_client

async def get_config_directly(tenant_id, config_key):
    config = await db_client.config_db.tenant_configs.find_one({
        "tenant_id": tenant_id,
        "config_key": config_key
    })
    
    if config:
        return config.get("config_value", {})
    return {}
```

## Cross-Tenant Configuration Access

The `/config/configs/{config_key}/all-tenants` endpoint provides access to a specific configuration across all tenants. This is useful for:

1. Administrative dashboards
2. Cross-tenant reporting and analytics
3. System-wide configuration management

Example response structure:

```json
[
  {
    "tenant_id": "tenant1",
    "config_key": "feature_flags",
    "config_value": {
      "new_ui_enabled": true
    },
    "metadata": {}
  },
  {
    "tenant_id": "tenant2",
    "config_key": "feature_flags",
    "config_value": {
      "new_ui_enabled": false
    },
    "metadata": {}
  }
]
```

## Schema Validation

Configuration values are validated against JSON schemas defined in the `config_schemas` collection. This ensures that configurations adhere to expected formats and constraints.

### Example Schema:

```json
{
  "key": "email_notifications",
  "schema": {
    "type": "object",
    "properties": {
      "enabled": {"type": "boolean"},
      "frequency": {
        "type": "string", 
        "enum": ["daily", "weekly", "monthly"]
      },
      "recipients": {
        "type": "array",
        "items": {"type": "string", "format": "email"}
      }
    },
    "required": ["enabled", "frequency"]
  },
  "metadata": {
    "description": "Email notification preferences",
    "category": "notifications"
  },
  "required": true,
  "default_value": {
    "enabled": false,
    "frequency": "weekly",
    "recipients": []
  }
}
```

## Best Practices

1. **Use Configuration Service**: Always use the configuration service instead of direct database access.
2. **Cache Appropriately**: Use Redis cache for frequently accessed configuration values.
3. **Follow Schema Definitions**: Ensure new configurations have appropriate schema definitions.
4. **Validate Before Storing**: Always validate configuration values against their schemas.
5. **Centralize Common Settings**: Keep related settings together under a single configuration key.
6. **Document Keys**: Maintain documentation of configuration keys and their purpose.
7. **Respect Tenant Boundaries**: Ensure cross-tenant access is restricted to administrative users. 