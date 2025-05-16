# PostgreSQL Multi-Tenancy Implementation

> **IMPORTANT UPDATE**: This document provides details on PostgreSQL multi-tenancy implementation. For a comprehensive reference of all database services, their APIs, and usage details, please refer to the new [Database Services Reference](database-services-reference.md) document.

## Overview

This document outlines our approach to implementing multi-tenancy using PostgreSQL within the MACH architecture. The system allows both shared and dedicated database access patterns for different tenant tiers, providing isolation, security, and scalability.

## PostgreSQL-Based Database Architecture

Our Database Access Layer (DAL) employs PostgreSQL for all database needs:

1. **PostgreSQL for Tenant Registry**: 
   - The tenant management service uses PostgreSQL to store tenant information, configurations, and database routing details
   - This provides a robust, transactional system for managing tenant metadata
   - JSONB columns allow for flexible tenant configuration storage

2. **PostgreSQL for User Data and Structured Information**:
   - The user data service uses PostgreSQL for system-wide, structured data
   - Strong relational capabilities and row-level security for tenant isolation
   - Suitable for complex joins and transactions needed for user management

This consistent PostgreSQL approach provides better operational simplicity and security across the database layer.

## Multi-Tenancy Strategy

We have implemented a schema-based multi-tenancy model in PostgreSQL, which offers the following benefits:

1. **Logical Isolation**: Each tenant's data is stored in a separate schema (namespace), providing logical isolation.
2. **Cost-Effective**: All tenants share the same database instance, reducing infrastructure costs.
3. **Performance**: PostgreSQL can efficiently handle multiple schemas within a single database.
4. **Security**: Schema-level permissions provide strong isolation between tenants.
5. **Operational Simplicity**: Easier to manage than separate databases per tenant.

## Database Architecture

### Data Isolation Models

Our system uses two different data isolation models:

1. **Multi-tenant data** (CRM, Products, etc.)
   - Shared database, separate schema approach
   - Each tenant gets their own dedicated schema
   - Schema names pattern: `tenant_<tenant_identifier>`
   - Logical isolation between tenants while sharing resources

2. **System-wide data** (User management, authentication)
   - Single database, single schema approach
   - The central `user_db` database in public schema
   - Common tables accessed by all services

### Per-Service Databases in One Cluster

We maintain separate databases per microservice, all operating within a single PostgreSQL cluster:

- **tenant_db**: Centralized tenant registry and configuration
- **user_db**: Centralized authentication, user management, RBAC
- **crm_db**: Customer relationship management data
- **product_db**: Product catalog and inventory data
- **[other service databases]**

This approach offers:
- Clear service boundaries (database-per-service)
- Operational simplicity (single cluster to manage)
- Resource sharing across databases
- Simplified backup/restore processes

### Centralized User Management

The `user_db` database serves as a central authentication and authorization system:

- Maintains user accounts across all tenants
- Handles role-based permissions
- Manages tenant-user associations
- Provides audit logging

### Centralized Tenant Registry

The `tenant_db` database serves as the central tenant management system:

- Maintains registry of all tenants
- Stores tenant metadata and configuration
- Tracks tenant database assignments
- Manages tenant provisioning status

### Service-Specific Databases

Each microservice has its own database (`crm_db`, `product_db`, etc.) with:

- A reference to the central tenant registry
- Per-tenant schemas created for each tenant
- Service-specific tables and indices
- Schema isolation between tenants

## Tenant Provisioning

When a new tenant is onboarded, the following provisioning steps occur:

1. A new tenant record is created in the `tenant_db.tenants` table
2. A corresponding schema is automatically created in each service database via the tenant management service
3. Tables, constraints, and indices are created in the new schema
4. Database roles and permissions are set up
5. The tenant admin user is created and associated with the tenant

## Security Model

Our multi-tenant security model consists of multiple layers:

### Schema Isolation

- Each tenant's data resides in a dedicated schema
- Schema names follow a pattern: `tenant_<tenant_identifier>`
- Cross-schema access is prevented

### Connection Context

- Applications set a session variable `app.current_tenant` to identify the active tenant
- The `get_current_tenant()` function enforces tenant context

```sql
-- Example of setting tenant context in application code
SET app.current_tenant = 'tenant_test001';
```

### Row-Level Security (RLS)

- Additional protection via row-level security policies
- Guards against programming errors that might leak data across tenants
- Enforces access control within shared tables

### Role-Based Access Control

- Database roles (`crm_admin`, `product_readonly`, etc.) restrict access
- Application-level permissions are stored in the JSONB `permissions` field
- The `has_permission()` function centralizes permission checks

