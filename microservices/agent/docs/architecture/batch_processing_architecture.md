# Batch Processing Architecture

## Overview

The batch processing system in the Agent microservice provides a robust framework for processing multiple requests efficiently, with support for different batch types, scheduling options, and result distribution mechanisms. This document outlines the architecture, components, and design decisions underlying the batch processing system.

## Key Components

The batch processing system consists of several core components that work together to provide a flexible and scalable solution:

### 1. BatchProcessor

The BatchProcessor is the central component responsible for executing batch jobs. It supports four distinct processing strategies:

#### Individual Batch Processing

In this mode, the BatchProcessor:
- Fetches individual items from a category based on specified filters
- Creates a separate request for each item
- Processes each request independently (with optional parallelism)
- Collects and aggregates results
- Tracks progress and handles failures

This approach is ideal for scenarios where each item needs to be processed separately, such as generating content for multiple users.

#### Object Batch Processing

In this mode, the BatchProcessor:
- Fetches data for an entire category as a single entity
- Creates a single request containing all category data
- Processes the request as a unified object
- Stores the results as a single entity
- Optionally distributes the results to specified users

This approach is best for analytical tasks that need to consider an entire dataset, such as trend analysis.

#### Combined Batch Processing

In this mode, the BatchProcessor:
- Fetches data from multiple categories
- Combines the data into a structured request
- Processes the combined data to generate cross-category insights
- Stores and distributes the combined results

This approach enables complex analysis across different data types, such as finding correlations between audience preferences and niche topics.

#### Preference-Based Batch Processing

In this mode, the BatchProcessor:
- Retrieves user preferences from the Config Database
- Groups users with similar preferences (e.g., all users who want daily content at 9 AM)
- Creates dynamic schedules based on preference groups
- Applies individual user preferences during processing
- Tracks results per user and tenant
- Adapts to preference changes in real-time

This approach enables personalized scheduling and processing based on individual user preferences while maintaining system efficiency through intelligent grouping.

### 2. BatchScheduler

The BatchScheduler manages the timing and execution of batch jobs:

- Loads batch configurations from the configuration file
- Creates cron-based schedules for each job
- Supports dynamic preference-based scheduling
- Triggers job execution at the scheduled times
- Handles prioritization when multiple jobs are scheduled simultaneously
- Monitors job execution and handles failures
- Provides status updates for scheduled jobs
- Detects and adapts to user preference changes

The scheduler supports various frequency options (hourly, daily, weekly, monthly, biweekly) with flexible timing parameters and can create schedules dynamically based on user preferences.

### 3. ContextManager

The ContextManager provides context management and persistence for batch operations:

- Creates and manages batch-level contexts for tracking progress and results
- Stores individual request contexts during processing
- Manages batch references that allow users to access relevant results
- Provides persistence for both immediate and long-term access to batch data
- Enables merging of contexts for complex operations
- Supports specialized contexts for preference-based processing
- Maintains tenant association for multi-tenant environments

### 4. CategoryRepository

The CategoryRepository is responsible for providing access to the data needed for batch processing:

- Retrieves individual items based on filters and limits
- Fetches category data for object-based processing
- Supports complex filtering to select specific subsets of data
- Implements caching to improve performance for frequently accessed data
- Provides fallback mechanisms for service unavailability
- Supports preference-based filtering and processing
- Enables tenant-specific data access patterns

### 5. ConfigDatabaseClient

The ConfigDatabaseClient provides access to user preferences and configuration data:

- Retrieves user preferences from the Config Database
- Groups users by similar preferences for efficient processing
- Caches frequently accessed preferences to improve performance
- Monitors preference changes for real-time adaptation
- Supports multi-tenant environments with optimized data access
- Provides fallback mechanisms for service unavailability

### 6. UserRepository

The UserRepository provides direct access to the system_users database for efficient user validation:

- Validates user existence without requiring API calls to user service
- Optimizes batch processing by filtering out invalid users early in the process
- Reduces network overhead and improves performance
- Supports efficient validation of user references within categories
- Maintains statistics on valid and invalid users for monitoring
- Validates users for both direct user batches and user references in categories

## Batch Processing Matrix

The batch processing system is built around a matrix model that defines different batch types based on two key dimensions:

### Basic Matrix (2x2)

1. **Processing Method**:
   - **INDIVIDUAL**: Each item is processed separately
   - **BATCH**: Multiple items are processed together

2. **Data Source Type**:
   - **USERS**: Data comes from or is associated with users
   - **CATEGORIES**: Data comes from category repositories

This creates four basic batch types:
- INDIVIDUAL_USERS: Process each user separately
- INDIVIDUAL_CATEGORIES: Process each category item separately
- BATCH_USERS: Process multiple users together
- BATCH_CATEGORIES: Process entire categories together

### Extended Matrix with Preference Dimension

The matrix is extended with a preference dimension:

3. **Preference Source**:
   - **STATIC**: Uses statically defined configuration
   - **DYNAMIC**: Uses user preferences from Config Database

