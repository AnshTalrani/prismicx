"""
Main FastAPI application for the Outreach System.

This module serves as the entry point for the outreach system,
providing the main FastAPI application with all necessary middleware,
routing, and configuration.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .config.settings import settings
from .config.logging_config import get_logger, setup_logging
from .api.endpoints import campaigns, conversations, health, analytics
from .core.orchestrator import WorkflowOrchestrator
from .services.campaign_service import CampaignService
from .services.conversation_service import ConversationService


# Set up logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Outreach System...")
    
    # Initialize services
    try:
        # Initialize workflow orchestrator
        app.state.orchestrator = WorkflowOrchestrator()
        await app.state.orchestrator.initialize()
        
        # Initialize services
        app.state.campaign_service = CampaignService()
        app.state.conversation_service = ConversationService()
        
        logger.info("Outreach System started successfully")
    except Exception as e:
        logger.error(f"Failed to start Outreach System: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Outreach System...")
    
    try:
        # Cleanup services
        if hasattr(app.state, 'orchestrator'):
            await app.state.orchestrator.cleanup()
        
        logger.info("Outreach System shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered outreach and communication system",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)


# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Custom middleware for logging and monitoring
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and responses."""
    import time
    
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "extra_fields": {
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        }
    )
    
    # Process request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} in {process_time:.4f}s",
            extra={
                "extra_fields": {
                    "status_code": response.status_code,
                    "process_time": process_time
                }
            }
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {str(e)} in {process_time:.4f}s",
            extra={
                "extra_fields": {
                    "error": str(e),
                    "process_time": process_time
                }
            },
            exc_info=True
        )
        raise


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "extra_fields": {
                "path": request.url.path,
                "method": request.method,
                "error": str(exc)
            }
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment
    }


# Include API routers
app.include_router(
    campaigns.router,
    prefix=f"{settings.api_prefix}/campaigns",
    tags=["campaigns"]
)

app.include_router(
    conversations.router,
    prefix=f"{settings.api_prefix}/conversations",
    tags=["conversations"]
)

app.include_router(
    health.router,
    prefix=f"{settings.api_prefix}/health",
    tags=["health"]
)

app.include_router(
    analytics.router,
    prefix=f"{settings.api_prefix}/analytics",
    tags=["analytics"]
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "AI-powered outreach and communication system",
        "docs": "/docs" if settings.debug else None,
        "health": "/health"
    }


# Metrics endpoint (if enabled)
if settings.enable_metrics:
    @app.get("/metrics")
    async def metrics():
        """System metrics endpoint."""
        # This would typically return Prometheus metrics
        return {
            "status": "metrics endpoint",
            "note": "Implement actual metrics collection"
        }


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    return app


def run_app():
    """Run the application using uvicorn."""
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    run_app() 