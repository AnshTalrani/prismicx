# Database Layer

This directory contains the database services, configurations, and initialization scripts for the PrismicX platform.

## Important Documentation

For a comprehensive reference of all database services, APIs, and usage details, please refer to:
- [Database Services Reference](docs/database-services-reference.md)
- [Vector Store Service](docs/vector-store-service.md)

## Structure

```
database-layer/
├── tenant-mgmt-service/     # Tenant Management Service
├── user-data-service/       # User Data Service
├── task-repo-service/       # Task Repository Service
├── category-repository-service/  # Category Repository Service
├── management-system-repo/  # Management System Repository
├── vector-store-service/    # Vector Store Service with Niche Support
├── init-scripts/           # Database initialization scripts
├── common/                 # Shared database utilities
└── docs/                  # Database documentation
```

## Database Architecture

The system uses a microservices-based database layer with multiple specialized database services:

| Service | Database Type | Primary Database | External Port | Internal Port | Description |
|---------|--------------|------------------|---------------|---------------|-------------|
| Tenant Management Service<br>(tenant-mgmt-service) | MongoDB | tenant_registry | 8501 | 8501 | Manages tenant configurations and database routing |
| User Data Service<br>(user-data-service) | PostgreSQL | system_users | 8502 | 8502 | Manages user data and authentication |
| Task Repository Service<br>(task-repo-service) | MongoDB | task_repository | 8503 | 8503 | Manages centralized task management |
| Category Repository Service<br>(category-repository-service) | MongoDB | category_repository | 8504 | 8080 | Manages categories, factors, campaigns, and entity assignments |
| Management System Repository<br>(management-system-repo) | PostgreSQL & MongoDB | management_system_repository & config_db | 8505 | 8080 | Manages system configurations and metadata |
| Vector Store Service<br>(vector-store-service) | MongoDB & Vector DBs | vector_store_system & vector files | 8510 | 8510 | Manages vector embeddings, semantic search, and specialized niche storage |

## Database Infrastructure

### Database Servers

| Server | Type | Port | Description | Used By |
|--------|------|------|-------------|---------|
| mongodb-system | MongoDB | 27018 | System-wide MongoDB for shared data | Tenant Management Service, Task Repository Service, Category Repository Service, Management System Repository (config_db), Vector Store Service |
| postgres-system | PostgreSQL | 5432 | System-wide PostgreSQL for structured data | User Data Service, Management System Repository (management_system_repository) |
| pgbouncer | Connection Pooling | 6432 | Connection pooling for PostgreSQL | All PostgreSQL clients |
| mongodb-tenant | MongoDB | 27017 | Multi-tenant MongoDB with replica set | Tenant-specific data storage |
| redis-cache | Redis | 6379 | Caching and messaging | All services for caching |

## Vector Store Service

The **Vector Store Service** is a recent addition to the database layer that provides:

- Centralized vector embeddings storage and retrieval
- Semantic search across multiple domains
- Support for multiple embedding models
- Support for multiple vector store backends (FAISS, Chroma, Qdrant)
- **NEW**: Niche-specific vector stores for efficient categorized storage and retrieval
- **NEW**: Hybrid search combining vector similarity with keyword matching
- Multi-tenant isolation for vector data

This service is crucial for:
- Bot-specific knowledge retrieval in the Communication Base
- Domain-specific knowledge in Expert Base
- Niche product information for the Sales Bot
- Expert knowledge retrieval for the Consultancy Bot

For detailed information, see the [Vector Store Service documentation](docs/vector-store-service.md).

## Setup Instructions

1. Start the database layer services:

```bash
# Start all database services
docker-compose -f docker-compose.database-layer.yml up -d
```

2. Verify the services are running:

```bash
docker-compose -f docker-compose.database-layer.yml ps
```

## Environment Variables

Each service uses standardized environment variables:

### Common Environment Variables

| Variable Pattern | Description |
|------------------|-------------|
| SERVICE_NAME | Standardized name of the service |
| HOST / *_HOST | Host binding address (usually 0.0.0.0) |
| PORT / *_PORT | Port binding for the service |
| *_DB_* | Database connection parameters |
| API_KEY | API authentication key |
| *_LOG_LEVEL | Logging level configuration |

### Service-Specific Variables

See the [Database Services Reference](docs/database-services-reference.md) document for detailed environment variables for each service.

## Security Notes

1. Change all default passwords in production
2. Use secure network configurations
3. Regular backup of all databases
4. Monitor database performance and usage

## Maintenance

- Regular backups should be configured for all database services
- Monitoring is available through Prometheus exporters
- Check logs in the respective docker containers:
  ```bash
  docker logs [service-name]
  ```

## Further Information

For more detailed information about the database layer services, including API endpoints, client usage examples, and best practices, refer to the [Database Services Reference](docs/database-services-reference.md) document. 