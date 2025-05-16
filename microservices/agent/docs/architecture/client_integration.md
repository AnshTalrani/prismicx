# Service Integration Guide

This document explains how to add new service workers to the Agent microservice, following the established worker-based architecture.

## Worker Architecture Overview

The Agent microservice uses specialized worker classes to process tasks and communicate with various backend services. These workers follow a consistent pattern for ease of maintenance and extension.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Agent Microservice                          │
│                                                                 │
│  ┌────────────────┐            ┌────────────────┐              │
│  │                │            │                │              │
│  │ RequestService │───────────►│ContextManager  │              │
│  │                │            │                │              │
│  └────────────────┘            └───────┬────────┘              │
│                                        │                        │
│                                        │ stores                 │
│                                        ▼                        │
│                              ┌────────────────┐                 │
│                              │   MongoDB      │                 │
│                              │   Contexts     │                 │
│                              └────────┬───────┘                 │
│                                       │                         │
│                                       │ poll                    │
│                                       ▼                         │
│  ┌────────────────┐     ┌────────────────┐    ┌──────────────┐ │
│  │                │     │                │    │              │ │
│  │  Generative    │     │   Analysis     │    │Communication │ │
│  │    Worker      │     │    Worker      │    │   Worker     │ │
│  │                │     │                │    │              │ │
│  └───────┬────────┘     └───────┬────────┘    └──────┬───────┘ │
│          │                      │                    │         │
└──────────┼──────────────────────┼────────────────────┼─────────┘
           │                      │                    │
           ▼                      ▼                    ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│                  │    │                  │    │                  │
│  Generation Base │    │  Analysis Base   │    │  Communication   │
│     Service      │    │     Service      │    │     Service      │
│                  │    │                  │    │                  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

## Adding a New Service Worker

To add a new worker for a different service, follow these steps:

### 1. Create the Worker Class

Create a new file under `src/infrastructure/workers/` with the naming convention `{service_name}_worker.py`.

Each worker should follow this basic structure:

```python
"""
Worker for [Service Name] service.

Processes contexts requiring [service name] services by pulling directly from the repository.
Includes integrated client functionality for communicating with the [Service Name] service.
"""
import logging
import httpx
import os
import uuid
from typing import Dict, Any, Optional

from src.infrastructure.workers.worker_base import ClientWorker

class ServiceNameWorker(ClientWorker):
    """Worker for [service name] service with integrated client functionality."""
    
    def __init__(
        self, 
        repository,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize [service name] worker.
        
        Args:
            repository: MongoDB repository for context access
            base_url: Base URL of the [Service Name] service
            api_key: API key for authentication
            **kwargs: Additional arguments to pass to base class
        """
        super().__init__("SERVICE_NAME", repository, **kwargs)
        
        # Client configuration
        self.base_url = base_url or os.getenv("SERVICE_NAME_URL", "http://service-name:8080")
        self.api_key = api_key or os.getenv("SERVICE_NAME_API_KEY", "")
        self.http_client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
            }
        )
        self.logger.info(f"Initialized ServiceNameWorker with URL: {self.base_url}")
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a context using the integrated [service name] client functionality.
        
        Args:
            context: Context to process
            
        Returns:
            Processing result
        """
        template_id = context["template"]["id"]
        service_template = context["template"].get("service_template", {})
        
        # Log processing start
        self.logger.info(f"Processing template {template_id} with [service name] service")
        
        # Execute template
        result = await self.execute_template(
            template_id=template_id,
            service_template=service_template,
            context=context
        )
        
        return result
    
    async def execute_template(
        self, 
        template_id: str, 
        service_template: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a template on the [Service Name] service.
        
        Args:
            template_id: ID of the template to execute
            service_template: The service-specific template data 
            context: Execution context
            
        Returns:
            Service result
        """
        try:
            # Prepare request payload
            payload = {
                "template_id": template_id,
                "template_data": service_template,
                "context": context,
                "request_id": context.get("request_id", str(uuid.uuid4()))
            }
            
            # Check if service is available
            if await self._is_service_available():
                # Send request to [Service Name] service
                url = f"{self.base_url}/api/v1/execute"
                response = await self.http_client.post(url, json=payload)
                
                if response.status_code == 200:
                    # Parse response
                    result = response.json()
                    self.logger.info(f"Successfully executed template {template_id}")
                    return result
                else:
                    # Handle error response
                    error_message = f"Error from [Service Name]: {response.status_code} - {response.text}"
                    self.logger.error(error_message)
                    return self._create_error_response(template_id, error_message)
            else:
                # Return error response if service not available
                error_message = "[Service Name] service not available"
                self.logger.error(error_message)
                return self._create_error_response(template_id, error_message)
                
        except Exception as e:
            self.logger.exception(f"Error executing template {template_id}: {str(e)}")
            return self._create_error_response(template_id, str(e))

    async def _is_service_available(self) -> bool:
        """
        Check if the [Service Name] service is available.
        
        Returns:
            True if the service is available, False otherwise
        """
        try:
            url = f"{self.base_url}/health"
            response = await self.http_client.get(url, timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False
            
    def _create_error_response(self, template_id: str, error_message: str) -> Dict[str, Any]:
        """
        Create an error response.
        
        Args:
            template_id: Template ID
            error_message: Error message
            
        Returns:
            Error response
        """
        return {
            "template_id": template_id,
            "success": False,
            "status": "error",
            "error": error_message
        }
        
    async def stop(self):
        """Stop the worker processing loop and close HTTP client."""
        # First call the parent stop method
        await super().stop()
        
        # Then close the HTTP client
        if self.http_client:
            await self.http_client.aclose()
            self.logger.info("Closed HTTP client")
            
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

### 2. Implement Service-Specific Methods

In addition to the core methods, you may need to implement service-specific methods based on the requirements of your service. For example:

```python
async def process_special_request(self, 
    data: Dict[str, Any], 
    context_id: str
) -> Dict[str, Any]:
    """
    Process a special request type.
    
    Args:
        data: Request data
        context_id: Context ID
    
    Returns:
        Processing result
    """
    try:
        # Implementation here
        # ...
        
        return {"success": True, "result": "..."}
    except Exception as e:
        self.logger.exception(f"Error processing special request: {str(e)}")
        return {"success": False, "error": str(e)}
