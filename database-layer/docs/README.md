# Database Layer Documentation

> **IMPORTANT**: For a comprehensive reference of all database services, their APIs, and usage details, please refer to the new [Database Services Reference](database-services-reference.md) document.

# Database Layer for PrismicX

This directory contains documentation for the Database Access Layer (DAL) for the PrismicX platform, implementing a comprehensive solution for handling both multi-tenant and system-wide databases in a microservices architecture.

## Key Documentation Files

- [Database Services Reference](database-services-reference.md) - Comprehensive reference of all database services, APIs, and usage guidelines
- [PostgreSQL Multi-Tenancy Implementation](multi-tenancy-postgresql.md) - Details of the PostgreSQL multi-tenancy approach
- [Management System Repository](management-system-repo.md) - Documentation for the Management System Repository service
- [Database Documentation Overview](database-documentation.md) - Entry point for all database-related documentation

## Architecture Overview

```
┌───────────────────────────────────────────────────────────────┐
│                       Client Applications                      │
└───────────────────┬───────────────────────┬───────────────────┘
                    │                       │
┌───────────────────▼───┐     ┌─────────────▼───────────────────┐
│   API Gateway Layer   │     │       Authentication Layer       │
└───────────────┬───────┘     └───────────────┬─────────────────┘
                │                             │
┌───────────────▼─────────────────────────────▼───────────────────┐
│                        Microservices Layer                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ Marketing  │  │Communication│  │ Analysis  │  │ Management │  │
│  │ Service    │  │ Service    │  │ Service   │  │ Service    │  │
│  └──────┬─────┘  └──────┬─────┘  └──────┬────┘  └──────┬─────┘  │
│         │              │              │              │         │
│         └──────────────┴──────────────┴──────────────┘         │
│                              │                                  │
└──────────────────────────────┼──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                      Database Access Layer                       │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │   Tenant    │  │    User     │  │    Task     │  │ Category │ │
│  │ Management  │  │    Data     │  │ Repository  │  │ Repository│ │
│  │  Service    │  │   Service   │  │  Service    │  │  Service  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────┬─────┘ │
│         │                │                │               │      │
│         │                │                │               │      │
│  ┌──────▼────────────────▼────────────────▼───────────────▼────┐ │
│  │                 System-wide Databases                        │ │
│  │                                                              │ │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────┐  ┌──────────┐  │ │
│  │  │ MongoDB    │  │ PostgreSQL │  │ Redis   │  │ MongoDB  │  │ │
│  │  │ System     │  │ System     │  │ Cache   │  │ Tenant   │  │ │
│  │  └────────────┘  └────────────┘  └─────────┘  └──────────┘  │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## Database Services

The Database Access Layer consists of the following key services:

### 1. Tenant Management Service (tenant-mgmt-service)
- **Port**: 8501
- **Database**: MongoDB (tenant_registry)
- **Purpose**: Centralized management of tenants and their database configurations
- **Key Capabilities**: Tenant provisioning, database routing, tenant isolation

### 2. User Data Service (user-data-service)
- **Port**: 8502
- **Database**: PostgreSQL (system_users)
- **Purpose**: Centralized access to system-wide user data
- **Key Capabilities**: User authentication, authorization, profile management

### 3. Task Repository Service (task-repo-service)
- **Port**: 8503
- **Database**: MongoDB (task_repository)
- **Purpose**: Centralized task management
- **Key Capabilities**: Task creation, claiming, and status management

### 4. Category Repository Service (category-repository-service)
- **Port**: 8504
- **Database**: MongoDB (category_repository)
- **Purpose**: Centralized category management
- **Key Capabilities**: Category, factor, campaign, and entity assignment management

### 5. Management System Repository (management-system-repo)
- **Port**: 8505
- **Databases**: PostgreSQL (management_system_repository), MongoDB (config_db)
- **Purpose**: Management systems data
- **Key Capabilities**: System configuration, structured data management

## Database Infrastructure

### MongoDB System Database (mongodb-system)
- **Purpose**: System-wide MongoDB for tenant registry and shared data
- **Data Stored**: Configuration data, tenant information, tasks, categories

### PostgreSQL System Database (postgres-system)
- **Purpose**: System-wide PostgreSQL for structured data
- **Data Stored**: User data, structured management system data

### MongoDB Tenant Database (mongodb-tenant)
- **Purpose**: Multi-tenant MongoDB for service-specific tenant data
- **Data Stored**: Tenant-specific data

### Redis Cache (redis-cache)
- **Purpose**: Caching and messaging
- **Data Stored**: Cached data, session information, queues

## Getting Started

For comprehensive information on how to use these database services, including API endpoints, client usage examples, and best practices, please refer to the [Database Services Reference](database-services-reference.md) document. 