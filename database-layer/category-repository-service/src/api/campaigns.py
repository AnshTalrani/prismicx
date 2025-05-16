"""
Campaign API endpoints.

This module provides the FastAPI router for campaign management API endpoints.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Path

from ..config.settings import get_settings, Settings
from ..models.category import Campaign, CampaignCreate, Metrics, MetricsUpdate
from ..repository.category_repository import CategoryRepository
from .categories import get_repository, verify_api_key

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# ======================
# Campaign API Endpoints
# ======================

@router.post("/api/v1/campaigns", response_model=Dict[str, str], dependencies=[Depends(verify_api_key)])
async def create_campaign(
    campaign: CampaignCreate,
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, str]:
    """
    Create a new campaign.
    
    Args:
        campaign: Campaign data to create
        repository: Category repository
        
    Returns:
        Dict with campaign ID
        
    Raises:
        HTTPException: If campaign creation fails
    """
    campaign_id = await repository.create_campaign(campaign)
    if campaign_id:
        return {"campaign_id": campaign_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to create campaign")


@router.get("/api/v1/campaigns/{campaign_id}", response_model=Dict[str, Any], dependencies=[Depends(verify_api_key)])
async def get_campaign(
    campaign_id: str = Path(..., description="Campaign ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, Any]:
    """
    Get a campaign by ID.
    
    Args:
        campaign_id: Campaign ID
        repository: Category repository
        
    Returns:
        Campaign document
        
    Raises:
        HTTPException: If campaign not found
    """
    campaign = await repository.get_campaign(campaign_id)
    if campaign:
        return campaign
    else:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")


@router.put("/api/v1/campaigns/{campaign_id}", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def update_campaign(
    update_data: Dict[str, Any],
    campaign_id: str = Path(..., description="Campaign ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Update a campaign.
    
    Args:
        update_data: Campaign data to update
        campaign_id: Campaign ID
        repository: Category repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If campaign update fails
    """
    success = await repository.update_campaign(campaign_id, update_data)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found or update failed")


@router.delete("/api/v1/campaigns/{campaign_id}", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def delete_campaign(
    campaign_id: str = Path(..., description="Campaign ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Delete a campaign.
    
    Args:
        campaign_id: Campaign ID
        repository: Category repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If campaign deletion fails
    """
    success = await repository.delete_campaign(campaign_id)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found or deletion failed")


@router.get("/api/v1/categories/{category_id}/campaigns", response_model=List[Dict[str, Any]], dependencies=[Depends(verify_api_key)])
async def get_campaigns_by_category(
    category_id: str = Path(..., description="Category ID"),
    skip: int = Query(0, ge=0, description="Number of campaigns to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of campaigns to return"),
    repository: CategoryRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings)
) -> List[Dict[str, Any]]:
    """
    Get campaigns by category.
    
    Args:
        category_id: Category ID
        skip: Number of campaigns to skip
        limit: Maximum number of campaigns to return
        repository: Category repository
        settings: Service settings
        
    Returns:
        List of campaign documents
    """
    campaigns = await repository.get_campaigns_by_category(
        category_id=category_id,
        skip=skip,
        limit=min(limit, settings.max_page_size)
    )
    return campaigns


@router.put("/api/v1/campaigns/{campaign_id}/metrics", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def update_campaign_metrics(
    metrics: MetricsUpdate,
    campaign_id: str = Path(..., description="Campaign ID"),
    repository: CategoryRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Update campaign metrics.
    
    Args:
        metrics: Metrics data to update
        campaign_id: Campaign ID
        repository: Category repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If metrics update fails
    """
    success = await repository.update_campaign_metrics(campaign_id, metrics.metrics)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found or metrics update failed") 