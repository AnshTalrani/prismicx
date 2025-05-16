# Configuration API

The Configuration API provides endpoints for managing tenant-specific configurations and configuration schemas.

## 1. Get Tenant Configuration

Retrieves a specific configuration for a tenant.

**Endpoint:** `/config/tenants/{tenant_id}/configs/{config_key}`  
**Method:** GET  
**Auth Required:** Yes (User)  

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| tenant_id | string | The ID of the tenant |
| config_key | string | The configuration key to retrieve |

### Response

**Status Code:** 200 OK

```json
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
  }
}
```

### Error Responses

- `404 Not Found` - Configuration not found
- `503 Service Unavailable` - Configuration service unavailable

## 2. Update Tenant Configuration

Updates a specific configuration for a tenant.

**Endpoint:** `/config/tenants/{tenant_id}/configs/{config_key}`  
**Method:** PUT  
**Auth Required:** Yes (User)  

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| tenant_id | string | The ID of the tenant |
| config_key | string | The configuration key to update |

### Request Body

```json
{
  "config_value": {
    "enabled": true,
    "frequency": "weekly"
  }
}
```

### Response

**Status Code:** 200 OK

```json
{
  "status": "success"
}
```

### Error Responses

- `400 Bad Request` - Invalid configuration format
- `503 Service Unavailable` - Configuration service unavailable

## 3. List Tenant Configurations

Lists all configurations for a tenant.

**Endpoint:** `/config/tenants/{tenant_id}/configs`  
**Method:** GET  
**Auth Required:** Yes (User)  

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| tenant_id | string | The ID of the tenant |

### Response

**Status Code:** 200 OK

```json
[
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
    }
  },
  {
    "tenant_id": "tenant123",
    "config_key": "system_preferences",
    "config_value": {
      "theme": "dark",
      "language": "en-US"
    },
    "metadata": {
      "description": "System preferences",
      "category": "user_interface"
    }
  }
]
```

### Error Responses

- `503 Service Unavailable` - Configuration service unavailable

## 4. Get Configuration for All Tenants

Retrieves a specific configuration for all tenants. This is an admin-level operation.

**Endpoint:** `/config/configs/{config_key}/all-tenants`  
**Method:** GET  
**Auth Required:** Yes (Admin only)  

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| config_key | string | The configuration key to retrieve |

### Response

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

### Error Responses

- `403 Forbidden` - Administrator privileges required
- `503 Service Unavailable` - Configuration service unavailable

### Example Usage

#### Using cURL:

```bash
curl -X GET \
  http://management-systems:8000/config/configs/email_notifications/all-tenants \
  -H 'Authorization: Bearer admin_token_here'
```

#### Using Python:

```python
import httpx

async def get_config_for_all_tenants(config_key, admin_token):
    url = f"http://management-systems:8000/config/configs/{config_key}/all-tenants"
    headers = {
        "Authorization": f"Bearer {admin_token}"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return []
```

## 5. Register Configuration Schema

Registers a new configuration schema.

**Endpoint:** `/config/schemas`  
**Method:** POST  
**Auth Required:** Yes (Admin)  

### Request Body

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

### Response

**Status Code:** 200 OK

```json
{
  "status": "success"
}
```

### Error Responses

- `400 Bad Request` - Invalid schema format
- `503 Service Unavailable` - Configuration service unavailable 