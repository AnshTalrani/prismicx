# Task Repository Service

The Task Repository Service provides a centralized system for managing tasks in the PrismicX microservices architecture. It offers a standardized way for microservices to create, claim, and update tasks, enabling efficient coordination between different system components.

## Features

- Centralized task management with MongoDB storage
- RESTful API for task operations
- Task prioritization and filtering
- Multi-tenant support
- Atomic task claiming to prevent duplicate processing
- Standardized task lifecycle (pending → processing → completed/failed)

## Architecture

The Task Repository Service follows the MACH architecture principles:

- **Microservices-based**: Self-contained service with a single responsibility
- **API-first**: All functionality exposed through a well-defined API
- **Cloud-native**: Containerized for deployment in any environment
- **Headless**: Focuses only on backend task management functionality

## API Endpoints

### Tasks

- `POST /api/v1/tasks` - Create a new task
- `GET /api/v1/tasks/{task_id}` - Get a task by ID
- `PUT /api/v1/tasks/{task_id}` - Update a task
- `DELETE /api/v1/tasks/{task_id}` - Delete a task
- `GET /api/v1/tasks` - Get pending tasks for processing
- `POST /api/v1/tasks/{task_id}/claim` - Claim a task for processing
- `POST /api/v1/tasks/{task_id}/complete` - Mark a task as completed
- `POST /api/v1/tasks/{task_id}/fail` - Mark a task as failed

### System

- `GET /health` - Health check endpoint

## Task Client Library

A client library is provided for microservices to interact with the Task Repository Service:

```python
from database_layer.common.task_client import (
    create_task,
    get_pending_tasks,
    claim_task,
    complete_task,
    fail_task
)

# Create a task
task_id = await create_task({
    "task_type": "GENERATIVE",
    "request": {
        "content": {"text": "Generate a response to this query"},
        "metadata": {"user_id": "user123"}
    },
    "template": {
        "service_type": "GENERATIVE",
        "parameters": {"model": "gpt-4", "max_tokens": 1024}
    },
    "tags": {
        "service": "generative-service",
        "source": "agent-api"
    }
})

# Get pending tasks for a specific service
tasks = await get_pending_tasks(task_type="GENERATIVE", limit=5)

# Claim a task
task = await claim_task(task_id)

# Complete a task with results
success = await complete_task(task_id, {
    "generated_text": "This is the generated response",
    "metadata": {"tokens_used": 150}
})

# Mark a task as failed
success = await fail_task(task_id, "Failed to generate response: invalid input")
```

## Configuration

Configuration is handled through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection URI | `mongodb://task_service:password@mongodb-system:27017/task_repository` |
| `MONGODB_DATABASE` | MongoDB database name | `task_repository` |
| `MONGODB_TASKS_COLLECTION` | MongoDB collection name | `tasks` |
| `API_KEY` | API key for authentication | `dev_api_key` |
| `HOST` | Host to bind to | `0.0.0.0` |
| `PORT` | Port to listen on | `8503` |
| `SERVICE_NAME` | Service name | `task-repo-service` |

## Development

### Prerequisites

- Python 3.9+
- MongoDB 5.0+
- Docker and Docker Compose (for containerized deployment)

### Local Development

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the service:

```bash
python -m src.main
```

### Docker Deployment

The service can be deployed using Docker Compose:

```bash
docker-compose -f docker-compose.database-layer.yml up -d task-repo-service
```

## Integration with Microservices

Each microservice should:

1. Use the task client library to interact with the Task Repository Service
2. Implement a task processor that polls for pending tasks of its type
3. Claim and process tasks atomically
4. Update task status appropriately (completed/failed)

## Task Processing Flow

1. **Creation**: A microservice creates a task with status "pending"
2. **Discovery**: A worker microservice polls for pending tasks of its type
3. **Claiming**: The worker claims a task, atomically setting status to "processing"
4. **Processing**: The worker processes the task
5. **Completion**: The worker marks the task as "completed" or "failed" with results 

## Migration Plan for Centralized Task Repository

This centralized MongoDB task repository is designed to replace individual task storage implementations in each microservice. The migration will follow these steps:

### Phase 1: Dual-Writing (Current)

1. **Implement Adapters**: Create `TaskRepositoryAdapter` in each microservice that communicates with this service
2. **Deploy Task Repository Service**: Ensure task-repo-service is deployed and accessible to all microservices
3. **Configure Credentials**: Set up proper authentication for each microservice
4. **Implement Dual-Writing**: Microservices write to both their original task storage and this centralized repository

### Phase 2: Read Integration (In Progress)

1. **Update Task Processors**: Modify task processors to read from this service instead of the old implementation
2. **Monitor Success**: Track success rates and performance metrics
3. **Implement Feature Parity**: Ensure all required functionality is available through the task client
4. **Test Recovery**: Verify that task recovery and error handling work correctly

### Phase 3: Full Migration (Planned)

1. **Switch to Read/Write**: Update all microservices to both read from and write to this service exclusively
2. **Remove Old Implementations**: Remove the old task repository implementations
3. **Decommission Old Databases**: Migrate any necessary historical data and decommission old databases
4. **Update Documentation**: Ensure all documentation reflects the new architecture

### Phase 4: Optimization (Future)

1. **Performance Tuning**: Optimize MongoDB indexes and query patterns
2. **Add Caching**: Implement Redis caching for frequently accessed tasks
3. **Implement Advanced Features**: Add batch operations, analytics, and other advanced features
4. **Scale Horizontally**: Set up sharding or replica sets as needed for scale

### Current Migration Status

- ✅ Agent Microservice: Fully migrated to the centralized repository
- ✅ Marketing Base: Fully migrated to the centralized repository via adapter, old implementations removed
- ✅ Analysis Base: Using the centralized repository for task management
- ❌ Other Microservices: Pending integration

### Rollback Plan

In case of issues during migration, each microservice has a configuration flag that can be used to revert to the original task repository implementation 