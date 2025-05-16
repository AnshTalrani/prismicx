# Component Architecture Diagram

## Overview

This document details the component architecture of our microservices, with a specific focus on the Generative Base Service's internal components and their interactions.

## Component-Based Design Principles

Our component design follows these key principles:

1. **Single Responsibility**: Each component has a clearly defined, focused purpose
2. **Encapsulation**: Components hide internal implementation details
3. **Composability**: Components can be combined in various ways to create complex processing pipelines
4. **Testability**: Components are designed for ease of unit testing
5. **Configurability**: Components can be configured for different use cases

## Generative Base Service Components

```mermaid
classDiagram
    class Settings {
        +mongodb_uri: str
        +mongodb_db: str
        +mongodb_collection: str
        +redis_uri: str
        +worker_poll_interval: int
        +batch_size: int
        +max_retries: int
        +component_registry: dict
        +validate()
    }
    
    class Repository {
        -settings: Settings
        -db_client: MongoClient
        -db: Database
        -collection: Collection
        +get_pending_contexts()
        +get_pending_batch()
        +update_context_status()
        +update_context_result()
        +get_context_by_id()
    }
    
    class WorkerService {
        -settings: Settings
        -repository: Repository
        -processing_engine: ProcessingEngine
        -logger: Logger
        -running: bool
        +start()
        +stop()
        -process_contexts()
        -process_single()
        -process_batch()
        -handle_error()
    }
    
    class ProcessingEngine {
        -component_registry: ComponentRegistry
        -pipeline_factory: PipelineFactory
        +process_context()
        -create_pipeline()
        -execute_pipeline()
    }
    
    class ComponentRegistry {
        -components: Dict
        +register_component()
        +get_component()
        +list_components()
    }
    
    class PipelineFactory {
        -component_registry: ComponentRegistry
        +create_pipeline()
    }
    
    class ProcessingPipeline {
        -components: List[BaseComponent]
        -context: Dict
        +execute()
        -validate_components()
    }
    
    class BaseComponent {
        <<abstract>>
        +name: str
        +description: str
        +process(context)
        +validate_input(context)
    }
    
    class TemplateComponent {
        +template_service_url: str
        +process(context)
        -fetch_template()
        -apply_template()
    }
    
    class AIComponent {
        +model_name: str
        +api_key: str
        +process(context)
        -prepare_prompt()
        -call_ai_service()
    }
    
    class TransformationComponent {
        +transformation_rules: dict
        +process(context)
        -apply_transformations()
    }
    
    Settings --> Repository : configures
    Repository --> WorkerService : used by
    Settings --> WorkerService : configures
    ProcessingEngine --> WorkerService : used by
    ComponentRegistry --> ProcessingEngine : used by
    PipelineFactory --> ProcessingEngine : used by
    ComponentRegistry --> PipelineFactory : used by
    ProcessingPipeline --> PipelineFactory : creates
    BaseComponent <|-- TemplateComponent : extends
    BaseComponent <|-- AIComponent : extends
    BaseComponent <|-- TransformationComponent : extends
    ProcessingPipeline o-- BaseComponent : contains
```

## Component Responsibilities

| Component | Responsibility | Key Functionality |
|-----------|----------------|-------------------|
| Settings | Configuration management | Load and validate service configuration |
| Repository | Data access layer | CRUD operations for contexts in MongoDB |
| WorkerService | Main service orchestration | Poll for contexts, manage processing lifecycle |
| ProcessingEngine | Execute processing logic | Coordinate pipeline execution |
| ComponentRegistry | Component management | Register and retrieve components |
| PipelineFactory | Create processing pipelines | Assemble components into pipelines |
| ProcessingPipeline | Pipeline execution | Execute component chain in sequence |
| BaseComponent | Component contract | Define component interface |
| TemplateComponent | Template processing | Fetch and apply content templates |
| AIComponent | AI integration | Call AI services for content generation |
| TransformationComponent | Content transformation | Apply transformations to content |

## Component Interactions

### Context Processing Flow

```mermaid
sequenceDiagram
    participant WS as WorkerService
    participant R as Repository
    participant PE as ProcessingEngine
    participant PF as PipelineFactory
    participant CR as ComponentRegistry
    participant PP as ProcessingPipeline
    participant C1 as Component 1
    participant C2 as Component 2
    
    WS->>R: get_pending_contexts()
    R-->>WS: [context1, context2, ...]
    
    loop For each context
        WS->>PE: process_context(context)
        PE->>PF: create_pipeline(context.pipeline_config)
        PF->>CR: get_component(component_name)
        CR-->>PF: component_instance
        PF->>PP: new ProcessingPipeline(components)
        PE->>PP: execute(context)
        PP->>C1: process(context)
        C1-->>PP: updated_context
        PP->>C2: process(updated_context)
        C2-->>PP: final_context
        PP-->>PE: result
        PE-->>WS: result
        WS->>R: update_context_result(context_id, result)
    end
```

## Component Configuration

Components are configured through the service settings and context-specific configuration. Example configuration:

```json
{
  "component_registry": {
    "template": {
      "class": "TemplateComponent",
      "config": {
        "template_service_url": "http://template-service:8080/api/templates"
      }
    },
    "ai_generator": {
      "class": "AIComponent",
      "config": {
        "model_name": "gpt-4",
        "temperature": 0.7
      }
    },
    "transformer": {
      "class": "TransformationComponent",
      "config": {
        "transformation_rules": {
          "format": "markdown",
          "max_length": 1000
        }
      }
    }
  }
}
```

## Component Extension

The system is designed for extensibility. New components can be added by:

1. Creating a new class that inherits from `BaseComponent`
2. Implementing the required interface methods
3. Registering the component in the `ComponentRegistry`

## Error Handling

Components implement error handling strategies:

1. Pre-validation of inputs
2. Error capture during processing
3. Standardized error responses
4. Retry mechanisms for transient failures

## Next Steps

For more detailed information, refer to:
- [Data Flow Diagram](03-data-flow-diagram.md)
- [Context Processing Sequence Diagram](04-context-processing-sequence.md)
- [Component Design Pattern Documentation](07-component-design-pattern.md) 