"""Endpoints for template-purpose alignment checks and operations."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from src.application.services.application_service import ApplicationService
from src.infrastructure.factories.service_factory import ServiceFactory

logger = logging.getLogger(__name__)

alignment_router = APIRouter(
    prefix="/api/alignment",
    tags=["alignment"],
    responses={404: {"description": "Not found"}},
)

# Service dependency - defined at module level for easier testing
async def get_app_service() -> ApplicationService:
    """Get application service instance."""
    return await ServiceFactory.create_and_initialize_application_service()

@alignment_router.post("/check")
async def check_alignment(
    app_service: ApplicationService = Depends(get_app_service)
) -> Dict[str, Any]:
    """
    Trigger an alignment check between templates and purposes.
    
    Returns:
        Dict containing lists of unaligned templates and purposes
    """
    try:
        unaligned_items = await app_service.check_and_notify_alignment()
        return unaligned_items
    except Exception as e:
        logger.error(f"Error performing alignment check: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Alignment check failed",
                "message": str(e)
            }
        )

@alignment_router.get("/status")
async def get_alignment_status(
    app_service: ApplicationService = Depends(get_app_service)
) -> Dict[str, Any]:
    """
    Get the current alignment status.
    
    Returns:
        Dict containing alignment status and last check time
    """
    try:
        # Get latest alignment check results
        issues = await app_service.check_and_notify_alignment()
        
        # Determine status based on whether there are any issues
        has_issues = (
            len(issues["templates_without_purposes"]) > 0 or
            len(issues["purposes_without_templates"]) > 0 or
            len(issues["purposes_with_missing_templates"]) > 0
        )
        
        status = "misaligned" if has_issues else "aligned"
        
        return {
            "status": status,
            "last_checked": datetime.utcnow().isoformat(),
            "issues": issues
        }
    except Exception as e:
        logger.error(f"Error getting alignment status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get alignment status",
                "message": str(e)
            }
        ) 