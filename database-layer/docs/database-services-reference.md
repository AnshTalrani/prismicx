# Database Services Reference

*Documentation Version: 1.0 - Last Updated: 2023*

## Overview

This document provides a comprehensive reference for all database services in the PrismicX platform. It details which services manage which databases, how to interact with them, available APIs, and best practices.

## Database Architecture

The PrismicX platform employs a microservices-based database layer with multiple specialized database services. Each service is responsible for managing specific types of data and providing access to other services through well-defined APIs.

### Database Technology Selection

The platform uses multiple database technologies to meet different needs:

1. **PostgreSQL**
   - Used for structured data with complex relationships
   - Supports ACID transactions and complex queries
   - Implements schema-based tenant isolation

2. **MongoDB**
   - Used for semi-structured and dynamic data
   - Supports flexible schema evolution and high write throughput
   - Implements database-level tenant isolation

3. **Redis**
   - Used for caching and messaging
   - Provides fast in-memory operations for temporary data
   - Supports pub/sub for service communication

## Database Services Overview

| Service | Database Type | Primary Database | External Port | Internal Port | Purpose |
|---------|--------------|------------------|---------------|---------------|---------|
| Tenant Management Service | MongoDB | tenant_registry | 8501 | 8501 | Multi-tenant database routing and provisioning |
| User Data Service | PostgreSQL & MongoDB | system_users, user_insights, user_extensions | 8502 | 8502 | Centralized access to system-wide user data |
| Task Repository Service | MongoDB | task_repository | 8503 | 8503 | Centralized task management |
| Category Repository Service | MongoDB | category_repository | 8504 | 8080 | Centralized category management |
| Management System Repository | PostgreSQL & MongoDB | management_system_repository & config_db | 8505 | 8080 | Management systems data |

## Database Infrastructure

### MongoDB System Database (mongodb-system)
- **Purpose**: System-wide MongoDB for tenant registry and shared data
- **Data Stored**: Configuration data, tenant information, tasks, categories
- **Connection Details**:
  - Host: mongodb-system
  - Port: 27017
  - Authentication: Username/password based
- **Used By**:
  - Tenant Management Service (tenant_registry database)
  - Task Repository Service (task_repository database)
  - Category Repository Service (category_repository database)
  - Management System Repository (config_db database)
  - User Data Service (user_insights database)

### PostgreSQL System Database (postgres-system)
- **Purpose**: System-wide PostgreSQL for structured data
- **Data Stored**: User data, structured management system data
- **Connection Details**:
  - Host: postgres-system
  - Port: 5432
  - Authentication: Username/password based
- **Connection Pooling**: Uses pgbouncer for PostgreSQL connection pooling
  - Host: pgbouncer
  - Port: 6432
- **Used By**:
  - User Data Service (system_users database, user_extensions database)
  - Management System Repository (management_system_repository database)

### MongoDB Tenant Database (mongodb-tenant)
- **Purpose**: Multi-tenant MongoDB for service-specific tenant data
- **Data Stored**: Tenant-specific data
- **Connection Details**:
  - Host: mongodb-tenant
  - Port: 27017
  - Authentication: Username/password based
  - Replica Set: rs0

### Redis Cache (redis-cache)
- **Purpose**: Caching and messaging
- **Data Stored**: Cached data, session information, queues
- **Connection Details**:
  - Host: redis-cache
  - Port: 6379
  - Authentication: Password-based

## Detailed Service Reference

### Tenant Management Service (tenant-mgmt-service)

#### Overview
The Tenant Management Service provides centralized management of tenants and their database configurations. It's the entry point for multi-tenant database routing and provisioning.

#### Technical Details
- **Service Port**: 8501 (external and internal)
- **Database Technology**: MongoDB
- **Database Name**: tenant_registry
- **Docker Container**: tenant-mgmt-service

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/tenants` | GET | List all tenants |
| `/api/v1/tenants/{tenant_id}` | GET | Get tenant details |
| `/api/v1/tenants` | POST | Create a new tenant |
| `/api/v1/tenants/{tenant_id}` | PUT | Update tenant details |
| `/api/v1/tenants/{tenant_id}` | DELETE | Delete a tenant |
| `/api/v1/tenants/{tenant_id}/databases` | GET | Get tenant database config |
| `/api/v1/databases` | GET | List all tenant databases |
| `/api/v1/databases` | POST | Create a new tenant database |

#### Client Usage
```python
import httpx

