# Management Systems API

## Overview

The Management Systems API provides a comprehensive interface for managing business management systems within the PrismicX platform, including CRM, Sales Automation, Marketing Automation, and other business tools.

## Architecture

### MACH Architecture Implementation

The Management Systems API fully implements the MACH architecture principles:

1. **Microservices-based**: Focused solely on management systems functionality
2. **API-first**: All functionality is available through REST APIs
3. **Cloud-native**: Designed to run in containerized environments
4. **Headless**: Provides pure data functionality without UI concerns

### Database Layer Integration

The Management Systems API no longer connects directly to any databases. Instead, it communicates with database layer services through HTTP APIs:

- **management-system-repo**: Provides access to management system data, templates, and configuration
- **tenant-mgmt-service**: Manages tenant-specific configurations and data
- **user-data-service**: Handles user data and permissions
- **task-repo-service**: Manages long-running tasks

This approach:
- Simplifies the Management Systems microservice by removing direct database access
- Follows MACH architecture principles for clear separation of concerns
- Enables better scalability and maintenance
- Provides consistent access patterns across services

## Key Features

- Tenant-specific management system configuration
- Multi-tenant management system management
- Version control for management systems
- Management system configuration
- Automation workflows for management systems
- Plugin system for extending functionality

## Components

- **Management API**: Core API for management system operations
- **Configuration API**: API for accessing configuration data (via database layer)
- **Automation API**: API for automation workflows
- **Plugin System**: Extensible plugin architecture

## Required Environment Variables

### Database Layer Services
```
MANAGEMENT_SYSTEM_REPO_URL=http://management-system-repo:8080
MANAGEMENT_SYSTEM_REPO_API_KEY=dev_api_key
TENANT_MGMT_SERVICE_URL=http://tenant-mgmt-service:8000
TENANT_MGMT_SERVICE_API_KEY=dev_api_key
USER_DATA_SERVICE_URL=http://user-data-service:8000
USER_DATA_SERVICE_API_KEY=dev_api_key
TASK_REPO_SERVICE_URL=http://task-repo-service:8000
TASK_REPO_SERVICE_API_KEY=dev_api_key
```

### Redis Cache
```
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=password
```

## API Endpoints

- `GET /api/v1/systems` - List all available management systems
- `GET /api/v1/systems/{system_id}` - Get management system details
- `GET /api/v1/tenants/{tenant_id}/systems` - List tenant's installed management systems
- `POST /api/v1/tenants/{tenant_id}/systems` - Install management system for tenant
- `GET /api/v1/config/tenants/{tenant_id}/configs/{config_key}` - Get tenant configuration
- `PUT /api/v1/config/tenants/{tenant_id}/configs/{config_key}` - Set tenant configuration

## Running the Service

### Docker Compose

```yaml
version: '3.8'
services:
  management-systems:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MANAGEMENT_SYSTEM_REPO_URL=http://management-system-repo:8080
      - MANAGEMENT_SYSTEM_REPO_API_KEY=dev_api_key
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis
      - management-system-repo
```

### Local Development

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```

## Dependencies

The Management Systems API depends on the following database layer services:

- `management-system-repo`: Repository service for management system data
- `tenant-mgmt-service`: Service for tenant management
- `user-data-service`: Service for user data
- `task-repo-service`: Service for managing long-running tasks

## Prerequisites

- Docker and Docker Compose
- Access to the database-layer services
- Redis for caching

## Environment Variables

Configure the service with these environment variables:

```
# Database Layer Services
MANAGEMENT_SYSTEM_REPO_URL=http://management-system-repo:8080
MANAGEMENT_SYSTEM_REPO_API_KEY=dev_api_key
TENANT_MGMT_SERVICE_URL=http://tenant-mgmt-service:8000
TENANT_MGMT_SERVICE_API_KEY=dev_api_key
USER_DATA_SERVICE_URL=http://user-data-service:8000
USER_DATA_SERVICE_API_KEY=dev_api_key
TASK_REPO_SERVICE_URL=http://task-repo-service:8000
TASK_REPO_SERVICE_API_KEY=dev_api_key

# Redis settings
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=password

# API settings
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO

# Plugin settings
PLUGINS_ENABLED=true
PLUGINS_WATCH=true
PLUGINS_DIR=/app/plugins
```

## Running the Service

### Development

1. Clone the repository
2. Navigate to the management_systems directory
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the service:

```bash
uvicorn src.main:app --reload
```

### Docker

```bash
docker-compose up -d
```

## API Documentation

When the service is running, access the Swagger UI documentation at:

```
http://localhost:8000/docs
```

## Health Checks

The service provides health check endpoints:

- `/health` - Overall health check of the service and dependencies
- `/health/live` - Simple liveness check 
- `/health/ready` - Readiness check for Kubernetes

## Development

### Project Structure

```
management_systems/
│
├── src/                  # Source code
│   ├── api/              # API routes
│   ├── automation/       # Automation engine and trigger management
│   ├── clients/          # HTTP clients for database layer services
│   ├── common/           # Shared utilities
│   ├── config/           # Configuration
│   ├── data/             # Data templates
│   ├── models/           # Data models
│   ├── plugins/          # Plugin system
│   │   ├── ms/           # Domain-specific management modules
│   │   └── dispatcher.py # Event dispatching system
│   ├── routers/          # API routers
│   ├── services/         # Business logic
│   └── main.py           # Application entry point
│
├── tests/                # Test files
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
└── requirements.txt      # Dependencies
```

### Adding Plugins

Create a new plugin in the plugins directory following the plugin template. The plugin should implement the `PluginBase` class.

### Management Modules

Each business domain (CRM, Sales, etc.) has a dedicated management module in `plugins/ms/` that implements domain-specific logic and automation triggers.

### Automation System

The service includes a powerful event-driven automation system for creating trigger-based workflows:

#### Key Components:

- **AutomationEngine**: Processes events and executes actions based on trigger conditions
- **Event Dispatcher**: Routes events between management modules and the automation engine
- **Management Modules**: Define domain-specific triggers and condition evaluation logic

#### Available Triggers

Each management module defines its own set of triggers:

**CRM Module Triggers:**
- Contact created/updated
- Contact status changed
- Lead created

**Sales Module Triggers:**
- Opportunity created
- Deal stage changed
- Deal closed (won/lost)
- High-value opportunity identified

#### Automation API

Manage automation rules through the API:

```
GET /api/v1/automation/triggers     # List available triggers
POST /api/v1/automation/rules       # Create new automation rule
GET /api/v1/automation/rules        # List automation rules
PUT /api/v1/automation/rules/{id}/toggle  # Enable/disable rule
```

Example rule creation:
```json
{
  "name": "High Value Deal Alert", 
  "module_type": "sales",
  "trigger_id": "high_value_opportunity",
  "conditions": [
    {
      "type": "value_threshold",
      "value": 10000
    }
  ],
  "actions": [
    {
      "type": "send_notification",
      "parameters": {
        "recipient": "sales-manager@example.com",
        "message": "High value opportunity detected!"
      }
    }
  ]
}
```

## Security

- All database operations are performed through authenticated API calls
- API keys are managed through environment variables
- API endpoints require authentication
- Tenant data is isolated through the database layer services

## Monitoring

- Health checks are configured for both the application and its dependencies
- Logging is configured for all operations
- Prometheus metrics are available for monitoring 