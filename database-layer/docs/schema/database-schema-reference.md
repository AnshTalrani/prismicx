# PrismicX Database Schema Reference

*Documentation Version: 1.0 - Last Updated: 2023*

## Overview

This document provides a comprehensive reference for all databases used in the PrismicX platform. The system uses a multi-tenant architecture with both PostgreSQL and MongoDB databases to support different data requirements.

## Table of Contents

1. [PostgreSQL Databases](#postgresql-databases)
   1. [System Users Database](#system-users-database)
   2. [Management System Repository Database](#management-system-repository-database)
   3. [User Extensions Database](#user-extensions-database)
2. [MongoDB Databases](#mongodb-databases)
   1. [Tenant Registry Database](#tenant-registry-database)
   2. [Task Repository Database](#task-repository-database)
   3. [Category Repository Database](#category-repository-database)
   4. [User Insights Database](#user-insights-database)
3. [Multi-Tenancy Implementation](#multi-tenancy-implementation)
4. [Database Access Patterns](#database-access-patterns)
5. [Security Considerations](#security-considerations)

---

## PostgreSQL Databases

### System Users Database

**Database Name**: `system_users`

#### Schema: `user_data`

##### Tables:

| Table Name | Description |
|------------|-------------|
| `users` | Stores user account information |

##### `users` Table:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the user |
| `tenant_id` | VARCHAR(50) | NOT NULL | Tenant identifier for multi-tenancy |
| `username` | VARCHAR(100) | NOT NULL | User's login name |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE (tenant) | User's email address |
| `password_hash` | VARCHAR(255) | NOT NULL | Hashed password |
| `first_name` | VARCHAR(100) | | User's first name |
| `last_name` | VARCHAR(100) | | User's last name |
| `role` | VARCHAR(50) | NOT NULL | User role (admin, user, etc.) |
| `status` | VARCHAR(20) | NOT NULL | Account status (active, inactive, etc.) |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |
| `last_login_at` | TIMESTAMP | | Last login timestamp |
| `metadata` | JSONB | | Additional user data |

**Indexes**:
- Primary Key: `id`
- Index: `(tenant_id, email)` - Unique per tenant
- Index: `tenant_id` - For tenant filtering
- Index: `status` - For status filtering

**Row-Level Security**:
```sql
CREATE POLICY tenant_isolation_policy ON user_data.users
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE));
```

#### Schema: `user_preferences`

##### Tables:

| Table Name | Description |
|------------|-------------|
| `preferences` | Stores user preferences |

##### `preferences` Table:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | UUID | NOT NULL, REFERENCES users(id) | Foreign key to users table |
| `preference_key` | VARCHAR(100) | NOT NULL | Preference identifier |
| `preference_value` | JSONB | NOT NULL | Preference data |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**:
- Primary Key: `(user_id, preference_key)`
- Index: `user_id` - For user filtering

---

### Management System Repository Database

**Database Name**: `management_system_repository`

#### Schema: `public`

##### Tables:

| Table Name | Description |
|------------|-------------|
| `management_systems` | Core management system metadata |
| `system_versions` | Management system version information |
| `tenant_systems` | Tenant-specific management system installations |
| `schema_migrations` | Management system schema migration scripts |

##### `management_systems` Table:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `system_id` | VARCHAR(50) | PRIMARY KEY | Unique identifier for the management system |
| `name` | VARCHAR(100) | NOT NULL | Management system name |
| `description` | TEXT | | Management system description |
| `type` | VARCHAR(50) | NOT NULL | Management system type (crm, sales, marketing, etc.) |
| `vendor` | VARCHAR(100) | NOT NULL | Management system vendor |
| `status` | VARCHAR(20) | NOT NULL | Management system status (active, deprecated, etc.) |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |
| `metadata` | JSONB | | Additional system metadata |

**Indexes**:
- Primary Key: `system_id`
- Index: `type` - For filtering by system type
- Index: `vendor` - For filtering by vendor
- Index: `status` - For filtering by status

##### `system_versions` Table:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `version_id` | VARCHAR(50) | PRIMARY KEY | Unique identifier for the version |
| `system_id` | VARCHAR(50) | NOT NULL, REFERENCES management_systems(system_id) | Foreign key to management_systems table |
| `version` | VARCHAR(20) | NOT NULL | Version string (e.g., "1.0.0") |
| `release_notes` | TEXT | | Release notes |
| `schema_version` | INTEGER | NOT NULL | Schema version number |
| `is_latest` | BOOLEAN | NOT NULL | Whether this is the latest version |
| `release_date` | TIMESTAMP | NOT NULL | Release date |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `dependencies` | JSONB | | System dependencies |
| `compatibility` | JSONB | | Compatibility information |

**Indexes**:
- Primary Key: `version_id`
- Index: `system_id` - For filtering by system
- Index: `(system_id, is_latest)` - For getting latest version
- Index: `schema_version` - For schema version filtering

##### `tenant_systems` Table:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `tenant_id` | VARCHAR(50) | NOT NULL | Tenant identifier |
| `system_id` | VARCHAR(50) | NOT NULL, REFERENCES management_systems(system_id) | Foreign key to management_systems table |
| `version_id` | VARCHAR(50) | NOT NULL, REFERENCES system_versions(version_id) | Foreign key to system_versions table |
| `status` | VARCHAR(20) | NOT NULL | Installation status |
| `installed_at` | TIMESTAMP | NOT NULL | Installation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |
| `configurations` | JSONB | | System configuration |
| `features_enabled` | JSONB | | Enabled features |
| `error_message` | TEXT | | Error message if installation failed |

**Indexes**:
- Primary Key: `(tenant_id, system_id)`
- Index: `tenant_id` - For tenant filtering
- Index: `system_id` - For system filtering
- Index: `status` - For status filtering

##### `schema_migrations` Table:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `migration_id` | VARCHAR(50) | PRIMARY KEY | Unique identifier for the migration |
| `system_id` | VARCHAR(50) | NOT NULL, REFERENCES management_systems(system_id) | Foreign key to management_systems table |
| `version_from` | VARCHAR(20) | NOT NULL | Starting version |
| `version_to` | VARCHAR(20) | NOT NULL | Target version |
| `schema_version_from` | INTEGER | NOT NULL | Starting schema version |
| `schema_version_to` | INTEGER | NOT NULL | Target schema version |
| `migration_sql` | TEXT | NOT NULL | SQL to execute for migration |
| `rollback_sql` | TEXT | | SQL to execute for rollback |
| `description` | TEXT | | Migration description |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |

**Indexes**:
- Primary Key: `migration_id`
- Index: `system_id` - For system filtering
- Index: `(system_id, version_from, version_to)` - For migration path lookup

#### Tenant-Specific Schemas:

For each tenant with installed management systems, schemas are created in the following pattern:

**Schema**: `tenant_[tenant_id]_[system_type]`

Example for CRM system installed for tenant "tenant-001":
- Schema: `tenant_tenant_001_crm`
- Tables depend on management system schema definitions

---

### User Extensions Database

**Database Name**: `system_users`

#### Schema: `user_extensions`

##### Tables:

| Table Name | Description |
|------------|-------------|
| `extensions` | User extension metadata |
| `extension_metrics` | Extension usage metrics |
| `practicality_factors` | Extension practicality evaluation |

##### `extensions` Table:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the extension |
| `user_id` | UUID | NOT NULL, REFERENCES user_data.users(id) | Foreign key to users table |
| `tenant_id` | VARCHAR(50) | NOT NULL | Tenant identifier |
| `extension_type` | VARCHAR(50) | NOT NULL | Type of extension |
| `name` | VARCHAR(100) | NOT NULL | Extension name |
| `description` | TEXT | | Extension description |
| `enabled` | BOOLEAN | NOT NULL DEFAULT TRUE | Whether the extension is enabled |
| `priority` | INTEGER | NOT NULL DEFAULT 0 | Extension priority order |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |
| `metadata` | JSONB | | Additional extension data |

**Indexes**:
- Primary Key: `id`
- Index: `user_id` - For user filtering
- Index: `tenant_id` - For tenant filtering
- Index: `extension_type` - For type filtering
- Index: `enabled` - For enabled filtering

##### `extension_metrics` Table:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the metrics |
| `extension_id` | UUID | NOT NULL, REFERENCES extensions(id) | Foreign key to extensions table |
| `usage_count` | INTEGER | NOT NULL DEFAULT 0 | Number of times the extension was used |
| `last_used_at` | TIMESTAMP | | Last usage timestamp |
| `feedback_score` | FLOAT | | User feedback score |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**:
- Primary Key: `id`
- Index: `extension_id` - For extension filtering

##### `practicality_factors` Table:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier for the factor |
| `extension_id` | UUID | NOT NULL, REFERENCES extensions(id) | Foreign key to extensions table |
| `factor_name` | VARCHAR(100) | NOT NULL | Factor name |
| `factor_value` | INTEGER | NOT NULL CHECK (factor_value BETWEEN 1 AND 10) | Factor value (1-10) |
| `factor_weight` | FLOAT | NOT NULL DEFAULT 1.0 | Factor weight |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**:
- Primary Key: `id`
- Index: `extension_id` - For extension filtering
- Unique Constraint: `(extension_id, factor_name)`

##### Views:

| View Name | Description |
|-----------|-------------|
| `tenant_XXX_extensions` | Filtered view for each tenant |
| `extension_practicality` | Calculated practicality scores for extensions |

**Row-Level Security**:
```sql
ALTER TABLE user_extensions.extensions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy 
    ON user_extensions.extensions
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE));
```

---

## MongoDB Databases

### Tenant Registry Database

**Database Name**: `tenant_registry`

#### Collections:

##### `tenants` Collection:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `tenant_id` | String | Required, Unique | Unique identifier for the tenant |
| `name` | String | Required | Tenant organization name |
| `database_config` | Object | Required | Database configuration |
| `database_config.type` | String | Required, Enum: ['dedicated', 'shared'] | Database isolation type |
| `database_config.connection_string` | String | Required | Database connection string |
| `database_config.database_name` | String | | Name of the tenant database |
| `database_config.shard_key` | String | | Shard key for shared databases |
| `created_at` | Date | Required | Creation timestamp |
| `updated_at` | Date | | Last update timestamp |
| `status` | String | Required, Enum: ['active', 'inactive', 'suspended', 'provisioning'] | Tenant status |
| `settings` | Object | | Tenant-specific settings |
| `tier` | String | | Service tier |
| `region` | String | | Geographical region |

**Indexes**:
- Unique Index: `tenant_id`
- Index: `name`
- Index: `status`
- Index: `region`

##### `tenant_databases` Collection:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `database_name` | String | Required, Unique | Name of the tenant database |
| `type` | String | Required, Enum: ['dedicated', 'shared'] | Database type |
| `tenants` | Array[String] | | List of tenant IDs using this database |
| `status` | String | Required, Enum: ['active', 'provisioning', 'decommissioning', 'archived'] | Database status |
| `created_at` | Date | Required | Creation timestamp |
| `server` | String | | Database server hostname |
| `region` | String | | Geographical region |

**Indexes**:
- Unique Index: `database_name`
- Index: `type`
- Index: `status`
- Index: `region`

---

### Task Repository Database

**Database Name**: `task_repository`

#### Collections:

##### `tasks` Collection:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `task_id` | String | Required, Unique | Unique identifier for the task |
| `tenant_id` | String | Required | Tenant identifier |
| `service_id` | String | Required | Service identifier |
| `type` | String | Required | Task type |
| `status` | String | Required, Enum: ['pending', 'running', 'completed', 'failed', 'cancelled'] | Task status |
| `priority` | Number | Required | Task priority |
| `payload` | Object | Required | Task data |
| `result` | Object | | Task result |
| `created_at` | Date | Required | Creation timestamp |
| `updated_at` | Date | | Last update timestamp |
| `started_at` | Date | | Execution start timestamp |
| `completed_at` | Date | | Completion timestamp |
| `error` | Object | | Error information if failed |

**Indexes**:
- Unique Index: `task_id`
- Index: `tenant_id`
- Index: `service_id`
- Index: `status`
- Index: `type`
- Index: `created_at`
- Compound Index: `(tenant_id, status)`
- Compound Index: `(tenant_id, type)`

---

### Category Repository Database

**Database Name**: `category_repository`

#### Collections:

##### `categories` Collection:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `category_id` | String | Required, Unique | Unique identifier for the category |
| `name` | String | Required | Category name |
| `description` | String | | Category description |
| `parent_id` | String | | Parent category ID |
| `tenant_id` | String | Required | Tenant identifier |
| `attributes` | Array[Object] | | Category attributes |
| `created_at` | Date | Required | Creation timestamp |
| `updated_at` | Date | | Last update timestamp |

**Indexes**:
- Unique Index: `category_id`
- Index: `tenant_id`
- Index: `parent_id`
- Compound Index: `(tenant_id, name)`

---

### User Insights Database

**Database Name**: `tenant_XXX_db` (One database per tenant, e.g., `tenant_001_db`)

#### Collections:

##### `user_insights` Collection:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `user_id` | String | Required, Unique | User identifier |
| `tenant_id` | String | Required | Tenant identifier |
| `topics` | Array[Object] | | List of user interest topics |
| `topics.topic_id` | String | Required | Topic identifier |
| `topics.name` | String | Required | Topic name |
| `topics.description` | String | | Topic description |
| `topics.subtopics` | Array[Object] | | List of subtopics |
| `topics.subtopics.subtopic_id` | String | Required | Subtopic identifier |
| `topics.subtopics.name` | String | Required | Subtopic name |
| `topics.subtopics.content` | Object | | Subtopic content |
| `topics.subtopics.content.key_points` | Array[String] | | List of key points |
| `topics.subtopics.content.resources` | Array[String] | | List of resource URLs |
| `topics.subtopics.created_at` | Date | Required | Creation timestamp |
| `topics.subtopics.updated_at` | Date | Required | Last update timestamp |
| `topics.created_at` | Date | Required | Creation timestamp |
| `topics.updated_at` | Date | Required | Last update timestamp |
| `metadata` | Object | | Additional user insights data |
| `metadata.profile_completeness` | Number | | Profile completeness score |
| `metadata.interest_score` | Number | | Interest score |
| `created_at` | Date | Required | Creation timestamp |
| `updated_at` | Date | Required | Last update timestamp |

**Indexes**:
- Unique Index: `user_id`
- Index: `topics.name`
- Index: `updated_at`

---

## Multi-Tenancy Implementation

The PrismicX platform implements multi-tenancy using different strategies depending on the database technology:

### PostgreSQL Multi-Tenancy

- **Schema-based Isolation**: Each tenant gets its own PostgreSQL schema in a shared database
- **Row-Level Security**: For shared tables, row-level security policies ensure tenant data isolation
- **Connection Pooling**: Connections are pooled and tenant context is set using session variables
- **Dynamic Schema Creation**: Schemas are created automatically during tenant provisioning

### MongoDB Multi-Tenancy

- **Database-level Isolation**: Each tenant gets its own MongoDB database or collections
- **Shard Keys**: For shared collections, tenant_id is used as a shard key
- **Connection Management**: Connections are managed per tenant with appropriate authentication
- **Dynamic Database Creation**: Databases and collections are created automatically during tenant provisioning

## Database Access Patterns

Refer to the [Database Access Patterns](../patterns/database-access-patterns.md) document for detailed examples of how to access data in these databases.

## Security Considerations

### Data Isolation

- PostgreSQL: Schema isolation and row-level security
- MongoDB: Database/collection isolation and access control

### Authentication and Authorization

- Service-specific database roles with limited permissions
- Tenant context validation for all database operations
- Encryption of sensitive data

### Encryption

- Transport encryption using TLS
- Column-level encryption for sensitive fields
- Key management handled by separate service

---

*For ER diagrams and visual representations of these schemas, see the [diagrams](../diagrams/) directory.* 