async def get_tenant_info(tenant_id):
    """Get tenant information from Tenant Management Service."""
    url = f"http://tenant-mgmt-service:8501/api/v1/tenants/{tenant_id}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json() if response.status_code == 200 else None
```

#### Environment Variables
```
# MongoDB connection
TENANT_MONGODB_URI=mongodb://admin:password@mongodb:27017
TENANT_REGISTRY_DB=tenant_registry

# Service configuration
TENANT_SERVICE_HOST=0.0.0.0  # Host binding
TENANT_SERVICE_PORT=8501     # Port binding
TENANT_SERVICE_LOG_LEVEL=INFO
SERVICE_NAME=tenant-mgmt-service  # Standard service name
```

### User Data Service (user-data-service)

#### Overview
The User Data Service provides centralized access to system-wide user data, including authentication, authorization, user profiles, user insights, and user extensions.

#### Technical Details
- **Service Port**: 8502 (external and internal)
- **Database Technologies**:
  - PostgreSQL: For structured user data and extensions
  - MongoDB: For semi-structured user insights
- **Database Names**:
  - PostgreSQL: system_users (core user data), user_extensions (user extension data)
  - MongoDB: user_insights (user insight data)
- **Docker Container**: user-data-service

#### Data Distribution
- **PostgreSQL system_users database** stores:
  - User authentication data
  - User profiles and core attributes
  - Tenant user assignments
- **PostgreSQL user_extensions database** stores:
  - User extensions configuration
  - Extension metrics and usage data
  - Practicality factors for extensions
- **MongoDB user_insights database** stores:
  - User insights with topics and subtopics
  - Knowledge structure for users
  - Tenant-specific collections for insights

#### Database Tables and Collections
The User Data Service manages the following databases and collections:

- **PostgreSQL system_users database**:
  - `user_data.users`: Core user information (authentication, profiles)
  - `user_preferences.preferences`: User preferences

- **PostgreSQL user_extensions database**:
  - `user_extensions.extensions`: User extension data
  - `user_extensions.extension_metrics`: Extension usage metrics
  - `user_extensions.practicality_factors`: Extension practicality factors

- **MongoDB user_insights database**:
  - `insights_{tenant_id}`: User insights with topics and subtopics

- **MongoDB system_users database**:
  - `system_users_conversation_{tenant_id}`: Conversation data for system users
  - Interfaces with core system_users database in PostgreSQL
  - Long-term storage with no automatic expiration

- **MongoDB campaign_users database** (New):
  - `campaign_{campaign_id}`: Campaign participants context data
  - Temporary storage with configurable TTL (default: 90 days)
  - Automatic expiration using MongoDB TTL indexes

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/users` | GET | List users |
| `/api/v1/users/{user_id}` | GET | Get user details |
| `/api/v1/users` | POST | Create a new user |
| `/api/v1/users/{user_id}` | PUT | Update user details |
| `/api/v1/users/{user_id}` | DELETE | Delete a user |
| `/api/v1/auth/login` | POST | User login |
| `/api/v1/auth/logout` | POST | User logout |
| `/api/v1/auth/refresh` | POST | Refresh token |
| `/api/v1/insights/{user_id}` | GET | Get user insights |
| `/api/v1/insights/{user_id}` | POST | Create user insights |
| `/api/v1/insights/{user_id}/topics` | GET | Get user topics |
| `/api/v1/extensions/{user_id}` | GET | Get user extensions |
| `/api/v1/extensions/{user_id}` | POST | Create user extension |
| `/api/v1/extensions/{user_id}/{extension_id}` | PUT | Update user extension |
| `/api/v1/user_context/{user_id}` | GET | Get user context data for a specific user |
| `/api/v1/user_context/system` | POST | Create/update system user context |
| `/api/v1/user_context/campaign` | POST | Create/update campaign user context |
| `/api/v1/user_context/{user_id}` | PUT | Update user context metadata |
| `/api/v1/user_context/{user_id}` | DELETE | Delete user context |
| `/api/v1/user_context/migrate` | POST | Migrate a user from the campaign repository to the system repository |
| `/api/v1/user_context/campaign/{campaign_id}` | GET | List campaign users |
| `/api/v1/user_context/system/{tenant_id}` | GET | List system users |
| `/api/v1/user_context/campaign/{campaign_id}/user/{user_id}/ttl` | PUT | Update campaign user TTL |

