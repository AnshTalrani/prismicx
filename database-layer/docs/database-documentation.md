# PrismicX Database Layer Documentation

> **IMPORTANT UPDATE**: For a comprehensive reference of all database services, their APIs, and usage details, please refer to the new [Database Services Reference](database-services-reference.md) document.

*Documentation Version: 1.0 - Last Updated: 2023*

## Overview

This document serves as the entry point for all database-related documentation in the PrismicX platform. The database layer is a critical component of the system, providing multi-tenant data storage and access patterns for all microservices.

## Documentation Structure

The database documentation is organized as follows:

1. **Schema Documentation**
   - [Database Schema Reference](schema/database-schema-reference.md) - Comprehensive reference of all database schemas, tables, and fields

2. **Diagrams**
   - [PostgreSQL ER Diagram](diagrams/postgresql-er-diagram.png) - Entity-relationship diagram for PostgreSQL databases
   - [MongoDB ER Diagram](diagrams/mongodb-er-diagram.png) - Entity-relationship diagram for MongoDB databases
   - [Multi-Tenancy Architecture](diagrams/multi-tenancy-architecture.png) - High-level architecture diagram of the multi-tenancy implementation

3. **Patterns and Guidelines**
   - [Database Access Patterns](patterns/database-access-patterns.md) - Common patterns for accessing data in a multi-tenant environment

4. **Microservice-Specific Documentation**
   - [Management System Repository](management-system-repo.md) - Manages management systems and their configurations
   - [Multi-Tenancy PostgreSQL](multi-tenancy-postgresql.md) - PostgreSQL multi-tenancy implementation details
   - [Vector Store Service](vector-store-service.md) - Vector embeddings and semantic search across microservices

## Database Services Summary

| Service | Database Type | Primary Database | External Port | Internal Port |
|---------|--------------|------------------|---------------|---------------|
| Tenant Management Service<br>(tenant-mgmt-service) | MongoDB | tenant_registry | 8501 | 8501 |
| User Data Service<br>(user-data-service) | PostgreSQL | system_users | 8502 | 8502 |
| Task Repository Service<br>(task-repo-service) | MongoDB | task_repository | 8503 | 8503 |
| Category Repository Service<br>(category-repository-service) | MongoDB | category_repository | 8504 | 8080 |
| Management System Repository<br>(management-system-repo) | PostgreSQL & MongoDB | management_system_repository & config_db | 8505 | 8080 |
| Vector Store Service<br>(vector-store-service) | MongoDB & Filesystem | vector_store_system | 8510 | 8510 |

### Database Servers

| Server | Type | Port | Description | Used By |
|--------|------|------|-------------|---------|
| mongodb-system | MongoDB | 27018 | System-wide MongoDB | All MongoDB-based services |
| postgres-system | PostgreSQL | 5432 | System-wide PostgreSQL | All PostgreSQL-based services |
| pgbouncer | Connection Pooling | 6432 | PostgreSQL connection pooling | PostgreSQL clients |
| mongodb-tenant | MongoDB | 27017 | Multi-tenant MongoDB | Tenant-specific storage |
| redis-cache | Redis | 6379 | Caching and messaging | All services |

### Standardized Environment Variables

All database services follow these environment variable patterns:

| Variable Pattern | Description | Example |
|------------------|-------------|---------|
| SERVICE_NAME | Service identifier | `tenant-mgmt-service` |
| HOST / *_HOST | Host binding | `0.0.0.0` |
| PORT / *_PORT | Port binding | `8501` |
| *_DB_* | Database connection | `MONGODB_URI`, `USER_DB_HOST` |
| API_KEY | Authentication | `dev_api_key` |
| *_LOG_LEVEL | Logging configuration | `INFO` |

## Key Architecture Concepts

### Multi-Tenancy Approach

The PrismicX platform implements multi-tenancy using a hybrid approach:

1. **PostgreSQL Multi-Tenancy**
   - Schema-based isolation for tenant-specific data
   - Row-level security for shared tables
   - Tenant context maintained via session variables

2. **MongoDB Multi-Tenancy**
   - Database-level isolation for tenant-specific data
   - Collection-level filtering for shared collections
   - Tenant-specific databases for high-value customers

### Database Technology Selection

The platform uses multiple database technologies to meet different needs:

1. **PostgreSQL**
   - Used for structured data with complex relationships
   - Primary database for user management, management system repository, and system data
   - Supports ACID transactions and complex queries

2. **MongoDB**
   - Used for semi-structured and dynamic data
   - Primary database for tenant registry, user insights, and task management
   - Supports flexible schema evolution and high write throughput

## Setting Up the Database Layer

To set up the database layer locally:

1. Ensure Docker and Docker Compose are installed
2. Navigate to the `database-layer` directory
3. Run `docker-compose up -d` to start all database services
4. Run initialization scripts from the `init-scripts` directory

## Generating Documentation

### Diagrams

To generate the ER diagrams and architecture diagrams:

1. Navigate to the `database-layer/docs/diagrams` directory
2. Run `./generate-diagrams.sh` to generate PNG files from PlantUML sources
3. View the generated diagrams in the same directory

## Best Practices

### Schema Design

1. Always include tenant_id in all tables/collections that store tenant-specific data
2. Use UUIDs for primary keys in PostgreSQL tables
3. Maintain created_at and updated_at timestamps for all records
4. Use JSONB for extensible attributes in PostgreSQL
5. Design MongoDB schemas with proper indexing for tenant-based queries

### Data Access

1. Always establish tenant context before performing operations
2. Use connection pooling for database connections
3. Handle connection errors with proper retries and backoff
4. Use transactions for operations that modify multiple records
5. Follow the patterns documented in [Database Access Patterns](patterns/database-access-patterns.md)

## Contributing to Documentation

To update this documentation:

1. Make changes to the relevant Markdown files
2. Update PlantUML diagrams if database schema changes
3. Run `./generate-diagrams.sh` to regenerate diagrams
4. Submit a pull request with your changes

---

For questions or feedback about the database layer documentation, please contact the Database Team. 