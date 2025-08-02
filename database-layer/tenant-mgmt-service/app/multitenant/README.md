# Multitenant Architecture for Database Layer

This directory contains the implementation of the multitenant architecture for the database layer of the PrismicX platform. It provides a clean, maintainable way to handle tenant isolation in database operations.

## Architecture Overview

The multitenant architecture follows a layered approach:

1. **Tenant Context** - Maintains the current tenant information throughout the request lifecycle
2. **Tenant Manager** - Coordinates tenant operations and serves as the main entry point
3. **Tenant Service** - Implements business logic for tenant operations
4. **Tenant Repository** - Handles database operations for tenant data

## Components

### Tenant Context

`TenantContext` maintains tenant-specific information throughout the request lifecycle. It uses Python's context variables to ensure thread safety in async operations.

```python
from multitenant import TenantContext

# Get current tenant ID
tenant_id = TenantContext.get_tenant_id()

# Get current tenant information
tenant_info = TenantContext.get_current_tenant()
```

### Tenant Manager

`TenantManager` coordinates tenant operations and serves as the main entry point for other services to interact with tenant functionality.

```python
from multitenant import TenantManager

# Create tenant manager
tenant_manager = TenantManager()

# Get tenant information
tenant_info = await tenant_manager.get_tenant_by_id("tenant-123")

# Create new tenant
new_tenant = await tenant_manager.create_tenant({
    "name": "Example Tenant",
    "domain": "example.com"
})
```

### Tenant Middleware

`TenantMiddleware` extracts tenant information from request headers and sets up the tenant context for the duration of the request.

```python
from multitenant.tenant_middleware import TenantMiddleware

# Add middleware to FastAPI application
app.add_middleware(
    TenantMiddleware,
    tenant_manager=TenantManager(),
    tenant_header="X-Tenant-ID"
)
```

## Database Isolation Strategies

The architecture supports different tenant isolation strategies:

1. **Schema-based Isolation** - Each tenant gets its own schema in a shared database
2. **Database-per-Tenant** - Each tenant gets its own database
3. **Row-level Security** - Tenants share tables with tenant ID columns and row-level security

The default strategy is schema-based isolation, where each tenant gets its own schema in a shared PostgreSQL database.

## Usage Example

Here's a complete example of how to use the multitenant architecture:

```python
from fastapi import FastAPI, Depends
from multitenant import TenantManager, get_tenant_manager
from multitenant.tenant_context import TenantContext
from multitenant.tenant_middleware import TenantMiddleware

app = FastAPI()

# Add tenant middleware
app.add_middleware(
    TenantMiddleware,
    tenant_manager=TenantManager(),
    tenant_header="X-Tenant-ID"
)

@app.get("/api/v1/current-tenant")
async def get_current_tenant():
    """Get information about the current tenant."""
    tenant = TenantContext.get_current_tenant()
    if not tenant:
        return {"tenant": None}
    
    return {"tenant": tenant}

@app.post("/api/v1/tenants")
async def create_tenant(
    tenant_data: dict,
    tenant_manager: TenantManager = Depends(get_tenant_manager)
):
    """Create a new tenant."""
    new_tenant = await tenant_manager.create_tenant(tenant_data)
    return new_tenant
```

## Integration with Microservices

Microservices can use the tenant information to connect to the appropriate database with the correct tenant isolation:

```python
from fastapi import Depends
from multitenant import TenantContext
from sqlalchemy import text
from database import get_db_session

@app.get("/api/v1/data")
async def get_data(db = Depends(get_db_session)):
    """Get data for the current tenant."""
    tenant_info = TenantContext.get_current_tenant()
    
    # Set search path to tenant schema for this session
    if tenant_info:
        await db.execute(text(f'SET search_path TO "{tenant_info.schema_name}"'))
    
    # Data is now queried from the tenant's schema
    result = await db.execute(text("SELECT * FROM data"))
    return {"data": result.all()}
``` 