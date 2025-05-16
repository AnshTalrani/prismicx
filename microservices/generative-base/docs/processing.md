# Processing Architecture

This document explains the processing architecture of the Generative Base service, including how context processing, components, and flows are managed through the document-driven configuration approach.

## Overview

The processing system is the core of the Generative Base service, responsible for taking input contexts and transforming them through a sequence of specialized components. The entire processing workflow can be configured through YAML files without modifying code.

## Key Components

### 1. Processing Pipeline

The processing pipeline orchestrates the flow of data through a series of processing components. It:

- Manages the lifecycle of processing contexts
- Executes components in the defined sequence
- Handles errors and retries
- Collects metrics on processing performance

The pipeline can be tailored for different templates, allowing specialized processing for different types of generative tasks.

### 2. Pipeline Builder

The pipeline builder constructs processing pipelines based on flow definitions from YAML configuration files. It:

- Creates component instances from module configurations
- Applies template-specific overrides
- Builds template-specific pipelines on demand
- Supports dynamic pipeline creation based on context requirements

### 3. Context Poller

The context poller retrieves pending contexts from the repository for processing. It:

- Polls for contexts based on service type and status
- Maps templates to appropriate flows
- Supports both single and batch context retrieval
- Applies prioritization and retry policies

### 4. Component Registry

The component registry manages all available processing components. It:

- Registers components by name
- Loads component configurations from YAML
- Creates component instances with the correct configuration
- Supports automatic discovery of components

### 5. Base Component

The base component class serves as the foundation for all processing components. Each component:

- Processes a specific aspect of the context
- Has a configurable behavior through YAML
- Supports customizable prompt templates
- Can be extended with specialized processing logic

## Processing Flows

Processing flows define sequences of components that work together to process contexts. Flows are defined in the `framework_definition.yaml` file and include:

```yaml
flows:
  - id: "standard_generation"
    name: "Standard Content Generation"
    description: "Complete pipeline for high-quality content generation"
    modules:
      - id: "input_preprocessing"
        config_override: {}
      - id: "deep_input_fusion"
        config_override: {}
      # ... additional components
```

Each flow specifies:
- A unique identifier
- A human-readable name and description
- A sequence of modules (components) to execute
- Optional configuration overrides for each module

## Template Processing

Templates are mapped to flows in the configuration, allowing different processing pipelines for different template types:

1. When a context is retrieved, its template ID is used to determine the appropriate flow
2. The pipeline builder constructs a pipeline specific to that template
3. The worker service processes the context through the template-specific pipeline

This approach allows for specialized processing without modifying code.

## Batch Processing

The Generative Base service supports batch processing for efficient handling of multiple related contexts:

1. The context poller groups pending contexts by template ID
2. The worker service processes the batch through a template-specific pipeline
3. Results are updated for all contexts in the batch simultaneously

Batch processing can significantly improve throughput for similar contexts.

## Document-Driven Configuration

All aspects of processing can be configured through YAML files:

1. **Component Behavior**: `modules/<module_id>.yaml` files define the behavior, prompts, and configuration options for each processing component
2. **Processing Flows**: The `framework_definition.yaml` file defines the available flows and their component sequences
3. **Template Mapping**: The framework configuration maps templates to flows, determining how each context is processed

## Error Handling

The processing architecture includes robust error handling:

1. Component-level error handling with configurable "continue_on_error" behavior
2. Pipeline-level retry mechanisms
3. Fallback options when components fail
4. Detailed error logging and tracking

## Extending with Custom Components

To extend the processing capabilities:

1. Create a new component class that inherits from `BaseComponent`
2. Implement the required methods (`process`, `validate_config`)
3. Create a module configuration file in the `docs/modules/` directory
4. Register the component in the component registry
5. Add the module to flows in `framework_definition.yaml`

Custom components can be added without modifying existing components or flows.

## Metrics and Monitoring

The processing system collects metrics at multiple levels:

1. **Component-level metrics**: Processing time, success/failure rates
2. **Pipeline metrics**: Overall throughput, bottleneck identification
3. **Template-specific metrics**: Performance by template type
4. **Worker metrics**: Worker utilization, batch processing efficiency

These metrics are accessible through the `/metrics` API endpoint. 