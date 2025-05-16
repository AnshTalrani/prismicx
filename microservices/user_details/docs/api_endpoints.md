# Configuration API Endpoints

This document details the API endpoints for managing configuration templates in the User Details Microservice.

## Configuration Management Endpoints

### Reload Configurations

Reloads all configuration templates from disk. This endpoint should be called after making changes to any template files.

**Endpoint:** `POST /api/v1/admin/config/reload`

**Headers:**
- `X-Tenant-ID` (required): The tenant identifier

**Response:**
```json
{
  "status": "success",
  "message": "Configurations reloaded successfully",
  "last_reload": "2023-06-15T10:30:00.000Z"
}
```

### Get All Extension Types

Returns a list of all available extension types configured in the system.

**Endpoint:** `GET /api/v1/config/extension-types`

**Response:**
```json
{
  "extension_types": [
    "content_recommender",
    "learning_path"
  ]
}
```

### Get Extension Type Configuration

Returns the configuration for a specific extension type.

**Endpoint:** `GET /api/v1/config/extension-types/{extension_type}`

**Parameters:**
- `extension_type`: The name of the extension type to retrieve

**Response:**
```json
{
  "extension_type": "content_recommender",
  "schema": {
    "required": ["name", "enabled"],
    "metadata": {
      "required": ["version", "configuration"],
      "configuration": {
        "required": ["refresh_frequency", "max_recommendations"]
      }
    },
    "metrics": {
      "properties": ["usage_count", "feedback_score", "last_used_at"]
    },
    "practicality": {
      "factors": ["relevance", "utility", "ease_of_use"]
    }
  },
  "defaults": {
    "priority": 1,
    "enabled": true,
    "metadata": {
      "version": "1.0",
      "configuration": {
        "refresh_frequency": "weekly",
        "max_recommendations": 5
      }
    }
  }
}
```

### Get User Insight Structure

Returns the current user insight structure configuration.

**Endpoint:** `GET /api/v1/config/insight-structure`

**Response:**
```json
{
  "version": "1.0",
  "schema": {
    "topics": {
      "required": ["topic_id", "name"],
      "properties": {
        "topic_id": "string",
        "name": "string",
        "description": "string",
        "subtopics": "array"
      }
    },
    "subtopics": {
      "required": ["subtopic_id", "name"],
      "properties": {
        "subtopic_id": "string",
        "name": "string",
        "content": "object"
      }
    },
    "metadata": {
      "allowed_properties": ["primary_interests", "learning_style", "preferred_content_formats"]
    }
  },
  "default_metadata": {
    "learning_style": "unspecified",
    "preferred_content_formats": ["text"]
  }
}
```

### Get Default Topics

Returns the default topics that are created for new users.

**Endpoint:** `GET /api/v1/config/default-topics`

**Response:**
```json
{
  "default_topics": [
    {
      "name": "Getting Started",
      "description": "Initial topics to help new users get started",
      "subtopics": [
        {
          "name": "System Introduction",
          "content": {
            "expertise_level": "beginner",
            "key_points": ["Overview of system features", "How to navigate interfaces"]
          }
        }
      ]
    }
  ]
}
```

## Usage Examples

### Reloading Configuration After Changes

After editing a template file, you should reload the configuration:

```bash
curl -X POST http://your-api-host/api/v1/admin/config/reload \
  -H "X-Tenant-ID: your_tenant_id" \
  -H "Content-Type: application/json"
```

### Getting All Extension Types

To see all available extension types:

```bash
curl -X GET http://your-api-host/api/v1/config/extension-types
```

### Getting Configuration for a Specific Extension Type

To see the configuration for a specific extension type:

```bash
curl -X GET http://your-api-host/api/v1/config/extension-types/content_recommender
``` 