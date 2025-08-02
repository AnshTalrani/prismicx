# Management Systems API Documentation

This section documents the API endpoints provided by the Management Systems microservice.

## Base URL

All API endpoints are relative to the base URL:

```
http://management-systems:8000/
```

## Authentication

Most endpoints require authentication using OAuth2 Bearer tokens. Include the token in the `Authorization` header:

```
Authorization: Bearer {your_token}
```

## Multi-tenancy

For tenant-specific operations, the tenant ID should be:
1. Included in the URL path for tenant-specific endpoints
2. Provided in the `X-Tenant-ID` header for request context

## Available Endpoints

### Configuration Management

| Endpoint | Method | Description | Auth Level |
|----------|--------|-------------|-----------|
| `/config/tenants/{tenant_id}/configs/{config_key}` | GET | Get a specific tenant configuration | User |
| `/config/tenants/{tenant_id}/configs/{config_key}` | PUT | Update a tenant configuration | User |
| `/config/tenants/{tenant_id}/configs` | GET | List all configurations for a tenant | User |
| `/config/configs/{config_key}/all-tenants` | GET | Get a specific configuration for all tenants | Admin |
| `/config/schemas` | POST | Register a configuration schema | Admin |

### System Management

| Endpoint | Method | Description | Auth Level |
|----------|--------|-------------|-----------|
| `/api/v1/systems` | GET | Get all available management systems | User |
| `/api/v1/systems/{system_id}` | GET | Get a specific management system | User |
| `/api/v1/systems` | POST | Create a new management system | Admin |
| `/api/v1/systems/{system_id}` | PUT | Update a management system | Admin |
| `/api/v1/systems/{system_id}` | DELETE | Delete a management system | Admin |

### Tenant System Instances

| Endpoint | Method | Description | Auth Level |
|----------|--------|-------------|-----------|
| `/api/v1/tenant/{tenant_id}/systems` | GET | Get all systems for a tenant | User |
| `/api/v1/tenant/{tenant_id}/systems` | POST | Create a new system instance | User |
| `/api/v1/tenant/{tenant_id}/systems/{instance_id}` | GET | Get a specific system instance | User |
| `/api/v1/tenant/{tenant_id}/systems/{instance_id}` | PUT | Update a system instance | User |
| `/api/v1/tenant/{tenant_id}/systems/{instance_id}` | DELETE | Delete a system instance | User |

### Data Operations

| Endpoint | Method | Description | Auth Level |
|----------|--------|-------------|-----------|
| `/api/v1/tenant/{tenant_id}/systems/{instance_id}/data` | GET | Get data items for a system instance | User |
| `/api/v1/tenant/{tenant_id}/systems/{instance_id}/data` | POST | Create a new data item | User |
| `/api/v1/tenant/{tenant_id}/systems/{instance_id}/data/{item_id}` | GET | Get a specific data item | User |
| `/api/v1/tenant/{tenant_id}/systems/{instance_id}/data/{item_id}` | PUT | Update a data item | User |
| `/api/v1/tenant/{tenant_id}/systems/{instance_id}/data/{item_id}` | DELETE | Delete a data item | User |
| `/api/v1/tenant/{tenant_id}/systems/{instance_id}/data/bulk` | POST | Bulk import data | User |

## Detailed API Documentation

For more detailed information about each endpoint, including request/response formats and examples, refer to the following pages:

- [Configuration API](./configuration.md)
- [System Management API](./system-management.md)
- [Tenant System API](./tenant-system.md)
- [Data Operations API](./data-operations.md)

## Error Handling

The API uses standard HTTP status codes to indicate success or failure:

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request format or parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server-side error

Error responses include a JSON body with details:

```json
{
  "detail": "Error message describing the issue"
}
``` 