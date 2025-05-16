# Management System Repository Service

## Overview

The Management System Repository Service is a centralized repository for managing business management system data within the PrismicX platform. This service handles the storage, versioning, and configuration of management systems data including CRM, Sales Automation, Marketing Automation, and other business tools.

## Key Features

- Management systems data storage
- Multi-tenant management system data storage
- Version control for management systems
- Management system configuration
- Database schemas for common management systems (CRM, Sales, etc.)
- Management system dependency tracking
- Management system installation, update, and removal tracking

## Database Layer Integration

The Management System Repository Service now communicates with databases through the Database Layer services instead of direct database connections. This architectural change:

- Improves security by centralizing database access control
- Enhances scalability by separating concerns
- Provides consistent data access patterns across microservices
- Enables better monitoring and governance of database operations

All database operations (reads, writes, and schema migrations) are performed through authenticated API calls to the appropriate Database Layer services.

## Required Environment Variables

In addition to standard configuration, the following environment variables are required:

```
# Database Layer Services
DATABASE_LAYER_BASE_URL=http://database-layer-service:8000
DATABASE_LAYER_API_KEY=your_api_key_here
TENANT_DB_SERVICE_URL=http://tenant-db-service:8001
CONFIG_DB_SERVICE_URL=http://config-db-service:8002
```

## Supported Management Systems

The Management System Repository Service currently supports the following management systems:

- **CRM (Customer Relationship Management)**
  - Customer data management
  - Interaction tracking
  - Relationship history
  - Deal/opportunity pipeline

- **Sales Automation**
  - Lead management
  - Sales process automation
  - Quota and target tracking
  - Sales analytics

- **Marketing Automation**
  - Campaign management
  - Lead scoring
  - Marketing analytics
  - Content performance tracking

- **Customer Support**
  - Ticket management
  - Support workflow
  - SLA tracking
  - Customer satisfaction metrics

## Database Architecture

Each management system has its own schema within the tenant's database:

```
tenant_001.crm_system
tenant_001.sales_system
tenant_002.crm_system
```

The service follows these organization principles:

1. **System Registry**: Central registry of all available management systems with metadata
2. **System Versions**: Tracking of installed versions across tenants
3. **System Data**: Tenant-specific management system data stored in isolated schemas
4. **Schema Migrations**: Version-controlled schema updates for management systems
5. **Cross-System Relationships**: Managed relationships between management system data

## API Endpoints

The service exposes the following API endpoints:

- `GET /api/v1/systems` - List all available management systems
- `GET /api/v1/systems/{system_id}` - Get management system details
- `GET /api/v1/systems/{system_id}/versions` - List management system versions
- `POST /api/v1/tenants/{tenant_id}/systems` - Install management system for tenant
- `DELETE /api/v1/tenants/{tenant_id}/systems/{system_id}` - Uninstall management system for tenant
- `GET /api/v1/tenants/{tenant_id}/systems` - List tenant's installed management systems

## Project Structure

```
.
├── src/
│   ├── api/            - API endpoints implementation
│   ├── core/           - Core business logic
│   ├── models/         - Data models
│   ├── clients/        - HTTP clients for database layer services
│   ├── schemas/        - Validation schemas
│   └── utils/          - Utility functions
├── tests/              - Unit and integration tests
├── alembic/            - Database migration scripts
└── docs/               - Documentation files
```

## User Interaction Flow

1. **System Discovery**: Users browse available management systems through the UI, which fetches data via the `/api/v1/systems` endpoint.
2. **System Installation**: When a user installs a system for their tenant, the service:
   - Makes API calls to the database layer to create necessary schemas
   - Records installation metadata
   - Sets up initial configuration

3. **Configuration Storage**: User configurations are stored through the Configuration Database Layer service
   - Configurations are validated against schemas
   - Changes are versioned for audit and rollback capabilities

## Management System Databases

### CRM Database (crm_db)

The CRM database stores customer relationship data including:

- Customer profiles
- Communication history
- Sales opportunities
- Relationship status
- Custom fields
- Team assignments

### Sales Automation Database (sales_db)

The Sales Automation database manages sales processes:

- Lead information
- Sales pipeline stages
- Quotas and targets
- Product configurations
- Pricing rules
- Sales team performance

### Marketing Automation Database (marketing_db)

The Marketing Automation database tracks marketing activities:

- Campaign definitions
- Audience segments
- Content assets
- Campaign performance metrics
- A/B test results
- Attribution data

### Configuration Database (config_db)

The Configuration Database manages tenant and user-specific configuration settings:

- Tenant-specific configuration settings
- Configuration schemas and validation
- User preferences
- Feature frequency groups for batch processing
- Cross-tenant configuration management

For detailed information about the Configuration Database, see [config_db.md](./docs/config_db.md).

## Security

All database operations are performed through authenticated API calls to the Database Layer services. Direct database access has been removed, improving:

- Access control
- Audit capabilities
- Credential management
- Resource isolation

## Development Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Configure database and service URLs for your development environment

3. Run database migrations:
   ```bash
   alembic upgrade head
   ```

4. For local development with database layer services:
   - Ensure the database layer services are running locally or accessible
   - Update the DATABASE_LAYER_* environment variables in your .env file
   - If using Docker, ensure the services are in the same network

5. Start the service:
   ```bash
   uvicorn src.main:app --reload
   ```

## Docker Deployment

Build and run the service using Docker:

```bash
docker build -t management-system-repo .
docker run -p 8000:8000 --env-file .env management-system-repo
```

For orchestrated deployment with database layer services, use the provided `docker-compose.yml`:

```bash
docker-compose up -d
```

## Database Layer Communication

When implementing new features that require database access:

1. Use the appropriate client from `src/clients/` to communicate with database layer services
2. All database operations should be performed through these clients
3. Direct database connections should not be used

Example client usage:

```python
from src.clients.config_db import ConfigDbClient

config_client = ConfigDbClient()
result = await config_client.get_system_config(tenant_id, system_id)
```