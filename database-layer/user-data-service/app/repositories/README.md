# User Context Repositories

This directory contains repositories for managing user context data in both long-term (system users) and temporary (campaign users) storage.

## Overview

The implementation provides two distinct repositories with similar schemas but different retention policies:

1. **System Users Conversation** (`system_users_conversation.py`)
   - Interfaces with the existing system_users database
   - Provides long-term storage for subscribed users' conversation data
   - No automatic expiration
   - Connects to both MongoDB (for extended data) and PostgreSQL (for core user data)

2. **Campaign Users Repository** (`campaign_users_repository.py`)
   - Provides temporary storage for campaign participants
   - Uses MongoDB TTL indexes for automatic expiration
   - Default TTL of 90 days (configurable)
   - Organized by campaign ID

## Migration Functionality

The implementation includes functionality to migrate users from campaign storage to the system repository when they subscribe, preserving their context data.

## Architecture

- **Multi-Database Approach**: The system users conversation repository connects to both MongoDB and PostgreSQL, checking both sources when retrieving users.
- **TTL-Based Expiration**: Campaign users automatically expire after the configured TTL period.
- **Campaign Isolation**: Each campaign has its own MongoDB collection for isolation.
- **Tenant Isolation**: System users are isolated by tenant for multi-tenancy support.

## Environment Variables

- `CAMPAIGN_USERS_TTL_DAYS`: Default TTL for campaign users in days (default: 90)
- `POSTGRES_HOST`: PostgreSQL database host (default: postgres-system)
- `POSTGRES_PORT`: PostgreSQL database port (default: 5432)
- `POSTGRES_USER`: PostgreSQL database user (default: user_service)
- `POSTGRES_PASSWORD`: PostgreSQL database password (default: password)

## Usage

The repositories are accessed through the `UserContextService` in `services/user_context_service.py`, which provides a unified API for working with both repositories.

### Example

```python
from app.services.user_context_service import UserContextService

async def migrate_user_example(user_id, campaign_id, tenant_id):
    service = UserContextService()
    await service.initialize(mongo_client)
    
    # Migrate a user from campaign to system
    success = await service.migrate_to_system(user_id, campaign_id, tenant_id)
    
    if success:
        print(f"User {user_id} successfully migrated to system users")
    else:
        print(f"Migration failed for user {user_id}") 