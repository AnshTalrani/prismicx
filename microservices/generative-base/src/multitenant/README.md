# Multitenant Architecture

This directory contains the multitenant architecture for the generative-base microservice. It provides a clean, maintainable way to handle tenant isolation in database operations and request processing.

## Architecture Overview

The multitenant architecture follows a layered approach:

1. **Tenant Context** - Maintains the current tenant information throughout the request lifecycle
2. **Tenant Middleware** - Extracts tenant information from request headers
3. **Tenant Database Context** - Applies tenant context to database sessions
4. **Tenant Service Client** - Communicates with the tenant management service

## Components

### Tenant Context

`TenantContext` maintains tenant-specific information throughout the request lifecycle. It uses Python's context variables to ensure thread safety in async operations.

```python
from multitenant import TenantContext

# Set the current tenant ID
TenantContext.set_current_tenant("tenant-123")

# Get the current tenant ID
tenant_id = TenantContext.get_current_tenant()

# Clear the current tenant ID
TenantContext.clear_current_tenant()
```

### Tenant Middleware

`TenantMiddleware` extracts tenant information from request headers and sets up the tenant context for the duration of the request.

```python
from fastapi import FastAPI
from multitenant import TenantMiddleware

app = FastAPI()

app.add_middleware(
    TenantMiddleware,
    header_name="X-Tenant-ID",
    exclude_paths=["/docs", "/health"]
)
```

### Tenant Database Context

`TenantDatabaseContext` applies tenant context to database sessions. It ensures that database operations are performed in the correct schema for the current tenant.

```python
from sqlalchemy.ext.asyncio import AsyncSession
from multitenant import TenantDatabaseContext

async def perform_db_operation(session: AsyncSession):
    # Apply tenant context to the session
    await TenantDatabaseContext.apply_tenant_context(session)
    
    # Now operations will be performed in the tenant's schema
    result = await session.execute(...)
    return result
```

### Tenant Service Client

`TenantServiceClient` communicates with the tenant management service to retrieve tenant information and connection details.

```python
from multitenant import TenantServiceClient

# Create a client for the tenant management service
client = TenantServiceClient()

# Get connection information for a tenant
connection_info = await client.get_tenant_connection_info("tenant-123")

# Get information about a tenant
tenant_info = await client.get_tenant_info("tenant-123")
```

## Using the Context Manager

For isolating blocks of code to a specific tenant, use the `TenantContextManager`:

```python
from multitenant import TenantContextManager

async def process_for_tenant(tenant_id):
    async with TenantContextManager(tenant_id):
        # Code here runs with the tenant context set
        # Database operations will use the tenant's schema
        pass
```

## Using the Decorator

For functions that need to run in a tenant context, use the `with_tenant` decorator:

```python
from multitenant import with_tenant

@with_tenant("tenant-123")
async def process_tenant_data():
    # Function runs with the tenant context set to "tenant-123"
    pass
```

## Integration with Database Layer

This multitenant architecture integrates with the database layer through the `get_tenant_db_session` function:

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db
from multitenant import get_tenant_db_session

# Get a database session with tenant context applied
async def get_tenant_session() -> AsyncSession:
    async for session in get_tenant_db_session(get_db):
        yield session

# Use in FastAPI endpoints
@app.get("/api/data")
async def get_data(db: AsyncSession = Depends(get_tenant_session)):
    # Operations on db will be in the tenant's schema
    result = await db.execute(...)
    return result
``` 