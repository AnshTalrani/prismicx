# Database Access Patterns

*Documentation Version: 1.0 - Last Updated: 2023*

This document outlines common database access patterns in the PrismicX platform for both PostgreSQL and MongoDB databases. These patterns should be followed by all microservices to ensure consistent and secure data access.

## Table of Contents

1. [Introduction](#introduction)
2. [Accessing PostgreSQL Data](#accessing-postgresql-data)
3. [Accessing MongoDB Data](#accessing-mongodb-data)
4. [Multi-Tenant Operations](#multi-tenant-operations)
5. [Transaction Management](#transaction-management)
6. [Error Handling](#error-handling)

## Introduction

The PrismicX platform uses a multi-database, multi-tenant architecture. Proper database access patterns are essential for maintaining data integrity, security, and performance. This document provides examples and best practices for accessing data in various databases.

## Accessing PostgreSQL Data

### Connection Management

All PostgreSQL connections should be managed through the `DatabaseClient` class:

```python
from database.db_client import DatabaseClient

# Initialize client
db_client = DatabaseClient(
    host=config.DB_HOST,
    port=config.DB_PORT,
    user=config.DB_USER,
    password=config.DB_PASSWORD,
    database=config.DB_NAME,
    min_pool_size=5,
    max_pool_size=20
)

# Initialize connection pool
await db_client.initialize()

# Always close connections when done
await db_client.close()
```

### Setting Tenant Context

For operations in shared tables with row-level security, always set the tenant context:

```python
async with db_client.session() as session:
    # Set tenant context
    await session.execute(
        text("SET app.current_tenant_id = :tenant_id"),
        {"tenant_id": tenant_id}
    )
    
    # Perform operations
    # ...
```

### Using SQLAlchemy ORM

For standard CRUD operations, use SQLAlchemy ORM models:

```python
from sqlalchemy import select
from models.user_model import User

async def get_user_by_id(db_client, user_id, tenant_id):
    async with db_client.session() as session:
        # Set tenant context
        await session.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        )
        
        # Query using ORM
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalars().first()
        
        return user
```

### Accessing Tenant-Specific Schemas

For plugin data in tenant-specific schemas:

```python
async def get_tenant_crm_data(db_client, tenant_id, customer_id):
    # Construct schema name based on tenant
    schema_name = f"tenant_{tenant_id}_crm"
    
    async with db_client.session() as session:
        # Use raw SQL to access dynamic schema
        query = text(f"""
            SELECT * FROM {schema_name}.customers 
            WHERE id = :customer_id
        """)
        
        result = await session.execute(query, {"customer_id": customer_id})
        return result.mappings().first()
```

## Accessing MongoDB Data

### Connection Management

All MongoDB connections should be managed through the `MongoDBClient` class:

```python
from database.mongo_client import MongoDBClient

# Initialize client
mongo_client = MongoDBClient(
    connection_string=config.MONGODB_URI,
    database_name=config.MONGODB_DATABASE
)

# Connect to the database
await mongo_client.connect()

# Always close connections when done
await mongo_client.close()
```

### Tenant-Specific Database Access

For tenant-specific MongoDB databases:

```python
async def get_user_insights(mongo_client, tenant_id, user_id):
    # Switch to tenant-specific database
    tenant_db = mongo_client.client[f"tenant_{tenant_id}_db"]
    
    # Access collection
    insights_collection = tenant_db["user_insights"]
    
    # Query data
    user_insight = await insights_collection.find_one({"user_id": user_id})
    
    return user_insight
```

### Multi-Tenant Collection Access

For shared collections with tenant filtering:

```python
async def get_tenant_tasks(mongo_client, tenant_id):
    # Use shared database
    tasks_collection = mongo_client.db["tasks"]
    
    # Query with tenant filter
    cursor = tasks_collection.find({"tenant_id": tenant_id})
    
    # Convert cursor to list
    tasks = await cursor.to_list(length=100)
    
    return tasks
```

## Multi-Tenant Operations

### Creating a New Tenant

The process of creating a new tenant involves multiple databases:

```python
async def create_tenant(tenant_name, region, tier):
    # Generate tenant ID
    tenant_id = f"tenant-{uuid4().hex[:8]}"
    
    # 1. Register tenant in Tenant Registry (MongoDB)
    tenant_data = {
        "tenant_id": tenant_id,
        "name": tenant_name,
        "database_config": {
            "type": "shared",
            "connection_string": config.SHARED_DB_CONNECTION,
            "database_name": f"tenant_{tenant_id}_db"
        },
        "status": "provisioning",
        "created_at": datetime.utcnow(),
        "tier": tier,
        "region": region
    }
    
    await tenant_registry_client.db.tenants.insert_one(tenant_data)
    
    # 2. Create PostgreSQL schema for tenant
    async with pg_client.session() as session:
        # Create schemas for each plugin type
        for plugin_type in ["crm", "sales", "marketing"]:
            schema_name = f"tenant_{tenant_id}_{plugin_type}"
            await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        
        await session.commit()
    
    # 3. Create MongoDB database for tenant
    mongo_admin_client = MongoDBClient(connection_string=config.MONGO_ADMIN_URI)
    await mongo_admin_client.connect()
    
    # Create user insights database
    tenant_db_name = f"tenant_{tenant_id}_db"
    tenant_db = mongo_admin_client.client[tenant_db_name]
    
    # Create collections
    await tenant_db.create_collection("user_insights")
    
    # Create indexes
    await tenant_db.user_insights.create_index("user_id", unique=True)
    await tenant_db.user_insights.create_index("topics.name")
    await tenant_db.user_insights.create_index("updated_at")
    
    await mongo_admin_client.close()
    
    # 4. Update tenant status
    await tenant_registry_client.db.tenants.update_one(
        {"tenant_id": tenant_id},
        {"$set": {"status": "active"}}
    )
    
    return tenant_id
```

### Installing a Plugin for a Tenant

Example of installing a plugin for a tenant, which involves setting up schema:

```python
async def install_plugin_for_tenant(plugin_id, version_id, tenant_id):
    # 1. Get plugin and version information
    plugin = await plugin_repository.get_plugin(plugin_id)
    version = await plugin_repository.get_plugin_version(version_id)
    
    if not plugin or not version:
        raise ValueError("Plugin or version not found")
    
    # 2. Record plugin installation for tenant
    tenant_plugin = {
        "tenant_id": tenant_id,
        "plugin_id": plugin_id,
        "version_id": version_id,
        "status": "installing",
        "configurations": {},
        "features_enabled": []
    }
    
    await plugin_repository.install_tenant_plugin(tenant_plugin)
    
    try:
        # 3. Get schema migration script
        schema_migrations = await plugin_repository.get_schema_migrations(plugin_id)
        migration = next((m for m in schema_migrations if m.version_to == version.version), None)
        
        if migration:
            # 4. Execute schema migration
            schema_name = f"tenant_{tenant_id}_{plugin.type}"
            
            async with pg_client.session() as session:
                # Create schema if it doesn't exist
                await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                
                # Execute migration SQL
                migration_sql = migration.migration_sql.replace("${schema}", schema_name)
                await session.execute(text(migration_sql))
                
                await session.commit()
        
        # 5. Update installation status
        await plugin_repository.update_tenant_plugin(
            tenant_id, 
            plugin_id, 
            {"status": "active"}
        )
        
        return True
    
    except Exception as e:
        # Handle error and update status
        await plugin_repository.update_tenant_plugin(
            tenant_id,
            plugin_id,
            {"status": "failed", "error_message": str(e)}
        )
        
        return False
```

## Transaction Management

### PostgreSQL Transactions

```python
async def transfer_data_with_transaction(db_client, source_id, target_id, amount):
    async with db_client.session() as session:
        # Start transaction
        async with session.begin():
            # Multiple operations in a single transaction
            
            # Update source
            await session.execute(
                text("UPDATE accounts SET balance = balance - :amount WHERE id = :id"),
                {"amount": amount, "id": source_id}
            )
            
            # Update target
            await session.execute(
                text("UPDATE accounts SET balance = balance + :amount WHERE id = :id"),
                {"amount": amount, "id": target_id}
            )
            
            # Transaction automatically commits or rolls back
```

### MongoDB Transactions

MongoDB transactions should be used for operations that require atomicity across multiple documents:

```python
async def update_categories_with_transaction(mongo_client, tenant_id, updates):
    # Get session
    async with await mongo_client.client.start_session() as session:
        # Start transaction
        async with session.start_transaction():
            collection = mongo_client.db.categories
            
            # Perform multiple operations
            for update in updates:
                await collection.update_one(
                    {"category_id": update["id"], "tenant_id": tenant_id},
                    {"$set": update["data"]},
                    session=session
                )
                
            # Transaction automatically commits or aborts
```

## Error Handling

### Connection Errors

Handle database connection errors gracefully:

```python
async def get_data_with_retry(db_client, query_func, max_retries=3):
    retries = 0
    
    while retries < max_retries:
        try:
            # Attempt to execute the query function
            return await query_func(db_client)
            
        except ConnectionError as e:
            retries += 1
            
            if retries >= max_retries:
                # Log the error and raise after max retries
                logging.error(f"Database connection failed after {max_retries} attempts: {e}")
                raise
                
            # Wait before retrying (exponential backoff)
            wait_time = 0.5 * (2 ** retries)
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            # Log and re-raise other exceptions
            logging.error(f"Database error: {e}")
            raise
```

### Tenant Context Errors

Handle tenant context setting errors:

```python
async def execute_with_tenant_context(db_client, tenant_id, query_func):
    async with db_client.session() as session:
        try:
            # Set tenant context
            await session.execute(
                text("SET app.current_tenant_id = :tenant_id"),
                {"tenant_id": tenant_id}
            )
            
            # Execute query function with session
            return await query_func(session)
            
        except Exception as e:
            # Check if it's a tenant context error
            if "invalid tenant context" in str(e).lower():
                logging.error(f"Invalid tenant context for tenant ID {tenant_id}")
                raise ValueError(f"Invalid tenant ID: {tenant_id}")
            
            # Re-raise other exceptions
            raise
```

---

By following these database access patterns, microservices can maintain consistency in how they interact with different databases while ensuring proper multi-tenancy, security, and error handling.

For database schema details, refer to the [Database Schema Reference](../schema/database-schema-reference.md) document. 