# Agent Microservice

The Agent microservice is responsible for handling user requests, processing them through appropriate execution templates, and returning results.

## Key Features

- Request processing through templated execution
- Context management for request and execution state
- Batch processing capabilities
- Integration with other microservices
- Task Repository Service integration for task storage

## Architecture

The service follows the MACH architecture (Microservices, API-first, Cloud-native, Headless) and is designed with clear separation of concerns:

- **API Layer**: Handles incoming requests and provides REST endpoints
- **Application Layer**: Contains the business logic
- **Domain Layer**: Defines the core entities and business rules
- **Infrastructure Layer**: Provides implementations for external services

## Context Management System

The microservice includes a robust context management system that handles:

1. **Task Storage**: Integration with the central Task Repository Service in the database layer
2. **Context Lifecycle**: Managing contexts from creation to completion
3. **Output Routing**: Directing completed contexts to appropriate destinations
4. **Auto-Cleanup**: TTL-based automatic deletion of completed contexts after 24 hours

The system consists of several key components with clear separation of responsibilities:

- **TaskRepositoryAdapter**: Connects to the Task Repository Service in the database layer
- **ContextManager**: Coordinates workflow based on rules and conditions, and manages context cleanup
- **RequestService**: Creates and manages contexts during request processing, including batch operations
- **BatchProcessor**: Orchestrates batch jobs without direct context management, delegating to RequestService
- **OutputManager**: Routes completed contexts to appropriate destinations

### Recent Updates

The context management system has been significantly refactored:

- Removed direct MongoDB access via MongoContextRepository
- Integrated with the Task Repository Service through TaskRepositoryAdapter
- Enhanced with a rule-based processing system controlled by `context_conditions.json`
- Added auto-deletion of completed contexts after 24 hours
- Integrated cleanup functionality directly into the `ContextManager` class (no separate cleanup task)
- Refactored the `BatchProcessor` to focus on job orchestration, delegating context management to `RequestService`
- Enhanced the `RequestService` with dedicated batch processing methods
- Refined architecture to implement clean separation of concerns:
  - `BatchProcessor`: Job orchestration and scheduling
  - `RequestService`: Request processing and context management
  - `ContextManager`: Workflow coordination and cleanup
  - `TaskRepositoryAdapter`: Connection to the centralized Task Repository Service

For detailed architecture documentation, see [Context Management Architecture](docs/architecture/context_management.md).

## Setup

### Requirements

- Python 3.9+
- Access to Task Repository Service in the database layer
- Docker and Docker Compose (for containerized deployment)

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Configuration

Configuration is managed through environment variables:

- `TASK_REPOSITORY_URL`: URL of the Task Repository Service
- `TASK_REPOSITORY_API_KEY`: API key for the Task Repository Service
- `SERVICE_ID`: Identifier for this service instance
- `CONTEXT_CONDITIONS_PATH`: Path to context conditions JSON file
- `COMPLETED_CONTEXT_TTL`: TTL for completed contexts in seconds
- `FAILED_CONTEXT_TTL`: TTL for failed contexts in seconds
- `CONTEXT_CLEANUP_INTERVAL_HOURS`: Interval for context cleanup (default: 24 hours)

### Running with Docker Compose

```
docker-compose up -d
```

This will start the Agent microservice with proper configuration.

## API Endpoints

- `GET /health`: Health check endpoint
- `POST /admin/context/cleanup`: Run manual context cleanup (triggers ContextManager.run_manual_cleanup)
- Other endpoints as documented in the API specification

## Development

### Directory Structure

```
microservices/agent/
├── src/
│   ├── api/               # API controllers
│   ├── application/       # Application services
│   │   ├── interfaces/    # Service interfaces
│   │   └── services/      # Service implementations
│   ├── config/            # Configuration
│   ├── domain/            # Domain models and logic
│   └── infrastructure/    # External service implementations
│       ├── repositories/  # Data repositories
│       ├── services/      # External services
│       └── tasks/         # Background tasks
├── tests/                 # Unit and integration tests
├── data/                  # Data files
│   └── context/           # Context configuration
├── docs/                  # Documentation
│   └── architecture/      # Architecture documentation
└── docker/                # Docker configuration
    └── mongodb/           # MongoDB Docker configuration
```

