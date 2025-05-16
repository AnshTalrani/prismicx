"""
Main Application Module for Communication Base Service

This module serves as the entry point for the communication base service.
It initializes the application and starts the service.
"""

import asyncio
import logging
import uuid
import structlog
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import Settings, get_settings
from src.clients.system_users_repository_client import SystemUsersRepositoryClient
from src.clients.campaign_users_repository_client import CampaignUsersRepositoryClient
from src.storage.entity_repository_manager import EntityRepositoryManager
from src.processing.base_component import BaseComponent
from src.processing.component_registry import ComponentRegistry
from src.service.worker_service import WorkerService
from src.api.api import app as api_app
from src.common.monitoring import initialize_metrics, get_metrics

# Import new components
from src.models.llm.model_registry import ModelRegistry
from src.models.adapters.adapter_manager import AdapterManager
from src.models.adapters.hypnosis_adapter import HypnosisAdapter
from src.bot_integration.consultancy_bot.models.consultancy_llm import ConsultancyLLMManager
from src.bot_integration.sales_bot.models.sales_llm import SalesLLMManager
from src.bot_integration.support_bot.models.support_llm import SupportLLMManager
from src.config.config_integration import ConfigIntegration
from src.config.bot_configs import initialize_config_system

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger(__name__)

# Create main application
app = FastAPI(
    title="Communication Base Service",
    description="Microservice for handling various communication channels",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.mount("/api", api_app)

# Application state
app_state = {
    "system_repo": None,
    "campaign_repo": None,
    "entity_repo_manager": None,
    "component_registry": None,
    "worker_service": None,
    "settings": None,
    "initialized": False,
    # New state items
    "model_registry": None,
    "adapter_manager": None,
    "config_integration": None
}

# Initialize the configuration system during application startup
def initialize_app():
    """Initialize the application, including the configuration system."""
    # Initialize the configuration system
    if not initialize_config_system():
        logger.error("Failed to initialize configuration system")
        # You might want to exit the application or continue with default configs
    else:
        logger.info("Configuration system initialized successfully")

@app.on_event("startup")
async def startup_event():
    """
    Initialize the application on startup.
    """
    try:
        # Get settings
        settings = get_settings()
        app_state["settings"] = settings
        
        # Initialize metrics
        initialize_metrics(
            service_name=settings.service_name,
            include_prometheus=settings.enable_prometheus_metrics,
            enable_logging=True
        )
        
        # Initialize repositories
        system_repo = SystemUsersRepositoryClient()
        await system_repo.initialize()
        app_state["system_repo"] = system_repo
        
        campaign_repo = CampaignUsersRepositoryClient()
        await campaign_repo.initialize()
        app_state["campaign_repo"] = campaign_repo
        
        entity_repo_manager = EntityRepositoryManager()
        await entity_repo_manager.initialize()
        app_state["entity_repo_manager"] = entity_repo_manager
        
        logger.info("Repository clients initialized")
        
        # Initialize component registry
        component_registry = ComponentRegistry()
        app_state["component_registry"] = component_registry
        
        # Initialize and register components based on configuration
        await _initialize_components(settings, component_registry)

        # Initialize config integration
        config_integration = ConfigIntegration()
        app_state["config_integration"] = config_integration
        logger.info("Config integration initialized")
        
        # Initialize model registry and register LLM managers
        model_registry = ModelRegistry()
        app_state["model_registry"] = model_registry
        
        # Initialize LLM managers for each bot type
        consultancy_manager = ConsultancyLLMManager()
        sales_manager = SalesLLMManager()
        support_manager = SupportLLMManager()
        
        # Register LLM managers in the registry
        model_registry.register_manager("consultancy", consultancy_manager)
        model_registry.register_manager("sales", sales_manager)
        model_registry.register_manager("support", support_manager)
        
        logger.info("Model registry initialized with bot-specific LLM managers")
        
        # Initialize adapter manager and register hypnosis adapter
        adapter_manager = AdapterManager()
        app_state["adapter_manager"] = adapter_manager
        
        # Register default hypnosis adapter
        hypnosis_adapter = HypnosisAdapter()
        adapter_manager.registry.register_adapter(hypnosis_adapter)
        
        # Discover and register any other adapters
        num_adapters = adapter_manager.discover_and_register_adapters()
        logger.info(f"Adapter manager initialized with {num_adapters + 1} adapters")
        
        # Initialize worker service if workers are enabled
        if settings.workers_enabled:
            worker_id = f"{settings.service_name}-{uuid.uuid4().hex[:8]}"
            worker_service = WorkerService(
                worker_id=worker_id,
                system_repo=system_repo,
                component_registry=component_registry,
                settings=settings
            )
            
            app_state["worker_service"] = worker_service
            
            # Start worker service in background
            asyncio.create_task(worker_service.start())
            logger.info("Worker service started", worker_id=worker_id)
        
        # Mark as initialized
        app_state["initialized"] = True
        
        logger.info(
            "Application started successfully",
            service_name=settings.service_name,
            workers_enabled=settings.workers_enabled
        )
        
    except Exception as e:
        logger.error("Error during application startup", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up resources on application shutdown.
    """
    try:
        # Shutdown worker service if it exists
        if app_state["worker_service"]:
            await app_state["worker_service"].stop()
            logger.info("Worker service stopped")
        
        # Shutdown components
        if app_state["component_registry"]:
            await _shutdown_components(app_state["component_registry"])
        
        # Close repository connections
        if app_state["system_repo"]:
            await app_state["system_repo"].close()
        
        if app_state["campaign_repo"]:
            await app_state["campaign_repo"].close()
        
        logger.info("Repository connections closed")
        
        logger.info("Application shutdown complete")
        
    except Exception as e:
        logger.error("Error during application shutdown", error=str(e))

async def _initialize_components(
    settings: Settings, 
    registry: ComponentRegistry
) -> None:
    """
    Initialize and register components based on configuration.
    
    Args:
        settings: Application settings
        registry: Component registry
    """
    # Email component is intentionally disabled
    # Even if email_enabled is True in settings, we skip email component initialization
    """
    if settings.email_enabled:
        try:
            from src.processing.email_component import EmailComponent
            
            email_component = EmailComponent(
                component_id="email_sender",
                smtp_host=settings.smtp_host,
                smtp_port=settings.smtp_port,
                smtp_username=settings.smtp_username,
                smtp_password=settings.smtp_password,
                use_tls=settings.smtp_use_tls,
                default_sender=settings.default_email_sender,
                template_dir=settings.email_template_dir,
                tracking_domain=settings.tracking_domain
            )
            
            # Initialize and register
            await email_component.initialize()
            registry.register_component(email_component)
            
            logger.info("Email component registered")
            
        except Exception as e:
            logger.error("Failed to initialize email component", error=str(e))
    """
    
    # Add other components initialization here
    # (SMS, push notifications, etc.)

async def _shutdown_components(registry: ComponentRegistry) -> None:
    """
    Shutdown all registered components.
    
    Args:
        registry: Component registry
    """
    for component in registry.get_all_components():
        try:
            await component.shutdown()
            logger.info(f"Component {component.component_id} shutdown")
        except Exception as e:
            logger.error(
                f"Error shutting down component {component.component_id}",
                error=str(e)
            )

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Dictionary with health information
    """
    health_info = {
        "status": "healthy" if app_state["initialized"] else "initializing",
        "service": app_state["settings"].service_name if app_state["settings"] else "unknown",
        "version": app_state["settings"].version if app_state["settings"] else "unknown",
        "components": {}
    }
    
    # Add repository health
    if app_state["system_repo"] or app_state["campaign_repo"]:
        try:
            repo_health = {}
            if app_state["system_repo"]:
                repo_health["system_repo"] = await app_state["system_repo"].get_health()
            if app_state["campaign_repo"]:
                repo_health["campaign_repo"] = await app_state["campaign_repo"].get_health()
            
            health_info["repository"] = repo_health
            
            # If repository is not healthy, mark service as degraded
            if any(repo_health.get("status") != "healthy" for repo_health in repo_health.values()):
                health_info["status"] = "degraded"
                
        except Exception as e:
            health_info["repository"] = {"status": "error", "error": str(e)}
            health_info["status"] = "degraded"
    
    # Add component health
    if app_state["component_registry"]:
        components = app_state["component_registry"].get_all_components()
        for component_id, component in components.items():
            try:
                health_info["components"][component_id] = component.get_info()
            except Exception as e:
                health_info["components"][component_id] = {"status": "error", "error": str(e)}
    
    # Add worker health
    if app_state["worker_service"]:
        try:
            worker_health = app_state["worker_service"].get_health()
            health_info["worker"] = worker_health
            
            # If worker is not healthy, mark service as degraded
            if worker_health.get("status") != "healthy":
                health_info["status"] = "degraded"
                
        except Exception as e:
            health_info["worker"] = {"status": "error", "error": str(e)}
            health_info["status"] = "degraded"
    
    # Get metrics if available
    metrics = get_metrics()
    if metrics:
        try:
            health_info["metrics"] = {
                "counters_count": len(metrics.get_metrics().get("counters", {})),
                "gauges_count": len(metrics.get_metrics().get("gauges", {})),
                "observations_count": len(metrics.get_metrics().get("observations", {}))
            }
        except Exception as e:
            health_info["metrics"] = {"status": "error", "error": str(e)}
    
    return health_info

@app.get("/metrics")
async def get_service_metrics() -> Dict[str, Any]:
    """
    Get service metrics.
    
    Returns:
        Dictionary with metrics
    """
    metrics = get_metrics()
    if not metrics:
        raise HTTPException(status_code=503, detail="Metrics not initialized")
    
    return metrics.get_metrics()

# Main entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    
    # Get settings
    settings = get_settings()
    
    # Run server
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )

# Ensure the config system is initialized before starting the app
initialize_app() 