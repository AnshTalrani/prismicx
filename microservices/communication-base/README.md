# Communication Base Microservice

## 🔄 Architecture Upgrade Notice

**The system has been fully migrated to the new architecture.** 

The following legacy components have been removed:
- Repository components in `src/repository/`
- Storage components: `conversation_store.py` and `user_profile_store.py`
- NLP processor: `nlp_processor.py`
- Vector store components: `vectorstore_manager.py` and `vector_store.py`

All code now uses the improved implementations with enhanced capabilities.

## Overview

The Communication Base microservice provides core language model functionality and communication capabilities for all bots in the system. It acts as the central hub for natural language processing, context management, retrieval-augmented generation (RAG), and session tracking.

## Architecture

The microservice follows a worker-based processing model:

- **Campaign Poller**: Continuously checks for new batch requests with servicetype="communication"
- **Campaign Manager**: Manages campaign conversations and state
- **Worker Service**: Processes individual conversations using a worker pool
- **Repositories**: Handle data persistence in MongoDB

## Agent-Based Campaign Processing

Campaigns are created and processed through agent batch requests:

1. **Agent Microservice**:
   - Creates batch requests in the `agent_batch_requests` collection
   - Sets `servicetype="communication"` to target this microservice
   - Includes campaign template and recipient information

2. **Batch Request Format**:
   ```json
   {
     "_id": "batch_request_id",
     "name": "Campaign Name",
     "servicetype": "communication",
     "status": "new",
     "created_by": "agent",
     "created_at": "2023-04-12T14:30:00Z",
     "template": {
       "template_type": "campaign",
       "global_settings": { ... },
       "stages": [ ... ]
     },
     "recipients": [
       {"id": "user1", "contact_info": {...}},
       {"id": "user2", "contact_info": {...}}
     ],
     "scheduled_at": "2023-04-15T09:00:00Z"
   }
   ```

3. **Campaign Processing Flow**:
   - The campaign poller detects batch requests with `servicetype="communication"`
   - A campaign is created from the batch request
   - If scheduled for the future, the campaign is set to "scheduled" status
   - Otherwise, it's set to "pending" for immediate processing
   - The campaign manager initializes conversations for all recipients
   - The worker service processes conversations through their stages
   - The campaign completes when all conversations reach a final state

4. **Campaign Status Flow**:
   - **pending**: Ready for immediate processing
   - **initializing**: Campaign conversations being created
   - **active**: Campaign is running and conversations are being processed
   - **completed**: All conversations have reached a final state
   - **failed**: Campaign encountered errors during processing

5. **Batch Request Status Flow**:
   - **new**: Initial status when created by agent
   - **processing**: Being processed by the communication-base microservice
   - **completed**: Campaign successfully created
   - **failed**: Error occurred during processing

## Campaign Template Structure

Campaigns use templates that define stages, content, and progression rules:

```json
{
  "template_type": "campaign",
  "global_settings": {
    "follow_up_days": 3,
    "reminder_count": 1,
    ...
  },
  "stages": [
    {
      "stage": "awareness",
      "content_structure": { ... },
      "variables": { ... },
      "completion_criteria": { ... },
      "follow_up_timing": { ... },
      "conversation_guidance": { ... }
    },
    ...
  ]
}
```

Each stage defines:
- Content structure and variables
- Completion criteria
- Follow-up timing settings
- Conversation guidance for LLM

## Conversation Processing

Conversations progress through stages based on defined criteria:

1. **Stage Progression**:
   - Each conversation starts at the initial stage
   - Conversations are evaluated for progression to the next stage
   - Progression is based on completion criteria and timing rules

2. **Worker Processing**:
   - Workers process conversations in parallel
   - Each conversation is processed at its scheduled time
   - Workers handle message sending, status updates, and stage progression

3. **Conversation States**:
   - **pending**: Waiting to be processed
   - **processing**: Currently being processed by a worker
   - **completed**: Conversation has completed all stages
   - **failed**: Error occurred during processing

## Configuration

The microservice can be configured through environment variables:

```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=communication
LOG_LEVEL=info
CAMPAIGN_POLL_INTERVAL_SECONDS=60
WORKER_COUNT=5
BATCH_SIZE=10
```

## Monitoring

The microservice provides metrics for monitoring:

1. **Campaign Metrics**:
   - Counts of campaigns by status
   - Conversion rates
   - Completion rates

2. **Conversation Metrics**:
   - Stage progression rates
   - Time spent in each stage
   - Response rates

3. **Worker Metrics**:
   - Active worker count
   - Processing throughput
   - Error rates

## Error Handling

The system includes comprehensive error handling:

1. **Request Validation**:
   - Batch requests are validated before processing
   - Invalid requests are marked as failed with error details

2. **Processing Errors**:
   - Campaign processing errors are logged and the campaign is marked as failed
   - Conversation errors are retried with exponential backoff

3. **Recovery**:
   - Failed conversations can be reprocessed manually
   - The system can resume processing after restarts

## Features

- Campaign management (creation, scheduling, tracking)
- Conversation state tracking across multiple stages
- Asynchronous processing via worker services
- RESTful API for campaign and conversation management
- Prometheus metrics for monitoring
- Health endpoints for container orchestration

## API Usage (Alternative Method)

While the worker-first approach is preferred for production use, the service also provides a RESTful API for campaign and conversation management:

```bash
# Create a campaign (alternative to direct MongoDB insertion)
curl -X POST http://localhost:8000/api/v1/campaigns/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Example Campaign",
    "type": "email",
    "content": { ... },
    "recipients": [ ... ],
    "scheduled_at": "2023-10-15T14:30:00Z"
  }'

# Get campaign status
curl http://localhost:8000/api/v1/campaigns/123e4567-e89b-12d3-a456-426614174000

# Get campaign metrics
curl http://localhost:8000/api/v1/campaigns/123e4567-e89b-12d3-a456-426614174000/metrics
```

## MongoDB Schema

### Campaigns Collection

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Example Campaign",
  "type": "email",
  "status": "pending",
  "content": { ... },
  "recipients": [ ... ],
  "created_at": "2023-10-10T12:00:00Z",
  "scheduled_at": "2023-10-15T14:30:00Z",
  "metadata": { ... }
}
```

### Conversation States Collection

```json
{
  "id": "456e7890-e12b-34d5-a678-426614174000",
  "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
  "recipient_id": "user123",
  "status": "pending",
  "current_stage": "awareness",
  "stages": { ... },
  "history": [ ... ],
  "created_at": "2023-10-10T12:05:00Z",
  "next_processing_time": "2023-10-15T14:35:00Z",
  "metadata": { ... }
}
```

## Running the Service

### Docker

```