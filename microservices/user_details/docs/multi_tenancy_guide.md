# Multi-Tenancy Developer Guide

This guide provides instructions for working with the multi-tenant features of the User Details Microservice. The multi-tenancy implementation allows for complete isolation of data and configurations between different tenants.

## Table of Contents

1. [Overview](#overview)
2. [Setting Up Multi-Tenancy](#setting-up-multi-tenancy)
3. [Making Controllers Tenant-Aware](#making-controllers-tenant-aware)
4. [Tenant-Specific Configuration](#tenant-specific-configuration)
5. [Working with Tenant Data](#working-with-tenant-data)
6. [Managing Tenants](#managing-tenants)
7. [Testing Multi-Tenant Features](#testing-multi-tenant-features)
8. [Best Practices](#best-practices)

## Overview

The multi-tenancy system in the User Details Microservice follows these key principles:

- **Data Isolation**: Each tenant's data is stored separately and cannot be accessed by other tenants.
- **Configuration Isolation**: Each tenant can have its own configuration settings and templates.
- **Tenant Context**: All requests require a tenant context, provided via the `X-Tenant-ID` header.
- **Admin Operations**: Tenant management operations are restricted to admin users.

## Setting Up Multi-Tenancy

Multi-tenancy is enabled by default in the User Details Microservice. You can disable it by setting the `MULTI_TENANT_MODE` environment variable to `false`.

To set up the multi-tenant environment:

1. Initialize the directory structure:

```bash
python -m microservices.user_details.multitenant.utils.setup_tenants
```

2. Create sample tenants for testing (optional):

```bash
python -m microservices.user_details.multitenant.utils.setup_tenants --create-sample-tenants
```

3. Start the microservice:

```bash
cd microservices/user_details
python app.py
```

## Making Controllers Tenant-Aware

To make a controller tenant-aware, use the tenant middleware decorators:

### For routes that require a tenant:

```python
from multitenant.middleware import tenant_required

@app.route('/api/v1/resources')
@tenant_required
def get_resources():
    tenant_id = g.tenant_id
    # Use tenant_id to fetch tenant-specific resources
    return jsonify(resources)
```

### For routes that work with or without a tenant:

```python
from multitenant.middleware import tenant_aware

@app.route('/api/v1/public-resources')
@tenant_aware
def get_public_resources():
    tenant_id = g.tenant_id
    if tenant_id:
        # Fetch tenant-specific resources
        return jsonify(tenant_resources)
    else:
        # Fetch public resources
        return jsonify(public_resources)
```

### For admin-only routes:

```python
from multitenant.middleware import admin_required

@app.route('/api/v1/admin/resources')
@admin_required
def admin_resources():
    # Admin-only code here
    return jsonify(admin_resources)
```

## Tenant-Specific Configuration

The `TenantConfigService` provides tenant-specific configuration:

```python
from flask import current_app, g

# Get the tenant config service
tenant_config_service = current_app.config.get('tenant_config_service')

# Get tenant-specific configuration
tenant_id = g.tenant_id
insight_structure = tenant_config_service.get_insight_structure(tenant_id)
default_topics = tenant_config_service.get_default_topics(tenant_id)
extension_types = tenant_config_service.get_all_extension_types(tenant_id)
```

### ConfigService Compatibility

For backward compatibility, you can still use the standard ConfigService interface:

```python
from flask import current_app

# Get the standard config service (uses default templates)
config_service = current_app.config.get('config_service')

# Use standard methods
insight_structure = config_service.get_insight_structure()
```

## Working with Tenant Data

When working with tenant data, always include the tenant ID in repository operations:

### MongoDB (UserInsightRepository)

MongoDB uses a collection-per-tenant pattern, where each tenant's data is stored in a separate collection:

```python
# The repository automatically routes to the correct collection
insights = insight_repo.find_all_for_tenant(tenant_id)
```

### PostgreSQL (UserExtensionRepository)

PostgreSQL uses a discriminator column pattern, where tenant_id is included in all queries:

```python
# The repository automatically filters by tenant_id
extensions = extension_repo.find_by_user_id(user_id, tenant_id)
```

## Managing Tenants

Tenant management is done through the Tenant Service and API:

### Creating a Tenant

```python
from multitenant.services import TenantService

tenant_service = TenantService()

success, message = tenant_service.create_tenant(
    tenant_id='new-tenant',
    name='New Tenant',
    config={'setting': 'value'}
)
```

### REST API for Tenant Management

The following API endpoints are available for tenant management:

- `GET /api/v1/admin/tenants/` - Get all tenants
- `GET /api/v1/admin/tenants/{tenant_id}` - Get a specific tenant
- `POST /api/v1/admin/tenants/` - Create a new tenant
- `PUT /api/v1/admin/tenants/{tenant_id}` - Update a tenant
- `DELETE /api/v1/admin/tenants/{tenant_id}` - Delete a tenant
- `POST /api/v1/admin/tenants/{tenant_id}/activate` - Activate a tenant
- `POST /api/v1/admin/tenants/{tenant_id}/deactivate` - Deactivate a tenant
- `GET /api/v1/admin/tenants/current` - Get the current tenant

All of these endpoints (except `current`) require admin privileges.

## Testing Multi-Tenant Features

When testing multi-tenant features, always include the `X-Tenant-ID` header in your requests:

```bash
curl -H "X-Tenant-ID: tenant1" http://localhost:5000/api/v1/config/insight-structure
```

To test admin features, include an authentication token as well (implementation depends on your auth system).

## Best Practices

1. **Always check the tenant context**: Access the tenant ID via `g.tenant_id` in routes.
2. **Use tenant-specific paths**: Store tenant-specific files in tenant subdirectories.
3. **Include tenant ID in API headers**: Clients should include the `X-Tenant-ID` header in requests.
4. **Validate tenant access**: Use the provided middleware to ensure proper tenant validation.
5. **Handle tenant isolation**: Ensure that one tenant's data is never accessible to another tenant.
6. **Test with multiple tenants**: Always test features with different tenant contexts to ensure isolation.
7. **Default templates as a fallback**: Use default templates when tenant-specific ones don't exist.
8. **Document tenant-specific behavior**: Clearly document any differences in behavior between tenants.
9. **Consider tenant authorization**: Beyond basic tenant validation, consider tenant-specific authorization rules.
10. **Monitor tenant-specific metrics**: Track usage and performance metrics separately for each tenant. 