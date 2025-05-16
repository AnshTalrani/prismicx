"""
Management Systems API - Main Application Entry Point
"""
import logging
import os
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from .common.db_client_wrapper import db_client
from .config.settings import get_settings
from .api.health import router as health_router
# Replace api router imports with routers from src/routers
from .routers.management import router as management_router
from .routers.config import router as config_router
from .routers.automation import router as automation_router
from .routers.plugins import router as plugins_router
from .services.management_service import management_service
from .services.automation_service import get_automation_service
from .cache.redis_cache import initialize_cache, close_cache
from .tenant.middleware import TenantMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    settings = get_settings()
    logger.info(f"Starting Management Systems API with config: {settings.api_title}")
    
    # Initialize cache
    await initialize_cache()
    logger.info("Cache initialized")
    
    # Initialize database client wrapper
    try:
        await db_client.initialize()
        logger.info("Database client wrapper initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database client wrapper: {e}")
    
    # Initialize management service
    try:
        await management_service.initialize()
        logger.info("Management service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize management service: {e}")
    
    # Initialize automation service
    try:
        automation_service = get_automation_service()
        logger.info("Automation service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize automation service: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Management Systems API")
    
    # Close the database clients
    try:
        await db_client.close()
        logger.info("Database clients closed")
    except Exception as e:
        logger.error(f"Error closing database clients: {e}")
        
    # Close the cache
    await close_cache()
    logger.info("Cache closed")

# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant middleware
app.add_middleware(
    TenantMiddleware,
    tenant_header="X-Tenant-ID"
)

# Middleware for request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request details and timing information."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    logger.debug(
        f"Request: {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time:.2f}ms"
    )
    
    return response

# Include routers - updated to use the ones from src/routers
app.include_router(health_router)
app.include_router(management_router)
app.include_router(config_router)
app.include_router(automation_router)
app.include_router(plugins_router)

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint providing basic API information."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description
    } 