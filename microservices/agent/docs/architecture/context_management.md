# Context Management System Architecture

## Overview
The Context Management System is responsible for handling and tracking request contexts throughout their lifecycle. It provides a robust framework for creating, processing, and maintaining context data, which is essential for the Agent microservice's operation.

## Architecture Components

### Context Repository (Data Layer)
- **MongoContextRepository**: Implements the `IContextRepository` interface
  - Handles all CRUD operations for context documents
  - Manages TTL (Time-To-Live) indexes for automatic deletion of completed contexts
  - Provides query capabilities for finding contexts by status, user ID, etc.
  - Directly interacts with MongoDB for data persistence
  - Contains no business logic, focusing solely on data operations

### Context Manager (Workflow Layer)
- **ContextManager**: Coordinates context workflows based on rules
  - Routes completed contexts to the Output Manager
  - Processes contexts based on status conditions (defined in `context_conditions.json`)
  - Manages periodic cleanup of old contexts directly (no separate cleanup task)
  - Delegates all data persistence operations to the repository
  - Contains no direct data manipulation, focusing solely on workflow coordination
  - Provides a manual cleanup function for administrative purposes

### Request Service (Processing Layer)
- **RequestService**: Handles request processing and context management
  - Creates and manages contexts for individual requests
  - Provides dedicated methods for batch processing (batch_request, object_batch, combined_batch, items_batch)
  - Updates context statuses and results during processing
  - Acts as the primary interface for the Batch Processor
  - Manages batch context progress tracking

### Output Manager (Output Handling Layer)
- **OutputManager**: Processes outputs from completed contexts
  - Routes outputs to appropriate destinations based on context type
  - Handles formatting and transformation of outputs if needed
  - Uses the repository for any required data access

### Batch Processor (Orchestration Layer)
- **BatchProcessor**: Focuses on job orchestration
  - Coordinates batch job execution without direct context management
  - Maintains tracking information about active batches and job statistics
  - Delegates all context operations to the RequestService
  - Routes different batch types to appropriate RequestService methods
  - Handles job scheduling and prioritization

## Data Flow
1. **Context Creation**: A new context is created with initial status "created" through the RequestService using the ContextManager
2. **Context Processing**: The context is processed based on its status and conditions
3. **Output Handling**: Outputs from completed contexts are processed by the Output Manager
4. **Context Cleanup**: Completed contexts are automatically cleaned up after their TTL expires (integrated into the Context Manager)
5. **Batch Processing**: Batch operations are orchestrated by the BatchProcessor but processed by the RequestService to maintain clean responsibility separation

## Configuration

The system is configured through several key files:

1. **`context_conditions.json`**:
   - Defines rules for processing contexts based on status
   - Specifies actions to take when status changes
   - Configures TTL settings for different status types

2. **`mongo_context_config.py`**:
   - Centralizes MongoDB connection settings
   - Defines TTL settings
   - Configures collection names and index structures

## Integration Points
- **Request Service**: Creates and manages contexts, acts as primary interface for batch operations
- **Batch Processor**: Delegates to the Request Service rather than directly managing contexts
- **Context Manager**: Handles context lifecycle and cleanup internally

## Status Flow

Contexts follow a defined status flow:

1. **created** → Initial state when context is first created
2. **processing** → Context is being processed by a service
3. **completed** → Processing completed successfully
4. **failed** → Processing failed
5. **pending** → Context is waiting for additional processing

Each status change can trigger specific actions defined in the `context_conditions.json` file.

## MongoDB Schema

### Context Document

```json
{
  "_id": "req_api_20230515120000_abc123",
  "created_at": "2023-05-15T12:00:00.000Z",
  "updated_at": "2023-05-15T12:01:30.000Z",
  "status": "completed",
  "completed_at": "2023-05-15T12:01:30.000Z",
  "request": {
    "id": "req_api_20230515120000_abc123",
    "user_id": "user123",
    "text": "Example request",
    "purpose_id": "purpose123",
    "created_at": "2023-05-15T12:00:00.000Z",
    "data": {},
    "metadata": {}
  },
  "template": {
    "id": "template123",
    "service_type": "generative",
    "version": "1.0",
    "parameters": {}
  },
  "results": {
    "output": "Example result",
    "processing_time": 1500,
    "metadata": {}
  },
  "tags": {
    "source": "api",
    "status": "completed"
  },
  "metadata": {}
}
```

### Batch Context Document

```json
{
  "_id": "bat_scheduler_20230515120000_abc123",
  "created_at": "2023-05-15T12:00:00.000Z",
  "updated_at": "2023-05-15T12:05:30.000Z",
  "status": "completed",
  "completed_at": "2023-05-15T12:05:30.000Z",
  "request": {
    "id": "bat_scheduler_20230515120000_abc123",
    "type": "batch",
    "source": "scheduler",
    "created_at": "2023-05-15T12:00:00.000Z"
  },
  "template": {
    "id": "template123",
    "service_type": "batch",
    "version": "1.0"
  },
  "results": {
    "items": {
      "item1": {
        "status": "completed",
        "context_id": "req_batch_item_20230515120001_def456",
        "completed_at": "2023-05-15T12:03:00.000Z"
      },
      "item2": {
        "status": "completed",
        "context_id": "req_batch_item_20230515120002_ghi789",
        "completed_at": "2023-05-15T12:05:00.000Z"
      }
    },
    "progress": {
      "processed": 2,
      "succeeded": 2,
      "failed": 0,
      "total": 2
    }
  },
  "tags": {
    "source": "scheduler",
    "status": "completed"
  },
  "metadata": {}
}
```

## Best Practices
- Use the Context Manager for coordinating workflow, not for data operations
- Use the Repository directly for any data operations
- Always update the status using the Context Manager to ensure proper rule processing
- For batch processing, use the BatchProcessor which delegates to the RequestService
- For long-running operations, use background tasks to update context status periodically

## Service Responsibilities

### Clear Separation of Concerns
- **BatchProcessor**: Job orchestration, scheduling, and tracking
- **RequestService**: Context creation, management, and request processing  
- **ContextManager**: Workflow coordination and cleanup
- **MongoContextRepository**: Data persistence and retrieval

## Deployment
- The Context Management System is containerized with Docker as part of the Agent microservice
- MongoDB is used as the persistence layer for context data
- Context cleanup is handled internally by the Context Manager with both automatic TTL indexes and periodic cleanup tasks

## Monitoring

Key metrics to monitor:

1. Context count by status
2. Processing time for contexts
3. Error rate
4. MongoDB storage usage
5. Cleanup task performance

## Conclusion

The Context Management System provides a robust, maintainable, and scalable architecture for handling context throughout the Agent microservice. By separating concerns between the workflow coordination (ContextManager), processing (RequestService), orchestration (BatchProcessor), and data persistence (MongoContextRepository), it offers flexibility for future enhancements while maintaining clean architecture principles. 