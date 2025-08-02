# Communication Base Architecture

This document outlines the architecture of the communication-base microservice, following MACH architecture principles (Microservices, API-first, Cloud-native, Headless).

## MACH Architecture Implementation

The communication-base microservice follows the MACH architecture principles:

### Microservices
- **Autonomous Service**: Functions as an independent microservice focused solely on campaign processing
- **Single Responsibility**: Manages campaign workflows, conversation states, and message processing
- **Bounded Context**: Handles only the communication aspect of the larger application ecosystem

### API-first (Internal)
- **Worker-only Mode**: Operates without REST APIs, consuming data through MongoDB collections
- **Clear Data Contracts**: Well-defined document schemas for campaigns, templates, and conversation states
- **Integration Model**: Communicates with other microservices through a shared database pattern

### Cloud-native
- **Containerized**: Packaged as a Docker container for consistent deployment across environments
- **Horizontally Scalable**: Worker threads can be scaled based on workload demands
- **Configuration via Environment**: All settings are configurable through environment variables
- **Observability**: Comprehensive logging and monitoring for cloud environments

### Headless
- **Backend Processing**: Pure background processing with no frontend components
- **Data-driven**: Operates based on data changes in the MongoDB collections
- **Event Processing**: Reacts to new campaign creation and processes conversations without UI intervention

## System Components

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                Communication Base Service                │
│                                                         │
│  ┌───────────────┐    ┌────────────────┐    ┌────────┐  │
│  │ Campaign      │    │ Campaign       │    │        │  │
│  │ Poller        │───→│ Manager        │───→│ Worker │  │
│  │               │    │                │    │ Service│  │
│  └───────────────┘    └────────────────┘    └────────┘  │
│          │                     │                 │       │
│          ▼                     ▼                 ▼       │
│  ┌──────────────────────────────────────────────────┐   │
│  │                  Repositories                     │   │
│  │  ┌─────────────┐ ┌────────────────┐ ┌─────────┐  │   │
│  │  │ Campaign    │ │ Conversation   │ │ Config  │  │   │
│  │  │ Repository  │ │ State          │ │ Manager │  │   │
│  │  │             │ │ Repository     │ │         │  │   │
│  │  └─────────────┘ └────────────────┘ └─────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
         │                 │                   │
         ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│                        MongoDB                          │
│                                                         │
│   ┌────────────┐   ┌────────────────┐  ┌─────────────┐  │
│   │ Campaigns  │   │ Conversation   │  │ Templates &  │  │
│   │ Collection │   │ States         │  │ Configs     │  │
│   └────────────┘   └────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Component Responsibilities

1. **Campaign Poller**:
   - Polls MongoDB for pending and scheduled campaigns
   - Initiates the campaign processing workflow
   - Handles campaign status transitions

2. **Campaign Manager**:
   - Manages conversation state lifecycle
   - Controls stage progression logic
   - Maintains campaign metrics 

3. **Worker Service**:
   - Processes individual conversations
   - Sends messages through communication channels
   - Applies business rules for follow-ups and escalations

4. **Repositories**:
   - Provide data access abstractions
   - Handle MongoDB CRUD operations
   - Implement resilience patterns for database operations

5. **Config Manager**:
   - Processes campaign templates
   - Extracts timing rules and conversation flows
   - Configures stage progression logic

## Data Flow

### Campaign Ingestion
```
Agent Service → Campaign Document → MongoDB → Campaign Poller → Worker Service
```

### Conversation Processing
```
Worker Service → Retrieve Conversation State → Process Stage → Update State → Send Message
```

### Campaign Completion
```
Worker Service → Update Metrics → Mark Campaign Complete → Store Results in MongoDB
```

## Deployment Architecture

The communication-base microservice is deployed as a Docker container in a Kubernetes cluster:

```
┌─────────────────────────────────────────────────┐
│                Kubernetes Cluster                │
│                                                 │
│  ┌─────────────────────┐   ┌─────────────────┐  │
│  │ Communication Base  │   │                 │  │
│  │ Deployment          │   │  MongoDB        │  │
│  │ ┌─────────┐ ┌─────┐│   │  StatefulSet    │  │
│  │ │Container│ │     ││   │                 │  │
│  │ │Worker   │ │... n││   │                 │  │
│  │ └─────────┘ └─────┘│   │                 │  │
│  └─────────────────────┘   └─────────────────┘  │
│                                                 │
│  ┌─────────────────────┐   ┌─────────────────┐  │
│  │ Agent Service       │   │ Other           │  │
│  │ Deployment          │   │ Microservices   │  │
│  └─────────────────────┘   └─────────────────┘  │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Scaling Strategy

The service scales horizontally by:

1. **Worker Replication**: Multiple worker containers can be deployed
2. **Thread Scaling**: Each container can run multiple worker threads
3. **Batch Processing**: Conversations are processed in configurable batches

## Resilience Patterns

1. **Circuit Breakers**: Prevent cascading failures during MongoDB outages
2. **Retry Policies**: Automatically retry failed operations with exponential backoff
3. **Rate Limiting**: Prevent overwhelming external communication services
4. **Graceful Degradation**: Continue processing other campaigns when one fails
5. **Health Checks**: Kubernetes probes ensure service health

## Monitoring and Observability

1. **Metrics Collection**: Prometheus metrics for campaign processing
2. **Structured Logging**: JSON-formatted logs for better searchability
3. **Distributed Tracing**: Trace IDs for tracking campaign processing
4. **Alerting**: Configured alerts for processing errors and SLA violations

## Security Considerations

1. **Network Isolation**: Service operates in an internal network segment
2. **Secret Management**: Database credentials stored in Kubernetes secrets
3. **Data Encryption**: Sensitive data encrypted in MongoDB
4. **Access Control**: MongoDB authentication and authorization

## Evolution and Extension

The architecture supports the following extension points:

1. **New Campaign Types**: Add new campaign templates and processing logic
2. **Additional Channels**: Extend to support new communication channels
3. **Enhanced Analytics**: Add more detailed metrics and reporting
4. **Integration Endpoints**: Potential for adding event streams or webhooks 