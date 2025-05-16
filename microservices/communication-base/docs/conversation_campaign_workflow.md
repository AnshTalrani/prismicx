# Conversation-Based Campaign Workflow

## Overview

The communication-base microservice is responsible for managing conversation-based campaigns, specifically interactive sales conversations driven by intelligent bots. These campaigns follow a stage-based approach (awareness, interest, consideration, decision) where conversations evolve based on user responses and engagement.

This document outlines the complete workflow for conversation-based campaign processing, from agent batch creation to completion.

## Workflow Stages

### 1. Agent Batch Request Creation

- **Agent Microservice**: Creates batch requests in the `agent_batch_requests` collection with `servicetype="communication"`
- **Batch Request**: Includes:
  - Campaign template (like campaign_sales.json)
  - Target recipients list
  - Scheduled execution time (optional)
  - Campaign name and metadata

**Example Batch Request:**

```json
{
  "_id": "batch_request_id",
  "name": "Q4 Enterprise Software Campaign",
  "servicetype": "communication",
  "status": "new",
  "created_by": "agent",
  "created_at": "2023-10-15T08:00:00Z",
  "template": {
    "template_type": "campaign",
    "global_settings": { ... },
    "stages": [ ... ]
  },
  "recipients": [
    {"id": "user1", "contact_info": {...}},
    {"id": "user2", "contact_info": {...}}
  ],
  "scheduled_at": "2023-10-15T09:00:00Z"
}
```

### 2. Batch Request Discovery

- **Campaign Poller** continuously polls the `agent_batch_requests` collection for:
  - Documents with `servicetype="communication"`
  - Status set to `"new"`
- When a new batch request is found, the poller:
  - Updates its status to `"processing"`
  - Creates a campaign from the request
  - Updates the batch request status to `"completed"` with a reference to the created campaign

### 3. Campaign Processing

- If the campaign has a future `scheduled_at` date:
  - It's marked as `"scheduled"` and processed when the date arrives
- For immediately processable campaigns:
  - Status is set to `"pending"`
  - Campaign Manager initializes conversations for all recipients
  - Campaign is marked as `"active"` once initialized

### 4. Initial Conversation Setup

- **Campaign Manager** creates conversation states for each recipient:
  - Sets initial stage (typically "awareness")
  - Initializes conversation context with user and campaign data
  - Sets up stage history tracking
  - Sets initial metrics

### 5. Conversation Processing by Workers

- **Worker Service** continuously polls for pending conversations
- For each conversation ready for processing:
  - Loads the appropriate stage guidance from the template
  - Prepares personalized content based on the template
  - Generates and sends messages through appropriate channels
  - Records the interaction in the conversation state

### 6. Sales Bot Integration

- The **Sales Bot** uses the campaign's conversation guidance for the current stage to:
  - Extract specific information based on stage requirements
  - Apply the appropriate response strategy
  - Emphasize relevant product aspects
  - Handle objections according to stage-specific guidance
  - Guide the conversation toward appropriate next steps

### 7. Stage Progression Evaluation

- After each interaction, the **Campaign Manager** evaluates if the conversation should progress to the next stage
- Stage progression is determined based on:
  - Conversation analysis results
  - Time spent in current stage
  - Completion criteria from template configuration
  - User engagement signals

### 8. Follow-up Scheduling

- The **Config Manager** determines when follow-up messages should be sent based on:
  - Time since last interaction
  - User engagement metrics
  - Stage-specific timing rules from the template
  - Business hours and optimal contact times

### 9. Campaign Completion

- When all conversations have concluded or the campaign deadline is reached:
  - Final metrics are calculated
  - Success rates are determined
  - Campaign is marked as completed
  - Results are stored for reporting

## Key Components

The conversation-based campaign workflow involves these key components:

1. **Campaign Poller**: Discovers batch requests with `servicetype="communication"` and creates campaigns

2. **Conversation State Repository**: Manages storage and retrieval of conversation states, batch requests, and campaigns

3. **Campaign Manager**: Orchestrates campaign processing, conversation initialization, and stage progression

4. **Config Manager**: Processes templates to extract stage guidance and timing rules

5. **Worker Service**: Processes individual conversations, manages scheduling, and handles user interactions

6. **Sales Bot**: Handles the actual conversation with users based on stage-specific guidance

## Template Structure

The campaign template defines the structure and guidance for conversations at each stage. Key elements include:

- **Global Settings**: Business hours, timing rules, follow-up strategies
- **Stage Definitions**: For each sales stage (awareness, interest, consideration, decision)
- **Conversation Guidance**: Information to extract, response strategies, product emphasis
- **Objection Handling**: Strategies for handling common objections at each stage
- **Next Steps**: Guidance on advancing the conversation

## Workflow Diagram

```
┌──────────────┐       ┌─────────────────┐       ┌────────────────┐
│              │       │                 │       │                │
│ Agent Service├──────►│  Batch Requests ├──────►│ Campaign Poller│
│              │       │  Collection     │       │                │
└──────────────┘       └─────────────────┘       └────────┬───────┘
                                                          │
                                                          ▼
┌──────────────┐       ┌─────────────────┐       ┌────────────────┐
│              │       │                 │       │                │
│    Sales Bot ◄───────┤ Campaign Manager◄───────┤  Config Manager│
│              │       │                 │       │                │
└──────┬───────┘       └────────┬────────┘       └────────────────┘
       │                        │
       ▼                        ▼
┌──────────────┐       ┌─────────────────┐
│              │       │                 │
│    User      │       │ Worker Service  │
│              │       │                 │
└──────────────┘       └─────────────────┘
```

## Batch Request and Campaign Statuses

### Batch Request Status Flow:
- **new**: Initial status when created by agent service
- **processing**: Being processed by campaign poller
- **completed**: Campaign successfully created
- **failed**: Error occurred during processing

### Campaign Status Flow:
- **scheduled**: Waiting for scheduled time to arrive
- **pending**: Ready for immediate processing
- **initializing**: Conversations being created
- **active**: Campaign running with active conversations
- **completed**: All conversations finished
- **failed**: Campaign encountered unrecoverable errors

## Example Flow

1. Agent microservice creates a batch request with `servicetype="communication"`
2. Campaign poller discovers the batch request and creates a campaign
3. Campaign manager initializes conversation states for all recipients
4. Worker service processes conversations according to template stages
5. Sales bot handles the actual conversation using stage-specific guidance
6. Conversations progress through stages based on user interactions and template rules
7. Campaign completes when all conversations reach final states
8. Metrics and results are stored for reporting 