"""
Management System Repository Service main application.

This module initializes and starts the FastAPI application for the Management System Repository Service.
"""

import logging
import asyncio
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config.settings import get_settings, Settings
from .api.plugin_router import plugin_router
from .api.tenant_router import tenant_router
from .api.config_router import config_router
from .repository.plugin_repository import PluginRepository
from .repository.schema_manager import SchemaManager
from .repository.config_repository import ConfigRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


# Lifespan manager for FastAPI application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI application lifespan manager.
    
    Handles startup and shutdown tasks for the application.
    """
    # Get settings
    settings = get_settings()
    
    # Initialize database connections
    logger.info("Connecting to PostgreSQL...")
    plugin_repo = PluginRepository(
        db_host=settings.db_host,
        db_port=settings.db_port,
        db_user=settings.db_user,
        db_password=settings.db_password,
        db_name=settings.db_name
    )
    
    schema_manager = SchemaManager(
        db_host=settings.db_host,
        db_port=settings.db_port,
        db_user=settings.db_user,
        db_password=settings.db_password,
        db_name=settings.db_name
    )
    
    logger.info("Connecting to MongoDB config database...")
    config_repo = ConfigRepository(
        db_host=settings.mongodb_host,
        db_port=settings.mongodb_port,
        db_user=settings.mongodb_user,
        db_password=settings.mongodb_password,
        db_name=settings.mongodb_db
    )
    
    # Initialize connections
    await plugin_repo.initialize()
    await schema_manager.initialize()
    await config_repo.initialize()
    
    # Store repositories in app state
    app.state.plugin_repo = plugin_repo
    app.state.schema_manager = schema_manager
    app.state.config_repo = config_repo
    
    # Yield control to the application
    yield
    
    # Close connections on shutdown
    logger.info("Closing database connections...")
    await plugin_repo.close()
    await schema_manager.close()
    await config_repo.close()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Management System Repository Service",
    description="A centralized repository for managing business management system data within the PrismicX platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(plugin_router, prefix="/api/v1")
app.include_router(tenant_router, prefix="/api/v1")
app.include_router(config_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for the service."""
    return {"status": "ok", "service": "management-system-repository"}


# Main entry point
if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    ) 