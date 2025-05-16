"""
Application Module

This module provides the main application functionality for the generative service.
It initializes the required components, services, and API endpoints.
"""

import asyncio
import logging
import structlog
from typing import Dict, Any, List
import os

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Import the TaskRepositoryAdapter directly instead of RepositoryAdapter
from .infrastructure.repository.task_repository_adapter import TaskRepositoryAdapter
from .common.config import Settings, get_settings
from .worker.worker_service import WorkerService
from .processing import ProcessingPipeline, ContextPoller
from .processing.base_component import BaseComponent
from .processing.component_registry import ComponentRegistry
from .processing.pipeline_builder import PipelineBuilder
from .processing.components import TemplateProcessingComponent
from .api.router import configure_routes

# Import configuration loader and template renderer
from .common.config_loader import ConfigurationLoader
from .common.template_renderer import TemplateRenderer

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger(__name__)

# Initialize the FastAPI application
app = FastAPI(
    title="Generative Base Service",
    description="Microservice for processing generative contexts",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TENANT MIDDLEWARE DISABLED
# The tenant middleware that previously switched database schemas has been disabled
# as it creates unnecessary overhead for batch processing.
# We now use a single schema approach with batch_id field for organization.
#
# app.add_middleware(
#     TenantMiddleware,
#     header_name="X-Tenant-ID",
#     exclude_paths=[
#         "/docs",
#         "/openapi.json",
#         "/redoc",
#         "/health",
#         "/metrics",
#         "/"
#     ]
# )

# Global service instances
repository = None
worker_service = None
pipeline = None
poller = None
config_loader = None
component_registry = None
pipeline_builder = None

@app.on_event("startup")
async def startup_event():
    """Initialize application components on startup."""
    global repository, worker_service, pipeline, poller, config_loader, component_registry, pipeline_builder
    
    settings = get_settings()
    logger.info("Initializing application components", service_type=settings.service_type)
    
    # Initialize configuration loader
    config_path = os.environ.get("GENERATIVE_CONFIG_PATH", "docs")
    config_loader = ConfigurationLoader(config_path)
    success = config_loader.load_all_configurations()
    
    if success:
        logger.info("Successfully loaded configuration files")
    else:
        logger.warning("Failed to load some configuration files, using defaults")
    
    # Initialize TaskRepositoryAdapter directly
    repository = TaskRepositoryAdapter()
    
    # Store repository in app state for API access
    app.state.repository = repository
    
    # Initialize component registry with configuration loader
    component_registry = ComponentRegistry(config_loader)
    
    # Register built-in components
    register_builtin_components(component_registry)
    
    # Load component configurations from YAML
    component_registry.load_component_configs()
    
    # Initialize pipeline builder
    pipeline_builder = PipelineBuilder(config_loader, component_registry)
    
    # Initialize default processing components using either:
    # 1. Document-driven approach if configs are available
    # 2. Code-based approach as fallback
    components = initialize_components(settings, component_registry, config_loader)
    
    # Initialize pipeline
    pipeline = ProcessingPipeline(
        components=components,
        repository=repository,
        settings=settings
    )
    
    # Initialize context poller with config loader
    poller = ContextPoller(
        repository=repository,
        settings=settings,
        config_loader=config_loader
    )
    
    # Initialize worker service
    worker_service = WorkerService(
        repository=repository,
        settings=settings,
        pipeline=pipeline,
        poller=poller,
        pipeline_builder=pipeline_builder  # Add pipeline builder for template-specific flows
    )
    
    # Store services in app state for API access
    app.state.worker_service = worker_service
    app.state.config_loader = config_loader
    app.state.component_registry = component_registry
    app.state.pipeline_builder = pipeline_builder
    
    # Start the worker service
    await worker_service.start()
    
    logger.info("Application components initialized successfully")
    
    # Configure API routes
    configure_routes(app)

@app.on_event("shutdown")
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
    
    # Close database connections
    from .multitenant import close_db_connections
    await close_db_connections()
    
    logger.info("Application components shut down successfully")

def register_builtin_components(registry: ComponentRegistry):
    """
    Register built-in component classes with the registry.
    
    Args:
        registry: Component registry to register with
    """
    # Register components from the components module
    registry.register_from_module(
        module_path="src.processing.components",
        base_class=BaseComponent,
        suffix="Component"
    )
    
    # Register any additional modules
    registry.register_from_module(
        module_path="src.processing.components.custom",
        base_class=BaseComponent,
        suffix="Component"
    )
    
    logger.info(f"Registered built-in components: {registry.list_components()}")

def initialize_components(settings: Settings, 
                         registry: ComponentRegistry,
                         config_loader: ConfigurationLoader) -> List[BaseComponent]:
    """
    Initialize and configure processing components.
    
    This function tries to use the document-driven approach first,
    falling back to code-based configuration if needed.
    
    Args:
        settings: Application configuration settings
        registry: Component registry
        config_loader: Configuration loader
        
    Returns:
        List of configured processing components
    """
    components = []
    
    # Try to build components from YAML configuration
    if config_loader:
        # Use the "standard_generation" flow by default
        flow_config = config_loader.get_flow("standard_generation")
        if flow_config:
            try:
                # Use the pipeline builder to create components
                pipeline_builder = PipelineBuilder(config_loader, registry)
                components = pipeline_builder.build_component_chain(flow_config)
                logger.info(f"Created components from flow configuration: {flow_config.get('id')}")
                return components
            except Exception as e:
                logger.error(f"Failed to build components from flow: {str(e)}")
                # Fall back to code-based approach
    
    # Code-based component initialization (fallback)
    logger.info("Using code-based component initialization")
    
    # Create template processing component
    template_component = TemplateProcessingComponent(
        name="template_processing",
        config={"continue_on_error": False}  # Halt pipeline if template processing fails
    )
    components.append(template_component)
    
    # Add any additional components here
    # ...
    
    logger.info(f"Initialized {len(components)} components using code-based approach")
    return components

@app.get("/")
async def root():
    """Root endpoint returning service information."""
    settings = get_settings()
    return {
        "service": "Generative Base Service",
        "version": "1.0.0",
        "service_type": settings.service_type,
        "status": "running",
        "document_driven": config_loader is not None and len(config_loader.get_flows()) > 0
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global repository, worker_service
    
    # Check repository connection
    repo_status = "connected" if repository and repository.is_connected() else "disconnected"
    
    # Check worker service status
    worker_status = "running" if worker_service and worker_service.running else "stopped"
    
    # Check configuration status
    config_status = "loaded" if config_loader and len(config_loader.get_flows()) > 0 else "not_loaded"
    
    # Determine overall health status
    is_healthy = repo_status == "connected" and worker_status == "running"
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "repository": repo_status,
        "worker_service": worker_status,
        "configuration": config_status,
        "details": {
            "service_type": get_settings().service_type
        }
    }

@app.get("/metrics")
async def get_metrics():
    """Get service metrics."""
    global worker_service, pipeline
    
    if not worker_service or not pipeline:
        raise HTTPException(status_code=503, detail="Service not fully initialized")
    
    # Get pipeline metrics
    pipeline_metrics = pipeline.get_metrics()
    
    # Get worker metrics
    worker_metrics = worker_service.get_metrics()
    
    # Get configuration metrics if available
    config_metrics = {}
    if config_loader:
        config_metrics = {
            "flows_count": len(config_loader.get_flows()),
            "modules_count": len(config_loader.get_enabled_modules()),
            "templates_count": len(config_loader.template_flow_mapping)
        }
    
    return {
        "pipeline": pipeline_metrics,
        "worker": worker_metrics,
        "config": config_metrics
    }

@app.post("/contexts/{context_id}/process")
async def process_context(
    context_id: str, 
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
):
    """
    Trigger processing for a specific context.
    
    Args:
        context_id: ID of the context to process
        background_tasks: FastAPI background tasks
        settings: Application settings
        
    Returns:
        Processing status
    """
    global worker_service, repository
    
    if not worker_service or not repository:
        raise HTTPException(status_code=503, detail="Service not fully initialized")
    
    # Get the context
    context = await repository.get_context(context_id)
    if not context:
        raise HTTPException(status_code=404, detail=f"Context {context_id} not found")
    
    # Check if the context has a valid template ID
    template_id = context.get("template_id")
    if not template_id:
        raise HTTPException(status_code=400, detail="Context has no template ID")
    
    # Process the context in the background
    background_tasks.add_task(worker_service.process_context, context)
    
    return {
        "status": "processing",
        "context_id": context_id,
        "template_id": template_id
    }