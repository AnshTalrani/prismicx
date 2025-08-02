"""
Campaign controller.

This module provides HTTP API route handlers for campaign operations.
"""

import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status

from ....application.services.campaign_service import CampaignService
from ....domain.enums.campaign_status import CampaignStatus
from ..schemas.campaign_schemas import (
    CampaignCreate,
    CampaignUpdate,
    CampaignSchedule,
    CampaignResponse,
    CampaignDetailResponse,
    CampaignListResponse,
    CampaignStatisticsResponse,
)
from ....infrastructure.auth.dependencies import get_current_user, User
from ....infrastructure.dependencies import get_campaign_service

# Setup router
router = APIRouter(
    prefix="/api/campaigns",
    tags=["campaigns"],
)

logger = logging.getLogger(__name__)


@router.post(
    "", 
    response_model=CampaignResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new campaign",
    description="Creates a new email marketing campaign with the given details."
)
async def create_campaign(
    data: CampaignCreate,
    campaign_service: CampaignService = Depends(get_campaign_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new campaign."""
    try:
        campaign = await campaign_service.create_campaign(data.dict())
        return CampaignResponse.from_campaign(campaign)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error creating campaign")
        raise HTTPException(status_code=500, detail="Failed to create campaign")


@router.get(
    "", 
    response_model=CampaignListResponse,
    summary="List campaigns",
    description="Returns a paginated list of campaigns with optional filtering."
)
async def list_campaigns(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by campaign status"),
    tags: Optional[str] = Query(None, description="Filter by comma-separated tags"),
    search: Optional[str] = Query(None, description="Search in campaign name and description"),
    campaign_service: CampaignService = Depends(get_campaign_service),
    current_user: User = Depends(get_current_user)
):
    """List campaigns with pagination and filtering."""
    try:
        # Process tags filter
        tags_filter = tags.split(",") if tags else None
        
        # Calculate offset
        offset = (page - 1) * size
        
        # Get campaigns
        campaigns = await campaign_service.list_campaigns(
            limit=size,
            offset=offset,
            status=status,
            tags=tags_filter,
            search=search
        )
        
        # Get total count
        total = await campaign_service.count_campaigns(
            status=status,
            tags=tags_filter,
            search=search
        )
        
        # Calculate total pages
        total_pages = (total + size - 1) // size if total > 0 else 1
        
        # Convert to response format
        items = [CampaignResponse.from_campaign(campaign) for campaign in campaigns]
        
        return CampaignListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=total_pages
        )
    except Exception as e:
        logger.exception("Error listing campaigns")
        raise HTTPException(status_code=500, detail="Failed to list campaigns")


@router.get(
    "/{campaign_id}", 
    response_model=CampaignDetailResponse,
    summary="Get campaign details",
    description="Returns detailed information about a specific campaign."
)
async def get_campaign(
    campaign_id: str,
    campaign_service: CampaignService = Depends(get_campaign_service),
    current_user: User = Depends(get_current_user)
):
    """Get a specific campaign by ID."""
    try:
        campaign = await campaign_service.get_campaign(campaign_id)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return CampaignDetailResponse.from_campaign(campaign)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting campaign {campaign_id}")
        raise HTTPException(status_code=500, detail="Failed to get campaign")


@router.put(
    "/{campaign_id}", 
    response_model=CampaignResponse,
    summary="Update campaign",
    description="Updates an existing campaign with the provided data."
)
async def update_campaign(
    campaign_id: str,
    data: CampaignUpdate,
    campaign_service: CampaignService = Depends(get_campaign_service),
    current_user: User = Depends(get_current_user)
):
    """Update an existing campaign."""
    try:
        # Apply updates
        update_data = data.dict(exclude_unset=True)
        updated = await campaign_service.update_campaign(campaign_id, update_data)
        
        if not updated:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return CampaignResponse.from_campaign(updated)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error updating campaign {campaign_id}")
        raise HTTPException(status_code=500, detail="Failed to update campaign")


@router.delete(
    "/{campaign_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete campaign",
    description="Deletes a campaign if it's not in progress."
)
async def delete_campaign(
    campaign_id: str,
    campaign_service: CampaignService = Depends(get_campaign_service),
    current_user: User = Depends(get_current_user)
):
    """Delete a campaign."""
    try:
        success = await campaign_service.delete_campaign(campaign_id)
        if not success:
            raise HTTPException(status_code=404, detail="Campaign not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting campaign {campaign_id}")
        raise HTTPException(status_code=500, detail="Failed to delete campaign")


@router.post(
    "/{campaign_id}/schedule", 
    response_model=CampaignResponse,
    summary="Schedule campaign",
    description="Schedules a campaign to be sent at the specified time."
)
async def schedule_campaign(
    campaign_id: str,
    data: CampaignSchedule,
    campaign_service: CampaignService = Depends(get_campaign_service),
    current_user: User = Depends(get_current_user)
):
    """Schedule a campaign for sending."""
    try:
        updated = await campaign_service.schedule_campaign(campaign_id, data.scheduled_at)
        
        if not updated:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return CampaignResponse.from_campaign(updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error scheduling campaign {campaign_id}")
        raise HTTPException(status_code=500, detail="Failed to schedule campaign")


@router.post(
    "/{campaign_id}/send", 
    response_model=CampaignResponse,
    summary="Send campaign",
    description="Sends a campaign immediately in the background."
)
async def send_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    campaign_service: CampaignService = Depends(get_campaign_service),
    current_user: User = Depends(get_current_user)
):
    """Send a campaign immediately."""
    try:
        campaign = await campaign_service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Start sending campaign in background
        background_tasks.add_task(campaign_service.send_campaign, campaign_id)
        
        # Update status to IN_PROGRESS
        campaign.status = CampaignStatus.IN_PROGRESS
        updated = await campaign_service.update_campaign(
            campaign_id, 
            {"status": CampaignStatus.IN_PROGRESS}
        )
        
        return CampaignResponse.from_campaign(updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error sending campaign {campaign_id}")
        raise HTTPException(status_code=500, detail="Failed to send campaign")


@router.post(
    "/{campaign_id}/cancel", 
    response_model=CampaignResponse,
    summary="Cancel campaign",
    description="Cancels a scheduled campaign before it's sent."
)
async def cancel_campaign(
    campaign_id: str,
    campaign_service: CampaignService = Depends(get_campaign_service),
    current_user: User = Depends(get_current_user)
):
    """Cancel a scheduled campaign."""
    try:
        updated = await campaign_service.cancel_campaign(campaign_id)
        
        if not updated:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return CampaignResponse.from_campaign(updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error canceling campaign {campaign_id}")
        raise HTTPException(status_code=500, detail="Failed to cancel campaign")


@router.get(
    "/{campaign_id}/statistics", 
    response_model=CampaignStatisticsResponse,
    summary="Get campaign statistics",
    description="Returns statistics for a campaign including delivery and engagement metrics."
)
async def get_campaign_statistics(
    campaign_id: str,
    campaign_service: CampaignService = Depends(get_campaign_service),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a campaign."""
    try:
        # Get campaign
        campaign = await campaign_service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get statistics
        stats = await campaign_service.get_campaign_statistics(campaign_id)
        
        return CampaignStatisticsResponse(**stats)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting campaign statistics for {campaign_id}")
        raise HTTPException(status_code=500, detail="Failed to get campaign statistics") 