#### Client Usage
```python
import httpx

async def get_user_info(user_id, auth_token):
    """Get user information from User Data Service."""
    url = f"http://user-data-service:8502/api/v1/users/{user_id}"
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        return response.json() if response.status_code == 200 else None

async def get_user_insights(user_id, tenant_id, auth_token):
    """Get user insights from User Data Service."""
    url = f"http://user-data-service:8502/api/v1/insights/{user_id}"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "X-Tenant-ID": tenant_id
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        return response.json() if response.status_code == 200 else None

async def get_user_context(user_id, campaign_id=None, tenant_id=None):
    """Get user context from User Data Service."""
    url = f"http://user-data-service:8502/api/v1/user_context/{user_id}"
    params = {}
    if campaign_id:
        params["campaign_id"] = campaign_id
    if tenant_id:
        params["tenant_id"] = tenant_id
        
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json() if response.status_code == 200 else None

async def migrate_user(user_id, campaign_id, tenant_id):
    """Migrate a user from the campaign repository to the system repository."""
    url = "http://user-data-service:8502/api/v1/user_context/migrate"
    data = {
        "user_id": user_id,
        "campaign_id": campaign_id,
        "tenant_id": tenant_id
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.status_code == 200
```

#### Environment Variables
```
# PostgreSQL user data connection
USER_DB_HOST=postgres-system
USER_DB_PORT=5432
USER_DB_USER=user_service
USER_DB_PASSWORD=password
USER_DB_NAME=system_users

# PostgreSQL extensions connection
POSTGRES_URI=postgresql://extension_service:password@postgres-system:5432/user_extensions

# MongoDB insights connection
MONGODB_URI=mongodb://user_insights_service:password@mongodb-system:27017/user_insights

# Service configuration
USER_SERVICE_HOST=0.0.0.0  # Host binding
USER_SERVICE_PORT=8502     # Port binding 
USER_SERVICE_LOG_LEVEL=INFO
SERVICE_NAME=user-data-service  # Standard service name
```

### Task Repository Service (task-repo-service)

#### Overview
The Task Repository Service provides a centralized system for managing tasks in the PrismicX microservices architecture. It enables efficient coordination between different system components.

#### Technical Details
- **Service Port**: 8503 (external and internal)
- **Database Technology**: MongoDB
- **Database Name**: task_repository
- **Docker Container**: task-repo-service

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/tasks` | POST | Create a new task |
| `/api/v1/tasks/{task_id}` | GET | Get a task by ID |
| `/api/v1/tasks/{task_id}` | PUT | Update a task |
| `/api/v1/tasks/{task_id}` | DELETE | Delete a task |
| `/api/v1/tasks` | GET | Get pending tasks for processing |
| `/api/v1/tasks/{task_id}/claim` | POST | Claim a task for processing |
| `/api/v1/tasks/{task_id}/complete` | POST | Mark a task as completed |
| `/api/v1/tasks/{task_id}/fail` | POST | Mark a task as failed |
| `/health` | GET | Health check endpoint |

#### Client Usage
```python
from database_layer.common.task_client import (
    create_task,
    get_pending_tasks,
    claim_task,
    complete_task,
    fail_task
)

