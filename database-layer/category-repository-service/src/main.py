"""
Category Repository Service main application.

This module initializes and starts the FastAPI application for the Category Repository Service.
"""

import logging
import asyncio
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config.settings import get_settings, Settings
from .api import categories, factors, campaigns, assignments, batch_as_objects
from .repository.category_repository import CategoryRepository

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
    
    # Connect to database on startup
    logger.info("Connecting to MongoDB...")
    repository = CategoryRepository(
        mongodb_uri=settings.mongodb_uri,
        database_name=settings.mongodb_database,
        categories_collection=settings.mongodb_categories_collection,
        factors_collection=settings.mongodb_factors_collection,
        campaigns_collection=settings.mongodb_campaigns_collection,
        batch_as_objects_collection=settings.mongodb_batch_as_objects_collection,
        entity_assignments_collection=settings.mongodb_entity_assignments_collection
    )
    connected = await repository.connect()
    if not connected:
        logger.error("Failed to connect to MongoDB")
    else:
        logger.info("Connected to MongoDB successfully")
    
    # Store repository in app state
    app.state.repository = repository
    
    # Yield control to the application
    yield
    
    # Close connections on shutdown
    logger.info("Closing MongoDB connection...")
    await repository.close()
    logger.info("Shutdown complete")


# Create FastAPI application
def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI application instance
    """
    settings = get_settings()
    
    app = FastAPI(
        title="Category Repository Service",
        description="API for managing categories, factors, campaigns, batch as objects, and entity assignments",
        version=settings.service_version,
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(categories.router, tags=["categories"])
    app.include_router(factors.router, tags=["factors"])
    app.include_router(campaigns.router, tags=["campaigns"])
    app.include_router(batch_as_objects.router, tags=["batch_as_objects"])
    app.include_router(assignments.router, tags=["assignments"])
    
    # Add health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check(settings: Settings = Depends(get_settings)):
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": settings.service_name,
            "version": settings.service_version
        }
    
    return app


# Create application instance
app = create_app()


# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level="info"
    ) 