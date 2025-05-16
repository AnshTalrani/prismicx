# User Setup Process Documentation

## Overview

This document details the process of establishing new users in the system. The user details microservice is responsible for creating and managing user insights based on eligibility criteria such as subscription status.

## User Establishment Process Flow

The process of establishing a new user in the system follows these steps:

1. **User Registration** - Initial user registration is handled by the authentication system (not covered in this document)
2. **Eligibility Check** - The user details microservice checks if the user is eligible for insights creation
3. **User Insight Creation** - If eligible, a user insight record is created in the database
4. **Extension Setup** - Optional extensions can be added to the user profile

## Component Responsibilities

### User Details Microservice

The user details microservice is responsible for:

- Determining user eligibility based on subscription status or other criteria
- Creating and managing user insight records
- Organizing user data in a hierarchical topic/subtopic structure
- Managing user extensions

### Eligibility Criteria

Users must meet defined eligibility criteria before a user insight record is created. The primary criterion is typically a paid subscription, but the system is designed to accommodate additional or alternative criteria in the future.

The eligibility check is performed by the `_check_user_eligibility` method in the `InsightService` class, which:

1. Verifies subscription status through the subscription service API
2. Applies any additional business rules (configurable)
3. Returns a boolean indicating whether the user is eligible

## API Endpoints

### Create User Insight

```
POST /api/v1/insights/{user_id}
```

**Headers:**
- `X-Tenant-ID` (required): The tenant identifier for multi-tenant isolation

**Response Codes:**
- 201 Created: User insight created successfully
- 403 Forbidden: User not eligible for insight creation
- 400 Bad Request: Missing required headers

**Example Response (Success):**
```json
{
  "user_id": "user123",
  "tenant_id": "tenant1",
  "topics": [],
  "metadata": {},
  "created_at": "2023-06-15T10:30:00.000Z",
  "updated_at": "2023-06-15T10:30:00.000Z"
}
```

**Example Response (Not Eligible):**
```json
{
  "error": "User not eligible for insight creation",
  "user_id": "user123"
}
```

## Integration with Subscription Service

The user details microservice integrates with a subscription service to verify user eligibility:

1. Makes HTTP requests to the subscription service API endpoint:
   ```
   GET {SUBSCRIPTION_SERVICE_URL}/api/v1/users/{user_id}/subscription/status
   ```

2. Processes the response to determine if the user has an active subscription
   ```json
   {
     "is_active": true,
     "subscription_tier": "premium",
     "expiration_date": "2024-01-01T00:00:00.000Z"
   }
   ```

3. Falls back to environment-based defaults if the service is unavailable

## Configuration

The user details microservice uses these environment variables for eligibility checks:

- `SUBSCRIPTION_SERVICE_URL`: URL of the subscription service API
- `DEVELOPMENT_MODE`: When set to "true", all users are considered eligible (for development and testing)

## Multi-Tenant Support

The system supports multi-tenant isolation:

1. Each API request requires a tenant ID header
2. User insights are stored in tenant-specific collections in MongoDB
3. This ensures data isolation between different tenants

## Error Handling

The user details microservice handles these error scenarios:

1. Subscription service unavailable: Falls back to restrictive default (not eligible)
2. Missing tenant ID: Returns 400 Bad Request
3. User already has an insight: Returns the existing insight

## Future Enhancements

The eligibility checking system is designed to be extensible:

1. Additional eligibility criteria can be added to the `_check_user_eligibility` method
2. Integration with other services beyond subscription verification
3. Configurable eligibility rules based on tenant-specific settings 