# Migration Guide: Tenant Architecture Refactoring

This document guides you through the changes made to the tenant architecture in the analysis-base microservice.

## Overview of Changes

1. Removed schema management functionality
2. Simplified tenant context to only handle tenant IDs
3. Updated middleware and routes to work with simplified context
4. Removed schema-related database operations

## Key Changes

### Tenant Context
- Removed schema management
- Simplified to only handle tenant IDs
- Removed tenant info caching from context (now handled by client)

### Database Access
- Removed schema switching
- Using tenant_id column for data isolation
- Single unified schema for all tenants

### API Changes
- Removed schema-related endpoints
- Updated tenant info endpoint to only return tenant ID and info
- Database queries now filter by tenant_id

## Migration Steps

1. **Database Changes**:
   - Add tenant_id column to all tenant-specific tables
   - Update queries to filter by tenant_id
   - Remove schema-related functions and triggers

2. **Code Updates**:
   - Use `get_current_tenant_id()` instead of `TenantContext.get_tenant_id()`
   - Use `set_tenant_context()` instead of `TenantContext.set_tenant_id()`
   - Remove all schema-related function calls
   - Update queries to include tenant_id filters

3. **Configuration**:
   - Remove schema-related configuration
   - Update database connection settings to use single schema

## Why This Change?

1. **Simplification**: Schema-based isolation added complexity without significant benefits
2. **Performance**: Reduced overhead from schema switching
3. **Maintainability**: Simpler codebase with clearer data isolation
4. **Scalability**: Better support for database sharding and replication

## Breaking Changes

1. Removed schema-related functions:
   - `get_tenant_schema()`
   - `set_tenant_schema()`
   - `create_tenant_schema()`
   - `delete_tenant_schema()`

2. Changed database access pattern:
   - All queries must include tenant_id filter
   - No more automatic schema isolation

## Next Steps

1. Update existing applications to use tenant_id filtering
2. Add database migrations for tenant_id columns
3. Update documentation and examples
4. Consider implementing row-level security for additional isolation 