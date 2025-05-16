# User Preference-Based Batch Processing

This document provides instructions for implementing and using the user preference-based batch processing system in the Agent microservice.

## Overview

The user preference-based batch processing system allows for:

- Dynamic scheduling based on individual user preferences
- Intelligent grouping of similar preferences for efficient processing
- Customized processing with user-specific parameters
- Real-time adaptation to preference changes

## Implementation

### Required Components

1. **ConfigDatabaseClient** (`src/infrastructure/clients/config_database_client.py`)
   - Interacts with the Config Database to retrieve user preferences
   - Implements caching and resilient connection handling

2. **DynamicBatchScheduler** (`src/infrastructure/services/dynamic_batch_scheduler.py`)
   - Extends the standard BatchScheduler with preference-based scheduling
   - Handles preference changes and monitors for configuration updates

3. **EnhancedBatchProcessor** (`src/application/services/enhanced_batch_processor.py`)
   - Extends the standard BatchProcessor with preference-based processing
   - Customizes processing with individual preferences

### Configuration

1. **Environment Variables**:
   - `CONFIG_SERVICE_URL`: URL of the Config Database service API
   - `CONFIG_SERVICE_API_KEY`: API key for authentication
   - `CONFIG_CACHE_TTL`: Cache TTL in seconds (default: 3600)
   - `CONFIG_POLL_INTERVAL`: Interval for polling changes (default: 60)
   - `BATCH_MAX_CONCURRENT_ITEMS`: Maximum concurrent items (default: 25)
   - `BATCH_RETRY_LIMIT`: Maximum retries for failed items (default: 3)

2. **Batch Configuration**:
   - Update `data/batch/batch_config.json` to include preference-based jobs
   - Add `preference_based: true` flag to jobs that should use preferences
   - Specify `feature_type` to identify which preferences to use
   - Optionally add `default_preferences` for fallback

## Preference Schema

User preferences must follow this schema in the Config Database:

```json
{
  "tenant_id": "user123",
  "config_key": "feature_preferences",
  "config_value": {
    "feature_type": {
      "enabled": true,
      "frequency": "daily|weekly|monthly",
      "preferred_time": "09:00",
      "preferred_day": "monday",
      "template_overrides": {
        // Feature-specific parameters
      }
    }
  }
}
```

## Integration

### Management Systems

Management systems must:
1. Provide user interface for setting preferences
2. Store preferences in the Config Database
3. Implement change tracking for preferences

### Config Database

The Config Database must expose:
1. `/tenants/{tenant_id}/configs/{config_key}` for retrieving preferences
2. `/preferences/groups?feature_type={feature_type}` for retrieving grouped preferences
3. `/preferences/changes?since_id={since_id}` for tracking changes

## Usage

### Setup

1. Update `main.py` to use the enhanced components:
   ```python
   config_db_client = ConfigDatabaseClient(...)
   batch_processor = EnhancedBatchProcessor(..., config_db_client=config_db_client)
   batch_scheduler = DynamicBatchScheduler(..., config_db_client=config_db_client)
   ```

2. Add preference-based jobs to `batch_config.json`:
   ```json
   {
     "job_id": "instagram_post_preference_based",
     "type": "individual_batch",
     "purpose_id": "instagram_generation",
     "preference_based": true,
     "feature_type": "instagram_posts",
     "priority": "high"
   }
   ```

3. Update Docker configuration with required environment variables:
   ```yaml
   environment:
     - CONFIG_SERVICE_URL=http://config-service:8000/api/v1
     - CONFIG_SERVICE_API_KEY=${CONFIG_API_KEY}
     - CONFIG_CACHE_TTL=3600
     - CONFIG_POLL_INTERVAL=60
   ```

### Example Usage

1. Users set their preferences in the management system
2. DynamicBatchScheduler reads preferences and creates schedules
3. EnhancedBatchProcessor processes users with their preferences
4. Results are customized based on individual preferences

## Troubleshooting

Common issues and solutions:

1. **"No users found for feature_type"**
   - Check that users have preferences set for the specified feature
   - Verify Config Database connection settings

2. **"Error connecting to Config Database"**
   - Check network connectivity to the Config Database service
   - Verify API key and URL are correct

3. **"Preferences not being detected"**
   - Check polling interval (may need to be decreased)
   - Verify the change tracking in Config Database is working

## Additional Resources

- [User Preference Batch Processing Architecture](../docs/architecture/user-preference-batch-processing.md)
- [Batch Configuration Guide](docs/usage/batch_configuration_guide.md)
- [Batch Processing Architecture](docs/architecture/batch_processing_architecture.md) 