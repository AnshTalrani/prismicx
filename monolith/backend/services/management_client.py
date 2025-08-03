"""
Management Systems Client for PrismicX Dashboard
"""

import httpx
import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models.dashboard_models import (
    DashboardStats, CustomerSummary, OpportunitySummary, 
    TaskSummary, ActivityFeed
)

logger = structlog.get_logger(__name__)


class ManagementSystemsClient:
    def __init__(self, base_url: str = "http://localhost:8002", api_key: str = "dev_api_key"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    async def get_health(self) -> Dict[str, Any]:
        """Get management systems health status"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("Failed to get management systems health", error=str(e))
            return {"status": "error", "message": str(e)}
    
    async def get_templates(self) -> List[Dict[str, Any]]:
        """Get management system templates"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/management/templates",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("templates", [])
        except Exception as e:
            logger.error("Failed to get management templates", error=str(e))
            return []
    
    async def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get specific management template"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/management/templates/{template_id}",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("Failed to get management template", template_id=template_id, error=str(e))
            return None
    
    async def get_dashboard_stats(self) -> DashboardStats:
        """Get dashboard statistics (mock data for now)"""
        try:
            # In a real implementation, this would aggregate data from multiple sources
            # For now, we'll return mock data that looks realistic
            return DashboardStats(
                total_customers=156,
                active_opportunities=23,
                completed_tasks=89,
                pending_tasks=34,
                total_revenue=2456789.50,
                monthly_revenue=156789.25,
                conversion_rate=0.23,
                recent_activities=[
                    {
                        "id": "act_001",
                        "type": "customer_created",
                        "title": "New Customer Added",
                        "description": "Acme Corp added to CRM",
                        "timestamp": datetime.utcnow().isoformat(),
                        "user": "john.doe"
                    },
                    {
                        "id": "act_002", 
                        "type": "opportunity_updated",
                        "title": "Deal Stage Updated",
                        "description": "Enterprise deal moved to negotiation",
                        "timestamp": datetime.utcnow().isoformat(),
                        "user": "jane.smith"
                    }
                ]
            )
        except Exception as e:
            logger.error("Failed to get dashboard stats", error=str(e))
            # Return empty stats on error
            return DashboardStats(
                total_customers=0,
                active_opportunities=0,
                completed_tasks=0,
                pending_tasks=0,
                total_revenue=0.0,
                monthly_revenue=0.0,
                conversion_rate=0.0,
                recent_activities=[]
            )
    
    async def get_customers(self, limit: int = 50) -> List[CustomerSummary]:
        """Get customer summaries (mock data for now)"""
        try:
            # Mock customer data based on CRM models
            customers = [
                CustomerSummary(
                    customer_id="cust_001",
                    name="Acme Corporation",
                    email="contact@acme.com",
                    status="active",
                    total_value=125000.0,
                    last_interaction=datetime.utcnow(),
                    opportunities_count=3
                ),
                CustomerSummary(
                    customer_id="cust_002",
                    name="TechStart Inc",
                    email="hello@techstart.com",
                    status="active",
                    total_value=75000.0,
                    last_interaction=datetime.utcnow(),
                    opportunities_count=2
                ),
                CustomerSummary(
                    customer_id="cust_003",
                    name="Global Solutions Ltd",
                    email="info@globalsolutions.com",
                    status="prospect",
                    total_value=0.0,
                    last_interaction=datetime.utcnow(),
                    opportunities_count=1
                )
            ]
            return customers[:limit]
        except Exception as e:
            logger.error("Failed to get customers", error=str(e))
            return []
    
    async def get_opportunities(self, limit: int = 50) -> List[OpportunitySummary]:
        """Get opportunity summaries (mock data for now)"""
        try:
            opportunities = [
                OpportunitySummary(
                    opportunity_id="opp_001",
                    customer_id="cust_001",
                    customer_name="Acme Corporation",
                    title="Enterprise Software License",
                    value=125000.0,
                    stage="negotiation",
                    probability=0.75,
                    expected_close_date=datetime.utcnow()
                ),
                OpportunitySummary(
                    opportunity_id="opp_002",
                    customer_id="cust_002",
                    customer_name="TechStart Inc",
                    title="Consulting Services",
                    value=45000.0,
                    stage="proposal",
                    probability=0.60,
                    expected_close_date=datetime.utcnow()
                ),
                OpportunitySummary(
                    opportunity_id="opp_003",
                    customer_id="cust_003",
                    customer_name="Global Solutions Ltd",
                    title="Implementation Project",
                    value=85000.0,
                    stage="qualification",
                    probability=0.30,
                    expected_close_date=datetime.utcnow()
                )
            ]
            return opportunities[:limit]
        except Exception as e:
            logger.error("Failed to get opportunities", error=str(e))
            return []
    
    async def get_tasks(self, limit: int = 50) -> List[TaskSummary]:
        """Get task summaries (mock data for now)"""
        try:
            tasks = [
                TaskSummary(
                    task_id="task_001",
                    title="Follow up with Acme Corp",
                    description="Schedule demo call for next week",
                    due_date=datetime.utcnow(),
                    priority="high",
                    status="pending",
                    assigned_to="john.doe",
                    related_to_type="customer",
                    related_to_id="cust_001"
                ),
                TaskSummary(
                    task_id="task_002",
                    title="Prepare proposal for TechStart",
                    description="Create detailed proposal document",
                    due_date=datetime.utcnow(),
                    priority="medium",
                    status="in_progress",
                    assigned_to="jane.smith",
                    related_to_type="opportunity",
                    related_to_id="opp_002"
                ),
                TaskSummary(
                    task_id="task_003",
                    title="Update CRM records",
                    description="Sync latest interaction data",
                    due_date=datetime.utcnow(),
                    priority="low",
                    status="completed",
                    assigned_to="admin",
                    related_to_type="system",
                    related_to_id="maintenance"
                )
            ]
            return tasks[:limit]
        except Exception as e:
            logger.error("Failed to get tasks", error=str(e))
            return []