```

### 3. Update the Workers Package

Add your new worker to the `__init__.py` file in the workers package:

```python
"""
Worker implementations for the Agent microservice.
"""

from src.infrastructure.workers.worker_base import ClientWorker
from src.infrastructure.workers.generative_worker import GenerativeWorker
from src.infrastructure.workers.analysis_worker import AnalysisWorker
from src.infrastructure.workers.communication_worker import CommunicationWorker
from src.infrastructure.workers.service_name_worker import ServiceNameWorker  # Add this line

__all__ = [
    "ClientWorker",
    "GenerativeWorker",
    "AnalysisWorker", 
    "CommunicationWorker",
    "ServiceNameWorker"  # Add this line
]
```

### 4. Initialize the Worker in main.py

Initialize your worker in `main.py`:

```python
# Import the worker
from src.infrastructure.workers import ServiceNameWorker

# Create worker instance
service_name_worker = ServiceNameWorker(mongo_context_repository)

# Start/stop the worker in startup/shutdown events
@app.on_event("startup")
async def startup_event():
    # ... other startup code ...
    
    # Start your worker
    await service_name_worker.start()
    
@app.on_event("shutdown")
async def shutdown_event():
    # ... other shutdown code ...
    
    # Stop your worker
    await service_name_worker.stop()
```

## Worker Architecture Benefits

The worker-based architecture offers several advantages:

1. **Decentralized Processing**: Workers independently poll for relevant tasks, removing the need for central orchestration.
2. **Improved Scalability**: Each worker type can be scaled independently based on demand.
3. **Fault Isolation**: Failure in one worker doesn't affect others.
4. **Simplified Codebase**: Each worker encapsulates all the logic needed to process its service type.
5. **Reduced Latency**: Direct polling eliminates orchestration overhead.

## Best Practices

1. **Error Handling**: Implement comprehensive error handling within your worker class.
2. **Resource Management**: Ensure proper cleanup of resources in the `stop()` method.
3. **Contextual Logging**: Include relevant context information in log messages.
4. **Configuration**: Use environment variables for configuration whenever possible.
5. **Testing**: Create mock implementations for testing that don't require the actual service. 