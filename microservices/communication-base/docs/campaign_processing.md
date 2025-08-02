# Campaign Processing Workflow

This documentation outlines how campaigns are processed in the communication-base microservice using a worker-based architecture.

## Overview

The communication-base microservice processes campaigns through a polling mechanism that regularly checks for campaigns that need attention. The service operates in worker-only mode, with no API endpoints, focusing solely on processing campaigns received from agent batch requests.

## Key Components

1. **Campaign Poller**: Continuously polls for campaigns that need processing.
2. **Worker Service**: Processes individual conversations within campaigns.
3. **Campaign Manager**: Manages campaign state transitions and conversation flows.
4. **Conversation State Repository**: Stores and manages conversation states.
5. **Config Manager**: Processes campaign templates and timing configurations.

## Campaign Lifecycle

### 1. Campaign Creation

Campaigns originate from agent batch requests. The Campaign Poller detects these requests and creates new campaigns:

```
Agent Batch Request → Campaign Poller → New Campaign
```

### 2. Initialization

When a new campaign is detected, the Campaign Manager initializes conversation states for all recipients:

```
New Campaign → Campaign Manager → Initialize Conversation States
```

### 3. Processing Loop

The Campaign Poller continuously checks for campaigns that need action:

```
Campaign Poller
  ↓
Check Pending Campaigns
  ↓
Check Scheduled Campaigns
  ↓
Check Active Campaigns for Status Updates
  ↓
Sleep for Polling Interval
  ↓
Repeat
```

### 4. Conversation Processing

For active campaigns, the Worker Service processes each conversation:

```
Active Campaign → Get Pending Conversations → Worker Service → Process Each Conversation
```

## Processing Workflow

### Detailed Flow

1. **Campaign Detection**:
   - The Campaign Poller detects new batch requests and creates campaigns.
   - Campaigns are initially set to 'pending' status.

2. **Campaign Initialization**:
   - For pending campaigns, the Campaign Manager creates conversation states for each recipient.
   - Campaign status is updated to 'active'.

3. **Scheduled Campaign Handling**:
   - Scheduled campaigns are checked against their scheduled_at date.
   - When a scheduled campaign is due, its status is updated to 'pending'.

4. **Conversation Processing**:
   - For active campaigns, pending conversations are retrieved.
   - Each conversation is processed according to its current stage and the campaign template.
   - Worker Service handles each conversation, determining:
     - When to send the next message
     - What content to include
     - Whether to advance to the next stage
     - Whether to escalate the conversation

5. **Campaign Completion**:
   - Campaigns are marked 'completed' when:
     - All conversations have reached the final stage
     - Maximum campaign duration is reached
     - Maximum follow-up attempts are exhausted for all conversations

## Error Handling

The system includes comprehensive error handling:

- Processing errors are logged and don't affect other campaigns
- Failed conversations are retried according to configured retry policies
- System-wide failures trigger alerts via configured monitoring

## Worker Service Processing

The Worker Service processes conversations using this workflow:

```
┌─────────────────────┐
│  Retrieve Campaign  │
│    and Template     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│   Get Conversation  │
│        State        │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│Determine Next Action│
│Based on Stage Rules │
└──────────┬──────────┘
           ↓
      ┌────┴───┐
  ┌───┴───┐    │
  │ Send  │    │
  │Message│    │
  └───┬───┘    │
      │   ┌────┴───┐
      │   │ Advance│
      │   │ Stage  │
      │   └────┬───┘
      │        │
┌─────┴────────┴─────┐
│Update Conversation │
│       State        │
└─────────────────────┘
```

## Monitoring

The system provides several monitoring metrics:

- Active campaigns count
- Conversations processed per minute
- Message send success rate
- Stage advancement metrics
- Error rates by campaign type

## Configuration

The service is configured via environment variables:

```
MONGODB_URI: MongoDB connection string
MONGODB_DB: Database name
POLLING_INTERVAL_SECONDS: How often to check for campaigns (default: 60)
MAX_CONCURRENT_CAMPAIGNS: Maximum campaigns to process at once (default: 10)
MAX_CONVERSATIONS_PER_BATCH: Maximum conversations to process in one batch (default: 100)
WORKER_THREADS: Number of worker threads (default: 4)
LOG_LEVEL: Logging level (default: INFO)
```

## Docker Deployment

The service runs as a single Docker container in worker-only mode:

```dockerfile
FROM python:3.9-slim

# Copy application code
COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt

# Set environment variables
ENV PYTHONPATH=/app
ENV SERVICE_TYPE=worker

# Run with worker.sh entrypoint
CMD ["./worker.sh"]
```

The `worker.sh` script handles the startup process, health checks, and graceful shutdown.

## Integration with Agent Microservice

The communication-base microservice processes batch requests from the agent microservice:

1. The agent creates batch requests with campaign templates and recipient lists
2. The Campaign Poller discovers these requests and creates campaigns
3. The Worker Service processes these campaigns
4. Results and metrics are stored in MongoDB where they can be queried by the agent

## Best Practices

1. **Campaign Sizing**: Limit campaigns to manageable sizes (recommended: <1000 recipients per campaign)
2. **Template Design**: Create templates with clear stage progression and follow-up timing
3. **Monitoring**: Regularly check campaign metrics to ensure optimal processing
4. **Resource Allocation**: Adjust worker threads and batch sizes based on load testing 
5. **Error Handling**: Implement comprehensive logging and alerting for campaign processing errors 