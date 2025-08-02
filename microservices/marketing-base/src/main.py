"""
Main application entry point.

This module initializes the FastAPI application with all required middleware,
dependencies, and routes.
"""

import os
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .config.app_config import get_config
from .config.logging_config import configure_logging, LoggingMiddleware, get_logger
from .infrastructure.database.database_factory import DatabaseFactory
from .infrastructure.repositories.tenant_repository_impl import TenantRepositoryImpl
from .multitenant.tenant.tenant_middleware import TenantMiddleware
from .domain.repositories.tenant_repository import TenantRepository

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

# Create the FastAPI application
app = FastAPI(
    title="Marketing Service",
    description="API for managing marketing campaigns and automation",
    version="1.0.0"
)

# Get configuration
config = get_config()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Set up dependency injection
def get_tenant_repository() -> TenantRepository:
    """Get tenant repository instance."""
    return TenantRepositoryImpl()

# Add tenant middleware
app.add_middleware(
    TenantMiddleware,
    tenant_repository=get_tenant_repository()
)

# Register application startup event handler
@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    logger.info("Starting marketing service...")
    
    # Initialize database connections
    from .infrastructure.database.postgres_database import PostgresDatabase
    
    # Explicitly initialize each database connection
    user_db = DatabaseFactory.get_user_db()
    await user_db.initialize()
    
    crm_db = DatabaseFactory.get_crm_db()
    await crm_db.initialize()
    
    product_db = DatabaseFactory.get_product_db()
    await product_db.initialize()
    
    marketing_db = DatabaseFactory.get_marketing_db()
    await marketing_db.initialize()
    
    logger.info("Database connections initialized")

# Register application shutdown event handler
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown."""
    logger.info("Shutting down marketing service...")
    
    # Close database connections
    await DatabaseFactory.close_all()
    
    logger.info("Marketing service shutdown complete")

# Root endpoint for health checks
@app.get("/")
async def root():
    """Root endpoint for service health check."""
    return {"status": "healthy", "service": "marketing"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "marketing"}

# Import and include routers
from .interfaces.api.routes import campaigns, tasks

app.include_router(campaigns.router, prefix="/api/v1/campaigns", tags=["campaigns"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting marketing service on {config.host}:{config.port}")
    uvicorn.run(
        "src.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug
    ) 