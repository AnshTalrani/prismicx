# Management System Repository

> **IMPORTANT UPDATE**: This document provides specific information about the Management System Repository. For a comprehensive reference of all database services, their APIs, and usage details, please refer to the new [Database Services Reference](database-services-reference.md) document.

## Overview

The Management System Repository (formerly known as Plugin Repository Service) is a core component of the PrismicX Database Layer that manages business management systems and their associated data. This document outlines the architecture, data models, and implementation details of this service.

## Architecture

```
┌─────────────────────────────────────┐
│      Management System Repository   │
├─────────────────────────────────────┤
│                                     │
│  ┌───────────┐      ┌────────────┐  │
│  │ System    │      │  Version   │  │
│  │ Registry  │      │ Management │  │
│  └───────────┘      └────────────┘  │
│                                     │
│  ┌───────────┐      ┌────────────┐  │
│  │ Schema    │      │ Tenant     │  │
│  │ Migration │      │ Assignment │  │
│  └───────────┘      └────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │    Management System Data     │  │
│  │                               │  │
│  │   ┌──────┐ ┌──────┐ ┌──────┐  │  │
│  │   │ CRM  │ │Sales │ │Market│  │  │
│  │   │      │ │      │ │      │  │  │
│  │   └──────┘ └──────┘ └──────┘  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

The service follows a layered architecture:

1. **System Registry Layer**: Manages the catalog of available management systems
2. **Version Management Layer**: Tracks system versions and compatibility
3. **Schema Migration Layer**: Handles database schema changes for management systems
4. **Tenant Assignment Layer**: Maps management systems to tenants
5. **Management System Data Layer**: Stores the actual system data in tenant-specific schemas

## Database Design

The Management System Repository uses both PostgreSQL and MongoDB for data storage:

### PostgreSQL Database (management_system_repository)

#### Core Tables (in `public` schema)

1. **management_systems**: Central registry of all available management systems
   ```sql
   CREATE TABLE management_systems (
       system_id VARCHAR(50) PRIMARY KEY,
       name VARCHAR(100) NOT NULL,
       description TEXT,
       type VARCHAR(50) NOT NULL,  -- 'crm', 'sales', 'marketing', etc.
       status VARCHAR(20) NOT NULL DEFAULT 'active',
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       metadata JSONB
   );
   ```

2. **system_versions**: Tracks different versions of management systems
   ```sql
   CREATE TABLE system_versions (
       version_id VARCHAR(50) PRIMARY KEY,
       system_id VARCHAR(50) NOT NULL REFERENCES management_systems(system_id),
       version VARCHAR(20) NOT NULL,
       release_notes TEXT,
       schema_version INT NOT NULL,
       dependencies JSONB,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       UNIQUE(system_id, version)
   );
   ```

3. **tenant_systems**: Maps installed management systems to tenants
   ```sql
   CREATE TABLE tenant_systems (
       tenant_id VARCHAR(50) NOT NULL,
       system_id VARCHAR(50) NOT NULL REFERENCES management_systems(system_id),
       version_id VARCHAR(50) NOT NULL REFERENCES system_versions(version_id),
       status VARCHAR(20) NOT NULL DEFAULT 'active',
       installed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       configurations JSONB,
       PRIMARY KEY (tenant_id, system_id)
   );
   ```

4. **schema_migrations**: Tracks schema changes per system version
   ```sql
   CREATE TABLE schema_migrations (
       migration_id VARCHAR(50) PRIMARY KEY,
       system_id VARCHAR(50) NOT NULL REFERENCES management_systems(system_id),
       version_from VARCHAR(20) NOT NULL,
       version_to VARCHAR(20) NOT NULL,
       migration_sql TEXT NOT NULL,
       rollback_sql TEXT,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );
   ```

### MongoDB Database (config_db)

1. **system_configurations**: Stores flexible configuration data for management systems
   ```javascript
   {
     "_id": "ObjectId",
     "system_id": "crm_standard",
     "tenant_id": "tenant_abc123",
     "configuration": {
       // Flexible configuration structure
       "features": {
         "contact_management": true,
         "opportunity_tracking": true,
         "email_integration": false
       },
       "ui_settings": {
         "theme": "light",
         "dashboard_widgets": ["recent_contacts", "sales_pipeline", "activities"]
       },
       "integration_points": {
         "marketing": {
           "enabled": true,
           "sync_interval": 3600
         },
         "sales": {
           "enabled": true,
           "sync_interval": 1800
         }
       }
     },
     "created_at": "ISODate",
     "updated_at": "ISODate"
   }
   ```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/systems` | GET | List all management systems |
| `/api/v1/systems/{system_id}` | GET | Get system details |
| `/api/v1/systems` | POST | Create a new system |
| `/api/v1/systems/{system_id}` | PUT | Update system details |
| `/api/v1/systems/{system_id}/config` | GET | Get system configuration |
| `/api/v1/systems/{system_id}/config` | PUT | Update system configuration |
| `/health` | GET | Health check endpoint |