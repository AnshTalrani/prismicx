# PostgreSQL Configuration Module

## Overview

This module provides a standardized way to configure PostgreSQL database connections across all microservices in the MACH architecture. It follows the project's multi-tenant design principles and provides a clean interface for accessing database configuration settings.

## Features

- Centralized configuration for PostgreSQL connections
- Environment variable support with sensible defaults
- Service-specific prefixing for environment variables
- Support for connection pooling configuration
- SSL/TLS configuration options
- Multi-tenant awareness settings
- Helper methods for connection string and parameter generation

## Installation

This module is part of the `database-layer/common` package and can be imported directly into any microservice that requires PostgreSQL connectivity.

## Usage

### Basic Usage

```python
from database_layer.common.db_config import postgres_config

# Get a connection string
conn_string = postgres_config.get_connection_string()
# 'postgresql://postgres:password@postgres-system:5432/database'

# Get connection parameters for asyncpg
conn_params = postgres_config.get_connection_params()
pool = await asyncpg.create_pool(**conn_params)
```

### Service-Specific Configuration

You can get service-specific settings by providing the service name:

```python
# For a 'marketing' service, looks for MARKETING_PG_* environment variables
marketing_settings = postgres_config.get_settings('marketing')
marketing_conn_string = postgres_config.get_connection_string('marketing')
```

### Environment Variables

The module uses the following environment variables (with optional service-specific prefixing):

| Environment Variable | Default Value | Description |
|----------------------|---------------|-------------|
| PG_HOST | postgres-system | PostgreSQL host |
| PG_PORT | 5432 | PostgreSQL port |
| PG_USER | postgres | PostgreSQL username |
| PG_PASSWORD | *Required* | PostgreSQL password |
| PG_DATABASE | *Required* | PostgreSQL database name |
| PG_MIN_POOL_SIZE | 5 | Minimum connection pool size |
| PG_MAX_POOL_SIZE | 20 | Maximum connection pool size |
| PG_CONNECTION_TIMEOUT | 30 | Connection timeout in seconds |
| PG_TENANT_AWARE | true | Whether this database uses tenant schemas |
| PG_DEFAULT_SCHEMA | public | Default schema when no tenant is specified |
| PG_SSL_MODE | None | SSL mode (disable, allow, prefer, require, verify-ca, verify-full) |
| PG_SSL_ROOT_CERT | None | Path to SSL root certificate |
| PG_APPLICATION_NAME | prismicx-app | Application name for connection identification |

For service-specific configuration, prefix the variables with the service name. For example, for a service named "crm":

```
CRM_PG_HOST=custom-postgres-host
CRM_PG_PORT=5433
```

## Example Docker Configuration

```yaml
environment:
  - PG_HOST=postgres-system
  - PG_PORT=5432
  - PG_USER=service_user
  - PG_PASSWORD=strong_password
  - PG_DATABASE=service_db
  - PG_MIN_POOL_SIZE=10
  - PG_MAX_POOL_SIZE=50
  - PG_TENANT_AWARE=true
```

## Integration with PostgresDatabase Class

This module is designed to work seamlessly with the existing `PostgresDatabase` class:

```python
from database_layer.common.db_config import postgres_config
from your_service.infrastructure.database.postgres_database import PostgresDatabase

# Create a database instance using the configuration
conn_string = postgres_config.get_connection_string('service_name')
db = PostgresDatabase(connection_string=conn_string)
await db.initialize()
```

## Multi-Tenant Support

The configuration supports multi-tenant architecture by providing the `PG_TENANT_AWARE` setting. When set to `true`, the database connections will be expected to support tenant schema isolation.

## Advanced Configuration

For advanced scenarios, you can directly access the `PostgresSettings` class:

```python
from database_layer.common.db_config import PostgresSettings

# Create custom settings
custom_settings = PostgresSettings(
    PG_HOST="custom-host",
    PG_PORT=5433,
    PG_DATABASE="custom_db",
    PG_USER="custom_user",
    PG_PASSWORD="custom_password",
    PG_SSL_MODE="require"
)
``` 