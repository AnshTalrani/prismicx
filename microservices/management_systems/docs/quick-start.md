# Quick Start Guide

This guide provides a quick introduction to working with the Management Systems microservice, with a focus on the tenant configuration system.

## Prerequisites

- Docker and Docker Compose
- Access to the necessary environment variables
- Authentication credentials

## Running the Service

1. Clone the repository and navigate to the management_systems directory:

```bash
cd microservices/management_systems
```

2. Create a `.env` file based on the `.env.example`:

```bash
cp .env.example .env
```

3. Edit the `.env` file with appropriate values for your environment.

4. Start the service using Docker Compose:

```bash
docker-compose up -d
```

5. Verify the service is running:

```bash
curl http://localhost:8000/health
```

## Working with Tenant Configurations

### 1. Retrieving a Tenant Configuration

```bash
# Get a specific tenant configuration
curl -X GET \
  "http://localhost:8000/config/tenants/tenant123/configs/email_notifications" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Example response:
```json
{
  "tenant_id": "tenant123",
  "config_key": "email_notifications",
  "config_value": {
    "enabled": true,
    "frequency": "daily"
  },
  "metadata": {
    "description": "Email notification preferences"
  }
}
```

### 2. Updating a Tenant Configuration

```bash
# Update a tenant configuration
curl -X PUT \
  "http://localhost:8000/config/tenants/tenant123/configs/email_notifications" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"config_value": {"enabled": true, "frequency": "weekly"}}'
```

### 3. Listing All Configurations for a Tenant

```bash
# List all configurations for a tenant
curl -X GET \
  "http://localhost:8000/config/tenants/tenant123/configs" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Getting a Configuration for All Tenants (Admin Only)

```bash
# Get a configuration for all tenants (admin only)
curl -X GET \
  "http://localhost:8000/config/configs/email_notifications/all-tenants" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## Using Python

### 1. Basic Client Usage

```python
import httpx
import asyncio

async def get_tenant_config(tenant_id, config_key, token):
    url = f"http://localhost:8000/config/tenants/{tenant_id}/configs/{config_key}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None

# Example usage
async def main():
    token = "your_auth_token"
    config = await get_tenant_config("tenant123", "email_notifications", token)
    print(config)

asyncio.run(main())
```

### 2. Using the Configuration Service Within the Microservice

If you're developing within the Management Systems microservice:

```python
from ..plugins.plugin_manager import get_plugin_manager

async def get_config(tenant_id, config_key):
    plugin_manager = get_plugin_manager()
    config_service = plugin_manager.get_plugin("config_service")
    
    if config_service:
        return await config_service.get_tenant_config(tenant_id, config_key)
    return None
```

## Common Configuration Keys

Here are some common configuration keys you might use:

| Config Key | Purpose |
|------------|---------|
| `email_notifications` | Email notification settings |
| `system_preferences` | UI and system preferences |
| `integration_settings` | External integration settings |
| `feature_flags` | Toggle features on/off |
| `workflow_config` | Workflow configuration |

## Next Steps

For more detailed information:

- [API Documentation](./api/README.md) - Detailed API documentation
- [Configuration Guide](./config/README.md) - In-depth guide to configuration
- [Integration Guide](./config/integrating-with-other-services.md) - How to integrate with other services

## Troubleshooting

### Common Issues

1. **Authentication Failures**:
   - Ensure your token is valid and not expired
   - Verify you're using the correct token for the operation

2. **Missing Configurations**:
   - Check if the configuration exists for the tenant
   - Ensure you're using the correct config_key

3. **Permission Errors**:
   - Cross-tenant operations require admin privileges
   - Verify your token has the necessary permissions

### Logging

To view logs:

```bash
docker-compose logs -f management-systems
```

Add `DEBUG` level logging by setting `LOG_LEVEL=DEBUG` in your `.env` file. 