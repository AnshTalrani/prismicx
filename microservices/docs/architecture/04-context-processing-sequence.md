# Context Processing Sequence Diagram

## Overview

This document details the sequence of operations involved in processing a context through the system, from initial request to completion. It focuses on the interaction between components, services, and data stores during the context lifecycle.

## Context Processing Sequence

```mermaid
sequenceDiagram
    participant Client
    participant APIGateway
    participant ManagementSvc
    participant DB as MongoDB
    participant WorkerSvc
    participant ProcEngine as ProcessingEngine
    participant Component1
    participant Component2
    participant ExternalSvc as External Service
    
    %% Initial Context Creation
    Client->>APIGateway: POST /api/contexts
    APIGateway->>ManagementSvc: Forward request
    ManagementSvc->>DB: Create context (status: pending)
    DB-->>ManagementSvc: Context created
    ManagementSvc-->>APIGateway: 201 Created (context_id)
    APIGateway-->>Client: 201 Created (context_id)
    
    %% Worker polling
    WorkerSvc->>DB: Poll for pending contexts
    DB-->>WorkerSvc: Return pending contexts
    
    %% Processing starts
    WorkerSvc->>DB: Update context (status: processing)
    WorkerSvc->>ProcEngine: process_context(context)
    
    %% Component processing
    ProcEngine->>Component1: process(context)
    
    alt External service required
        Component1->>ExternalSvc: API Request
        ExternalSvc-->>Component1: API Response
    end
    
    Component1-->>ProcEngine: Updated context
    ProcEngine->>Component2: process(context)
    
    alt Error occurs
        Component2->>ProcEngine: Throw error
        ProcEngine->>WorkerSvc: Error details
        WorkerSvc->>DB: Update context (status: failed, error_details)
    else Success
        Component2-->>ProcEngine: Completed context
        ProcEngine-->>WorkerSvc: Processed context
        WorkerSvc->>DB: Update context (status: completed, result)
    end
    
    %% Result retrieval
    Client->>APIGateway: GET /api/contexts/{context_id}
    APIGateway->>ManagementSvc: Forward request
    ManagementSvc->>DB: Get context by ID
    DB-->>ManagementSvc: Return context
    ManagementSvc-->>APIGateway: 200 OK (context)
    APIGateway-->>Client: 200 OK (context)
```

## Detailed Process Steps

### 1. Context Creation

1. Client submits a new context processing request to the API Gateway
2. The request is routed to the Management Service
3. The Management Service creates a new context document in MongoDB with status "pending"
4. The context ID is returned to the client for later status checking

### 2. Worker Processing

1. The Worker Service periodically polls MongoDB for contexts with "pending" status
2. When pending contexts are found, the Worker updates their status to "processing"
3. The Worker Service invokes the Processing Engine to handle the context
4. The Processing Engine creates a pipeline based on the context's configuration
5. The Processing Engine executes the pipeline, invoking each component in sequence

### 3. Component Processing

1. Each component receives the context document with accumulated changes
2. Components may make external API calls to services like Template Service or AI Service
3. Components transform the context data according to their specific responsibilities
4. Components may enrich the context with additional data
5. Components pass the enriched context to the next component in the pipeline

### 4. Error Handling

If an error occurs during processing:
1. The component throws an error with details about the failure
2. The Processing Engine catches the error and forwards it to the Worker Service
3. The Worker Service updates the context with status "failed" and includes error details
4. Depending on configuration, the Worker Service may schedule a retry

### 5. Result Delivery

1. Upon successful processing, the Worker Service updates the context status to "completed"
2. The processed result is stored in the context document
3. The client can retrieve the context using the context ID
4. The Management Service returns the completed context with processing results

## Component-Specific Processing Flows

### Template Component

```mermaid
sequenceDiagram
    participant PE as ProcessingEngine
    participant TC as TemplateComponent
    participant TS as TemplateService
    
    PE->>TC: process(context)
    TC->>TS: GET /api/templates/{template_id}
    TS-->>TC: Template data
    TC->>TC: Apply template to context
    TC-->>PE: Return enriched context
```

### AI Generator Component

```mermaid
sequenceDiagram
    participant PE as ProcessingEngine
    participant AIC as AIComponent
    participant AIS as AI Service
    
    PE->>AIC: process(context)
    AIC->>AIC: Prepare prompt
    AIC->>AIS: POST /api/generate
    AIS-->>AIC: Generated content
    AIC->>AIC: Process generated content
    AIC-->>PE: Return enriched context
```

### Transformation Component

```mermaid
sequenceDiagram
    participant PE as ProcessingEngine
    participant TC as TransformationComponent
    
    PE->>TC: process(context)
    TC->>TC: Apply transformation rules
    TC->>TC: Format content
    TC-->>PE: Return transformed context
```

## Batch Processing Sequence

The batch processing workflow involves handling multiple contexts simultaneously:

```mermaid
sequenceDiagram
    participant WS as WorkerService
    participant DB as MongoDB
    participant PE as ProcessingEngine
    
    WS->>DB: get_pending_batch(batch_size)
    DB-->>WS: batch of contexts
    
    par Process context 1
        WS->>PE: process_context(context1)
        PE-->>WS: result1
        WS->>DB: update_context(context1_id, result1)
    and Process context 2
        WS->>PE: process_context(context2)
        PE-->>WS: result2
        WS->>DB: update_context(context2_id, result2)
    and Process context 3
        WS->>PE: process_context(context3)
        PE-->>WS: result3
        WS->>DB: update_context(context3_id, result3)
    end
```

## Retry Mechanism

When a processing failure occurs, the retry mechanism works as follows:

```mermaid
sequenceDiagram
    participant WS as WorkerService
    participant DB as MongoDB
    participant PE as ProcessingEngine
    
    WS->>PE: process_context(context)
    PE-->>WS: Error
    WS->>DB: update_context(context_id, status: failed, retry_count: n+1)
    Note over WS,DB: If retry_count < max_retries
    WS->>DB: update_context(context_id, status: pending, next_attempt: future_time)
    
    Note over WS,DB: Later, after delay
    WS->>DB: poll for pending contexts
    DB-->>WS: context (retry attempt)
    WS->>PE: process_context(context) 
```

## System Behavior Under Load

During high load conditions, the system scales as follows:

```mermaid
flowchart TD
    subgraph "Worker Scaling"
        Worker1[Worker Instance 1]
        Worker2[Worker Instance 2]
        Worker3[Worker Instance 3]
    end
    
    subgraph "Database"
        DB[(MongoDB)]
    end
    
    Worker1 -->|Poll Contexts| DB
    Worker2 -->|Poll Contexts| DB
    Worker3 -->|Poll Contexts| DB
    
    DB -->|Contexts 1-5| Worker1
    DB -->|Contexts 6-10| Worker2
    DB -->|Contexts 11-15| Worker3
```

## Next Steps

For more detailed information, refer to:
- [Batch Processing Flow Diagram](05-batch-processing-flow.md)
- [Processing Optimization Documentation](06-processing-optimization.md)
- [Component Design Pattern Documentation](07-component-design-pattern.md)
- [Scaling Strategy Documentation](08-scaling-strategy.md) 