### Adding New Features

1. Define interfaces in the appropriate application layer
2. Implement services in the application or infrastructure layer
3. Update API endpoints as needed
4. Add tests to verify functionality

## Documentation

- [Context Management Architecture](docs/architecture/context_management.md)
- [ID Utilities](docs/architecture/id_utilities.md)

## License

[Specify license here]

## Batch Processing System

The batch processing system allows for automated, scheduled execution of requests for multiple users. It consists of several components working together:

![Batch Processing Architecture Diagram](docs/images/batch_processing_diagram.png)

### Architecture Components

1. **BatchProcessor**: Core service for orchestrating batches with focus on job management
2. **RequestService**: Handles batch processing and context management
3. **BatchScheduler**: Service for scheduling batch executions at specific times
4. **Configuration**: File-based configurations for batch definitions
5. **Context Management**: Tracking and storing batch execution status and results

### Configuration: `batch_config.json`

The `batch_config.json` file controls job-based batch definitions, schedules, and processing types. Located in `data/batch/batch_config.json`, this file defines:

```json
{
  "batch_processing_jobs": [
    {
      "job_id": "instagram_post_generation",
      "type": "individual_batch",
      "purpose_id": "instagram_generation",
      "filters": {
        "all_users": true
      },
      "schedule": {
        "frequency": "weekly",
        "day": "monday",
        "time": "01:00"
      },
      "priority": "medium",
      "retry_failed": true,
      "max_retries": 3
    },
    {
      "job_id": "niche_trend_analysis",
      "type": "batch_as_object",
      "category_type": "niche",
      "purpose_id": "trend_analysis",
      "reference": "distribute_to_members",
      "schedule": {
        "frequency": "biweekly",
        "time": "03:00"
      }
    },
    {
      "job_id": "cross_audience_niche_analysis",
      "type": "combination",
      "categories": [
        {"type": "target_audience", "all": true},
        {"type": "niche", "all": true}
      ],
      "purpose_id": "cross_factor_analysis",
      "reference": "matrix",
      "schedule": {
        "frequency": "monthly",
        "day": "15",
        "time": "05:00"
      }
    }
  ]
}
```

#### Job Types

The system supports three primary job types:

1. **Individual Batch (`individual_batch`)**: Processes individual requests for users or items
2. **Object Batch (`batch_as_object`)**: Processes a batch as a single object/entity
3. **Combination Batch (`combination`)**: Processes multiple categories together in a matrix or combined structure

#### Key Configuration Parameters

| Parameter | Description | Example Values |
|-----------|-------------|---------------|
| `job_id` | Unique identifier for the job | `"instagram_post_generation"` |
| `type` | Type of batch job | `"individual_batch"`, `"batch_as_object"`, `"combination"` |
| `purpose_id` | Purpose to execute | `"instagram_generation"` |
| `filters` | Criteria to filter items/users | `{"all_users": true}`, `{"min_likes": 1000}` |
| `schedule.frequency` | Frequency of execution | `"daily"`, `"weekly"`, `"monthly"`, `"biweekly"`, `"hourly"` |
| `schedule.day` | Day for weekly/monthly schedules | `"monday"`, `"1"` (1st of month) |
| `schedule.time` | Time for execution (24h format) | `"09:00"`, `"18:30"` |
| `priority` | Job priority level | `"high"`, `"medium"`, `"low"` |
| `retry_failed` | Whether to retry failed attempts | `true`, `false` |
| `max_retries` | Maximum number of retry attempts | `3` |

### Controlling the Batch System

#### Adding a New Batch Job

To add a new batch job:

1. Edit `data/batch/batch_config.json`
2. Add a new job entry under `batch_processing_jobs` with a unique job_id
3. Define the job type, schedule, and other parameters
4. Restart the service

