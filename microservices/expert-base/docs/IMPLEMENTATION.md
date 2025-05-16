# Expert Base Microservice Implementation

## Overview

This document details the implementation of the Expert Base microservice, focusing on the processing pipeline, expert frameworks, vector database integration, and API layer. The implementation uses open-source components to provide a flexible and extensible system for content generation, analysis, and review.

## Core Components Implemented

### 1. Processing Pipeline

We implemented a modular processing pipeline that follows a component-based architecture:

- **BasePipeline**: The foundation for all processing pipelines, handling component execution and error management
- **Pipeline Types**:
  - `ContentGenerationPipeline`: For content creation and enhancement
  - `ContentAnalysisPipeline`: For content analysis and metrics
  - `ContentReviewPipeline`: For content review and feedback

- **Components**:
  - Base component interfaces with standard methods like `process()` and `validate()`
  - Specialized component types for different processing needs (enhancement, analysis, review)
  - LLM-powered component (`LLMContentEnhancement`) with expert-specific prompt templates
  - Fallback implementations for graceful degradation when specialized components aren't available

The pipeline architecture supports dynamic component chaining and robust error handling to ensure that processing can continue even if individual components fail.

### 2. Expert Frameworks

We implemented a framework-based system for managing expert knowledge and capabilities:

- **BaseExpertFramework**: Abstract class defining the interface for all expert frameworks
- **InstagramExpertFramework**: Concrete implementation for Instagram expertise with specialized prompt templates
- Framework configuration using YAML for easy management and extension
- Prompt templates for different intents (generate, analyze, review) with expert-specific knowledge integration
- Support for parameter merging (core config, mode config, user parameters)

The frameworks are designed to be easily extended with new domain expertise and support for specialized intents. The current implementation includes Instagram framework with support for Etsy, Marketing, and Branding frameworks in the configuration but not yet implemented as concrete classes.

### 3. Vector Database Integration

We implemented a vector database integration using ChromaDB:

- **VectorStoreClient**: Main client for interacting with the vector database
- **ChromaDBClient**: Implementation using ChromaDB with both persistent and in-memory options
- **PlaceholderVectorClient**: Fallback for when ChromaDB is not available
- **Knowledge Hub**: Integration with expert frameworks for retrieving relevant knowledge
- Example knowledge seeding for testing and demonstration purposes

The vector database integration allows for semantic search based on content and filtering based on expert type, intent, and other metadata. It provides the foundation for knowledge-augmented processing.

### 4. LLM Integration

We implemented a model provider for LLM inference:

- **ModelProvider**: Main provider for accessing different LLM models
- **HuggingFaceModel**: Implementation using HuggingFace models through LangChain
- **PlaceholderModel**: Fallback for when real models are not available
- Standardized interface for text generation with configurable parameters

The LLM integration supports different model types for different expert domains and provides a flexible interface for prompt-based generation with knowledge context.

### 5. API Layer

Enhanced the existing API layer to support our new components:

- Updated routes to work with the new expert frameworks
- Added capabilities discovery to expose framework functionality
- Added readiness checks for deployment health monitoring
- Improved error handling and logging

## Key Features

- **Modular Design**: All components are designed to be modular and replaceable
- **Open-Source Integration**: Uses open-source libraries like ChromaDB, HuggingFace, and LangChain
- **Fallback Mechanisms**: Graceful degradation when dependencies are not available
- **Configuration-Driven**: Expert capabilities defined through configuration files
- **Knowledge Integration**: Contextual knowledge retrieval for improved responses
- **Multi-Intent Support**: Specialized processing for different content intents (generate, analyze, review)
- **Parameter Flexibility**: Layered parameter merging with override capabilities

## Usage

### API Endpoints

The Expert Base microservice exposes the following key endpoints:

- `POST /api/v1/expert/process`: Process content using an expert in a specified mode
  ```json
  {
    "expert": "instagram",
    "intent": "generate",
    "content": "This is a draft post about photography",
    "parameters": {
      "tone": "enthusiastic",
      "include_hashtags": true
    }
  }
  ```

- `GET /api/v1/expert/capabilities`: Get capabilities of available experts
- `GET /health`: Health check endpoint
- `GET /ready`: Readiness check endpoint that verifies all components are initialized

### Using Different Expert Frameworks

You can use different expert frameworks by specifying the `expert` field in your request:

```json
{
  "expert": "instagram",
  "intent": "generate",
  "content": "..."
}
```

Available experts are:
- `instagram`: For Instagram content
- `etsy`: For Etsy product descriptions
- `marketing`: For marketing content
- `branding`: For brand messaging

### Intents

Each expert supports different intents:

- `generate`: Create or enhance content
- `analyze`: Analyze content and provide insights
- `review`: Review content and provide feedback

## Configuration

### Expert Framework Configuration

The expert frameworks are configured in `config/experts.yaml` with the following structure:

```yaml
framework_id:
  core_config:
    model_id: "model_identifier"
    expert_type: "framework_type"
    base_parameters:
      # Default parameters
    capabilities:
      # List of capabilities
  modes:
    intent_name:
      processor: "processor_identifier"
      parameters:
        # Intent-specific parameters
      knowledge_filters:
        # Filters for knowledge retrieval
      allowed_user_parameters:
        # Parameters that users can override
```

### Environment Variables

The microservice can be configured using the following environment variables:

- `EXPERT_CONFIG_PATH`: Path to the expert configuration file (default: `config/experts.yaml`)
- `VECTOR_DB_PATH`: Path for persistent vector database storage (default: in-memory)
- `ENVIRONMENT`: Environment type (`development` or `production`) which affects logging and debugging
- `PORT`: Port to run the service on (default: `8000`)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins

## Development and Testing

### Running Locally

To run the microservice locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python -m src.main
```

### Testing

To run tests:

```bash
pytest
```

### Adding a New Expert Framework

To add a new expert framework:

1. Create a new framework class extending `BaseExpertFramework`
2. Implement the abstract methods, especially `get_prompt_template`
3. Add framework configuration to `config/experts.yaml`
4. Update the `_initialize_framework` method in `ExpertRegistry` to instantiate your new framework

## Extension Points

The implementation is designed to be easily extended in the following ways:

1. **New Expert Frameworks**: Add new domain expertise by creating a new framework class
2. **Additional Processing Components**: Extend the pipeline with new processing components
3. **Alternative Vector Databases**: Replace ChromaDB with another vector database
4. **Different LLM Models**: Switch to commercial LLM models when needed
5. **New Processing Intents**: Add new intent types beyond generate, analyze, and review

## Open Source Dependencies

The implementation relies on the following open-source libraries:

- **FastAPI**: API framework
- **ChromaDB**: Vector database
- **LangChain**: LLM integration
- **Sentence-Transformers**: Embedding generation
- **HuggingFace Transformers**: LLM models

## Next Steps

1. **Implement Additional Frameworks**: Complete the implementation of Etsy, Marketing, and Branding framework classes
2. **Enhanced Processing Components**: Add more specialized processing components
3. **Subtypes Support**: Enable framework subdivision (e.g., Instagram posts vs. stories)
4. **Knowledge Population**: Add more domain-specific knowledge to the vector database
5. **Performance Optimization**: Optimize for scale and responsiveness
6. **Comprehensive Testing**: Add integration and unit tests

## Conclusion

This implementation provides a solid foundation for the Expert Base microservice, focusing on modularity, extensibility, and maintainability. The use of open-source components ensures that the system can be deployed without immediate dependency on commercial services, while the architecture supports easy integration with commercial options in the future.

The modular design allows for progressive enhancement as specific capabilities are needed, and the fallback mechanisms ensure the system remains functional even when some components are unavailable. 