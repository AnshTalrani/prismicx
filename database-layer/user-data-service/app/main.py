"""
User Data Service API

Main FastAPI application entry point.
"""

import logging
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db, close_db
from .middleware import TenantMiddleware
from .routers import users, preferences, extensions, insights, extensions_sync, insights_sync
from .config import settings
from .dependencies import close_mongo_connections

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="User Data Service",
    description="API for managing user data, extensions, and insights",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant middleware
app.add_middleware(TenantMiddleware)

# Register event handlers
@app.on_event("startup")
async def startup_event():
    """
    Execute startup tasks.
    """
    logger.info("User Data Service starting up")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    """
    Execute shutdown tasks.
    """
    logger.info("User Data Service shutting down")
    await close_db()
    close_mongo_connections()


# Include routers
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(preferences.router, prefix="/api/v1/preferences", tags=["preferences"])
app.include_router(extensions.router, prefix="/api/v1/extensions", tags=["Extensions (Async)"])
app.include_router(insights.router, prefix="/api/v1/insights", tags=["Insights (Async)"])
app.include_router(extensions_sync.router, prefix="/api/v1/sync/extensions", tags=["Extensions (Sync)"])
app.include_router(insights_sync.router, prefix="/api/v1/sync/insights", tags=["Insights (Sync)"])

# Import routers
from app.routers import user_extension, user_insight, user_context

# Include routers
app.include_router(user_extension.router)
app.include_router(user_insight.router)
app.include_router(user_context.router)


@app.get("/")
async def root():
    """Root endpoint for service health check."""
    return {
        "status": "healthy",
        "service": "user-data-service",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected"
    }


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    logger.debug(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response 