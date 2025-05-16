# Multitenant Architecture for Communication Base Microservice

This directory contains the implementation of the multitenant architecture for the communication base microservice. It provides a comprehensive solution for handling multi-tenant operations in the context of communication services.

## Overview

The multitenant architecture is designed to:

1. Identify tenants from incoming requests
2. Maintain tenant context throughout request processing
3. Provide tenant-specific configurations
4. Connect to tenant-specific database schemas
5. Isolate tenant data and operations

## Components

### Tenant Context (`tenant_context.py`)

The tenant context module provides thread-safe context for tenant-specific operations using Python's `contextvars`. It maintains the current tenant ID and metadata throughout request processing, even in asynchronous code.

```python
from multitenant import TenantContext

# Set tenant context
TenantContext.set_current_tenant("tenant-123", {"schema": "tenant_123"})

# Get tenant ID
tenant_id = TenantContext.get_current_tenant()

# Get tenant schema
schema = TenantContext.get_tenant_schema()

# Clear tenant context
TenantContext.clear_current_tenant()
```

It also provides a context manager and decorator for scoped tenant operations:

```python
from multitenant import TenantContextManager, with_tenant

# Using context manager
async with TenantContextManager("tenant-123"):
    # Operations within tenant context
    pass

# Using decorator
@with_tenant("tenant-123")
async def tenant_specific_operation():
    # Operations within tenant context
    pass
```

### Tenant Middleware (`tenant_middleware.py`)

The middleware extracts tenant information from HTTP requests and establishes tenant context for the duration of the request. It supports extraction from:

- HTTP headers (e.g., `X-Tenant-ID`)
- Query parameters (e.g., `?tenant_id=123`)
- Path parameters (e.g., `/tenants/123/...`)
- Host/domain (e.g., `tenant-123.example.com`)

```python
from fastapi import FastAPI
from multitenant import TenantMiddleware

app = FastAPI()

# Add tenant middleware
app.add_middleware(
    TenantMiddleware,
    tenant_header="X-Tenant-ID",
    exclude_paths=["/docs", "/health"]
)
```

### Tenant Service (`tenant_service.py`)

The tenant service communicates with the tenant management service to retrieve tenant information and metadata. It includes caching to minimize requests to the tenant service.

```python
from multitenant import TenantService

# Create tenant service
tenant_service = TenantService()

# Get tenant information
tenant_info = await tenant_service.get_tenant_info("tenant-123")

# List tenants
tenants = await tenant_service.list_tenants(limit=10, offset=0)
```

### Tenant Resolver (`tenant_resolver.py`)

The tenant resolver provides utilities to extract tenant information from various sources like HTTP requests and URLs.

```python
from multitenant import TenantResolver
from fastapi import Request

# Create resolver
resolver = TenantResolver(
    tenant_header="X-Tenant-ID",
    subdomain_tenant_pattern=r"^([^.]+)\."
)

# Resolve tenant from request
tenant_id = resolver.resolve_from_request(request)

# Resolve tenant from URL
tenant_id = resolver.resolve_from_url("https://tenant-123.example.com/api/v1/users")
```

### Tenant Configuration (`tenant_config.py`)

The tenant configuration provides tenant-specific configuration settings. It allows different tenants to have their own settings.

```python
from multitenant import get_communication_config

# Get communication config
config = get_communication_config()

# Get config for current tenant
tenant_config = config.get_config()

# Use config values
email_from = tenant_config.email_from
sms_sender = tenant_config.sms_sender_id

# Update config for specific tenant
config.update_config(
    {"email_from": "custom@example.com"},
    tenant_id="tenant-123"
)
```

### Database Adapter (`database_adapter.py`)

The database adapter provides tenant-specific database connections and session management. It ensures proper isolation between tenant data using schema-based isolation.

```python
from multitenant import get_db_session, get_system_db_session

# Get session for current tenant
async with get_db_session() as session:
    # Operations within tenant database context
    result = await session.execute("SELECT * FROM users")
    
# Get session for system-wide operations
async with get_system_db_session() as session:
    # Operations in public schema
    result = await session.execute("SELECT * FROM tenants")
```

## Integration with FastAPI

To fully integrate the multitenant architecture with FastAPI:

```python
from fastapi import FastAPI, Depends
from multitenant import (
    TenantMiddleware,
    TenantContext,
    get_db_session
)

app = FastAPI()

# Add tenant middleware
app.add_middleware(
    TenantMiddleware,
    tenant_header="X-Tenant-ID"
)

# Dependency for database session
async def get_db():
    async with get_db_session() as session:
        yield session

@app.get("/api/v1/users")
async def get_users(db = Depends(get_db)):
    """Get users for the current tenant."""
    tenant_id = TenantContext.get_current_tenant()
    # Query will automatically use the tenant's schema
    result = await db.execute("SELECT * FROM users")
    users = result.all()
    return {"tenant_id": tenant_id, "users": users}
```

## Best Practices

1. **Always clear tenant context**: The middleware handles this automatically, but be careful when setting tenant context manually.

2. **Use tenant context only when needed**: Not all operations are tenant-specific.

3. **Cache tenant information**: The tenant service does this automatically.

4. **Validate tenant IDs**: Ensure tenant IDs are valid before using them.

5. **Handle missing tenants gracefully**: Not all requests will have a tenant context.

6. **Use the database adapter**: Don't create your own database sessions; use the adapter.

7. **Consider performance**: Tenant resolution and database connections add overhead.

## Database Schema Management

The communication microservice relies on the tenant management service for tenant schema creation and management. When interacting with the database:

1. **Schema-Based Isolation**: Each tenant gets its own PostgreSQL schema.
2. **Schema Switching**: The database adapter sets the appropriate `search_path` for each tenant.
3. **Default Schema**: System-wide operations use the "public" schema.

## Tenant Identification Strategies

The architecture supports multiple strategies for tenant identification:

1. **Header-Based**: Using the `X-Tenant-ID` header (default)
2. **Query Parameter**: Using the `tenant_id` query parameter
3. **Path Parameter**: Using the `tenant_id` path parameter
4. **Subdomain**: Using subdomain patterns (e.g., `tenant-123.example.com`)
5. **Domain**: Using domain patterns

You can configure these strategies in the middleware and resolver.

## Security Considerations

- **Tenant data isolation**: Ensure proper schema isolation to prevent data leakage
- **Tenant ID validation**: Validate tenant IDs to prevent injection attacks
- **Rate limiting**: Implement per-tenant rate limiting
- **Authentication**: Ensure proper authentication before tenant resolution
- **Error handling**: Don't expose sensitive information in error messages 