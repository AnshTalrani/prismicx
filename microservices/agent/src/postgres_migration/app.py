#!/usr/bin/env python3
"""
PostgreSQL version of the Agent Service application entry point.
This module initializes and starts the agent service with PostgreSQL database support.
"""

import os
import logging
import asyncio
import uvicorn
from fastapi import FastAPI, Depends

from src.application.api.router import router as agent_router
from src.postgres_migration.middleware.tenant_middleware import TenantMiddleware
from src.postgres_migration.database.connection_manager import get_db_connection_manager
from src.postgres_migration.config.postgres_config import PostgresConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Agent Service",
    description="Agent Service with PostgreSQL multi-tenant support",
    version="1.0.0"
)

# Add tenant middleware
app.add_middleware(TenantMiddleware)

# Include agent router
app.include_router(agent_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize services and connections on application startup."""
    logger.info("Starting Agent Service with PostgreSQL support...")
    
    # Initialize database connection pool
    config = PostgresConfig()
    connection_manager = get_db_connection_manager()
    await connection_manager.initialize(config)
    
    logger.info("Agent Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown."""
    logger.info("Shutting down Agent Service...")
    
    # Close database connections
    connection_manager = get_db_connection_manager()
    await connection_manager.close_all_connections()
    
    logger.info("Agent Service shut down successfully")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to verify service is running."""
    return {"status": "healthy", "service": "agent", "database": "postgresql"}

if __name__ == "__main__":
    # Run the application with uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("src.postgres_migration.app:app", host="0.0.0.0", port=port, reload=False) 