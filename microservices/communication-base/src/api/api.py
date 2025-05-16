"""
API Module

This module provides the API routes for the communication-base service.
It includes endpoints for campaign management, component operations, and service status.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime
import uuid

from src.config.settings import Settings, get_settings
from src.clients.campaign_users_repository_client import CampaignUsersRepositoryClient
from src.clients.system_users_repository_client import SystemUsersRepositoryClient
from src.common.monitoring import get_metrics

# Create logger
logger = structlog.get_logger(__name__)

# Create FastAPI application
app = APIRouter(prefix="/v1")

# Global repository references (set during startup)
_campaign_repository = None
_system_repository = None

@app.on_event("startup")
async def startup_event():
    """
    Initialize API dependencies on startup.
    """
    global _campaign_repository, _system_repository
    
    try:
        settings = get_settings()
        
        # Initialize repositories if not already initialized
        if _campaign_repository is None:
            _campaign_repository = CampaignUsersRepositoryClient()
            await _campaign_repository.connect()
            
        if _system_repository is None:
            _system_repository = SystemUsersRepositoryClient()
            await _system_repository.connect()
            
        logger.info("API initialized")
        
    except Exception as e:
        logger.error("Error initializing API", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up resources on API shutdown.
    """
    global _campaign_repository, _system_repository
    
    if _campaign_repository:
        await _campaign_repository.disconnect()
    
    if _system_repository:
        await _system_repository.disconnect()
        
    logger.info("API shutdown complete")

async def get_campaign_repository() -> CampaignUsersRepositoryClient:
    """
    Get campaign repository instance as a dependency.
    
    Returns:
        CampaignUsersRepositoryClient instance
    """
    global _campaign_repository
    
    if _campaign_repository is None:
        _campaign_repository = CampaignUsersRepositoryClient()
        await _campaign_repository.connect()
        
    return _campaign_repository

async def get_system_repository() -> SystemUsersRepositoryClient:
    """
    Get system repository instance as a dependency.
    
    Returns:
        SystemUsersRepositoryClient instance
    """
    global _system_repository
    
    if _system_repository is None:
        _system_repository = SystemUsersRepositoryClient()
        await _system_repository.connect()
        
    return _system_repository

