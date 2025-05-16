# User Details Microservice Documentation

This directory contains the documentation for the User Details Microservice.

## Available Documentation

- [Quick Start Guide](quickstart.md): A quick guide to get started with structure templates.
- [Multi-Tenancy Guide](multi_tenancy_guide.md): Comprehensive guide for working with the multi-tenant features.

## Overview

The User Details Microservice provides the following key features:

1. **User Insights Management**: Store and retrieve user insights, including topics and subtopics.
2. **Extension Management**: Manage user extensions for additional functionality.
3. **Configuration-Driven Structure**: Use templates to define the structure of user insights and extensions.
4. **Multi-Tenancy Support**: Complete isolation of data and configuration between tenants.

## Architecture

The microservice follows the MACH architecture (Microservices, API-first, Cloud-native, Headless) and is organized as follows:

```
user_details/
├── app.py                    # Main application entry point
├── controllers/              # API controllers
├── services/                 # Business logic services
├── repositories/             # Data access layer
├── models/                   # Domain models
├── multitenant/              # Multi-tenancy implementation
│   ├── models/               # Tenant models
│   ├── services/             # Tenant services
│   ├── middleware/           # Tenant middleware
│   └── utils/                # Tenant utilities
└── docs/                     # Documentation
```

## Environment Variables

The following environment variables can be configured:

- `CONFIG_PATH`: Path to the configuration templates (default: `config/templates`)
- `TENANT_STORAGE_PATH`: Path to store tenant data (default: `config/tenants`)
- `DEFAULT_TEMPLATES_PATH`: Path to default templates (default: `config/templates`)
- `MULTI_TENANT_MODE`: Enable/disable multi-tenancy (default: `true`)

## Getting Started

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up multi-tenancy (optional):
   ```
   python -m microservices.user_details.multitenant.utils.setup_tenants --create-sample-tenants
   ```

3. Start the microservice:
   ```
   python app.py
   ```

4. Access the API at `http://localhost:5000/api/v1/`

For more detailed information, refer to the specific guides in this documentation directory. 