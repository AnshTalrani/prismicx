# Generative Base Microservice

A microservice for processing generative contexts using a component-based pipeline architecture.

## Overview

The Generative Base microservice processes contexts through a configurable pipeline of components. It provides a worker service that polls for pending contexts, processes them through the pipeline, and updates their status and results.

## Features

- **Component-based processing pipeline**: Modular architecture for easy extension
- **Template-based content generation**: Process templates with variables
- **Batch processing support**: Efficiently process groups of related contexts
- **MongoDB integration**: Store and retrieve contexts and templates
- **REST API**: Trigger and monitor context processing
- **Metrics and health monitoring**: Track processing performance

## Architecture

The service follows the MACH architecture principles:

- **Microservices-based**: Self-contained service with a single responsibility
- **API-first**: RESTful API for integration with other services
- **Cloud-native**: Containerized with Docker for easy deployment
- **Headless**: Pure backend service with no UI components

## Components

The main components of the service are:

- **Worker Service**: Manages the lifecycle of processing jobs
- **Processing Pipeline**: Coordinates the execution of processing components
- **Context Poller**: Retrieves pending contexts from the repository
- **Repository**: Handles database interactions with MongoDB
- **Processing Components**: Modular processing units for specific tasks

## Getting Started

### Prerequisites

- Python 3.10+
- MongoDB
- Docker (for containerized deployment)

### Environment Variables

Configure the service using environment variables:

```
# Service identification
GENERATIVE_SERVICE_TYPE=default
GENERATIVE_SERVICE_NAME=generative-base

# Database settings
GENERATIVE_MONGODB_URL=mongodb://localhost:27017
GENERATIVE_DATABASE_NAME=generative

# Worker settings
GENERATIVE_MAX_PROCESSING_ATTEMPTS=3
GENERATIVE_RETRY_DELAY=60
GENERATIVE_POLL_INTERVAL=1.0

# Batch processing settings
GENERATIVE_BATCH_PROCESSING_ENABLED=true
GENERATIVE_BATCH_SIZE=10
GENERATIVE_BATCH_WAIT_TIME=5

# API settings
GENERATIVE_HOST=0.0.0.0
GENERATIVE_PORT=8000
GENERATIVE_DEBUG=false

# Logging settings
GENERATIVE_LOG_LEVEL=INFO
```

Component-specific settings can be configured with the prefix `GENERATIVE_COMPONENT_`:

```
GENERATIVE_COMPONENT_TEMPLATE_CACHE_SIZE=100
```

### Local Development

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Set environment variables or create a `.env` file
6. Run the service: `python -m src.main`

### Docker Deployment

Build and run the Docker container:

```bash
docker build -t generative-base .
docker run -p 8000:8000 --env-file .env generative-base
```

## API Endpoints

- `GET /`: Service information
- `GET /health`: Health check endpoint
- `GET /metrics`: Service metrics
- `POST /contexts/{context_id}/process`: Trigger processing for a specific context

## Adding Custom Components

1. Create a new component class that inherits from `BaseComponent`
2. Implement the `process` method (and optionally `process_batch` for batch processing)
3. Register the component in the `initialize_components` function in `app.py`

## License

This project is licensed under the MIT License - see the LICENSE file for details.


