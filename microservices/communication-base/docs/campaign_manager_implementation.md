# Campaign Manager Implementation

This document provides a detailed explanation of the Campaign Manager component in the communication-base microservice, following MACH architecture principles.

## Overview

The Campaign Manager is a core component of the communication-base microservice responsible for managing campaign-related conversation flows, stage progression, and conversation state management. It operates in coordination with the Campaign Poller and Worker Service to enable effective management of conversation campaigns across their entire lifecycle.

```
┌───────────────┐    ┌────────────────┐    ┌────────┐
│ Campaign      │    │ Campaign       │    │        │
│ Poller        │───→│ Manager        │───→│ Worker │
│               │    │                │    │ Service│
└───────────────┘    └────────────────┘    └────────┘
```

## Responsibilities

The Campaign Manager is responsible for:

1. **Conversation State Management**: 
   - Initializing conversation states for all recipients in a campaign
   - Tracking the progression of conversations through various stages
   - Maintaining conversation context and history

2. **Stage Progression Logic**:
   - Evaluating when conversations should advance to the next stage
   - Managing stage-specific rules and conditions
   - Handling timing and delay requirements between stages

3. **Campaign Metrics Collection**:
   - Tracking conversation metrics (messages sent/received)
   - Monitoring stage progression and completion rates
   - Aggregating data for campaign performance analysis

4. **Conversation Retrieval**:
   - Identifying pending conversations ready for processing
   - Filtering conversations by campaign, stage, and status
   - Prioritizing conversations based on business rules

## Architecture

The Campaign Manager implements a service layer that sits between the data repositories and the Worker Service:

```
┌────────────────────────────────────────────────┐
│               Campaign Manager                 │
│                                                │
│  ┌────────────────┐      ┌───────────────────┐ │
│  │ Stage          │      │ Conversation      │ │
│  │ Progression    │      │ State Management  │ │
│  │ Engine         │      │                   │ │
│  └────────────────┘      └───────────────────┘ │
│                                                │
│  ┌────────────────┐      ┌───────────────────┐ │
│  │ Campaign       │      │ Metrics           │ │
│  │ Workflow       │      │ Collection        │ │
│  │ Controller     │      │                   │ │
│  └────────────────┘      └───────────────────┘ │
└────────────────────────────────────────────────┘
              │                    │
              ▼                    ▼
┌────────────────────────────────────────────────┐
│               Repositories                      │
│                                                │
│  ┌────────────────────┐  ┌─────────────────┐   │
│  │ Conversation State │  │ Campaign        │   │
│  │ Repository         │  │ Repository      │   │
│  └────────────────────┘  └─────────────────┘   │
└────────────────────────────────────────────────┘
```

## Key Methods

### Conversation Initialization

```python
async def initialize_campaign_conversations(self, campaign_id: str) -> int:
```

This method is the entry point for setting up a new campaign:

1. Retrieves campaign data and recipient list
2. Determines campaign type and initial stage
3. Creates conversation state records for each recipient
4. Sets up initial stage and metadata
5. Returns the count of initialized conversations

### Pending Conversation Retrieval

```python
async def get_pending_conversations(
    self, 
    campaign_id: str,
    stage: Optional[str] = None,
    limit: int = 100,
    status: str = "active"
) -> List[Dict[str, Any]]:
```

This method identifies conversations that are ready for processing:

1. Filters conversations by campaign ID and status
2. Optionally filters by specific stage
3. Applies timing rules for follow-ups
4. Limits the number of conversations returned
5. Returns prioritized conversations ready for processing

### Stage Progression Evaluation

```python
async def evaluate_stage_progression(
    self, 
    conversation_id: str,
    conversation_state: Dict[str, Any]
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
```

This method determines if a conversation should progress to the next stage:

1. Analyzes the current conversation state and stage
2. Applies progression rules specific to the campaign type
3. Evaluates conditions for advancement (time-based, response-based)
4. Determines the next stage if progression is warranted
5. Returns a decision tuple with progression flag, next stage, and updated state

### Campaign Metrics Collection

```python
async def get_campaign_metrics(self, campaign_id: str) -> Dict[str, Any]:
```

This method gathers performance metrics for a campaign:

1. Aggregates data across all conversation states
2. Calculates stage completion rates
3. Tracks message volumes and response rates
4. Measures time spent in each stage
5. Returns a comprehensive metrics object

## Data Flow

### Campaign Initialization Flow

```
Campaign Creation → Campaign Poller → Initialize Campaign Conversations → 
Create Conversation States → Ready for Processing
```

### Conversation Processing Flow

```
Worker Request → Get Pending Conversations → Process Conversation → 
Evaluate Stage Progression → Update Conversation State
```

### Campaign Completion Flow

```
Final Stage Completion → Mark Conversations Complete → 
Aggregate Campaign Metrics → Update Campaign Status
```

## Integration Points

The Campaign Manager integrates with:

1. **Conversation State Repository**: For persistent storage of conversation data
2. **Campaign Poller**: Which triggers campaign initialization and processing
3. **Worker Service**: Which consumes conversation data for processing
4. **Config Manager**: For campaign rules and configuration

## Configuration

Key configuration parameters that affect the Campaign Manager:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `MAX_BATCH_SIZE` | Maximum conversations to process in one batch | 100 |
| `STAGE_DELAY_FACTOR` | Multiplier for stage timing rules | 1.0 |
| `RETRY_DELAY_SECONDS` | Delay before retrying failed conversations | 300 |
| `CAMPAIGN_METRICS_TTL` | Time-to-live for cached metrics | 600 |

## Error Handling and Resilience

The Campaign Manager implements several resilience patterns:

1. **Isolated Failures**: Issues with one conversation don't affect others
2. **Retry Logic**: Failed operations are retried with exponential backoff
3. **Transaction Boundaries**: Conversation updates are atomic
4. **Logging**: Comprehensive logging of all operations and state changes
5. **Circuit Breaking**: Prevents cascading failures during repository issues

## Performance Considerations

To ensure optimal performance, the Campaign Manager:

1. Uses bulk operations where possible
2. Implements efficient MongoDB queries with proper indexes
3. Processes conversations in batches
4. Caches frequently accessed configuration
5. Uses pagination for large result sets

## Monitoring and Observability

The Campaign Manager exposes the following metrics:

1. `conversations_initialized`: Number of conversation states created
2. `stages_advanced`: Number of stage progressions
3. `conversations_completed`: Number of completed conversations
4. Processing duration metrics for key operations
5. Error rate metrics for tracking reliability

## Extension Points

The Campaign Manager's design allows for:

1. Adding new campaign types with custom stage progression logic
2. Implementing additional metrics collection
3. Supporting new conversation progression rules
4. Extending the conversation state model
5. Adding specialized campaign workflows

## Security Considerations

Key security aspects:

1. Input validation for all client-provided data
2. No direct exposure to external clients
3. Proper error handling to prevent information leakage
4. Repository-level access controls

## Related Components

For a complete understanding, also refer to:
- [Campaign Processing](./campaign_processing.md)
- [Conversation Campaign Workflow](./conversation_campaign_workflow.md)
- [Campaign Templates](./campaign_templates.md) 