# Campaign endpoints
@app.post("/campaigns", response_model=Dict[str, Any])
async def create_campaign(
    campaign: Dict[str, Any],
    campaign_repository: CampaignUsersRepositoryClient = Depends(get_campaign_repository),
    settings: Settings = Depends(get_settings)
):
    """
    Create a new communication campaign.
    
    The campaign data should include:
    - type: Type of campaign (email, sms, push, etc.)
    - name: Name of the campaign
    - content: Content of the campaign (depends on type)
    - recipients: List of recipient information
    - scheduled_at: When to send the campaign (ISO format datetime)
    
    Returns:
        Campaign information including ID
    """
    try:
        # Add metadata
        campaign["created_at"] = datetime.utcnow()
        campaign["status"] = "pending"
        campaign["id"] = str(uuid.uuid4())
        
        # Validate campaign data
        if "type" not in campaign:
            raise HTTPException(status_code=400, detail="Campaign type is required")
            
        # Create campaign
        campaign_id = await campaign_repository.create_campaign(campaign)
        
        # Log and track metrics
        metrics = get_metrics()
        if metrics:
            metrics.increment("api_campaigns_created", 1, {"type": campaign.get("type")})
        
        logger.info(
            "Campaign created", 
            campaign_id=campaign_id,
            campaign_type=campaign.get("type")
        )
        
        return {
            "id": campaign_id,
            "status": "pending",
            "message": "Campaign created successfully"
        }
        
    except Exception as e:
        logger.error("Error creating campaign", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/campaigns/{campaign_id}", response_model=Dict[str, Any])
async def get_campaign(
    campaign_id: str,
    campaign_repository: CampaignUsersRepositoryClient = Depends(get_campaign_repository)
):
    """
    Get information about a specific campaign.
    
    Args:
        campaign_id: ID of the campaign to retrieve
        
    Returns:
        Campaign information
    """
    try:
        campaign = await campaign_repository.get_campaign(campaign_id)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
            
        # Track metrics
        metrics = get_metrics()
        if metrics:
            metrics.increment("api_campaigns_retrieved", 1)
        
        return campaign
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting campaign", campaign_id=campaign_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/campaigns", response_model=List[Dict[str, Any]])
async def list_campaigns(
    limit: int = Query(10, ge=1, le=100),
    skip: int = Query(0, ge=0),
    status: Optional[str] = None,
    campaign_type: Optional[str] = None,
    campaign_repository: CampaignUsersRepositoryClient = Depends(get_campaign_repository)
):
    """
    List campaigns with filtering and pagination.
    
    Args:
        limit: Maximum number of campaigns to return
        skip: Number of campaigns to skip (for pagination)
        status: Optional filter by status
        campaign_type: Optional filter by campaign type
        
    Returns:
        List of campaign information
    """
    try:
        # This is a placeholder - the actual repository method would need to be implemented
        # For now, we'll return a dummy response
        return [
            {
                "id": "dummy-campaign-1",
                "name": "Example Campaign",
                "type": "email",
                "status": "pending",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
    except Exception as e:
        logger.error("Error listing campaigns", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/campaigns/{campaign_id}", response_model=Dict[str, Any])
async def update_campaign(
    campaign_id: str,
    updates: Dict[str, Any],
    campaign_repository: CampaignUsersRepositoryClient = Depends(get_campaign_repository)
):
    """
    Update a campaign.
    
    Args:
        campaign_id: ID of the campaign to update
        updates: Dictionary of fields to update
        
    Returns:
        Updated campaign information
    """
    try:
        # Make sure campaign exists
        campaign = await campaign_repository.get_campaign(campaign_id)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
            
        # Prevent updating certain fields
        for field in ["_id", "id", "created_at", "status"]:
            if field in updates:
                del updates[field]
                
        # Update campaign
        updates["updated_at"] = datetime.utcnow()
        success = await campaign_repository.update_campaign(campaign_id, updates)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update campaign")
            
        # Get updated campaign
        updated_campaign = await campaign_repository.get_campaign(campaign_id)
        
        # Track metrics
        metrics = get_metrics()
        if metrics:
            metrics.increment("api_campaigns_updated", 1)
        
        return updated_campaign
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating campaign", campaign_id=campaign_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/campaigns/{campaign_id}", response_model=Dict[str, Any])
async def cancel_campaign(
    campaign_id: str,
    campaign_repository: CampaignUsersRepositoryClient = Depends(get_campaign_repository)
):
    """
    Cancel a campaign.
    
    Args:
        campaign_id: ID of the campaign to cancel
        
    Returns:
        Cancellation status
    """
    try:
        # Make sure campaign exists
        campaign = await campaign_repository.get_campaign(campaign_id)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
            
        # Update campaign status to canceled
        updates = {
            "status": "canceled",
            "canceled_at": datetime.utcnow()
        }
        
        success = await campaign_repository.update_campaign(campaign_id, updates)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel campaign")
            
        # Track metrics
        metrics = get_metrics()
        if metrics:
            metrics.increment("api_campaigns_canceled", 1)
        
        return {
            "id": campaign_id,
            "status": "canceled",
            "message": "Campaign canceled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error canceling campaign", campaign_id=campaign_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/templates", response_model=Dict[str, Any])
async def create_template(
    template: Dict[str, Any],
    system_repository: SystemUsersRepositoryClient = Depends(get_system_repository)
):
    """
    Create a new message template.
    
    The template data should include:
    - type: Type of template (email, sms, push, etc.)
    - name: Name of the template
    - content: Content of the template with variable placeholders
    - variables: List of variables that can be used in the template
    
    Returns:
        Template information including ID
    """
    try:
        # Add metadata
        template["created_at"] = datetime.utcnow()
        template["id"] = str(uuid.uuid4())
        
        # Validate template data
        if "type" not in template:
            raise HTTPException(status_code=400, detail="Template type is required")
            
        if "content" not in template:
            raise HTTPException(status_code=400, detail="Template content is required")
            
        # Create template
        template_id = await system_repository.create_template(template)
        
        # Track metrics
        metrics = get_metrics()
        if metrics:
            metrics.increment("api_templates_created", 1, {"type": template.get("type")})
        
        return {
            "id": template_id,
            "message": "Template created successfully"
        }
        
    except Exception as e:
        logger.error("Error creating template", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_template(
    template_id: str,
    system_repository: SystemUsersRepositoryClient = Depends(get_system_repository)
):
    """
    Get a template by ID.
    
    Args:
        template_id: ID of the template to retrieve
        
    Returns:
        Template information
    """
    try:
        template = await system_repository.get_template(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
            
        # Track metrics
        metrics = get_metrics()
        if metrics:
            metrics.increment("api_templates_retrieved", 1)
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting template", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/campaigns/{campaign_id}/interactions", response_model=List[Dict[str, Any]])
async def get_campaign_interactions(
    campaign_id: str,
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    campaign_repository: CampaignUsersRepositoryClient = Depends(get_campaign_repository)
):
    """
    Get interactions for a specific campaign.
    
    Args:
        campaign_id: ID of the campaign
        limit: Maximum number of interactions to return
        skip: Number of interactions to skip (for pagination)
        
    Returns:
        List of interaction records
    """
    try:
        # Make sure campaign exists
        campaign = await campaign_repository.get_campaign(campaign_id)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
            
        # Get interactions
        interactions = await campaign_repository.get_campaign_interactions(
            campaign_id=campaign_id,
            limit=limit,
            skip=skip
        )
        
        # Track metrics
        metrics = get_metrics()
        if metrics:
            metrics.increment("api_campaign_interactions_retrieved", 1)
        
        return interactions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting campaign interactions", 
            campaign_id=campaign_id, 
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=Dict[str, Any])
async def api_health(
    campaign_repository: CampaignUsersRepositoryClient = Depends(get_campaign_repository),
    system_repository: SystemUsersRepositoryClient = Depends(get_system_repository),
    settings: Settings = Depends(get_settings)
):
    """
    Get API health status.
    
    Returns:
        Health status information
    """
    try:
        # Check repository connections
        campaign_repo_status = await campaign_repository.health_check()
        system_repo_status = await system_repository.health_check()
        
        # Get system info
        import platform
        import psutil
        
        health_info = {
            "status": "healthy" if campaign_repo_status and system_repo_status else "unhealthy",
            "repositories": {
                "campaign_repository": "connected" if campaign_repo_status else "disconnected",
                "system_repository": "connected" if system_repo_status else "disconnected",
            },
            "system_info": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return health_info
        
    except Exception as e:
        logger.error("Error getting API health", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/metrics", response_model=Dict[str, Any])
async def api_metrics():
    """
    Get API metrics.
    
    Returns:
        Metrics information
    """
    try:
        # Get metrics from metrics manager
        metrics_manager = get_metrics()
        
        if not metrics_manager:
            return {
                "message": "Metrics not available",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        # Get all metrics
        metrics_data = metrics_manager.get_all_metrics()
        
        return {
            "metrics": metrics_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error getting API metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) 