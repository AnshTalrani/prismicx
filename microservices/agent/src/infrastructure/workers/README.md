# Workers Architecture

## Overview

The workers architecture represents an evolution of the Agent microservice, transitioning from a centralized orchestration model to a decentralized, worker-based model. This design offers several advantages in terms of scalability, fault tolerance, and maintainability.

## Key Components

### ClientWorker (Base Class)

- Defined in `worker_base.py`
- Handles core worker functionality:
  - Polling MongoDB for pending contexts
  - Claiming and processing contexts
  - Updating context status and results
  - Error handling and logging

### Service-Specific Workers

Each worker handles one service type and integrates client functionality:

1. **GenerativeWorker** (`generative_worker.py`):
   - Processes contexts requiring generative AI services
   - Communicates with Generation Base service
   - Handles template execution for text generation

2. **AnalysisWorker** (`analysis_worker.py`):
   - Processes contexts requiring data analysis
   - Communicates with Analysis Base service
   - Handles template execution for data analysis tasks

3. **CommunicationWorker** (`communication_worker.py`):
   - Processes contexts requiring communication services
   - Communicates with Communication Base service
   - Handles template execution and notifications

## Architectural Evolution

### Previous Architecture (Clients)

The previous implementation relied on:
- A centralized orchestration service
- Separate client classes for communication with external services
- RequestService triggering orchestration on multiple external services

```
Request → RequestService → OrchestrationService → Clients → External Services
```

### New Architecture (Workers)

The new implementation follows a more decentralized, event-driven approach:
- Workers actively poll for relevant tasks
- Each worker handles a specific service type
- Context manager creates service contexts directly
- No central orchestration is needed

```
Request → RequestService → ContextManager → MongoDB ← Workers → External Services
```

## Benefits

1. **Scalability**: Workers can be scaled independently based on service demand.
2. **Resilience**: Failure of one worker type doesn't affect others.
3. **Simplified Code**: Each worker encapsulates all logic for its service type.
4. **Reduced Latency**: Direct polling eliminates orchestration overhead.
5. **Better Testability**: Isolated components with clear responsibilities.

## Usage

Workers are instantiated in `main.py` and automatically poll for relevant tasks. No manual intervention is required once the workers are started.

```python
# Create and start workers
generative_worker = GenerativeWorker(mongo_context_repository)
analysis_worker = AnalysisWorker(mongo_context_repository)
communication_worker = CommunicationWorker(mongo_context_repository)

await generative_worker.start()
await analysis_worker.start()
await communication_worker.start()
```

## Configuration

Each worker type accepts service-specific configuration:
- `base_url`: URL of the external service
- `api_key`: Authentication key for the service
- `poll_interval`: Time between polls (seconds)
- `batch_size`: Maximum number of contexts to process per poll

Environment variables can be used for configuration:
- `GENERATION_BASE_URL`
- `ANALYSIS_BASE_URL`
- `COMMUNICATION_BASE_URL`
- And corresponding API keys 