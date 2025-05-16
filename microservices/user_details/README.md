# User Details Microservice

## Overview

The User Details Microservice manages user insights, profiles, and eligibility within the system. It is responsible for creating and maintaining user data structures and extensions based on configurable templates.

## Features

- **User Insight Management**: Create, read, update, and delete user insights
- **Topic & Subtopic Organization**: Hierarchical data structure for user knowledge
- **User Extensions**: Extensible system to add functionality to user profiles
- **Configuration-Driven Structures**: All data structures defined via JSON templates
- **Multi-Tenant Support**: Data isolation across tenants
- **Database Layer Integration**: All database operations performed through the Database Layer service

## Configuration-Driven Structures

The microservice uses a configuration-driven approach for data structures. All user insights and extensions follow templates defined in JSON files, which can be modified without changing code.

### Key Benefits

- Standardized data structures across all users
- Ability to evolve structures without code changes
- Validation against defined schemas
- Default values and templates for new users

## Directory Structure

```
microservices/user_details/
├── api/                  # API endpoints
├── clients/              # Database Layer clients
│   ├── database_layer_client.py  # Base client for database layer
│   ├── user_insight_client.py    # Client for User Insight operations
│   └── user_extension_client.py  # Client for User Extension operations
├── config/               # Configuration files
│   └── templates/        # Structure templates
│       ├── extension_types/      # Extension type definitions
│       ├── user_insight_structure.json  # User insight structure
│       └── default_topics.json  # Default topics for new users
├── models/               # Data models
├── repositories/         # Data access layer
│   ├── user_insight_repo.py      # User Insight repository
│   └── extension_repo.py         # User Extension repository
├── services/             # Business logic
│   ├── config_service.py # Configuration management
│   └── insight_service.py # User insight business logic
└── validation/           # Input validation
```

## Database Architecture

### Physical Database Location

The physical databases used by this microservice are now deployed and managed exclusively within the Database Layer:

- **MongoDB** (for user insights) - Deployed within the database-layer services
- **PostgreSQL** (for user extensions) - Deployed within the database-layer services

These databases are no longer directly accessed by the User Details microservice; instead, all access is mediated through the Database Layer services.

### Data Flow Architecture

```
┌─────────────────────┐      HTTP API      ┌─────────────────────┐     Direct DB     ┌─────────────────┐
│                     │     Requests       │                     │    Connection     │                 │
│  User Details       ├────────────────────►  Database Layer     ├──────────────────►│   MongoDB       │
│  Microservice       │                    │  (user-data-service)│                   │                 │
│                     │                    │                     │                   └─────────────────┘
└─────────────────────┘                    │                     │                   ┌─────────────────┐
                                           │                     │                   │                 │
                                           │                     ├──────────────────►│   PostgreSQL    │
                                           │                     │                   │                 │
                                           └─────────────────────┘                   └─────────────────┘
```

## Database Layer Integration

This microservice communicates with databases through the Database Layer service instead of direct database connections. This architecture:

- Improves security by centralizing database access control
- Enhances scalability by separating concerns
- Provides consistent data access patterns across microservices
- Enables better monitoring and governance of database operations

### How It Works

1. All database operations are performed through the clients in the `clients/` directory
2. The clients make authenticated HTTP requests to the Database Layer service
3. The Database Layer service handles the actual database operations
4. The repositories have been updated to use these clients instead of direct database connections

### Database Management

- Database credentials are now stored only in the Database Layer configuration
- Database scaling, backup, and maintenance are handled at the Database Layer level
- Multi-tenant data isolation is enforced by the Database Layer
- Database migrations and schema updates are coordinated through the Database Layer

## Bulk Changes to User Insights

The system still maintains the ability to make bulk changes to user insights by updating configuration templates. When templates are modified and reloaded, changes are applied across all users through the Database Layer:

1. Edit the structure templates (`config/templates/user_insight_structure.json` or other templates)
2. Call the reload API endpoint: `POST /api/v1/admin/config/reload`
3. The system will apply these changes to all appropriate user insights in the MongoDB database through the Database Layer

## How to Customize Data Structures

### Modifying User Insight Structure

1. Edit the file `config/templates/user_insight_structure.json`
2. Call the reload API endpoint: `POST /api/v1/admin/config/reload`

### Adding New Extension Types

1. Create a new file in `config/templates/extension_types/`
2. Follow the extension type schema format
3. Call the reload API endpoint: `POST /api/v1/admin/config/reload`

### Changing Default Topics

1. Edit the file `config/templates/default_topics.json`
2. Call the reload API endpoint: `POST /api/v1/admin/config/reload`

## API Endpoints

### User Management

- `POST /api/v1/insights/{user_id}` - Create a new user insight
- `GET /api/v1/insights/{user_id}` - Get a user's insight data
- `GET /api/v1/insights/{user_id}/topics/{topic_id}` - Get a specific topic for a user

### Configuration Management

- `POST /api/v1/admin/config/reload` - Reload configuration files
- `GET /api/v1/config/extension-types` - Get all available extension types
- `GET /api/v1/config/extension-types/{type}` - Get configuration for a specific extension type
- `GET /api/v1/config/insight-structure` - Get the insight structure configuration
- `GET /api/v1/config/default-topics` - Get the default topics configuration

## Environment Variables

- `CONFIG_PATH` - Path to the templates directory (default: `config/templates`)
- `DATABASE_LAYER_BASE_URL` - URL of the Database Layer service
- `DATABASE_LAYER_API_KEY` - API key for authentication with the Database Layer service
- `SUBSCRIPTION_SERVICE_URL` - URL for subscription service integration
- `DEVELOPMENT_MODE` - When "true", all users are eligible for insights

## Deployment

See the included `docker-compose.yml` file for a complete deployment configuration that includes:

- The User Details microservice
- The Database Layer user-data-service
- MongoDB and PostgreSQL databases

All these components work together to provide a fully functioning User Details system with proper separation of concerns. 