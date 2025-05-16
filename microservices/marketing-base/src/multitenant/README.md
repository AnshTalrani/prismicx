# Multi-Tenant Architecture

This directory contains the components for implementing multi-tenant functionality in the marketing-base microservice.

## Directory Structure

- **context/** - Contains components for maintaining tenant context throughout request lifecycle
- **tenant/** - Contains middleware for extracting tenant information from requests
- **batch/** - Contains components for processing operations across multiple tenants

## Components

### Tenant Context

The `TenantContext` class provides methods for setting and retrieving tenant information
in the current execution context. It uses thread-local storage to ensure proper isolation
between different tenant operations.

```python
from multitenant import TenantContext

# Set tenant for current context
TenantContext.set_tenant_id("tenant_123")

# Get current tenant ID
tenant_id = TenantContext.get_tenant_id()

# Use context manager for scope-based tenant context
with TenantContext.with_tenant("tenant_456"):
    # All code in this block runs in the context of tenant_456
    pass
```

### Tenant Middleware

The `TenantMiddleware` extracts tenant information from incoming HTTP requests
and sets up the tenant context for the duration of the request.

```python
from fastapi import FastAPI
from multitenant import TenantMiddleware

app = FastAPI()
app.add_middleware(TenantMiddleware, tenant_repository=tenant_repository)
```

### Multi-Tenant Batch Processing

The batch processing components allow for efficient processing of operations
across multiple tenants:

- `MultiTenantCampaignBatch` - Model representing a batch of tenants sharing a campaign template
- `MultiTenantBatchProcessor` - Service for processing multi-tenant batches
- `MultiTenantBatchRepository` - Repository for storing batch data

```python
from multitenant.batch import MultiTenantBatchProcessor

batch_processor = MultiTenantBatchProcessor()
batch_id = await batch_processor.create_multi_tenant_batch({
    "name": "Monthly Newsletter",
    "tenant_ids": ["tenant_123", "tenant_456", "tenant_789"],
    "campaign_template": {...}
})
```

## Integration with Database Layer

The multi-tenant components integrate with the database layer through:

1. **Tenant Context** - Maintains which tenant is active during database operations
2. **Database Connections** - Uses the tenant ID to connect to the appropriate database/schema
3. **Tenant Management Service** - Retrieves tenant information from the central tenant registry 