This creates additional batch types:
- PREFERENCE_INDIVIDUAL_USERS: Process each user based on their preferences
- PREFERENCE_INDIVIDUAL_CATEGORIES: Process category items based on user preferences
- PREFERENCE_BATCH_USERS: Process multiple users together based on grouped preferences
- PREFERENCE_BATCH_CATEGORIES: Process entire categories based on user preferences

The preference dimension adds the capability to dynamically schedule and process batches based on user-defined preferences, while still leveraging the efficiency of the existing matrix model.

## Processing Flow

The batch processing system follows a well-defined flow:

1. **Configuration Loading**:
   - The system loads batch configurations from a JSON configuration file.
   - Each job configuration specifies the type, schedule, filters, and other parameters.
   - Preference-based jobs identify their feature type for preference matching.

2. **User Validation**:
   - Before processing begins, user IDs are validated against the system_users database.
   - Invalid users are filtered out early to optimize processing resources.
   - Validation statistics are captured and stored in the batch context.
   - For category batches with user references, those references are also validated.

3. **Job Scheduling**:
   - The BatchScheduler creates cron-based schedules for static jobs.
   - For preference-based jobs, it creates dynamic schedules based on user preference groups.
   - Jobs are prioritized based on their configured priority levels.

4. **Job Execution**:
   - When a job is triggered (either by schedule or manually), the BatchProcessor is invoked.
   - The processor determines the batch type (individual, object, combined, or preference-based).
   - A batch context is created to track progress and store results, including validation statistics.
   - For preference-based jobs, a specialized preference batch context is created.

5. **Data Retrieval**:
   - For standard jobs, the CategoryRepository is used to retrieve the required data.
   - For preference-based jobs, user preferences are retrieved from the Config Database.
   - Data retrieval may be customized based on user preferences.

6. **Processing**:
   - For individual batches, items are processed in parallel with controlled concurrency.
   - For object batches, the entire category is processed as a single entity.
   - For combined batches, multiple categories are processed together.
   - For preference batches, user-specific contexts are created and processed with their preferences.

7. **Result Handling**:
   - Results are stored in the batch context.
   - For preference-based jobs, results are organized by user and tenant.
   - Progress is tracked and updated throughout the processing.
   - Failed items may be retried based on configuration.

8. **Distribution**:
   - If configured, results are distributed to specified users.
   - Batch references are created in user contexts to provide access to the results.
   - For preference-based jobs, results are delivered to the respective users.

9. **Status Reporting**:
   - Status information is available through the API.
   - For preference-based jobs, status can be viewed by user, tenant, or feature type.
   - Logs and metrics are generated for monitoring.

10. **Preference Change Handling**:
    - The BatchScheduler monitors for preference changes.
    - When detected, affected schedules are updated automatically.
    - Users are moved between preference groups as needed.
    - Processing continues uninterrupted with the updated preferences.

## Design Decisions

Several key design decisions shape the batch processing architecture:

### 1. Job-Based Configuration

The system uses a configuration-driven approach that allows:
- Defining jobs in a structured JSON format
- Modifying job parameters without code changes
- Supporting different batch types with specific parameters
- Enabling flexible scheduling options
- Specifying preference-based processing requirements

This design promotes extensibility and reduces the need for code modifications when adding or changing jobs.

### 2. Separation of Scheduling and Processing

By separating the BatchScheduler from the BatchProcessor:
- Scheduling concerns are isolated from processing logic
- Jobs can be triggered both on schedule and on-demand
- The scheduler can be modified independently from the processor
- Different scheduling strategies can be implemented without affecting processing
- Preference-based dynamic scheduling can be added without disrupting static scheduling

### 3. Extended Batch Type System

Supporting multiple distinct batch types:
- Provides flexibility for different use cases
- Optimizes resource usage for each scenario
- Enables complex cross-category analysis
- Allows for preference-based personalization
- Simplifies the addition of new batch types in the future

### 4. Context-Based State Management

Using the context service for state management:
- Provides persistence for batch state
- Enables recovery from failures
- Facilitates result sharing and distribution
- Maintains a history of batch executions and results
- Supports specialized contexts for preference-based batches
- Enables tenant-specific context tracking

### 5. Pluggable Repository Architecture

Implementing repositories as interfaces with concrete implementations:
- Decouples data access from processing logic
- Enables different data sources to be used
- Allows for caching and performance optimizations
- Provides fallback mechanisms for resilience
- Supports preference-based filtering and processing

### 6. User Preference Integration

Integrating with the Config Database for user preferences:
- Enables personalized scheduling and processing
- Allows for dynamic adaptation to preference changes
- Supports multi-tenant environments
- Provides caching for improved performance
- Maintains backward compatibility with static job configurations

### 7. Direct Database Validation

Implementing direct database access for user validation:
- Eliminates network overhead from API calls to user service
- Improves performance for large batch operations
- Enables early filtering of invalid users
- Maintains detailed validation statistics
- Reduces load on other microservices
- Supports validation of user references in categories

