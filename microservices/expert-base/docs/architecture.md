# Expert Base Microservice Architecture

## Overview

The Expert Base microservice provides specialized AI-powered content expertise for various purposes including generation, analysis, and review. This service follows MACH architecture principles (Microservices, API-first, Cloud-native, Headless) and employs an intent-based hybrid configuration model to support flexible use across different services.

## Core Principles

- **Domain Expertise Encapsulation**: Consolidates platform-specific knowledge and best practices
- **Multi-Intent Processing**: Supports different processing modes (generate, analyze, review)
- **Extensible Expert Framework**: Easily add new expert domains and capabilities
- **Configurable Processing**: Adaptable behavior based on use case requirements
- **Knowledge-Augmented Processing**: Leverages vector databases for context-aware responses

## Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────┐
│                           Expert Base API Layer                        │
└───────────────┬─────────────────────────────────┬────────────────────┘
                │                                 │
┌───────────────▼────────────┐      ┌────────────▼─────────────────┐
│    Intent-Based Router     │      │      Discovery API           │
└───────────────┬────────────┘      └────────────┬─────────────────┘
                │                                │
┌───────────────▼────────────────────────────────▼─────────────────┐
│                      Orchestration Layer                          │
│                                                                   │
│  ┌──────────────────┐  ┌───────────────┐  ┌────────────────────┐ │
│  │ Parameter        │  │ Expert        │  │ Mode Selection     │ │
│  │ Transformation   │  │ Registry      │  │ & Configuration    │ │
│  └──────────┬───────┘  └───────┬───────┘  └──────────┬─────────┘ │
└─────────────┼────────────────┬─┼──────────────────┬──┼───────────┘
              │                │ │                  │  │
┌─────────────▼────────┐    ┌──▼─▼──────────┐    ┌─▼──▼────────────┐
│ Expert Bot Framework │    │ Knowledge Hub │    │ Processing      │
│                      │    │              │    │ Pipelines        │
│ ┌──────────────────┐ │    │ ┌──────────┐ │    │ ┌──────────────┐ │
│ │ Instagram Bot    │ │    │ │Vector DB │ │    │ │Generate Mode │ │
│ └──────────────────┘ │    │ │Interface │ │    │ └──────────────┘ │
│ ┌──────────────────┐ │    │ └──────────┘ │    │ ┌──────────────┐ │
│ │ Twitter Bot      │ │    │ ┌──────────┐ │    │ │Analyze Mode  │ │
│ └──────────────────┘ │    │ │Knowledge │ │    │ └──────────────┘ │
│ ┌──────────────────┐ │    │ │Retrieval │ │    │ ┌──────────────┐ │
│ │ LinkedIn Bot     │ │    │ └──────────┘ │    │ │Review Mode   │ │
│ └──────────────────┘ │    └──────────────┘    │ └──────────────┘ │
└──────────────────────┘                         └──────────────────┘
```

## Key Components

### 1. API Layer
The API layer provides endpoints for processing requests and discovering capabilities:

- **Process API**: Handle requests for processing content through expert bots
- **Discovery API**: Provide information about available experts and capabilities
- **Health & Monitoring API**: Status and performance monitoring endpoints

### 2. Orchestration Layer
The orchestration layer coordinates the processing of requests:

- **Intent-Based Router**: Routes requests to appropriate processing pipelines
- **Parameter Transformation**: Merges configurations from different sources
- **Expert Registry**: Manages the registration and retrieval of expert bots
- **Mode Selection**: Selects the appropriate processing mode based on intent

### 3. Expert Bot Framework
The expert bot framework provides the foundation for implementing expert bots:

- **Base Expert Bot**: Common functionality for all expert bots
- **Domain-Specific Bots**: Specialized bots for different platforms
- **Adapters**: LLM adaptation for specific domains
- **Model Integration**: Interface with underlying LLM models

### 4. Knowledge Hub
The knowledge hub manages the retrieval and use of domain-specific knowledge:

- **Vector DB Interface**: Integration with vector databases
- **Knowledge Retrieval**: Semantically relevant knowledge retrieval
- **Embedding Generation**: Convert content to embeddings for retrieval
- **Knowledge Fusion**: Integrate retrieved knowledge with processing

### 5. Processing Pipelines
Processing pipelines handle different types of requests:

- **Generate Mode**: Content generation and enhancement
- **Analyze Mode**: Content analysis and evaluation
- **Review Mode**: Content review and feedback

## Integration Patterns

The expert base microservice supports multiple integration patterns for different use cases:

### 1. Direct API Integration
Services make direct API calls to the expert base for synchronous processing.

```
┌─────────────────┐      ┌─────────────────┐
│ Generative Base │─────▶│   Expert Base   │
└─────────────────┘      └─────────────────┘
```

### 2. Event-Driven Integration
Services communicate through events for asynchronous processing.

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Marketing Base  │─────▶│  Event Bus      │─────▶│   Expert Base   │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

### 3. Worker-Based Processing
Expert base workers process items from shared storage or queues.

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Analysis Base   │─────▶│  Shared Queue   │◀────▶│ Expert Base     │
└─────────────────┘      └─────────────────┘      │ Workers         │
                                                  └─────────────────┘
```

## Configuration Model

The expert base uses a hybrid configuration model that combines:

1. **Core Configuration**: Base configuration for each expert bot
2. **Mode Configuration**: Intent-specific configuration for different processing modes
3. **User Parameters**: Request-specific parameters provided by the calling service

This hybrid approach balances centralized management with flexible usage across different services.

## Deployment Model

The expert base microservice is designed for containerized deployment:

```
┌─────────────────────────────────────────────────────────────┐
│                       API Gateway                           │
└────────────────────────────┬────────────────────────────────┘
                             │
                  ┌──────────▼───────────┐
                  │  Expert Base Service │
                  └──────────┬───────────┘
                             │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
┌────────▼─────────┐ ┌──────▼──────┐  ┌───────▼────────┐
│ Expert Processing │ │ Vector DB  │  │ Model Inference │
│ Workers          │ │ Service    │  │ Service         │
└──────────────────┘ └─────────────┘  └────────────────┘
``` 