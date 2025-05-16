# User Preference-Based Batch Processing

## Overview

The user preference-based batch processing system provides a flexible framework for executing batch jobs based on individual user preferences. This allows for personalized scheduling and processing while maintaining system efficiency through intelligent grouping of similar preferences.

## Architecture

The system consists of several key components:

1. **Management Systems**
   - User-facing interfaces where preferences are set
   - Store preferences in the Config Database
   - Provide real-time updates when preferences change

2. **Config Database**
   - Central storage for user preferences
   - Maintains configuration schemas
   - Tracks preference changes

3. **Agent Microservice**
   - Uses enhanced batch processing components
   - Reads preferences from Config Database
   - Groups users by similar preferences
   - Schedules and processes based on preferences

## Component Interaction

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│ Management      │     │                  │     │ Agent Microservice │
│ Systems         │────▶│ Config Database  │────▶│                    │
└─────────────────┘     └──────────────────┘     └────────────────────┘
        │                         ▲                        │
        │                         │                        │
        └─────────────────────────┴────────────────────────┘
                    Preference updates & feedback
```

### Preference Flow

1. User sets preferences in management system
2. Preferences stored in Config Database
3. DynamicBatchScheduler polls for preferences
4. Similar preferences grouped together
5. Schedules created for each group
6. EnhancedBatchProcessor processes users with their individual preferences

## Key Components

### ConfigDatabaseClient

Provides a client interface to the Config Database:

- Retrieves user preferences with caching
- Groups users by frequency preferences
- Monitors for preference changes
- Implements resilient connection handling

```python
await config_db_client.get_user_preferences(user_id)
await config_db_client.get_frequency_groups(feature_type)
await config_db_client.get_preference_changes()
```

### DynamicBatchScheduler

Extends the standard BatchScheduler with preference-based scheduling:

- Creates schedules based on user preferences
- Handles preference changes dynamically
- Provides fallback mechanisms
- Monitors for configuration changes

```python
await dynamic_scheduler.initialize_dynamic_schedules()
await dynamic_scheduler.schedule_preference_group(feature_type, frequency, time_key)
await dynamic_scheduler.refresh_feature_schedules(feature_type)
```

### EnhancedBatchProcessor

Extends the standard BatchProcessor with preference-based processing:

- Processes batches based on user preferences
- Customizes processing with individual preferences
- Controls concurrency and chunking
- Manages failure handling and retries

```python
await enhanced_processor.process_user_preference_batch(feature_type, frequency, time_key)
```

## Preference Schema

User preferences are stored in a structured format:

```json
{
  "tenant_id": "user123",
  "config_key": "feature_preferences",
  "config_value": {
    "instagram_posts": {
      "enabled": true,
      "frequency": "daily",
      "preferred_time": "09:00",
      "template_overrides": {
        "tone": "professional",
        "length": "medium"
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
  }
}
```

## Configuration

The system is configured through:

1. **Environment Variables**
   ```
   CONFIG_SERVICE_URL=http://config-service:8000/api/v1
   CONFIG_SERVICE_API_KEY=your_api_key_here
   CONFIG_CACHE_TTL=3600
   CONFIG_POLL_INTERVAL=60
   ```

2. **Batch Config**
   ```json
   {
     "job_id": "instagram_post_preference_based",
     "type": "individual_batch",
     "purpose_id": "instagram_generation",
     "preference_based": true,
     "feature_type": "instagram_posts",
     "priority": "high",
     "default_preferences": {
       "frequency": "weekly",
       "preferred_day": "monday",
       "preferred_time": "10:00"
     }
   }
   ```

## Example Scenarios

### Scenario 1: Instagram Post Generation

- 2000 users want daily posts (9 AM)
- 100 users want weekly posts (Monday)
- 900 users want monthly posts (1st of month)

The system:
1. Creates three primary schedules (daily, weekly, monthly)
2. Further segments by specific time preferences
3. Processes each group efficiently
4. Applies individual user preferences during processing

### Scenario 2: User Changes Preference

When a user changes from daily to weekly posting:
1. Management system updates Config Database
2. DynamicBatchScheduler detects change during polling
3. User is removed from daily group and added to weekly group
4. Change takes effect at next scheduled run

## Performance Considerations

- User preferences are cached (default: 1 hour TTL)
- Similar preferences are processed together
- Processing occurs in controlled chunks (max 25 users)
- Parallel processing with concurrency limits
- Exponential backoff for retries

## Integration Requirements

### Management Systems
- Must implement preference storage API
- Should validate preferences against schemas
- Need to track preference changes

### Config Database
- Requires REST API for preference access
- Must support filtering by feature type
- Should implement change tracking

### Agent Microservice
- Uses DynamicBatchScheduler
- Uses EnhancedBatchProcessor
- Requires configuration for integration

## Deployment

The system is deployed as part of the microservices architecture:

```yaml
# docker-compose.yml excerpt
services:
  agent:
    environment:
      - CONFIG_SERVICE_URL=http://config-service:8000/api/v1
      - CONFIG_SERVICE_API_KEY=${CONFIG_API_KEY}
      - CONFIG_CACHE_TTL=3600
      - CONFIG_POLL_INTERVAL=60
    depends_on:
      - config-service
      
  config-service:
    image: prismicx/config-service:latest
    environment:
      - DATABASE_URL=${CONFIG_DB_URL}
```

## Conclusion

The user preference-based batch processing system provides a flexible, efficient way to handle batch processing with personalized scheduling and processing options. By intelligently grouping similar preferences while still respecting individual settings, the system balances personalization with system efficiency. 