#### Schedule Types

- **Daily**: Runs every day at the specified time
  ```json
  "schedule": {
    "frequency": "daily",
    "time": "09:00"
  }
  ```

- **Weekly**: Runs on specific days of the week
  ```json
  "schedule": {
    "frequency": "weekly",
    "day": "monday",
    "time": "10:30"
  }
  ```

- **Monthly**: Runs on a specific day of the month
  ```json
  "schedule": {
    "frequency": "monthly",
    "day": "1",
    "time": "08:00"
  }
  ```

- **Biweekly**: Runs twice a month (on the 1st and 15th)
  ```json
  "schedule": {
    "frequency": "biweekly",
    "time": "08:00"
  }
  ```

- **Hourly**: Runs every hour
  ```json
  "schedule": {
    "frequency": "hourly"
  }
  ```

#### Batch Job Execution Process

When a batch job is executed:

1. The job configuration is loaded from the configuration file
2. The BatchProcessor orchestrates the job execution and tracking
3. The RequestService handles context management for the batch
4. For individual batches, each item is processed according to the specified purpose
5. For object batches, the entire category is processed as a unit
6. For combination batches, multiple categories are processed together
7. Results are stored in MongoDB through the context management system
8. Status updates are logged throughout execution

## Purpose Management System

The purpose system maps user intents to execution templates. There are several related components:

### Purpose Configuration: `purpose_mapping.json`

The `purpose_mapping.json` file (located in `config/purpose_mapping.json`) defines mappings between purpose IDs, templates, and keywords:

```json
{
  "insta.post.generation": {
    "id": "IPG001",
    "service_type": "GENERATIVE",
    "template_id": "instagram_post_generator",
    "keywords": [
      "create instagram post", 
      "generate instagram post", 
      "instagram content"
    ]
  },
  // ... other purpose definitions ...
}
```

#### Key Purpose Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `id` | Unique identifier | `"IPG001"` |
| `service_type` | Type of service to use | `"GENERATIVE"` |
| `template_id` | Associated template | `"instagram_post_generator"` |
| `keywords` | Keywords for detection | `["create post", "generate content"]` |

### Purpose Domain Model

The `Purpose` entity (`domain/entities/purpose.py`) defines the structure for purposes in the domain model:

```python
@dataclass
class Purpose:
    id: str
    name: str
    description: str
    keywords: List[str]
    template_ids: List[str]
    attributes: Dict[str, Any]
    is_active: bool
    priority: int
```

### FilePurposeRepository

The `FilePurposeRepository` is responsible for loading and storing purpose entities. By default, it's configured to use `data/purposes/purposes.json`, but this file doesn't exist yet. 

When you add your `purpose_mapping.json` file, the system uses it in two separate ways:

1. `TemplateService` directly reads `purpose_mapping.json` to map purpose IDs to templates
2. `FilePurposeRepository` attempts to load purposes from `data/purposes/purposes.json`

#### Important Notes:

- The `data/purposes` directory exists but is currently empty
- The system has two conflicting sources of purpose data
- For consistency, you should either:
  - Create a `purposes.json` file in `data/purposes` with compatible format
  - Modify `FilePurposeRepository` to use `purpose_mapping.json` directly

## Recommended Actions

1. Create and maintain `data/batch/batch_config.json` for batch scheduling
2. Create and maintain `config/purpose_mapping.json` for purpose definitions
3. Consider syncing purpose data by either:
   - Creating `data/purposes/purposes.json` (in Purpose entity format)
   - Or modifying `FilePurposeRepository` to use `purpose_mapping.json`

## Additional Documentation

For more detailed information about specific components:

- [Batch Configuration Guide](docs/usage/batch_configuration_guide.md) - Detailed guide for configuring batch jobs
- [API Documentation](docs/api/README.md) - API endpoints and usage
- [Batch Processing Architecture](docs/architecture/batch_processing_architecture.md) - Architectural overview of the batch processing system 