## Database Schema Synchronization

When new changes need to be deployed to tenant schemas:

1. Updates are applied to a template schema
2. A migration script iterates through all tenant schemas
3. Changes are applied to each tenant schema individually
4. Migration state is tracked in a migrations table

```sql
-- Example migration pattern
DO $$
DECLARE
    tenant_rec RECORD;
BEGIN
    FOR tenant_rec IN SELECT schema_name FROM tenants WHERE is_active = TRUE LOOP
        EXECUTE 'ALTER TABLE ' || quote_ident(tenant_rec.schema_name) || '.products ADD COLUMN new_column TEXT';
    END LOOP;
END $$;
```

## Cross-Tenant Operations

For operations that need to access data across multiple tenants:

- Admin-specific views like `all_products` provide cross-tenant visibility
- Aggregate functions allow reporting across tenants
- ETL processes can access multiple schemas for data warehousing

## Backup and Restore

Tenant-specific backup strategies:

- Full database backups include all tenant schemas
- Individual tenant schemas can be backed up separately:
  ```
  pg_dump -n tenant_test001 crm_db > tenant_test001_crm_backup.sql
  ```
- Point-in-time recovery supports either full or per-tenant restoration

## Implementation Details

### Tenant Schemas

Each service database contains identical schema structures for each tenant. New schemas are created via database triggers when a tenant is created in the tenant registry database.

### Tenant Identification

Applications must identify the current tenant. This is done by:

1. Extracting tenant information from the domain or request headers
2. Looking up the tenant schema from the PostgreSQL `tenants` table via the tenant management service
3. Setting the PostgreSQL session variable `app.current_tenant`
4. Using `set search_path to <tenant_schema>` for queries

### Connection Pooling

Connection pools are managed per tenant to prevent session confusion:

- Each tenant has a dedicated connection pool
- Connections are pre-configured with the correct search path
- Connection pool keys include the tenant identifier

## Docker Implementation

Our database layer is containerized using Docker, with the following services:

1. **tenant-mgmt-service**: FastAPI service connected to PostgreSQL for tenant management
2. **user-data-service**: FastAPI service connected to PostgreSQL for user data
3. **postgres-system**: PostgreSQL instance containing both the tenant registry and system-wide data
4. **pgbouncer**: Connection pooling for PostgreSQL
5. **redis-cache**: Redis for caching and messaging

The Docker services are configured in a `docker-compose.database-layer.yml` file and use dedicated volumes for data persistence. Network segregation is implemented with separate networks for system and tenant databases.

## Performance Considerations

- Schema-based approach performs well up to hundreds of tenants
- For thousands of tenants, consider partitioning strategies
- Index shared tables with tenant identifiers as the first column
- Regular VACUUM and analyze operations are essential

## Global Distribution Strategy (Future Plan)

For global deployments, we plan to implement the following strategies:

### Read Replicas for Low Latency Access

- Deploy read replicas geographically close to users
- Use managed database services:
  - AWS: Amazon RDS with Read Replicas or Aurora Global Database
  - GCP: Cloud SQL for PostgreSQL with read replicas or AlloyDB
  - Azure: Azure Database for PostgreSQL with read replicas

### High Availability and Disaster Recovery

- Implement regional failovers for high availability
- Set up cross-region replication for disaster recovery
- Use database services with automatic failover capabilities
- Deploy in multiple availability zones within each region

### Data Residency and Compliance

- Store tenant data in specific regions to comply with data sovereignty requirements
- Implement data sharding strategies based on geographic regions
- Use tenant metadata to route connections to appropriate regional databases

### Caching Strategy

- Implement distributed caching layer (Redis, Memcached)
- Deploy caches in each region for low-latency access
- Cache tenant-specific data with appropriate invalidation strategies

## PostgreSQL-Only Architecture Benefits

Our PostgreSQL-only approach provides several benefits:

1. **Operational Simplicity**: A single database technology to manage, monitor, and scale
2. **Consistent Access Patterns**: Common connection handling and query patterns across services
3. **Simplified Security Model**: Uniform security policies and user management
4. **Advanced Features**: Leveraging PostgreSQL's mature feature set consistently:
   - JSONB for flexible schema requirements where needed
   - Row-level security for tenant isolation
   - Robust transactional integrity
   - Full-text search capabilities
   - Schema-based tenant isolation

## Future Considerations

As the system grows, consider:

- Implementing automated schema migration tools
- Setting up tenant-specific connection pools
- Monitoring per-tenant resource usage
- Implementing a caching layer to improve performance
- Exploring PostgreSQL table partitioning for very large tenants 