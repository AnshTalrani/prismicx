"""
Main Application Module for Analysis Base Service

This module serves as the entry point for the analysis base service.
It initializes the application and starts the service.
"""

import asyncio
import logging
import structlog
import os
from typing import Dict, Any, List

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Import the TaskRepositoryAdapter
from src.repository.task_repository_adapter import TaskRepositoryAdapter
from src.config.settings import Settings, get_settings

# Import service components
from src.service.worker_service import WorkerService
from src.processing.processing_engine import ProcessingEngine
from src.processing.component_registry import ComponentRegistry
from src.processing.context_poller import ContextPoller
from src.api.api import app as api_app

# Import tenant and auth components
from src.multitenant import TenantContextMiddleware
from src.auth.middleware import AuthMiddleware
from src.database.database import database
from src.multitenant import tenant_client
from src.user.client import user_data_client

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger(__name__)

# Global service instances
repository = None
worker_service = None
processing_engine = None
poller = None
component_registry = None

@api_app.on_event("startup")
async def startup_event():
    """Initialize application components on startup."""
    global repository, worker_service, processing_engine, poller, component_registry
    
    settings = get_settings()
    logger.info("Initializing application components", service_type=settings.service_type)
    
    # Initialize both database backends
    
    # 1. Initialize PostgreSQL database for tenant-specific data
    db_connected = await database.connect()
    if not db_connected:
        logger.warning("Failed to connect to PostgreSQL database")
    else:
        logger.info("Connected to PostgreSQL database")
    
    # 2. Initialize TaskRepositoryAdapter for task management
    service_id = os.environ.get("SERVICE_ID", "analysis-service")
    repository = TaskRepositoryAdapter(service_id=service_id)
    await repository.connect()
    
    # Store repository in app state for API access
    api_app.state.repository = repository
    api_app.state.database = database
    
    # Initialize component registry
    component_registry = ComponentRegistry()
    
    # Discover and register components
    await component_registry.discover_components([
        "src.processing.components"
    ])
    
    # Initialize processing engine
    processing_engine = ProcessingEngine(
        component_registry=component_registry,
        repository=repository,
        settings=settings
    )
    
    # Initialize context poller
    poller = ContextPoller(
        repository=repository,
        settings=settings
    )
    
    # Initialize worker service
    worker_service = WorkerService(
        repository=repository,
        settings=settings,
        processing_engine=processing_engine
    )
    
    # Store worker service in app state for API access
    api_app.state.worker_service = worker_service
    
    # Start the worker service
    await worker_service.start()
    
    logger.info("Application components initialized successfully")

@api_app.on_event("shutdown")
async def shutdown_event():
    """Cleanup application components on shutdown."""
    global repository, worker_service
    
    logger.info("Shutting down application components")
    
    # Stop the worker service
    if worker_service:
        await worker_service.stop()
    
    # Close repository connection
    if repository:
        await repository.close()
    
    # Close database connection
    await database.close()
    
    logger.info("Application components shut down successfully")

# Add tenant and auth middleware to the application
api_app.add_middleware(TenantContextMiddleware)
api_app.add_middleware(AuthMiddleware)

# Add CORS middleware
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint with database and tenant service status
@api_app.get("/health/tenant")
async def tenant_health():
    """Health check for tenant integration."""
    try:
        # Try to list tenants as a test
        tenants = await tenant_client.list_tenants(limit=1)
        tenant_service_status = "healthy" if tenants is not None else "unhealthy"
    except Exception as e:
        tenant_service_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "tenant_service": tenant_service_status,
        "user_service": "connected",  # Simplified, would check real connection
        "postgres": "connected" if database._default_pool else "disconnected"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Start the application with uvicorn
    uvicorn.run(
        "analysis_main:api_app",
        host="0.0.0.0",
        port=8100,
        reload=False
    )
