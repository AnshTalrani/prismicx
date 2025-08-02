# Analysis Base Microservice

## Overview

The Analysis Base Microservice is designed to perform data analysis operations on contexts. It follows a component-based architecture similar to the generative-base service, allowing for modular and extensible analysis capabilities through a pipeline framework.

## Architecture

The service follows the MACH architecture principles:

- **Microservices-based**: Self-contained service focusing solely on analysis capabilities
- **API-first**: Provides RESTful APIs for context submission and retrieval
- **Cloud-native**: Designed to be deployed in containers with horizontal scaling
- **Headless**: Functions as a backend service consumed by other applications

## Key Components

### 1. Worker Service (`src/service/worker_service.py`)
- Polls for pending contexts from MongoDB
- Processes contexts individually or in batches
- Handles retries and error conditions
- Updates context statuses and results

### 2. Context Repository (`src/repository/context_repository.py`)
- Manages the persistence of contexts in MongoDB
- Provides methods for CRUD operations on contexts
- Handles optimistic locking with Redis to prevent duplicate processing
- Implements efficient indexing and batch operations

### 3. Processing Engine (`src/processing/processing_engine.py`)
- Coordinates the processing of contexts
- Creates and executes pipelines based on context configuration
- Handles errors and provides meaningful error messages
- Tracks metrics for processing time and component performance

### 4. Component Registry (`src/processing/component_registry.py`)
- Manages the registration and instantiation of components
- Provides factory methods for creating components
- Loads component configurations from settings or database
- Creates components from specifications via the Specification Interpreter

### 5. Pipeline and Pipeline Factory (`src/processing/pipeline.py`)
- Executes sequences of components in defined order
- Creates pipelines based on configuration or context type
- Manages the flow of data between components
- Collects metrics on pipeline execution

### 6. Component Contracts (`src/processing/components/contracts/`)
- Abstract base classes defining interfaces for different component types
- Ensures consistent behavior across component implementations
- Provides type safety and clear component responsibilities
- Enables compatibility checking in pipelines

### 7. Specification Interpreter (`src/processing/spec_interpreter.py`)
- Loads and interprets declarative specifications in YAML/JSON format
- Supports model specifications, decision trees, and pipeline specifications
- Translates high-level specifications into executable configurations
- Enables data scientists and domain experts to create models and pipelines without coding
- See [README-SPEC-INTERPRETER.md](README-SPEC-INTERPRETER.md) for detailed documentation

### 8. Analysis Components (`src/processing/components/`)
- Statistical Analysis Component: Performs statistical analysis on numerical data
- Text Analyzer Component: Analyzes text data for insights
- Entity Extractor Component: Extracts entities from structured and unstructured data
- Sentiment Analyzer Component: Analyzes sentiment in text
- And more specialized components

## Data Flow

1. A context is submitted for analysis through the API
2. The context is stored in MongoDB with "pending" status
3. The Worker Service polls for pending contexts
4. The Processing Engine creates a pipeline based on the context configuration
5. The pipeline executes each component in sequence on the context
6. Each component adds its analysis results to the context
7. The context is updated in MongoDB with results and "completed" status
8. The client can retrieve the completed context with analysis results

## Specification-Driven Analysis

The service supports a specification-driven approach to analysis:

1. Data scientists create declarative specifications in YAML/JSON format
2. The Specification Interpreter loads and interprets the specifications
3. The Component Registry creates components based on specifications
4. The Pipeline Factory creates pipelines based on specifications
5. Analysis is performed using the created pipelines and components

This approach separates the concerns of:
- **What** to analyze (defined by domain experts in specifications)
- **How** to analyze (implemented by developers in components)

## Error Handling

The service implements a comprehensive error handling strategy:

- Component-specific errors with retry recommendations
- Automatic retries with exponential backoff
- Detailed error tracking and reporting
- Graceful handling of timeouts and connection issues

## Scalability

The service can be scaled horizontally:

- Multiple worker instances can process contexts in parallel
- Redis locks prevent duplicate processing
- Batch processing for improved throughput
- Priority-based processing for time-sensitive analyses

## Getting Started

### Prerequisites

- Docker and Docker Compose
- MongoDB
- Redis

### Running the Service

1. Clone the repository
2. Configure environment variables in `.env`
3. Run with Docker Compose:

```bash
docker-compose up -d
```

### API Endpoints

- `POST /api/contexts`: Submit a context for analysis
- `GET /api/contexts/{context_id}`: Get a context by ID
- `GET /api/contexts?status=completed`: List contexts by status
- `GET /api/components`: List available analysis components
- `GET /api/pipelines`: List available analysis pipelines
- `GET /api/specs`: List available specifications
- `GET /api/health`: Health check endpoint

## Development

### Adding a New Component

1. Create a new class in `src/processing/components/` that inherits from the appropriate contract (e.g., `AnalyzerContract`)
2. Implement the required methods defined in the contract
3. Register the component in `component_registry.py`

### Creating a New Specification

1. Create a new YAML/JSON file in the appropriate specifications directory:
   - Model specifications: `specs/models/`
   - Decision tree specifications: `specs/decision_trees/`
   - Pipeline specifications: `specs/pipelines/`
2. Follow the templates in the `specs/examples/` directory
3. Test your specification with the test script: `tests/test_spec_interpreter.py`

### Configuration

The service is configured through:

- Environment variables
- MongoDB configuration collection
- Component and pipeline configuration files
- Declarative specifications in YAML/JSON format

## License

[Specify your license here] 