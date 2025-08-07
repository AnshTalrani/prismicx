"""
Campaign API endpoints.

This module contains all API routes related to campaign management,
including CRUD operations and campaign execution controls.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from ...models.schemas import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    WorkflowCreate, WorkflowResponse
)
from ...services.campaign_service import CampaignService
from ...config.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_campaign_service() -> CampaignService:
    """Dependency to get campaign service."""
    # In a real implementation, this would get the service from app state
    return CampaignService()


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign: CampaignCreate,
    service: CampaignService = Depends(get_campaign_service)
):
    """Create a new campaign."""
    try:
        logger.info(f"Creating campaign: {campaign.name}")
        created_campaign = await service.create_campaign(campaign)
        logger.info(f"Campaign created successfully: {created_campaign.id}")
        return created_campaign
    except Exception as e:
        logger.error(f"Failed to create campaign: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}"
        )


@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    skip: int = Query(0, ge=0, description="Number of campaigns to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of campaigns to return"),
    status_filter: Optional[str] = Query(None, description="Filter by campaign status"),
    campaign_type: Optional[str] = Query(None, description="Filter by campaign type"),
    service: CampaignService = Depends(get_campaign_service)
):
    """List all campaigns with optional filtering."""
    try:
        logger.info(f"Listing campaigns: skip={skip}, limit={limit}")
        campaigns = await service.list_campaigns(
            skip=skip,
            limit=limit,
            status_filter=status_filter,
            campaign_type=campaign_type
        )
        logger.info(f"Retrieved {len(campaigns)} campaigns")
        return campaigns
    except Exception as e:
        logger.error(f"Failed to list campaigns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list campaigns: {str(e)}"
        )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    service: CampaignService = Depends(get_campaign_service)
):
    """Get a specific campaign by ID."""
    try:
        logger.info(f"Getting campaign: {campaign_id}")
        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        return campaign
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get campaign: {str(e)}"
        )


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    campaign_update: CampaignUpdate,
    service: CampaignService = Depends(get_campaign_service)
):
    """Update an existing campaign."""
    try:
        logger.info(f"Updating campaign: {campaign_id}")
        updated_campaign = await service.update_campaign(campaign_id, campaign_update)
        if not updated_campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        logger.info(f"Campaign updated successfully: {campaign_id}")
        return updated_campaign
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update campaign: {str(e)}"
        )


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: UUID,
    service: CampaignService = Depends(get_campaign_service)
):
    """Delete a campaign."""
    try:
        logger.info(f"Deleting campaign: {campaign_id}")
        success = await service.delete_campaign(campaign_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        logger.info(f"Campaign deleted successfully: {campaign_id}")
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete campaign: {str(e)}"
        )


@router.post("/{campaign_id}/start", response_model=CampaignResponse)
async def start_campaign(
    campaign_id: UUID,
    service: CampaignService = Depends(get_campaign_service)
):
    """Start a campaign."""
    try:
        logger.info(f"Starting campaign: {campaign_id}")
        campaign = await service.start_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        logger.info(f"Campaign started successfully: {campaign_id}")
        return campaign
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start campaign: {str(e)}"
        )


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: UUID,
    service: CampaignService = Depends(get_campaign_service)
):
    """Pause a campaign."""
    try:
        logger.info(f"Pausing campaign: {campaign_id}")
        campaign = await service.pause_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        logger.info(f"Campaign paused successfully: {campaign_id}")
        return campaign
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause campaign: {str(e)}"
        )


@router.post("/{campaign_id}/resume", response_model=CampaignResponse)
async def resume_campaign(
    campaign_id: UUID,
    service: CampaignService = Depends(get_campaign_service)
):
    """Resume a paused campaign."""
    try:
        logger.info(f"Resuming campaign: {campaign_id}")
        campaign = await service.resume_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        logger.info(f"Campaign resumed successfully: {campaign_id}")
        return campaign
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume campaign: {str(e)}"
        )


@router.get("/{campaign_id}/metrics")
async def get_campaign_metrics(
    campaign_id: UUID,
    service: CampaignService = Depends(get_campaign_service)
):
    """Get campaign metrics and analytics."""
    try:
        logger.info(f"Getting metrics for campaign: {campaign_id}")
        metrics = await service.get_campaign_metrics(campaign_id)
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get campaign metrics: {str(e)}"
        )


# Workflow endpoints
@router.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow: WorkflowCreate,
    service: CampaignService = Depends(get_campaign_service)
):
    """Create a new workflow."""
    try:
        logger.info(f"Creating workflow: {workflow.name}")
        created_workflow = await service.create_workflow(workflow)
        logger.info(f"Workflow created successfully: {created_workflow.id}")
        return created_workflow
    except Exception as e:
        logger.error(f"Failed to create workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("/workflows", response_model=List[WorkflowResponse])
async def list_workflows(
    skip: int = Query(0, ge=0, description="Number of workflows to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of workflows to return"),
    service: CampaignService = Depends(get_campaign_service)
):
    """List all workflows."""
    try:
        logger.info(f"Listing workflows: skip={skip}, limit={limit}")
        workflows = await service.list_workflows(skip=skip, limit=limit)
        logger.info(f"Retrieved {len(workflows)} workflows")
        return workflows
    except Exception as e:
        logger.error(f"Failed to list workflows: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflows: {str(e)}"
        )


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    service: CampaignService = Depends(get_campaign_service)
):
    """Get a specific workflow by ID."""
    try:
        logger.info(f"Getting workflow: {workflow_id}")
        workflow = await service.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        return workflow
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow: {str(e)}"
        )
