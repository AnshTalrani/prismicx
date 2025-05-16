"""
Marketing Base Microservice

This microservice provides the API endpoints for the marketing base service.
The actual campaign processing is handled by dedicated workers that poll for campaigns from the central task repository.
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, Any, List

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Body, Response, status

from src.api.api import create_api
from src.config.settings import get_settings
from src.infrastructure.repositories.task_repository_adapter import TaskRepositoryAdapter
from src.processing.component_registry import ComponentRegistry
from src.common.metrics import setup_metrics

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(title="Marketing Base API", version="1.0.0")

# Main application state
app_state: Dict[str, Any] = {}


async def startup():
    """Initialize and start the application components."""
    settings = get_settings()
    
    # Setup metrics
    setup_metrics("marketing_base")
    
    logger.info("Starting Marketing Base microservice", settings=settings.dict())
    
    # Initialize task repository adapter
    repository = TaskRepositoryAdapter(service_id="marketing-api")
    app_state["repository"] = repository
    
    # Initialize component registry - only needed for API endpoints
    component_registry = ComponentRegistry()
    app_state["component_registry"] = component_registry
    
    # Initialize minimal components for API endpoints
    await register_components(component_registry, repository, settings)
    
    # Create and mount API routes
    api_router = create_api(repository=repository, settings=settings)
    app.include_router(api_router)
    
    logger.info("Marketing Base API started successfully")


async def shutdown():
    """Shutdown the application components."""
    logger.info("Shutting down Marketing Base API")
    
    # Shutdown components
    if "component_registry" in app_state:
        await app_state["component_registry"].shutdown_all()
    
    # Close repository
    if "repository" in app_state:
        await app_state["repository"].close()
    
    logger.info("Marketing Base API shutdown complete")


async def register_components(
    component_registry: ComponentRegistry,
    repository: TaskRepositoryAdapter,
    settings: Any
) -> None:
    """
    Register minimal components with the component registry for API functionality.
    
    Args:
        component_registry: The component registry
        repository: Task repository adapter
        settings: Application settings
    """
    # Import components here to avoid circular imports
    from src.processing.template_processor import TemplateProcessor
    
    # Register template processor for API preview capabilities
    template_processor = TemplateProcessor(
        template_dir=settings.template_dir,
        repository=repository
    )
    component_registry.register_component(template_processor)
    
    # Initialize all components
    await component_registry.initialize_all()
    
    logger.info(
        "Components registered",
        components=list(component_registry.get_all_components().keys())
    )


@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint."""
    health_info = {
        "status": "OK",
        "task_repository": "connected" 
    }
    
    return health_info


@app.get("/metrics", response_model=Dict[str, Any])
async def get_metrics():
    """Get application metrics."""
    metrics_data = {
        "service": "marketing_base"
    }
    
    # Add component metrics if available
    if "component_registry" in app_state:
        component_registry = app_state["component_registry"]
        metrics_data["components"] = component_registry.get_registry_info()
    
    return metrics_data


def handle_signals():
    """Setup signal handlers for graceful shutdown."""
    loop = asyncio.get_event_loop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))


@app.on_event("startup")
async def on_startup():
    """FastAPI startup event handler."""
    await startup()
    handle_signals()


@app.on_event("shutdown")
async def on_shutdown():
    """FastAPI shutdown event handler."""
    await shutdown()


def main():
    """Main entry point for running the application directly."""
    settings = get_settings()
    
    uvicorn.run(
        "src.marketing_main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )


if __name__ == "__main__":
    main()
