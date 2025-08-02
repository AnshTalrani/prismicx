# Batch Configuration Guide

This guide provides detailed information on configuring batch processing jobs within the Agent microservice. The batch processing system supports various job types, scheduling options, and result distribution mechanisms.

## Table of Contents

1. [Overview](#overview)
2. [Configuration Structure](#configuration-structure)
3. [Job Types](#job-types)
4. [Scheduling Options](#scheduling-options)
5. [Priority Levels](#priority-levels)
6. [Filtering Options](#filtering-options)
7. [Result Distribution](#result-distribution)
8. [User Preference Integration](#user-preference-integration)
9. [Complete Examples](#complete-examples)
10. [Troubleshooting](#troubleshooting)
11. [User Validation in Batch Processing](#user-validation-in-batch-processing)

## Overview

The batch processing system allows you to process multiple requests efficiently, either as individual items or as grouped objects. Batch jobs can be scheduled to run at specific times or triggered immediately through the API.

Key features:
- Support for different batch types (individual, object, combined, preference-based)
- Flexible scheduling options (hourly, daily, weekly, monthly)
- Priority-based execution
- Automatic retries for failed items
- Result distribution to users
- User preference-based scheduling and processing

## Configuration Structure

Batch jobs are configured using a JSON structure that defines how, when, and what to process. The configuration file is located at `microservices/agent/src/config/batch_config.json`.

### Basic Structure

```json
{
  "batch_processing_jobs": [
    {
      "id": "unique_job_id",
      "name": "Job Name",
      "description": "Description of the job",
      "type": "individual|object|combined|preference",
      "priority": "low|medium|high|critical",
      "category": "category_name",
      "template_id": "template_id",
      "schedule": {
        "frequency": "hourly|daily|weekly|monthly|biweekly",
        "at": "15:00",
        "days": ["Monday"],
        "day_of_month": 1
      },
      "filters": {},
      "limit": 1000,
      "retry_limit": 3,
      "distribute_results": true,
      "distribution": {
        "users": ["user_id_1", "user_id_2"]
      },
      "purpose_id": "purpose_id",
      "preference_based": false,
      "feature_type": "feature_type"
    }
  ]
}
```

### Required Fields

| Field | Description |
|-------|-------------|
| `id` | Unique identifier for the job. Should use the format `bat_{source}_{timestamp}_{random}` (e.g., `bat_scheduled_job_20230415123045_e5f6g7h8`) for better traceability. |
| `name` | Display name of the job |
| `type` | Type of batch job (individual, object, combined, or preference) |
| `template_id` | ID of the execution template to use |

### Optional Fields

| Field | Description | Default |
|-------|-------------|---------|
| `description` | Detailed description of the job | `""` |
| `priority` | Priority level for the job | `"medium"` |
| `schedule` | Scheduling information (if omitted, job must be triggered manually) | `null` |
| `filters` | Filters to apply when selecting items | `{}` |
| `limit` | Maximum number of items to process | `1000` |
| `retry_limit` | Maximum number of retries for failed items | `3` |
| `distribute_results` | Whether to distribute results to users | `false` |
| `distribution` | Configuration for result distribution | `null` |
| `purpose_id` | Purpose ID for categorizing the job | `null` |
| `preference_based` | Whether this job uses user preferences | `false` |
| `feature_type` | Type of feature for preference-based jobs | `null` |

## Job Types

The batch processing system supports four types of batch jobs:

### Individual

Individual batch jobs process each item separately. This is useful when you need to perform the same operation on multiple independent items, such as generating content for multiple users.

```json
{
  "id": "bat_scheduled_job_20230415123045_a1b2c3d4",
  "name": "Instagram Post Generation",
  "type": "individual",
  "category": "users",
  "template_id": "tpl_api_20230414153012_f7g8h9j0",
  "filters": {
    "min_followers": 1000,
    "has_profile_pic": true
  }
}
```

### Object

Object batch jobs process an entire category as a single entity. This is useful for analytics tasks that need to consider all data together, such as trend analysis.

```json
{
  "id": "bat_scheduled_job_20230416091530_b2c3d4e5",
  "name": "Niche Trend Analysis",
  "type": "object",
  "category": "niche",
  "template_id": "tpl_api_20230414160045_g7h8i9j0",
  "filters": {
    "min_posts": 100
  }
}
```

### Combined

Combined batch jobs process multiple categories together. This is useful for cross-category analysis, such as finding correlations between audience preferences and niche topics.

```json
{
  "id": "bat_scheduled_job_20230417103000_c3d4e5f6",
  "name": "Cross-Analysis of Audience and Niche",
  "type": "combined",
  "categories": ["audience", "niche"],
  "template_id": "tpl_api_20230415143022_h8i9j0k1",
  "filters": {
    "audience": {
      "min_size": 1000
    },
    "niche": {
      "min_engagement": 5.0
    }
  }
}
```

### Preference-Based

Preference-based batch jobs process items based on user preferences stored in the Config Database. This type of job is dynamically scheduled based on user-defined frequencies and times.

```json
{
  "id": "bat_pref_instagram_posts_20230501123045_d4e5f6g7",
  "name": "Preference-Based Instagram Posts",
  "type": "individual",
  "preference_based": true,
  "feature_type": "instagram_posts",
  "template_id": "tpl_api_20230414153012_f7g8h9j0",
  "priority": "high"
}
```

In preference-based jobs:
- The scheduling is determined by user preferences, not by the job configuration
- Users are grouped by similar preferences (e.g., all users who want daily posts at 9:00 AM)
- Each user's preferences are applied during processing
- The job scales automatically as users change their preferences

## Scheduling Options

Batch jobs can be scheduled to run at specific times using the `schedule` configuration.

### Frequency Options

| Frequency | Description | Additional Fields |
|-----------|-------------|-------------------|
| `hourly` | Run every hour | `minute` (default: 0) |
| `daily` | Run every day | `at` (time in HH:MM format) |
| `weekly` | Run on specific days of the week | `at`, `days` (array of day names) |
| `biweekly` | Run every two weeks | `at`, `days` |
| `monthly` | Run on specific days of the month | `at`, `day_of_month` |

### Examples

#### Hourly Schedule

```json
"schedule": {
  "frequency": "hourly",
  "minute": 30
}
```

Runs every hour at 30 minutes past the hour.

#### Daily Schedule

```json
"schedule": {
  "frequency": "daily",
  "at": "03:00"
}
```

Runs every day at 3:00 AM.

#### Weekly Schedule

```json
"schedule": {
  "frequency": "weekly",
  "days": ["Monday", "Thursday"],
  "at": "15:30"
}
```

Runs every Monday and Thursday at 3:30 PM.

#### Biweekly Schedule

```json
"schedule": {
  "frequency": "biweekly",
  "days": ["Wednesday"],
  "at": "09:00"
}
```

Runs every other Wednesday at 9:00 AM.

#### Monthly Schedule

```json
"schedule": {
  "frequency": "monthly",
  "day_of_month": 1,
  "at": "00:15"
}
```

Runs on the 1st day of each month at 00:15 AM.

## Priority Levels

Batch jobs can be assigned priority levels that determine their execution order when multiple jobs are scheduled at the same time.

| Priority | Description |
|----------|-------------|
| `low` | Lowest priority, executed after all higher priority jobs |
| `medium` | Default priority level |
| `high` | High priority, executed before medium and low priority jobs |
| `critical` | Highest priority, executed before all other jobs |

Example:

```json
"priority": "high"
```

## Filtering Options

Filters allow you to specify which items should be included in a batch job. The available filters depend on the category being processed.

### Common Filters

| Filter | Description | Example |
|--------|-------------|---------|
| `min_followers` | Minimum follower count (users) | `{"min_followers": 1000}` |
| `min_engagement` | Minimum engagement rate | `{"min_engagement": 3.5}` |
| `max_items` | Maximum number of items to include | `{"max_items": 500}` |
| `created_after` | Include items created after date | `{"created_after": "2023-01-01"}` |
| `tags` | Include items with specific tags | `{"tags": ["fashion", "beauty"]}` |

### Category-Specific Filters

Different categories may support additional filters. Consult the category documentation for details.

## Result Distribution

Batch jobs can distribute their results to specific users by setting `distribute_results` to `true` and configuring the `distribution` object.

```json
"distribute_results": true,
"distribution": {
  "users": ["user_id_1", "user_id_2"]
}
```

When results are distributed, users will receive a reference to the batch results in their context, which they can access through the API.

## User Preference Integration

The batch processing system integrates with user preferences stored in the Config Database. This allows for dynamic scheduling based on user-specific requirements rather than just static configurations.

### Architecture Components

The preference-based batch processing system consists of several components:

1. **ConfigDatabaseClient**: Retrieves and caches user preferences from the Config Database
2. **CategoryRepositoryClient**: Enhanced to support filtering and processing based on user preferences
3. **BatchScheduler**: Creates dynamic schedules based on grouped user preferences
4. **ContextManager**: Creates specialized contexts for preference-based batches
5. **BatchProcessor**: Processes users with their individual preferences

### Config Database Integration

User preferences are retrieved from the Config Database using the following endpoints:

```
GET /config/configs/{config_key}/all-tenants    # Retrieve a config for all tenants at once
GET /tenants/{tenant_id}/configs/{config_key}   # Retrieve a specific tenant's config
```

The system uses the optimized all-tenants endpoint for efficient retrieval, which significantly improves performance when dealing with many tenants.

### User Preference Schema

User preferences for batch processing follow this structure in the Config Database:

```json
{
  "features": {
    "instagram_posts": {
      "enabled": true,
      "frequency": "daily",
      "preferred_time": "09:00",
      "template_overrides": {
        "tone": "professional",
        "length": "medium",
        "categories": ["fashion", "beauty"],
        "tags": ["trendy", "seasonal"],
        "focus_areas": ["engagement", "growth"],
        "sort_by": "popularity",
        "sort_order": "desc",
        "item_limit": 10,
        "custom_filters": {
          "min_engagement": 3.5
        }
      }
    },
    "etsy_analysis": {
      "enabled": true,
      "frequency": "weekly",
      "preferred_day": "monday",
      "preferred_time": "10:00",
      "template_overrides": {
        "focus_areas": ["pricing", "description"]
      }
    }
  },
  "tenant_id": "tenant123",
  "active": true
}
```

### Preference-Based Batch Configuration

To configure a preference-based batch job, add the following to your job configuration:

```json
{
  "id": "bat_pref_instagram_posts_20230601",
  "name": "Preference-Based Instagram Posts",
  "description": "Generate Instagram posts based on user preferences",
  "type": "individual",
  "preference_based": true,
  "feature_type": "instagram_posts",
  "template_id": "tpl_instagram_post_generator",
  "priority": "high",
  "retry_limit": 3,
  "distribute_results": true,
  "default_preferences": {
    "frequency": "weekly",
    "preferred_day": "monday",
    "preferred_time": "10:00",
    "template_overrides": {
      "tone": "casual",
      "length": "short"
    }
  }
}
```

The key fields for preference-based jobs are:

| Field | Description | Required |
|-------|-------------|----------|
| `preference_based` | Set to `true` to indicate this is a preference-based job | Yes |
| `feature_type` | The feature type identifier used in user preferences | Yes |
| `default_preferences` | Default preferences to use when user preferences are not available | No |

### Dynamic Scheduling

The BatchScheduler automatically groups users with similar preferences and creates schedules accordingly:

1. For daily frequency: Users are grouped by preferred time
2. For weekly frequency: Users are grouped by preferred day and time
3. For monthly frequency: Users are grouped by preferred day of month and time

When a user changes their preference:
1. The change is recorded in the Config Database
2. The BatchScheduler detects the change during its polling interval
3. The affected schedules are updated automatically
4. The user is moved from their old schedule to the new one

### Tenant-Specific Processing

The batch processor provides tenant awareness in preference-based jobs:

1. Processing includes tenant-specific configurations
2. Results are tracked by tenant ID
3. Template overrides are applied per tenant
4. Error tracking includes tenant information

### Category Repository Integration

The CategoryRepositoryClient supports preference-based operations:

1. `get_items_with_preferences`: Retrieves items filtered by user preferences
2. `get_preference_compatible_categories`: Gets categories compatible with a feature type
3. `get_batch_data_with_preferences`: Gets batch data with preferences applied

```python
# Example usage in code
items = await category_repository.get_items_with_preferences(
    category="fashion_posts",
    user_preferences=user_preferences,
    limit=10
)
```

### Context Management

The ContextManager provides specialized contexts for preference-based processing:

1. `create_preference_batch_context`: Creates a batch context for preference-based processing
2. `create_user_preference_context`: Creates a context for an individual user with preferences

These contexts include:
- Feature type identifier
- Frequency and time information
- User-specific preferences
- Tenant awareness
- Template overrides

### Example: Preference-Based Job Configuration

```json
{
  "id": "bat_pref_instagram_posts_20230601",
  "name": "Preference-Based Instagram Posts",
  "description": "Generate Instagram posts based on user preferences",
  "type": "individual",
  "preference_based": true,
  "feature_type": "instagram_posts",
  "template_id": "tpl_instagram_post_generator",
  "priority": "high",
  "retry_limit": 3,
  "distribute_results": true,
  "default_preferences": {
    "frequency": "weekly",
    "preferred_day": "monday",
    "preferred_time": "10:00",
    "template_overrides": {
      "tone": "casual",
      "length": "short"
    }
  }
}
```

## Complete Examples

### Individual Batch Job Example

```json
{
  "id": "bat_scheduled_job_20230415123045_a1b2c3d4",
  "name": "Instagram Post Generation",
  "description": "Generate Instagram post ideas for users with at least 1000 followers",
  "type": "individual",
  "priority": "medium",
  "category": "users",
  "template_id": "tpl_api_20230414153012_f7g8h9j0",
  "schedule": {
    "frequency": "weekly",
    "days": ["Monday"],
    "at": "01:00"
  },
  "filters": {
    "min_followers": 1000,
    "has_profile_pic": true
  },
  "limit": 500,
  "retry_limit": 3,
  "distribute_results": true,
  "distribution": {
    "users": ["admin_1", "content_manager_1"]
  },
  "purpose_id": "content_generation"
}
```

### Object Batch Job Example

```json
{
  "id": "bat_scheduled_job_20230416091530_b2c3d4e5",
  "name": "Etsy Product Analysis",
  "description": "Analyze trending Etsy products with high engagement",
  "type": "object",
  "priority": "high",
  "category": "etsy_products",
  "template_id": "tpl_api_20230414160045_g7h8i9j0",
  "schedule": {
    "frequency": "weekly",
    "days": ["Wednesday"],
    "at": "02:00"
  },
  "filters": {
    "min_likes": 1000,
    "min_engagement": 4.5
  },
  "retry_limit": 2,
  "distribute_results": false,
  "purpose_id": "market_research"
}
```

### Combined Batch Job Example

```json
{
  "id": "bat_scheduled_job_20230417103000_c3d4e5f6",
  "name": "Cross-Analysis of Audience and Niche",
  "description": "Analyze correlations between audience preferences and niche topics",
  "type": "combined",
  "priority": "high",
  "categories": ["audience", "niche"],
  "template_id": "tpl_api_20230415143022_h8i9j0k1",
  "schedule": {
    "frequency": "monthly",
    "day_of_month": 15,
    "at": "05:00"
  },
  "filters": {
    "audience": {
      "min_size": 1000,
      "active_last_days": 30
    },
    "niche": {
      "min_engagement": 5.0,
      "min_posts": 100
    }
  },
  "retry_limit": 1,
  "distribute_results": true,
  "distribution": {
    "users": ["marketing_manager", "strategy_director"]
  },
  "purpose_id": "marketing_strategy"
}
```

### Batch Config Example with Multiple Jobs

```json
{
  "batch_processing_jobs": [
    {
      "id": "bat_scheduled_job_20230415123045_a1b2c3d4",
      "name": "Instagram Post Generation",
      "description": "Generate Instagram post ideas for users with at least 1000 followers",
      "type": "individual",
      "priority": "medium",
      "category": "users",
      "template_id": "tpl_api_20230414153012_f7g8h9j0",
      "schedule": {
        "frequency": "weekly",
        "days": ["Monday"],
        "at": "01:00"
      },
      "filters": {
        "min_followers": 1000,
        "has_profile_pic": true
      },
      "limit": 500,
      "retry_limit": 3,
      "distribute_results": true,
      "distribution": {
        "users": ["admin_1", "content_manager_1"]
      },
      "purpose_id": "content_generation"
    },
    {
      "id": "bat_scheduled_job_20230416091530_b2c3d4e5",
      "name": "Etsy Product Analysis",
      "description": "Analyze trending Etsy products with high engagement",
      "type": "object",
      "priority": "high",
      "category": "etsy_products",
      "template_id": "tpl_api_20230414160045_g7h8i9j0",
      "schedule": {
        "frequency": "weekly",
        "days": ["Wednesday"],
        "at": "02:00"
      },
      "filters": {
        "min_likes": 1000,
        "min_engagement": 4.5
      },
      "retry_limit": 2,
      "distribute_results": false,
      "purpose_id": "market_research"
    },
    {
      "id": "bat_scheduled_job_20230417103000_c3d4e5f6",
      "name": "Cross-Analysis of Audience and Niche",
      "description": "Analyze correlations between audience preferences and niche topics",
      "type": "combined",
      "priority": "high",
      "categories": ["audience", "niche"],
      "template_id": "tpl_api_20230415143022_h8i9j0k1",
      "schedule": {
        "frequency": "monthly",
        "day_of_month": 15,
        "at": "05:00"
      },
      "filters": {
        "audience": {
          "min_size": 1000,
          "active_last_days": 30
        },
        "niche": {
          "min_engagement": 5.0,
          "min_posts": 100
        }
      },
      "retry_limit": 1,
      "distribute_results": true,
      "distribution": {
        "users": ["marketing_manager", "strategy_director"]
      },
      "purpose_id": "marketing_strategy"
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **Job not running at scheduled time**
   - Check that the BatchScheduler service is running
   - Verify the cron expression is correct
   - Ensure the server timezone matches your expected timezone

2. **Items not being included in batch**
   - Check the filters to make sure they're not too restrictive
   - Verify that the category exists and contains data
   - Check the limit setting

3. **Results not being distributed**
   - Ensure `distribute_results` is set to `true`
   - Verify that the user IDs in the distribution list are correct
   - Check that the purpose_id is valid

4. **Preference-based job not running**
   - Verify that the Config Database is accessible
   - Check that users have preferences set for the specified feature type
   - Ensure the `CONFIG_POLL_INTERVAL` is set appropriately
   - Verify that the feature type in the job matches the preferences

### Logs

Check the logs for batch processing at:
```
microservices/agent/logs/batch_processor.log
microservices/agent/logs/batch_scheduler.log
```

### Batch Status API

You can check the status of a batch job using the API:

```
GET /api/v1/batch/{batch_id}
```

For more information, see the [API Documentation](../api/README.md).

## User Validation in Batch Processing

The batch processing system now includes enhanced user validation capabilities directly integrated with the system_users database. This provides several advantages:

1. **Improved Efficiency**: Direct database validation is faster than API calls to user services
2. **Early Filtering**: Invalid users are identified and filtered out before processing begins
3. **Better Resource Utilization**: System resources are only used for valid users
4. **Enhanced Monitoring**: Detailed validation statistics are maintained throughout processing
5. **User Reference Validation**: Category data with user references is validated for existing users

### User Batch Validation

When processing user batches, the system automatically validates each user against the system_users database:

```json
{
  "source": "user_management",
  "template_id": "user_report",
  "items": [
    {
      "id": "user_123",
      "data": {
        "report_type": "activity"
      }
    },
    {
      "id": "invalid_user",
      "data": {
        "report_type": "activity"
      }
    }
  ],
  "batch_metadata": {
    "data_source_type": "users",
    "processing_method": "individual"
  }
}
```

In this example:
- The user with ID "user_123" will be validated against the database
- If valid, the user will be processed
- The user with ID "invalid_user" will be identified as invalid
- Invalid users are excluded from processing, saving resources
- Validation statistics are included in the response and batch context

### Category Batch with User References

When processing category batches that include user references (e.g., member_ids, user_ids):

```json
{
  "source": "category_management",
  "template_id": "category_report",
  "items": [
    {
      "id": "category_123",
      "name": "Electronics",
      "user_ids": ["user_123", "invalid_user"],
      "data": {
        "report_type": "sales"
      }
    }
  ],
  "batch_metadata": {
    "data_source_type": "categories",
    "processing_method": "individual"
  }
}
```

In this example:
- Both categories and referenced users are validated
- Valid user references (user_123) are preserved
- Invalid user references (invalid_user) are identified
- Validation results are tracked in the batch context
- This information can be used by downstream processors 