# Create a task
task_id = await create_task({
    "task_type": "GENERATIVE",
    "request": {
        "content": {"text": "Generate a response to this query"},
        "metadata": {"user_id": "user123"}
    },
    "template": {
        "service_type": "GENERATIVE",
        "parameters": {"model": "gpt-4", "max_tokens": 1024}
    },
    "tags": {
        "service": "generative-service",
        "source": "agent-api"
    }
})
```

#### Environment Variables
```
# MongoDB connection
MONGODB_URI=mongodb://task_service:password@mongodb-system:27017/task_repository
MONGODB_DATABASE=task_repository
MONGODB_TASKS_COLLECTION=tasks

# Service configuration
HOST=0.0.0.0  # Host binding
PORT=8503     # Port binding
API_KEY=dev_api_key
SERVICE_NAME=task-repo-service  # Standard service name
```

### Category Repository Service (category-repository-service)

#### Overview
The Category Repository Service provides centralized management of categories, factors, campaigns, and entity assignments.

#### Technical Details
- **Service Port**: 8504 (external) / 8080 (internal)
- **Database Technology**: MongoDB
- **Database Name**: category_repository
- **Docker Container**: category-repository-service

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/categories` | GET | List categories |
| `/api/v1/categories/{category_id}` | GET | Get category details |
| `/api/v1/categories` | POST | Create a new category |
| `/api/v1/categories/{category_id}` | PUT | Update category |
| `/api/v1/factors` | GET | List factors |
| `/api/v1/campaigns` | GET | List campaigns |
| `/api/v1/entity-assignments` | GET | List entity assignments |
| `/health` | GET | Health check endpoint |

#### Client Usage
```python
import httpx

async def get_categories(auth_token):
    """Get categories from Category Repository Service."""
    url = "http://category-repository-service:8504/api/v1/categories"
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        return response.json() if response.status_code == 200 else None
```

#### Environment Variables
```
# MongoDB connection
MONGODB_URI=mongodb://category_service:password@mongodb-system:27017/category_repository
MONGODB_DATABASE=category_repository
MONGODB_CATEGORIES_COLLECTION=categories
MONGODB_FACTORS_COLLECTION=factors
MONGODB_CAMPAIGNS_COLLECTION=campaigns
MONGODB_BATCH_AS_OBJECTS_COLLECTION=batch_as_objects
MONGODB_ENTITY_ASSIGNMENTS_COLLECTION=entity_assignments

# Service configuration
HOST=0.0.0.0       # Host binding
PORT=8080          # Internal port binding
API_KEY=dev_api_key
SERVICE_NAME=category-repository-service  # Standard service name
MAX_PAGE_SIZE=100

# Note: This service has an external port (8504) mapping to an internal port (8080)
```

### Management System Repository (management-system-repo)

#### Overview
The Management System Repository provides centralized management systems data using both PostgreSQL and MongoDB for different types of data.

#### Technical Details
- **Service Port**: 8505 (external) / 8080 (internal)
- **Database Technologies**: 
  - PostgreSQL: For structured relational data
  - MongoDB: For flexible configuration data
- **Database Names**: 
  - PostgreSQL: management_system_repository
  - MongoDB: config_db
- **Docker Container**: management-system-repo

#### Data Distribution
- **PostgreSQL Database** stores:
  - Management systems metadata
  - System versions
  - Tenant system assignments
  - Schema migrations
- **MongoDB Database** stores:
  - Flexible system configurations
  - UI settings
  - Feature configurations
  - Integration settings

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/systems` | GET | List all management systems |
| `/api/v1/systems/{system_id}` | GET | Get system details |
| `/api/v1/systems` | POST | Create a new system |
| `/api/v1/systems/{system_id}` | PUT | Update system details |
| `/api/v1/systems/{system_id}/config` | GET | Get system configuration |
| `/api/v1/systems/{system_id}/config` | PUT | Update system configuration |
| `/health` | GET | Health check endpoint |

#### Client Usage
```python
import httpx

async def get_system_config(system_id, auth_token):
    """Get system configuration from Management System Repository."""
    url = f"http://management-system-repo:8505/api/v1/systems/{system_id}/config"
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        return response.json() if response.status_code == 200 else None
```

#### Environment Variables
```
# PostgreSQL settings for system repo
SYSTEM_DB_HOST=postgres-system
SYSTEM_DB_PORT=5432
SYSTEM_DB_USER=postgres
SYSTEM_DB_PASSWORD=password
SYSTEM_DB_NAME=management_system_repository

