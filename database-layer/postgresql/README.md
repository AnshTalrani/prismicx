# PostgreSQL Database Layer

This directory contains the PostgreSQL database configuration and schemas for the PrismicX application.

## Structure

The PostgreSQL database layer is organized as follows:

- **User Extension Tables**: Multiple tables per tenant to store user extension data
  - All tenants share the same database `system_users`
  - Data is isolated using the `tenant_id` column and row-level security
  - Tenant-specific views are created for easier access

## Schemas

### Extensions Table

```sql
CREATE TABLE user_extensions.extensions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,
    extension_type VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);
```

### Extension Metrics Table

```sql
CREATE TABLE user_extensions.extension_metrics (
    id UUID PRIMARY KEY,
    extension_id UUID NOT NULL,
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    feedback_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Practicality Factors Table

```sql
CREATE TABLE user_extensions.practicality_factors (
    id UUID PRIMARY KEY,
    extension_id UUID NOT NULL,
    factor_name VARCHAR(100) NOT NULL,
    factor_value INTEGER NOT NULL,
    factor_weight FLOAT NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(extension_id, factor_name)
);
```

## Tenant Isolation

Multi-tenant access is managed through:

1. Row-level security policies based on `tenant_id`
2. Tenant-specific views
3. Connection settings that set the current tenant context

## Indexes

The following indexes are created for efficient querying:

- `user_id`: To quickly retrieve extensions for a specific user
- `tenant_id`: To filter data by tenant
- `extension_type`: To filter extensions by type
- `enabled`: To filter active/inactive extensions

## Views

The following views are provided for easier data access:

- `tenant_001_extensions`: View of extensions for tenant-001
- `tenant_002_extensions`: View of extensions for tenant-002
- `tenant_003_extensions`: View of extensions for tenant-003
- `extension_practicality`: Calculated practicality scores for extensions

## Access Control

- A dedicated service role `extension_service` is created with appropriate permissions
- Row-level security ensures tenant data isolation

## Initialization

The PostgreSQL tables and views are initialized through scripts located in:
- `/database-layer/init-scripts/postgres/02-init-user-extensions.sql` 