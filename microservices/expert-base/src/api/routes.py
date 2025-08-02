"""
API routes for the Expert Base microservice.

This module defines FastAPI routes for the Expert Base microservice.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger
from typing import Dict, Optional, Any

from src.api.models import (
    ExpertRequest,
    ExpertResponse,
    ExpertCapability,
    ExpertCapabilitiesResponse,
)
from src.common.exceptions import ExpertBaseException
from src.api.dependencies import (
    get_expert_orchestrator,
    verify_api_key
)

# Create router
router = APIRouter(
    dependencies=[Depends(verify_api_key)]
)


@router.post("/expert/process", response_model=ExpertResponse)
async def process_expert_request(
    request: ExpertRequest,
    expert_orchestrator=Depends(get_expert_orchestrator)
) -> ExpertResponse:
    """
    Process a request using the appropriate expert in the specified mode.
    
    Args:
        request: The expert request.
        expert_orchestrator: The expert orchestrator dependency.
        
    Returns:
        The expert response.
    """
    logger.info(f"Processing expert request: {request.expert}/{request.intent} (tracking_id: {request.tracking_id})")
    try:
        return await expert_orchestrator.process_request(request)
    except ExpertBaseException as e:
        logger.error(f"Expert base exception: {e.message}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing request: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/expert/capabilities", response_model=Dict[str, ExpertCapability])
async def get_expert_capabilities(
    expert_id: Optional[str] = None,
    expert_orchestrator=Depends(get_expert_orchestrator)
) -> Dict[str, ExpertCapability]:
    """
    Get capabilities of experts.
    
    Args:
        expert_id: Optional ID of the expert to get capabilities for.
        expert_orchestrator: The expert orchestrator dependency.
        
    Returns:
        Dictionary mapping expert IDs to their capabilities.
    """
    logger.info(f"Getting expert capabilities for: {expert_id if expert_id else 'all'}")
    try:
        return await expert_orchestrator.get_capabilities(expert_id)
    except ExpertBaseException as e:
        logger.error(f"Expert base exception: {e.message}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error getting capabilities: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 