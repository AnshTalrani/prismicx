# Multi-Tenancy Implementation for User Details Microservice

This directory contains the multi-tenancy implementation for the User Details Microservice. The implementation follows a clean architecture approach and isolates multi-tenancy concerns into their own module.

## Architecture

The multi-tenancy implementation consists of the following components:

### Models

- `Tenant`: Represents a tenant in the system, with attributes like ID, name, active status, and configuration.

### Services

- `TenantRepository`: Manages storage and retrieval of tenant data using a file-based approach (can be extended to use a database).
- `TenantService`: Provides high-level operations for tenant management, including creation, configuration, and directory management.
- `TenantConfigService`: A tenant-aware adaptation of the ConfigService that loads configurations from tenant-specific directories.

### Middleware

- `tenant_middleware`: Contains decorators and functions for handling tenant context in requests, including:
  - `tenant_required`: A decorator that requires a valid tenant ID for a route.
  - `tenant_aware`: A decorator that uses a tenant ID if provided but doesn't require it.
  - `admin_required`: A decorator for routes that require admin privileges.
  - `init_tenant_middleware`: Initializes tenant middleware for a Flask app.

## Usage

### Setting Up Multi-Tenancy

To enable multi-tenancy in the User Details Microservice, add the following to your `app.py`:

```python
from multitenant.middleware import init_tenant_middleware
from multitenant.services import TenantService, TenantConfigService

# Create and configure the app
app = Flask(__name__)

# Initialize tenant service
tenant_service = TenantService()
app.config['tenant_service'] = tenant_service

# Initialize tenant config service
tenant_config_service = TenantConfigService(tenant_service)
app.config['tenant_config_service'] = tenant_config_service

# Initialize tenant middleware
init_tenant_middleware(app)
```

### Using Tenant Context in Routes

To create a route that requires a tenant ID:

```python
from multitenant.middleware import tenant_required

@app.route('/api/v1/resources')
@tenant_required
def get_resources():
    tenant_id = g.tenant_id
    # Use tenant_id to fetch tenant-specific resources
    return jsonify(resources)
```

To create a route that works with or without a tenant ID:

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

### Managing Tenants

```python
from multitenant.services import TenantService

tenant_service = TenantService()

# Create a new tenant
success, message = tenant_service.create_tenant(
    tenant_id='tenant1',
    name='First Tenant',
    config={'setting1': 'value1'}
)

# Get tenant information
tenant = tenant_service.get_tenant('tenant1')

# Update tenant configuration
tenant.set_config_value('setting2', 'value2')
tenant_service.update_tenant(tenant)
```

## Folder Structure

```
multitenant/
├── README.md
├── __init__.py
├── models/
│   ├── __init__.py
│   └── tenant.py
├── services/
│   ├── __init__.py
│   ├── tenant_repository.py
│   ├── tenant_service.py
│   └── tenant_config_service.py
├── middleware/
│   ├── __init__.py
│   └── tenant_middleware.py
└── utils/
    └── __init__.py
```

## Best Practices

1. **Always use the tenant context**: Access the tenant ID via `g.tenant_id` in routes.
2. **Use tenant-specific paths**: Store tenant-specific files in tenant subdirectories.
3. **Include tenant ID in API headers**: Clients should include the `X-Tenant-ID` header in requests.
4. **Validate tenant access**: Use the provided middleware to ensure proper tenant validation.
5. **Handle tenant isolation**: Ensure that one tenant's data is never accessible to another tenant. 