# Migration Guide: Tenant Architecture Refactoring

This document guides you through the changes made to the tenant architecture in the marketing-base microservice.

## Overview of Changes

We've moved all tenant-related functionality from various parts of the codebase into a single, dedicated `multitenant` directory. This reorganization improves code organization, maintainability, and makes the tenant architecture more discoverable.

## Directory Structure Changes

**Old structure:**
```
microservices/marketing-base/src/
├── domain/
│   └── repositories/
│       └── tenant_repository.py  <-- Tenant repository interface
├── infrastructure/
│   └── repositories/
│       └── tenant_repository_impl.py <-- Tenant repository implementation
├── tenant_context.py
├── tenant_middleware.py
├── multi_tenant_batch.py
└── ...
```

**New structure:**
```
microservices/marketing-base/src/
├── multitenant/
│   ├── context/
│   │   ├── __init__.py
│   │   └── tenant_context.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── tenant_middleware.py
│   ├── batch/
│   │   ├── __init__.py
│   │   └── multi_tenant_batch.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── tenant_repository.py
│   │   └── tenant_repository_impl.py
│   ├── __init__.py
│   └── MIGRATION.md
└── ...
```

## Import Changes

If you're importing any of these files, you'll need to update your imports.

**Old imports:**
```python
from ...infrastructure.tenant.tenant_context import TenantContext
from ...infrastructure.tenant.tenant_middleware import TenantMiddleware
from ...domain.models.multi_tenant_batch import MultiTenantCampaignBatch
from ...application.services.multi_tenant_batch_processor import MultiTenantBatchProcessor
from ...infrastructure.repositories.multi_tenant_batch_repository import MultiTenantBatchRepository
```

**New imports:**
```python
from ...multitenant.context.tenant_context import TenantContext
from ...multitenant.tenant.tenant_middleware import TenantMiddleware
from ...multitenant.batch.multi_tenant_batch import MultiTenantCampaignBatch
from ...multitenant.batch.multi_tenant_batch_processor import MultiTenantBatchProcessor
from ...multitenant.batch.multi_tenant_batch_repository import MultiTenantBatchRepository
```

**Simplified imports:**
You can also use the simplified imports provided by the package's `__init__.py`:

```python
from ...multitenant import TenantContext, TenantMiddleware, MultiTenantCampaignBatch
```

## Migration Steps

1. **Update imports** in your code:
   
   - Replace `from tenant_context import TenantContext` with `from multitenant.context import TenantContext`
   - Replace `from tenant_middleware import TenantMiddleware` with `from multitenant.middleware import TenantMiddleware`
   - Replace `from multi_tenant_batch import MultiTenantBatchProcessor` with `from multitenant.batch import MultiTenantBatchProcessor`
   - Replace `from domain.repositories.tenant_repository import TenantRepository` with `from multitenant.repositories import TenantRepository`
   - Replace `from infrastructure.repositories.tenant_repository_impl import TenantRepositoryImpl` with `from multitenant.repositories import TenantRepositoryImpl`

2. Update all imports in your code to use the new locations
3. If you've extended any of the moved classes, update your imports
4. For any integration tests, update paths to the tenant-related functionality

## Functionality Changes

There are no functional changes - all components maintain the same API and behavior. This refactoring is purely structural to improve code organization.

## Why This Change?

This reorganization:
1. Improves code discoverability - all tenant-related code is now in one place
2. Clarifies the architecture - the relationship between components is clearer
3. Facilitates future enhancements - a dedicated tenant module can grow more naturally
4. Follows the principle of cohesion - related functionality is grouped together 

## Files Moved

The following files have been moved to the new structure:

- `tenant_context.py` → `multitenant/context/tenant_context.py`
- `tenant_middleware.py` → `multitenant/middleware/tenant_middleware.py`  
- `multi_tenant_batch.py` → `multitenant/batch/multi_tenant_batch.py`
- `domain/repositories/tenant_repository.py` → `multitenant/repositories/tenant_repository.py`
- `infrastructure/repositories/tenant_repository_impl.py` → `multitenant/repositories/tenant_repository_impl.py` 