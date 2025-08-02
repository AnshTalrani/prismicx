"""
API Module for Analysis Base Service

This module provides the REST API endpoints for the analysis base service.
It handles analysis requests and manages analysis workflows.
"""

import asyncio
import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..repository.repository import Repository
from ..config.settings import Settings, get_settings
from ..service.worker_service import WorkerService
from ..processing.processing_engine import ProcessingEngine
# Import tenant API router
from ..multitenant import tenant_router

# Configure structured logging
logger = structlog.get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Analysis Base Service",
    description="Microservice for processing analytical contexts",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include tenant API router
app.include_router(tenant_router)

# API models
class TemplateRequest(BaseModel):
    """Model for template processing requests"""
    template: Dict[str, Any]
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="Input data for processing")

class TemplateResponse(BaseModel):
    """Model for template processing responses"""
    context_id: str = Field(description="ID of the created context")
    status: str = Field(description="Status of the request")
    message: str = Field(description="Response message")

class HealthResponse(BaseModel):
    """Model for health check responses"""
    status: str = Field(description="Service health status")
    repository: str = Field(description="Repository connection status")
    worker_service: str = Field(description="Worker service status")
    details: Dict[str, Any] = Field(description="Additional health details")

@app.get("/")
async def root():
    """Root endpoint returning service information."""
    settings = get_settings()
    return {
        "service": "Analysis Base Service",
        "version": "1.0.0",
        "service_type": settings.service_type,
        "status": "running"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service health status
    """
    settings = get_settings()
    
    # Get repository and worker service status from application context
    repository = app.state.repository if hasattr(app.state, "repository") else None
    worker_service = app.state.worker_service if hasattr(app.state, "worker_service") else None
    
    # Check repository connection
    repo_status = "connected" if repository and repository.is_connected() else "disconnected"
    
    # Check worker service status
    worker_status = "running" if worker_service and worker_service.running else "stopped"
    
    # Determine overall health status
    is_healthy = repo_status == "connected" and worker_status == "running"
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "repository": repo_status,
        "worker_service": worker_status,
        "details": {
            "service_type": settings.service_type
        }
    }

@app.get("/metrics")
async def get_metrics():
    """Get service metrics."""
    worker_service = app.state.worker_service if hasattr(app.state, "worker_service") else None
    
    if not worker_service:
        raise HTTPException(status_code=503, detail="Worker service not initialized")
    
    # Get metrics from worker service
    metrics = worker_service.get_metrics()
    
    return {
        "timestamp": metrics.get("timestamp"),
        "worker": {
            "running": metrics.get("running", False),
            "batch_mode": metrics.get("batch_mode", False),
            "processed_count": metrics.get("processed_count", 0),
            "success_count": metrics.get("success_count", 0),
            "error_count": metrics.get("error_count", 0)
        },
        "processing_engine": metrics.get("processing_engine", {})
    }

@app.post("/api/v1/templates/process", response_model=TemplateResponse)
async def process_template(
    request: TemplateRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
):
    """
    Process a template and execute the analysis workflow.
    
    Args:
        request: Template processing request containing template and input data
        background_tasks: FastAPI background tasks
        settings: Application settings
        
    Returns:
        Response with context ID and status
    """
    repository = app.state.repository
    
    if not repository:
        raise HTTPException(status_code=503, detail="Repository not initialized")
    
    try:
        # Validate template
        if not request.template:
            raise HTTPException(status_code=400, detail="Template is required")
        
        # Create a context from the template
        context = {
            "template": request.template,
            "input": request.input_data or {},
            "status": "pending",
            "service_type": settings.service_type,
            "priority": request.template.get("priority", 5),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert the context
        context_id = await repository.create_context(context)
        
        return {
            "context_id": str(context_id),
            "status": "accepted",
            "message": "Template processing request accepted"
        }
        
    except Exception as e:
        logger.error(f"Error processing template: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing template: {str(e)}")

@app.get("/api/v1/contexts/{context_id}")
async def get_context(context_id: str):
    """
    Get the status and result of a context.
    
    Args:
        context_id: ID of the context to retrieve
        
    Returns:
        Context document
    """
    repository = app.state.repository
    
    if not repository:
        raise HTTPException(status_code=503, detail="Repository not initialized")
    
    try:
        context = await repository.get_context(context_id)
        
        if not context:
            raise HTTPException(status_code=404, detail="Context not found")
        
        return context
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving context: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving context: {str(e)}")

@app.post("/api/v1/contexts/{context_id}/process")
async def process_context(
    context_id: str, 
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
):
    """
    Trigger processing for a specific context.
    
    Args:
        context_id: ID of the context to process
        background_tasks: FastAPI background tasks
        settings: Application settings
        
    Returns:
        Processing status
    """
    repository = app.state.repository
    worker_service = app.state.worker_service
    
    if not repository:
        raise HTTPException(status_code=503, detail="Repository not initialized")
    
    if not worker_service:
        raise HTTPException(status_code=503, detail="Worker service not initialized")
    
    try:
        # Get the context
        context = await repository.get_context(context_id)
        
        if not context:
            raise HTTPException(status_code=404, detail="Context not found")
        
        # Update context to pending for processing
        await repository.update_context_status(
            context_id=context_id,
            status="pending"
        )
        
        return {
            "context_id": context_id,
            "status": "pending",
            "message": "Context processing triggered"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering context processing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error triggering context processing: {str(e)}")
