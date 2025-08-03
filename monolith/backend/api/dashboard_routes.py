"""
Dashboard API Routes for PrismicX Monolith
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import structlog

from ..services.management_client import ManagementSystemsClient
from ..models.dashboard_models import (
    DashboardStats, CustomerSummary, OpportunitySummary, 
    TaskSummary, APIResponse
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# Dependency to get management client
def get_management_client() -> ManagementSystemsClient:
    return ManagementSystemsClient()


@router.get("/health")
async def dashboard_health():
    """Dashboard health check"""
    return {"status": "healthy", "service": "dashboard"}


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    management_client: ManagementSystemsClient = Depends(get_management_client)
):
    """Get dashboard statistics"""
    try:
        stats = await management_client.get_dashboard_stats()
        return stats
    except Exception as e:
        logger.error("Failed to get dashboard stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard statistics")


@router.get("/customers", response_model=List[CustomerSummary])
async def get_customers(
    limit: int = 50,
    management_client: ManagementSystemsClient = Depends(get_management_client)
):
    """Get customer summaries"""
    try:
        customers = await management_client.get_customers(limit=limit)
        return customers
    except Exception as e:
        logger.error("Failed to get customers", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve customers")


@router.get("/opportunities", response_model=List[OpportunitySummary])
async def get_opportunities(
    limit: int = 50,
    management_client: ManagementSystemsClient = Depends(get_management_client)
):
    """Get opportunity summaries"""
    try:
        opportunities = await management_client.get_opportunities(limit=limit)
        return opportunities
    except Exception as e:
        logger.error("Failed to get opportunities", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve opportunities")


@router.get("/tasks", response_model=List[TaskSummary])
async def get_tasks(
    limit: int = 50,
    management_client: ManagementSystemsClient = Depends(get_management_client)
):
    """Get task summaries"""
    try:
        tasks = await management_client.get_tasks(limit=limit)
        return tasks
    except Exception as e:
        logger.error("Failed to get tasks", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")


@router.get("/templates")
async def get_management_templates(
    management_client: ManagementSystemsClient = Depends(get_management_client)
):
    """Get management system templates"""
    try:
        templates = await management_client.get_templates()
        return APIResponse(
            success=True,
            message="Templates retrieved successfully",
            data={"templates": templates}
        )
    except Exception as e:
        logger.error("Failed to get management templates", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve management templates")


@router.get("/templates/{template_id}")
async def get_management_template(
    template_id: str,
    management_client: ManagementSystemsClient = Depends(get_management_client)
):
    """Get specific management template"""
    try:
        template = await management_client.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return APIResponse(
            success=True,
            message="Template retrieved successfully",
            data=template
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get management template", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve management template")


@router.get("/system-status")
async def get_system_status(
    management_client: ManagementSystemsClient = Depends(get_management_client)
):
    """Get overall system status"""
    try:
        management_health = await management_client.get_health()
        
        return APIResponse(
            success=True,
            message="System status retrieved successfully",
            data={
                "dashboard": {"status": "healthy"},
                "management_systems": management_health,
                "timestamp": "2025-01-04T01:15:58Z"
            }
        )
    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve system status")
