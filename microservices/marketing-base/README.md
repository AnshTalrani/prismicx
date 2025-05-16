# Marketing Base Microservice

This microservice handles email marketing campaigns, providing tools for creating, managing, and sending bulk email campaigns to recipients with customizable templates and tracking.

## Features

- **Batch Email Processing**: Send large campaigns in manageable batches to avoid overloading resources
- **Scheduled Campaigns**: Schedule campaigns for future delivery with precise timing
- **Template Personalization**: Personalize email content for each recipient
- **Task-based Architecture**: Process campaigns through a centralized task repository
- **Campaign Analytics**: Track delivery, opens, clicks, and other engagement metrics
- **Monitoring**: Prometheus metrics and Grafana dashboards for system health and performance

## Architecture

The system follows the MACH architecture principles (Microservices, API-first, Cloud-native, Headless) and consists of:

### Core Components

1. **Campaign Model**: Data models for campaigns, recipients, and tracking
2. **Campaign Service**: Business logic for managing and processing campaigns
3. **Task Processor**: Worker that polls for tasks and processes them in batches
4. **Campaign Processor**: Worker that executes scheduled campaigns
5. **Repositories**: Data access layer for campaigns and tasks

### Task Repository Architecture

The marketing microservice uses the centralized MongoDB task repository service for all task management:

- Tasks are stored in a central MongoDB repository managed by the task-repo-service
- The service uses a TaskRepositoryAdapter to communicate with the task repository service via its API
- All task creation, retrieval, claiming, completion, and failure operations go through this adapter
- This provides a unified task management system across all microservices

The old PostgreSQL and direct MongoDB task repository implementations have been completely removed from this microservice. All task management now goes through the centralized task repository service exclusively.

### Template Architecture

This microservice uses a simplified architecture where template content is embedded directly within each campaign:

- Each campaign is fully self-contained with its complete template definitions
- There is no separate template repository or template sharing between campaigns
- All template content is defined in the campaign JSON file
- The system extracts template content from the JSON structure during processing

This approach simplifies the architecture and ensures that all campaign data is kept together, making campaigns easier to manage, transport, and process.

### Technologies

- Python 3.10
- MongoDB for data storage
- Docker containers for deployment
- Prometheus for metrics
- Grafana for dashboards

## Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for development)

### Environment Variables

Create a `.env` file in the project root with:

```
# MongoDB for campaign storage
MONGO_USERNAME=admin
MONGO_PASSWORD=password
MONGODB_DATABASE=marketing

# Central task repository
TASK_MONGO_USERNAME=taskadmin
TASK_MONGO_PASSWORD=taskpassword
TASK_REPO_DB=agent_tasks
TASK_COLLECTION=marketing_tasks

# Worker settings
CAMPAIGN_CHECK_INTERVAL=60
TASK_CHECK_INTERVAL=30
MAX_BATCH_SIZE=100
WORKER_ID=worker-1

# Grafana
GRAFANA_PASSWORD=admin
```

### Running with Docker Compose

1. Start the services:

```bash
docker-compose up -d
```

2. Check that all services are running:

```bash
docker-compose ps
```

3. Access the API at http://localhost:8000
4. Access Grafana at http://localhost:3000 (login with admin/admin or your configured password)
5. Access Prometheus at http://localhost:9090

### Scaling Workers

To scale the campaign processor workers for higher throughput:

```bash
docker-compose up -d --scale campaign-processor=3
```

## Batch Processing Architecture

The system processes large email campaigns using a batch processing approach:

1. **Task Submission**: Campaign tasks are submitted to the central task repository via:
   - API (through the marketing API service)
   - CLI tools (see tools directory)
   - Other microservices in the ecosystem

2. **Task Processing**:
   - The Task Processor polls for pending tasks in the central repository
   - Tasks contain a complete campaign definition with embedded templates
   - Tasks are processed in batches based on the `batch_size` parameter
   - Each batch is executed with configurable retry logic

3. **Scheduled Processing**:
   - Campaigns can be scheduled for future execution
   - The Campaign Processor checks for due campaigns on a configurable interval
   - Scheduled campaigns are processed using the same batch mechanics

4. **Monitoring and Recovery**:
   - Failed batches can be automatically retried based on configuration
   - Processing metrics are exposed through Prometheus
   - Health checks ensure system stability

## Usage Examples

### Submitting a Campaign Task

Use the provided CLI tool to submit a campaign task:

```bash
python tools/submit_campaign_task.py \
  --template tools/sample_campaign.json \
  --recipients tools/sample_recipients.json \
  --count 100
```

### Checking Campaign Status

Query the API for campaign status:

```bash
curl http://localhost:8000/api/v1/campaigns/{campaign_id}/status
```

### Scheduling a Campaign

Schedule a campaign for future delivery:

```bash
curl -X POST http://localhost:8000/api/v1/campaigns/{campaign_id}/schedule \
  -H "Content-Type: application/json" \
  -d '{"scheduled_at": "2023-12-25T08:00:00Z"}'
```

## Monitoring

The system exposes the following metrics via Prometheus:

- `campaigns_processed_total`: Counter of processed campaigns by status
- `campaign_processing_seconds`: Time spent processing campaigns
- `campaign_processor_healthy`: Health status of the campaign processor

## Troubleshooting

### Worker Not Processing Tasks

1. Check the worker logs:
```bash
docker-compose logs campaign-processor
```

2. Verify MongoDB connection:
```bash
docker-compose exec mongodb mongosh -u admin -p password
```

3. Check task repository:
```bash
docker-compose exec task-repo-service curl -X GET http://localhost:8503/health
```

### Failed Campaigns

Review the campaign status and error messages:

```bash
docker-compose exec mongodb mongosh -u admin -p password marketing -e "db.campaigns.find({status: 'FAILED'}).pretty()"
```

## License

[MIT License](LICENSE)