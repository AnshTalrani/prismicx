# Architecture Documentation

This directory contains documentation about the architecture of the Management Systems microservice.

## Overview

The Management Systems microservice follows the MACH architecture principles:

- **Microservices-based**: Focused solely on management systems functionality
- **API-first**: All functionality is available through REST APIs
- **Cloud-native**: Designed to run in containerized environments
- **Headless**: Provides pure data functionality without UI concerns

## System Architecture

### Core Components

1. **API Layer**:
   - REST API endpoints
   - Authentication and authorization
   - Request validation

2. **Service Layer**:
   - Business logic
   - Data processing
   - Integration with other services

3. **Data Layer**:
   - Database abstraction
   - Data access
   - Schema management

4. **Plugin System**:
   - Extensibility
   - Custom behavior
   - Integrations

### Database Architecture

The service uses a multi-tenant database architecture through database layer services:

1. **Management System Repository Service**:
   - Provides access to system definitions and templates
   - Stores tenant-specific system instances
   - Handles configuration storage
   - Accessed via HTTP API calls through client objects

2. **Tenant-Specific Data**:
   - Stored in tenant-specific databases
   - Accessed via database layer services
   - Strong isolation between tenants

### Multi-tenancy

The service implements multi-tenancy through:

1. **Tenant Middleware**:
   - Extracts tenant ID from requests
   - Sets tenant context
   - Ensures proper isolation

2. **Schema Namespacing**:
   - Each tenant gets its own schema
   - Schema creation is automated
   - Alembic migrations support tenant schemas

3. **Tenant Config**:
   - Tenant-specific configurations
   - Stored in the configuration database
   - Accessible through the Configuration API

## Component Relationships

```
                         ┌────────────────────┐
                         │    API Gateway     │
                         └────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────┐
│              Management Systems Microservice            │
│                                                         │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   │
│  │  API Layer  │──▶│  Services   │──▶│  DB Clients │   │
│  └─────────────┘   └─────────────┘   └─────────────┘   │
│                                             │           │
└─────────────────────────────────────────────┼───────────┘
                                              │
                                              ▼
                           ┌───────────────────────────────┐
                           │     Database Layer Services   │
                           │  ┌──────────────┐ ┌─────────┐ │
                           │  │System Repo   │ │Tenant DB│ │
                           │  │Service       │ │Service  │ │
                           │  └──────────────┘ └─────────┘ │
                           └───────────────────────────────┘
                                        │
                                        ▼
                           ┌───────────────────────────────┐
                           │     Databases                 │
                           │  ┌────────────┐ ┌──────────┐  │
                           │  │ Config DB  │ │Tenant DBs│  │
                           │  └────────────┘ └──────────┘  │
                           └───────────────────────────────┘
```

## Key Design Decisions

1. **MACH Architecture**:
   - Microservices-based design
   - API-first approach for all functionality
   - Cloud-native with containerization
   - Headless design separating backend from UI concerns

2. **Database Layer Integration**:
   - No direct database connections
   - All database operations through HTTP API calls
   - Clear separation of concerns
   - Improved security and maintainability

3. **Plugin Architecture**:
   - Enables extensibility
   - Allows customization without changing core code
   - Supports tenant-specific behavior

4. **Tenant Isolation**:
   - Strong boundaries between tenant data
   - Authorization checks at the API level
   - Schema-level isolation in the database

5. **Caching Strategy**:
   - Redis for shared caching
   - Cache invalidation on data changes
   - Tiered TTL values based on data type

## Technology Stack

- **FastAPI**: Web framework for API endpoints
- **MongoDB**: Document database for flexible data storage (accessed via database layer)
- **Redis**: Caching and pub/sub messaging
- **Docker/Docker Compose**: Containerization
- **HTTPX**: Asynchronous HTTP client library for database layer communication

## Integration Points

1. **External APIs**:
   - REST API endpoints
   - OAuth2 authentication

2. **Database Layer**:
   - HTTP API clients for database access
   - Standardized request/response formats

3. **Event Bus**:
   - Message publishing for system events
   - Subscription for relevant external events

## Further Reading

- [System Synchronization and User Experience](./system-sync-and-user-experience.md)
- [Automation Architecture](./automation-architecture.md)
- [Deployment Architecture](./deployment.md)
- [Security Architecture](./security.md)
- [Data Model](./data-model.md) 