# Campaign Manager Class Diagram

This document provides a class diagram and relationship overview for the Campaign Manager component in the communication-base microservice.

## Class Structure

```
┌────────────────────────────────────────────────────────────────────┐
│                           CampaignManager                          │
├────────────────────────────────────────────────────────────────────┤
│ - conversation_state_repository: ConversationStateRepository       │
│ - config_manager: ConfigManager                                    │
│ - metrics: Metrics                                                 │
├────────────────────────────────────────────────────────────────────┤
│ + initialize_campaign_conversations(campaign_id: str) → int        │
│ + get_pending_conversations(campaign_id: str, stage: str,          │
│     limit: int, status: str) → List[Dict]                         │
│ + evaluate_stage_progression(conversation_id: str,                 │
│     conversation_state: Dict) → Tuple[bool, str, Dict]            │
│ + advance_conversation_stage(conversation_id: str,                 │
│     next_stage: str) → Dict                                       │
│ + get_campaign_metrics(campaign_id: str) → Dict                    │
│ + update_conversation_state(conversation_id: str,                  │
│     updates: Dict) → Dict                                         │
│ + get_conversation_history(conversation_id: str) → List[Dict]      │
│ + mark_conversation_complete(conversation_id: str) → Dict          │
│ - _get_stage_data(conversation_state: Dict, stage: str) → Dict     │
│ - _get_stages_for_campaign_type(template: Dict,                    │
│     campaign_type: str) → List[str]                               │
│ - _should_advance_to_next_stage(conversation_state: Dict,          │
│     stage_data: Dict) → Tuple[bool, str]                          │
└────────────────────────────────────────────────────────────────────┘
                      △
                      │
                      │ uses
                      │
┌─────────────────────────────────────────┐
│     ConversationStateRepository         │
├─────────────────────────────────────────┤
│ - _db: Database                         │
│ - _collection: Collection               │
├─────────────────────────────────────────┤
│ + initialize()                          │
│ + create_conversation_state(data: Dict) │
│ + get_conversation_state(id: str)       │
│ + update_conversation_state(id: str,    │
│     updates: Dict)                      │
│ + delete_conversation_state(id: str)    │
│ + find_conversation_states(query: Dict) │
└─────────────────────────────────────────┘
```

## Component Relationships

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│                 │       │                 │       │                 │
│  Campaign       │──────→│  Campaign       │──────→│  Worker         │
│  Poller         │       │  Manager        │       │  Service        │
│                 │       │                 │       │                 │
└─────────────────┘       └────────┬────────┘       └─────────────────┘
                                   │
                                   │ uses
                                   ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│                 │       │                 │       │                 │
│  Config         │◄──────│  Conversation   │       │  Metrics        │
│  Manager        │       │  State          │       │  Collector      │
│                 │       │  Repository     │       │                 │
└─────────────────┘       └─────────────────┘       └─────────────────┘
        △                         △                         △
        │                         │                         │
        └─────────────────────────┴─────────────────────────┘
                              uses
```

## Sequence Diagram: Campaign Initialization

```
┌──────────┐          ┌────────────┐          ┌───────────────┐          ┌──────────────┐
│ Campaign  │          │ Campaign   │          │ Conversation  │          │  MongoDB     │
│ Poller    │          │ Manager    │          │ State Repo    │          │              │
└─────┬─────┘          └──────┬─────┘          └──────┬────────┘          └──────┬───────┘
      │                       │                       │                          │
      │ Poll Campaigns        │                       │                          │
      │─────────────────────►│                       │                          │
      │                       │                       │                          │
      │                       │ Get Campaign Data     │                          │
      │                       │──────────────────────►│                          │
      │                       │                       │ Find Campaign            │
      │                       │                       │─────────────────────────►│
      │                       │                       │                          │
      │                       │                       │◄─────────────────────────│
      │                       │◄──────────────────────│                          │
      │                       │                       │                          │
      │                       │ For each recipient    │                          │
      │                       │─────────────────┐     │                          │
      │                       │                 │     │                          │
      │                       │◄────────────────┘     │                          │
      │                       │                       │                          │
      │                       │ Create Conversation   │                          │
      │                       │ States                │                          │
      │                       │──────────────────────►│                          │
      │                       │                       │ Insert Documents         │
      │                       │                       │─────────────────────────►│
      │                       │                       │                          │
      │                       │                       │◄─────────────────────────│
      │                       │◄──────────────────────│                          │
      │                       │                       │                          │
      │                       │ Update Campaign       │                          │
      │                       │ Status                │                          │
      │                       │──────────────────────►│                          │
      │                       │                       │ Update Document          │
      │                       │                       │─────────────────────────►│
      │                       │                       │                          │
      │                       │                       │◄─────────────────────────│
      │                       │◄──────────────────────│                          │
      │                       │                       │                          │
      │◄──────────────────────│                       │                          │
      │                       │                       │                          │
