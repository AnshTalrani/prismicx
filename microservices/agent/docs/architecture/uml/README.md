# UML Diagrams

This directory contains UML diagrams that provide visual representations of the Agent microservice's architecture, components, and workflows.

## Diagram Types

### 1. Class Diagrams

#### Domain Layer Classes
- `ExecutionTemplate` - Core entity for defining service execution templates
- `Request` - Represents user requests to be processed
- `User` - User entity for authentication and authorization
- `Purpose` - Represents intent detection for template selection
- `BatchJob` - Manages processing of multiple items in batch
- `Context` - Stores processing context for requests or batch operations

#### Application Layer Services
- `RequestService` - Central service for processing individual requests
- `TemplateService` - Manages templates and their selection
- `BatchProcessor` - Handles processing of multiple requests as batches
- `DefaultOrchestrationService` - Routes requests to appropriate service implementations
- `DefaultNLPService` - Handles natural language processing and purpose detection
- `DefaultContextService` - Manages execution contexts for requests and batches
- `LoggingCommunicationService` - Handles notifications and communication

#### Infrastructure Layer Components
- Repository implementations (File-based, In-memory)
- Service clients for external service integration
- Context storage mechanisms
- Batch scheduling components

#### Interface Layer Controllers
- API endpoints for request processing, template management, and batch operations
- Integration points for specialized services like ConsultancyBot

### 2. Sequence Diagrams

#### Request Processing Flow
1. Client sends request through API Gateway
2. Request validation and purpose detection (if needed)
3. Template selection based on purpose
4. Context creation and management
5. Orchestration of service execution
6. Result processing and standardization
7. Notifications and response handling

#### Batch Processing Flow
1. Batch job submission (immediate or scheduled)
2. Batch context creation
3. Template retrieval for batch items
4. Individual item processing via RequestService
5. Progress tracking and context updates
6. Completion handling and notification

#### Error Handling Flow
1. Error detection at different levels
2. Standardized error response creation
3. Error context preservation
4. Client notification and logging
5. Recovery strategies for retriable errors

### 3. Component Diagrams

#### System Architecture Overview
- Agent microservice boundary
- Internal layer organization (API, Application, Domain, Infrastructure)
- External service integration points
- Data storage mechanisms

#### Microservice Interactions
- Communication with Generation Base, Analysis, and Communication services
- Event and notification handling
- Batch processing orchestration
- Context management across request lifecycle

### 4. State Diagrams

#### Request Lifecycle
- States: PENDING, PROCESSING, COMPLETED, FAILED
- Transitions between states during processing
- Error handling and recovery paths

#### Batch Job Lifecycle
- States: PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED
- Progress tracking through item processing
- Completion and error handling

### 5. Activity Diagrams

#### Template Execution Workflow
- Template validation
- Service type determination
- Client selection and execution
- Result processing and standardization

#### Batch Processing Workflow
- Job scheduling
- Item iteration and processing
- Progress tracking
- Result collection and summarization

## Current Diagram Status

The following diagrams have been updated to reflect the current implementation:

- `component_diagrams/agent_architecture.puml` - Updated with batch processing and consultancy bot components
- `class_diagrams/core_interfaces.puml` - Updated with all current interfaces and service implementations
- `class_diagrams/domain_entities.puml` - Updated with Purpose, BatchJob, and Context entities
- `sequence_diagrams/request_flow.puml` - Updated with current request processing flow
- `sequence_diagrams/batch_processing_flow.puml` - Updated with current batch processing implementation

## Diagram Location

Each diagram type has its own directory:
```
uml/
├── class_diagrams/
├── sequence_diagrams/
├── component_diagrams/
├── state_diagrams/
└── activity_diagrams/
```

## Tools and Standards

- All diagrams are created using PlantUML
- Following UML 2.5 standards
- Diagrams include clear legends and explanatory notes
- Consistent styling is maintained across all diagrams
- Diagrams are version controlled alongside code

## Best Practices

1. **Clarity**
   - Use clear, descriptive names
   - Include explanatory notes
   - Maintain consistent notation
   - Avoid overcrowding

2. **Maintenance**
   - Keep diagrams up to date with code changes
   - Review regularly as part of code reviews
   - Version control changes with corresponding code
   - Document updates in commit messages

3. **Organization**
   - Group related diagrams by type and function
   - Use consistent naming conventions
   - Include metadata and creation dates
   - Cross-reference with implementation documentation

4. **Collaboration**
   - Share diagrams for team review
   - Gather feedback during design discussions
   - Update based on implementation changes
   - Maintain history of design decisions

## Usage

These diagrams serve multiple purposes:
1. System understanding for new team members
2. Development guidance for feature implementation
3. Documentation for architecture decisions
4. Training material for onboarding
5. Troubleshooting aid for complex interactions

## Contributing

When updating diagrams:
1. Ensure consistency with current implementation
2. Update all related diagrams affected by changes
3. Include relevant notes explaining major changes
4. Get peer review before committing
5. Keep diagrams synchronized with code changes 