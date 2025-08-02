# Configuration Database (config_db)

## Overview

The Configuration Database (config_db) is a centralized MongoDB-based storage system for managing tenant-specific configuration settings within the PrismicX platform. It provides a flexible, scalable solution for storing, retrieving, and managing configurations across multiple tenants.

## Key Features

- **Multi-tenant configuration storage**: Store and manage configuration settings for each tenant separately
- **Schema validation**: Define and enforce JSON schemas for configuration values
- **User preferences**: Store and manage user-specific preferences
- **Batch processing**: Group tenants by feature and frequency for scheduled processing
- **Optimized querying**: Efficiently retrieve configurations for specific tenants or across all tenants

## Database Architecture

The Configuration Database uses MongoDB collections to organize different types of configuration data:

- **tenant_configs**: Stores tenant-specific configuration settings
- **config_schemas**: Defines schemas for configuration values
- **user_preferences**: Stores user-specific preferences
- **feature_frequency_groups**: Groups tenants by feature type and frequency for batch processing

### Indexing Strategy

The database uses optimized indexes for efficient queries:

- Compound index on `tenant_id` and `config_key` in the `tenant_configs` collection
- Index on `config_key` for prefix queries in the `tenant_configs` collection
- Unique index on `key` in the `config_schemas` collection
- Compound index on `user_id` and `feature_type` in the `user_preferences` collection
- Compound index on `feature_type`, `frequency`, and `time_key` in the `feature_frequency_groups` collection

## Data Models

### TenantConfig

Stores configuration settings for a specific tenant and configuration key:

```python
{
    "tenant_id": "tenant123",
    "config_key": "email_notifications",
    "config_value": {
        "enabled": true,
        "frequency": "daily"
    },
    "metadata": {
        "description": "Email notification preferences",
        "category": "notifications"
    },
    "created_at": "2023-06-15T10:30:00Z",
    "updated_at": "2023-06-15T10:30:00Z",
    "created_by": "admin",
    "updated_by": "admin"
}
```

### ConfigSchema

Defines the schema and constraints for a configuration key:

```python
{
    "key": "email_notifications",
    "schema": {
        "type": "object",
        "properties": {
            "enabled": {"type": "boolean"},
            "frequency": {
                "type": "string",
                "enum": ["daily", "weekly", "monthly"]
            }
        }
    },
    "metadata": {
        "description": "Email notification preferences",
        "category": "notifications"
    },
    "required": true,
    "default_value": {
        "enabled": false,
        "frequency": "weekly"
    }
}
```

### UserPreference

Stores user-specific preferences for a feature:

```python
{
    "user_id": "user123",
    "feature_type": "notifications",
    "preferences": {
        "email": true,
        "push": false,
        "sms": false
    },
    "created_at": "2023-06-15T10:30:00Z",
    "updated_at": "2023-06-15T10:30:00Z"
}
```

### FeatureFrequencyGroup

Groups tenants by feature and frequency for batch processing:

```python
{
    "feature_type": "reports",
    "frequency": "weekly",
    "time_key": "2023-W01",
    "tenant_ids": ["tenant1", "tenant2", "tenant3"]
}
```

## API Endpoints

The config_db exposes the following API endpoints:

### Tenant Configurations

- `GET /api/v1/tenants/{tenant_id}/configs/{config_key}` - Get configuration for a specific tenant
- `PUT /api/v1/tenants/{tenant_id}/configs/{config_key}` - Set configuration for a specific tenant
- `DELETE /api/v1/tenants/{tenant_id}/configs/{config_key}` - Delete configuration for a specific tenant
- `GET /api/v1/tenants/{tenant_id}/configs` - Get all configurations for a specific tenant
- `GET /api/v1/configs/{config_key}/all-tenants` - Get configuration for all tenants at once

### Configuration Schemas

- `GET /api/v1/schemas/{key}` - Get configuration schema for a specific key
- `PUT /api/v1/schemas/{key}` - Set configuration schema for a specific key
- `DELETE /api/v1/schemas/{key}` - Delete configuration schema for a specific key
- `GET /api/v1/schemas` - Get all configuration schemas

### User Preferences

- `GET /api/v1/users/{user_id}/preferences/{feature_type}` - Get user preferences for a specific feature
- `PUT /api/v1/users/{user_id}/preferences/{feature_type}` - Set user preferences for a specific feature
- `DELETE /api/v1/users/{user_id}/preferences/{feature_type}` - Delete user preferences for a specific feature
- `GET /api/v1/users/{user_id}/preferences` - Get all preferences for a specific user

### Feature Frequency Groups

- `GET /api/v1/feature-types` - Get all available feature types
- `GET /api/v1/features/{feature_type}/frequency-groups` - Get frequency groups for a specific feature
- `GET /api/v1/features/{feature_type}/frequency-groups/{frequency}/{time_key}/tenants` - Get tenants in a frequency group
- `PUT /api/v1/features/{feature_type}/frequency-groups/{frequency}/{time_key}` - Set a frequency group
- `POST /api/v1/features/{feature_type}/frequency-groups/{frequency}/{time_key}/tenants/{tenant_id}` - Add a tenant to a frequency group
- `DELETE /api/v1/features/{feature_type}/frequency-groups/{frequency}/{time_key}/tenants/{tenant_id}` - Remove a tenant from a frequency group
- `DELETE /api/v1/features/{feature_type}/frequency-groups/{frequency}/{time_key}` - Delete a frequency group

## Usage Examples

### Setting Tenant Configuration

```python
import requests
import json

# API endpoint
url = "http://management-system-repo:8080/api/v1/tenants/tenant123/configs/email_notifications"

# Configuration data
config_data = {
    "config_value": {
        "enabled": True,
        "frequency": "daily"
    },
    "metadata": {
        "description": "Email notification preferences",
        "updated_reason": "User preference change"
    }
}

# Set configuration
response = requests.put(url, json=config_data)
print(response.json())
```

### Getting Tenant Configuration

```python
import requests

# API endpoint
url = "http://management-system-repo:8080/api/v1/tenants/tenant123/configs/email_notifications"

# Get configuration
response = requests.get(url)
print(response.json())
```

### Setting Configuration Schema

```python
import requests
import json

# API endpoint
url = "http://management-system-repo:8080/api/v1/schemas/email_notifications"

# Schema data
schema_data = {
    "schema": {
        "type": "object",
        "properties": {
            "enabled": {"type": "boolean"},
            "frequency": {
                "type": "string",
                "enum": ["daily", "weekly", "monthly"]
            }
        }
    },
    "metadata": {
        "description": "Email notification preferences",
        "category": "notifications"
    },
    "required": True,
    "default_value": {
        "enabled": False,
        "frequency": "weekly"
    }
}

# Set schema
response = requests.put(url, json=schema_data)
print(response.json())
```

## Integration with Other Services

The Configuration Database integrates with other services within the PrismicX platform:

- **Management System Repository Service**: Hosts and manages the config_db
- **Tenant Management Service**: Uses tenant configurations for tenant-specific settings
- **User Data Service**: Accesses user preferences
- **Feature Services**: Access feature-specific configurations

## Setup and Configuration

The Configuration Database requires MongoDB and is configured through environment variables:

```yaml
CONFIG_DB_HOST: mongodb-system
CONFIG_DB_PORT: 27017
CONFIG_DB_USER: admin
CONFIG_DB_PASSWORD: password
CONFIG_DB_NAME: config_db
```

These environment variables can be set in the deployment configuration or through a `.env` file. 