## Integration Points

The batch processing system integrates with several other components:

### 1. Request Service

- Processes individual requests created by the BatchProcessor
- Handles template execution and result processing
- Provides a consistent interface for different request types

### 2. Template Service

- Provides execution templates used by the batch jobs
- Defines how requests should be processed
- Enables consistent processing across batch items
- Supports template overrides from user preferences

### 3. External Services

- Generative, Analysis, and Communication services process the actual requests
- Each service has a specific client adapter in the infrastructure layer
- Results from these services are standardized and incorporated into batch results

### 4. Config Database

- Stores and manages user preferences
- Provides an API for retrieving and updating preferences
- Supports multi-tenant environments
- Enables efficient retrieval of grouped preferences
- Tracks changes to preferences for real-time adaptation

### 5. API Layer

- Provides endpoints for creating, monitoring, and managing batch jobs
- Enables access to batch results and statuses
- Allows for manual triggering of batch jobs
- Supports tenant-specific views of batch results

### 6. System Users Database

- Provides direct access to user data through the UserRepository
- Enables efficient validation of user IDs
- Supports validation of user references in category data
- Maintains statistics on valid and invalid users

## Performance Considerations

The batch processing system includes several features to ensure optimal performance:

### 1. Controlled Concurrency

- Processing of individual items is parallelized with a configurable concurrency limit
- This prevents overloading the system while maximizing throughput
- Concurrency limits can be set differently for different job types

### 2. Chunked Processing

- Large batches are processed in chunks to manage memory usage
- Progress is tracked at the chunk level for better monitoring
- Chunk size is configurable through environment variables

### 3. Caching

- The CategoryRepository implements caching to reduce repeated data access
- The ConfigDatabaseClient caches user preferences to improve performance
- Cache TTL is configurable through environment variables

### 4. Prioritization

- Jobs are prioritized based on their configuration
- Critical jobs are executed before lower-priority jobs when scheduled simultaneously
- Long-waiting jobs are gradually promoted to prevent starvation

### 5. Efficient Preference Grouping

- Users with similar preferences are grouped together
- This reduces the number of schedules and optimizes processing
- Groups are updated dynamically as preferences change

## Error Handling and Resilience

The system implements robust error handling and resilience mechanisms:

### 1. Automatic Retries

- Failed items can be automatically retried with configurable limits
- Exponential backoff is used to prevent overwhelming the system
- Different retry strategies can be applied to different job types

### 2. Fallback Mechanisms

- Repositories provide fallback mechanisms when services are unavailable
- Default preferences can be specified for preference-based jobs
- This ensures that batch processing can continue even if some dependencies are temporarily down

### 3. Progress Tracking

- Detailed progress is tracked and persisted
- This allows for recovery and resumption of batch processing
- Tenant-specific progress tracking is available for multi-tenant environments

### 4. Status Monitoring

- Comprehensive status information is available through the API
- Logs provide detailed information about execution and failures
- Metrics are generated for monitoring and alerting

### 5. Enhanced Validation Tracking

- Detailed tracking of user validation results
- Statistics on valid and invalid users/categories
- Clear identification of invalid user references
- Improved logging for validation failures

## Batch Context Format

The batch context has been enhanced to provide better tracking of validation results:

```json
{
  "results": {
    "metadata": {
      // Job-specific metadata
    },
    "items": {
      "valid_users": ["user1", "user2", "..."],
      "invalid_users": ["invalid1", "invalid2", "..."]
    },
    "progress": {
      "processed": 10,
      "succeeded": 8,
      "failed": 2,
      "total": 10,
      "percentage": 100
    },
    "validation": {
      "total": 12,
      "valid": 10,
      "invalid": 2
    }
  }
}
```

For category batches that include user references, the validation information is extended:

```json
{
  "results": {
    "metadata": {
      "data_source_type": "categories",
      "category_type": "product_category",
      "user_references": {
        "total": 8,
        "valid": 6,
        "invalid": 2
      }
    },
    "items": {
      "valid_categories": ["cat1", "cat2", "..."],
      "invalid_categories": []
    },
    // ... other fields ...
  }
}
```

This enhanced context format improves monitoring, debugging, and reporting capabilities for batch operations.

## Future Enhancements

The batch processing architecture is designed to accommodate future enhancements:

### 1. Advanced Scheduling

- Support for more complex scheduling patterns
- Dynamic scheduling based on system load or external triggers

### 2. Batch Dependencies

- Definition of dependencies between batch jobs
- Sequential or conditional execution based on results

### 3. Distributed Processing

- Distribution of batch processing across multiple nodes
- Centralized coordination with distributed execution

### 4. Advanced Monitoring

- Real-time monitoring dashboards
- Predictive analysis for job duration and resource usage

### 5. Custom Batch Types

- Framework for defining custom batch types
- Plugin architecture for extending processing capabilities 