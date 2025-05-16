"""
API Module for Generative Base Service

This module provides the REST API endpoints for the generative base service.
It handles generative requests and manages generation workflows.
"""

import asyncio
import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, APIRouter
from pydantic import BaseModel, Field

from ..repository.repository import Repository
from ..common.config import Settings, get_settings
from ..service.worker_service import WorkerService

# Configure structured logging
logger = structlog.get_logger(__name__)

# Create API router
router = APIRouter()

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

@router.post("/api/v1/templates/process", response_model=TemplateResponse)
async def process_template(
    request: TemplateRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
):
    """
    Process a template and execute the generative workflow.
    
    Args:
        request: Template processing request containing template and input data
        background_tasks: FastAPI background tasks
        settings: Application settings
        
    Returns:
        Response with context ID and status
    """
    from ..app import app
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

@router.get("/api/v1/contexts/{context_id}")
async def get_context(context_id: str):
    """
    Get the status and result of a context.
    
    Args:
        context_id: ID of the context to retrieve
        
    Returns:
        Context document
    """
    from ..app import app
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

@router.post("/api/v1/contexts/{context_id}/process")
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
    from ..app import app
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

# Add API routes to main app
def setup_routes(app: FastAPI):
    """Add API routes to the main FastAPI app."""
    app.include_router(router) 