# MongoDB settings for config_db
CONFIG_DB_HOST=mongodb-system
CONFIG_DB_PORT=27017
CONFIG_DB_USER=admin
CONFIG_DB_PASSWORD=password
CONFIG_DB_NAME=config_db

# Service configuration
HOST=0.0.0.0       # Host binding
PORT=8080          # Internal port binding
API_KEY=dev_api_key
SERVICE_NAME=management-system-repo  # Standard service name

# Note: This service has an external port (8505) mapping to an internal port (8080)
```

## Common Access Patterns

### Multi-Tenant Context

All services should maintain tenant context when accessing tenant-specific data:

```python
# Setting tenant context
async def with_tenant_context(tenant_id, func, *args, **kwargs):
    """Execute a function with a tenant context."""
    # Set tenant context
    TenantContext.set_current_tenant(tenant_id)
    try:
        # Execute function within tenant context
        return await func(*args, **kwargs)
    finally:
        # Clear tenant context
        TenantContext.clear()
```

### Database Connection Management

Always use connection pooling and proper connection management:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_connection(service, tenant_id=None):
    """Get a database connection for a service, optionally with tenant context."""
    pool = await get_connection_pool(service)
    async with pool.acquire() as conn:
        if tenant_id:
            # Set tenant context for this connection
            await conn.execute(f"SET app.current_tenant = '{tenant_id}'")
        try:
            yield conn
        finally:
            if tenant_id:
                # Clear tenant context
                await conn.execute("RESET app.current_tenant")
```

## Authentication and Authorization

### API Authentication

All database services use API key authentication for service-to-service communication:

```python
def get_auth_headers():
    """Get authentication headers for service-to-service communication."""
    return {
        "X-API-Key": os.environ.get("SERVICE_API_KEY", "dev_api_key")
    }
```

### Database Authentication

Database connections use username/password authentication:

```python
# MongoDB connection string
mongodb_uri = f"mongodb://{username}:{password}@{host}:{port}/{database}"

# PostgreSQL connection string
postgres_uri = f"postgresql://{username}:{password}@{host}:{port}/{database}"
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if the database service is running
   - Verify network connectivity between services
   - Ensure correct port is being used

2. **Authentication Failure**
   - Verify credentials in environment variables
   - Check that the database user exists and has correct permissions

3. **Tenant Not Found**
   - Verify tenant ID is correct
   - Check if tenant exists in Tenant Management Service
   - Ensure tenant is properly provisioned

### Logging and Monitoring

All database services log to standard output with configurable log levels. To diagnose issues:

1. Check service logs:
   ```bash
   docker logs tenant-mgmt-service
   ```

2. Enable debug logging by setting the environment variable:
   ```
   *_SERVICE_LOG_LEVEL=DEBUG
   ```

3. Monitor database metrics using Prometheus exporters:
   - MongoDB Exporter: http://mongodb-exporter:9216/metrics
   - PostgreSQL Exporter: http://postgres-exporter:9187/metrics
   - Redis Exporter: http://redis-exporter:9121/metrics

## Best Practices

1. **Always establish tenant context** before performing operations on tenant-specific data
2. **Use connection pooling** for all database connections
3. **Handle connection errors** with proper retries and backoff
4. **Use transactions** for operations that modify multiple records
5. **Include proper indices** for tenant-filtered queries
6. **Cache frequently accessed data** using Redis
7. **Implement rate limiting** to prevent database overload
8. **Follow the principle of least privilege** when creating database users
9. **Use prepared statements** to prevent SQL injection (for PostgreSQL)
10. **Implement proper error handling** and report database errors correctly

## Migration Strategies

When migrating between database versions or schemas:

1. **Use versioned migrations** to track schema changes
2. **Implement backward compatibility** for critical services
3. **Test migrations** thoroughly in staging environments
4. **Schedule migrations** during low-usage periods
5. **Have a rollback plan** for failed migrations

---

*For questions or feedback about this database services reference, please contact the Database Team.* 