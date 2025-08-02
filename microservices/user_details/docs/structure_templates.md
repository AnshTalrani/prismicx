# Structure Templates Guide

This document explains how to use and modify the JSON template files that define data structures in the User Details Microservice.

## Overview

The User Details Microservice uses a configuration-driven approach where all data structures are defined in JSON template files. This allows you to modify the structure of user insights and extensions without changing code.

## Template Files

The following template files control the structure of data in the system:

| File Path | Purpose |
|-----------|---------|
| `config/templates/user_insight_structure.json` | Defines the structure of user insights |
| `config/templates/default_topics.json` | Defines default topics for new users |
| `config/templates/extension_types/*.json` | Defines different types of extensions |

## User Insight Structure

The user insight structure template (`user_insight_structure.json`) defines the overall structure of user insights, including:

- Schema for topics and subtopics
- Required fields
- Property types
- Default metadata

### Example

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

## Default Topics

The default topics template (`default_topics.json`) defines the topics and subtopics that are automatically created for new users.

### Example

```json
[
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
```

## Extension Types

Extension type templates (in the `extension_types` directory) define different types of extensions that can be added to users, including:

- Schema requirements
- Required fields
- Default values
- Metrics structure
- Practicality factors

### Example

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

## How to Modify Templates

1. **Locate the template file** you want to modify
2. **Edit the JSON** according to your requirements
3. **Save the file**
4. **Reload the configuration** by calling the API endpoint:
   ```
   POST /api/v1/admin/config/reload
   ```
   With header: `X-Tenant-ID: your_tenant_id`

## Creating New Extension Types

To create a new extension type:

1. Create a new JSON file in the `config/templates/extension_types` directory
2. Name it according to the extension type (e.g., `skill_tracker.json`)
3. Follow the extension type schema format
4. Include the `extension_type` field with a unique identifier
5. Define the schema and defaults
6. Reload the configuration

## Important Notes

- Changes to templates only affect new data or when validation occurs
- Existing user insights will not be automatically updated
- Always validate your JSON before saving to avoid syntax errors
- The system will create default templates if they don't exist 