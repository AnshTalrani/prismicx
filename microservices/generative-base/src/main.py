"""
Main Module

This is the main entry point for the Generative Base microservice.
It initializes the FastAPI application and starts the service.
"""

import logging
import asyncio
import structlog
from contextlib import asynccontextmanager

from .app import app
from .common.config import get_settings

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()]
)

logger = structlog.get_logger(__name__)

if __name__ == "__main__":
    """
    Run the application directly (for development).
    In production, use the Dockerfile which runs uvicorn.
    """
    import uvicorn
    
    settings = get_settings()
    logger.info(
        "Starting Generative Base service",
        host=settings.host,
        port=settings.port,
        service_type=settings.service_type
    )
    
    uvicorn.run(
        "src.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )


