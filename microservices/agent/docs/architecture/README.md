# Agent Microservice Architecture

This document provides an overview of the Agent microservice architecture, design principles, and key components.

## Recent Updates

The architecture has been significantly updated to transition from an orchestration-based model to a worker-based model:

- **Removed the centralized orchestration service** in favor of decentralized workers
- **Introduced worker-based processing** with dedicated workers for each service type
- **Enhanced the Context Manager** to directly create service-specific contexts
- **Simplified the request flow** by reducing the number of components involved

For a detailed explanation of the architecture changes, see the [ARCHITECTURE_NOTES.md](../../ARCHITECTURE_NOTES.md) file.

For detailed diagrams, see the [UML directory](./uml).

## Architecture Overview

The Agent microservice is designed following the principles of Clean Architecture and MACH (Microservices, API-first, Cloud-native, Headless). It consists of several layers:

1. **Domain Layer**: Contains the core business entities, value objects, and domain logic
2. **Application Layer**: Contains the use cases and services that orchestrate the domain logic
3. **Infrastructure Layer**: Contains implementations of repositories, workers, and external service communications
4. **API Layer**: Contains the HTTP endpoints and controllers that expose the application's functionality

## Key Components

### API Layer
- RequestController: Handles incoming request processing
- TemplateController: Manages template CRUD operations
- BatchController: Manages batch processing operations
- ConsultancyBotAPI: Specialized API for consultancy bot integration

### Application Layer
- RequestService: Central service for processing individual requests
- TemplateService: Manages templates and their lifecycle
- BatchProcessor: Handles processing of multiple requests as batches
- ContextManager: Creates and manages execution contexts

### Domain Layer
- ExecutionTemplate: Core entity for defining service execution templates
- Request: Represents user requests to be processed
- Purpose: Represents intent detection for template selection
- BatchJob: Manages batch processing operations

### Infrastructure Layer
- Workers: Service-specific workers that poll for and process relevant tasks
  - GenerativeWorker: Processes generative AI tasks
  - AnalysisWorker: Processes data analysis tasks
  - CommunicationWorker: Processes communication tasks
- Repository implementations (MongoDB, File-based, In-memory)
- Service integration within each worker

### Scheduler
- BatchScheduler: Manages scheduled batch processing jobs

## Worker Architecture

The worker-based architecture is a key evolution of the system:

1. **ClientWorker Base Class**: Provides core functionality for all workers
   - Polling for relevant tasks
   - Claiming and processing contexts
   - Updating context status and results
   - Error handling

2. **Service-Specific Workers**: Each worker type handles one service type
   - Includes integrated client functionality
   - Communicates with external services
   - Processes contexts matching its service type

3. **Decentralized Processing**:
   - Workers operate independently and asynchronously
   - No central orchestration bottleneck
   - Improved scalability and fault tolerance

For more details, see the [Workers README](../../src/infrastructure/workers/README.md).

## Design Patterns

The Agent microservice uses several design patterns:

1. **Repository Pattern**: For data access abstraction
2. **Worker Pattern**: For decentralized task processing
3. **Factory Pattern**: For creating domain objects
4. **Dependency Injection**: For loose coupling between components
5. **Command Pattern**: For encapsulating request processing operations

## Flow Diagrams

The main execution flow is:
1. Request Service creates a context via Context Manager
2. Context Manager stores the context in MongoDB
3. Workers poll for contexts matching their service type
4. Workers process contexts by communicating with external services
5. Workers update contexts with results

## Integration Points

The Agent microservice integrates with:
1. **Generation Base Service**: For generative AI operations (via GenerativeWorker)
2. **Analysis Service**: For analytical operations (via AnalysisWorker)
3. **Communication Service**: For notification and messaging operations (via CommunicationWorker)

## Data Storage

The Agent microservice uses:
1. **MongoDB**: For storing and querying contexts
2. **File Storage**: For templates and purposes
3. **In-Memory Storage**: For request tracking and caching

## Configuration Management

Configuration is managed through:
1. Environment variables
2. External configuration files
3. Default configurations with override capabilities

## Error Handling

The Agent microservice implements error handling at multiple levels:
1. Worker-level error handling for service communication
2. Context-level error tracking in MongoDB
3. Detailed error logging
4. Standardized error responses

## Testing Strategy

The Agent microservice follows a comprehensive testing strategy:
1. Unit tests for domain logic
2. Integration tests for service interactions
3. Worker-specific tests
4. End-to-end tests for full request processing
5. Mock implementations for external dependencies

## Security Considerations

Security is implemented through:
1. Input validation and sanitization
2. Authentication and authorization
3. Rate limiting and request validation
4. Secure handling of sensitive data 