```

## Sequence Diagram: Conversation Processing

```
┌──────────┐          ┌────────────┐          ┌───────────────┐          ┌──────────────┐
│ Worker    │          │ Campaign   │          │ Conversation  │          │  MongoDB     │
│ Service   │          │ Manager    │          │ State Repo    │          │              │
└─────┬─────┘          └──────┬─────┘          └──────┬────────┘          └──────┬───────┘
      │                       │                       │                          │
      │ Request Pending       │                       │                          │
      │ Conversations         │                       │                          │
      │─────────────────────►│                       │                          │
      │                       │                       │                          │
      │                       │ Get Pending           │                          │
      │                       │ Conversations         │                          │
      │                       │──────────────────────►│                          │
      │                       │                       │ Find Documents           │
      │                       │                       │─────────────────────────►│
      │                       │                       │                          │
      │                       │                       │◄─────────────────────────│
      │                       │◄──────────────────────│                          │
      │                       │                       │                          │
      │◄──────────────────────│                       │                          │
      │                       │                       │                          │
      │ Process               │                       │                          │
      │ Conversation          │                       │                          │
      │─────────────┐         │                       │                          │
      │             │         │                       │                          │
      │◄────────────┘         │                       │                          │
      │                       │                       │                          │
      │ Evaluate Stage        │                       │                          │
      │ Progression           │                       │                          │
      │─────────────────────►│                       │                          │
      │                       │                       │                          │
      │                       │ Check Progression     │                          │
      │                       │ Rules                 │                          │
      │                       │─────────────┐         │                          │
      │                       │             │         │                          │
      │                       │◄────────────┘         │                          │
      │                       │                       │                          │
      │◄──────────────────────│                       │                          │
      │                       │                       │                          │
      │ Update Conversation   │                       │                          │
      │ State                 │                       │                          │
      │─────────────────────►│                       │                          │
      │                       │                       │                          │
      │                       │ Update State          │                          │
      │                       │──────────────────────►│                          │
      │                       │                       │ Update Document          │
      │                       │                       │─────────────────────────►│
      │                       │                       │                          │
      │                       │                       │◄─────────────────────────│
      │                       │◄──────────────────────│                          │
      │                       │                       │                          │
      │◄──────────────────────│                       │                          │
```

## Data Structures

### Conversation State Document

```json
{
  "_id": "conversation_id",
  "user_id": "recipient_id",
  "campaign_id": "campaign_id",
  "campaign_type": "sales",
  "current_stage": "awareness",
  "stages": [
    {
      "name": "awareness",
      "entered_at": "2023-06-01T12:00:00Z",
      "exited_at": null,
      "completed": false
    }
  ],
  "message_history": [
    {
      "message_id": "msg123",
      "direction": "outbound",
      "content": "Hello!",
      "timestamp": "2023-06-01T12:05:00Z",
      "metadata": {}
    }
  ],
  "context": {
    "template_id": "template123",
    "available_stages": ["awareness", "consideration", "decision"]
  },
  "metrics": {
    "messages_sent": 1,
    "messages_received": 0,
    "stage_progressions": 0
  },
  "status": "active",
  "created_at": "2023-06-01T12:00:00Z",
  "last_active": "2023-06-01T12:05:00Z"
}
```

### Campaign Metrics Document

```json
{
  "campaign_id": "campaign123",
  "total_recipients": 100,
  "active_conversations": 80,
  "completed_conversations": 15,
  "failed_conversations": 5,
  "stage_metrics": {
    "awareness": {
      "entered": 100,
      "completed": 50,
      "avg_duration_seconds": 3600
    },
    "consideration": {
      "entered": 50,
      "completed": 20,
      "avg_duration_seconds": 7200
    },
    "decision": {
      "entered": 20,
      "completed": 15,
      "avg_duration_seconds": 10800
    }
  },
  "message_metrics": {
    "total_sent": 250,
    "total_received": 120,
    "response_rate": 0.48
  },
  "updated_at": "2023-06-05T12:00:00Z"
}
```

## Implementation Notes

1. The Campaign Manager maintains a clean separation of concerns:
   - Business logic for stage progression
   - Data access through the repository layer
   - Metrics collection for monitoring

2. Thread safety considerations:
   - Repository methods are designed to be thread-safe
   - Campaign metrics use atomic operations for updates
   - Conversation state updates use MongoDB's atomic operations

3. Performance optimizations:
   - Indexes on campaign_id, user_id, and status fields
   - Batch processing for bulk operations
   - Connection pooling for MongoDB access 