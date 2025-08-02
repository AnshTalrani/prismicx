"""
Vector Store Service - FastAPI Application
-----------------------------------------

This module defines the FastAPI application for the Vector Store Service.
"""

import os
import logging
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional

from dependencies import get_validated_token
from middleware import RequestLoggerMiddleware, TenantMiddleware
from routers import health, vector_store, admin, niche_store

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("vector-store-service")

# Get environment variables
APP_ENV = os.getenv("APP_ENV", "production")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Create FastAPI app
app = FastAPI(
    title="Vector Store Service",
    description="Service for managing vector embeddings and semantic search",
    version="1.0.0",
    debug=DEBUG,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(TenantMiddleware)

# Error handling
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Root endpoint
@app.get("/")
async def root(token: Optional[str] = Depends(get_validated_token)):
    """Root endpoint to verify the service is running."""
    return {
        "service": "Vector Store Service",
        "status": "running",
        "version": "1.0.0",
    }

# Include routers
app.include_router(
    health.router,
    prefix="/health",
    tags=["health"],
)

app.include_router(
    vector_store.router,
    prefix="/api/v1/vectors",
    tags=["vectors"],
    dependencies=[Depends(get_validated_token)],
)

app.include_router(
    admin.router,
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(get_validated_token)],
)

# Add the niche vector store router
app.include_router(
    niche_store.router,
    prefix="/api/v1/niches",
    tags=["niches"],
    dependencies=[Depends(get_validated_token)],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logger.info("Vector Store Service starting up")
    
    # Create data directories if they don't exist
    os.makedirs(os.getenv("VECTOR_STORE_DIR", "./data/vector_stores"), exist_ok=True)
    os.makedirs(os.getenv("NICHE_VECTOR_STORE_DIR", "./data/niche_vector_stores"), exist_ok=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Vector Store Service shutting down") 