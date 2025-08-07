"""
Campaign Service

This module provides comprehensive campaign management functionality,
including CRUD operations, workflow management, and campaign execution.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.logging_config import get_logger, LoggerMixin
from ..models.schemas import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    WorkflowCreate, WorkflowResponse
)
from ..repositories.campaign_repository import CampaignRepository
from ..repositories.workflow_repository import WorkflowRepository

class MockCampaignRepository:
    """Mock campaign repository for testing."""
    
    async def create_campaign(self, campaign_data: CampaignCreate) -> CampaignResponse:
        """Mock create campaign."""
        from uuid import uuid4
        from datetime import datetime
        
        return CampaignResponse(
            id=uuid4(),
            name=campaign_data.name,
            description=campaign_data.description,
            campaign_type=campaign_data.campaign_type,
            workflow_id=campaign_data.workflow_id,
            start_date=campaign_data.start_date,
            end_date=campaign_data.end_date,
            metadata=campaign_data.metadata or {},
            status="draft",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def get_campaign(self, campaign_id: UUID) -> Optional[CampaignResponse]:
        """Mock get campaign."""
        return None
    
    async def list_campaigns(self, skip: int = 0, limit: int = 100, status_filter: Optional[str] = None, campaign_type: Optional[str] = None) -> List[CampaignResponse]:
        """Mock list campaigns."""
        return []
    
    async def update_campaign(self, campaign_id: UUID, campaign_update: CampaignUpdate) -> Optional[CampaignResponse]:
        """Mock update campaign."""
        return None
    
    async def delete_campaign(self, campaign_id: UUID) -> bool:
        """Mock delete campaign."""
        return True

class MockWorkflowRepository:
    """Mock workflow repository for testing."""
    
    async def create_workflow(self, workflow_data: WorkflowCreate) -> WorkflowResponse:
        """Mock create workflow."""
        from uuid import uuid4
        from datetime import datetime
        
        return WorkflowResponse(
            id=uuid4(),
            name=workflow_data.name,
            description=workflow_data.description,
            definition=workflow_data.definition,
            is_active=workflow_data.is_active,
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def get_workflow(self, workflow_id: UUID) -> Optional[WorkflowResponse]:
        """Mock get workflow."""
        return None
    
    async def list_workflows(self, skip: int = 0, limit: int = 100) -> List[WorkflowResponse]:
        """Mock list workflows."""
        return []

logger = get_logger(__name__)


class CampaignService(LoggerMixin):
    """Service for managing campaigns and workflows."""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        """Initialize the campaign service."""
        self.db_session = db_session
        self.campaign_repository = None
        self.workflow_repository = None
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the service."""
        try:
            self.logger.info("Initializing Campaign Service...")
            if self.db_session:
                self.campaign_repository = CampaignRepository(self.db_session)
                self.workflow_repository = WorkflowRepository(self.db_session)
            else:
                # Create mock repositories for testing
                self.campaign_repository = MockCampaignRepository()
                self.workflow_repository = MockWorkflowRepository()
            self.is_initialized = True
            self.logger.info("Campaign Service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Campaign Service: {str(e)}")
            raise
    
    async def create_campaign(self, campaign_data: CampaignCreate) -> CampaignResponse:
        """Create a new campaign."""
        try:
            self.logger.info(f"Creating campaign: {campaign_data.name}")
            
            # Validate workflow if provided
            if campaign_data.workflow_id:
                workflow = await self.workflow_repository.get_workflow(campaign_data.workflow_id)
                if not workflow:
                    raise ValueError(f"Workflow not found: {campaign_data.workflow_id}")
            
            # Create campaign
            campaign = await self.campaign_repository.create_campaign(campaign_data)
            
            self.logger.info(f"Campaign created successfully: {campaign.id}")
            return campaign
            
        except Exception as e:
            self.logger.error(f"Failed to create campaign: {str(e)}")
            raise
    
    async def get_campaign(self, campaign_id: UUID) -> Optional[CampaignResponse]:
        """Get a campaign by ID."""
        try:
            self.logger.info(f"Getting campaign: {campaign_id}")
            campaign = await self.campaign_repository.get_campaign(campaign_id)
            return campaign
        except Exception as e:
            self.logger.error(f"Failed to get campaign {campaign_id}: {str(e)}")
            raise
    
    async def list_campaigns(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        campaign_type: Optional[str] = None
    ) -> List[CampaignResponse]:
        """List campaigns with optional filtering."""
        try:
            self.logger.info(f"Listing campaigns: skip={skip}, limit={limit}")
            campaigns = await self.campaign_repository.list_campaigns(
                skip=skip,
                limit=limit,
                status_filter=status_filter,
                campaign_type=campaign_type
            )
            return campaigns
        except Exception as e:
            self.logger.error(f"Failed to list campaigns: {str(e)}")
            raise
    
    async def update_campaign(
        self, 
        campaign_id: UUID, 
        campaign_update: CampaignUpdate
    ) -> Optional[CampaignResponse]:
        """Update an existing campaign."""
        try:
            self.logger.info(f"Updating campaign: {campaign_id}")
            
            # Check if campaign exists
            existing_campaign = await self.campaign_repository.get_campaign(campaign_id)
            if not existing_campaign:
                return None
            
            # Update campaign
            updated_campaign = await self.campaign_repository.update_campaign(
                campaign_id, 
                campaign_update
            )
            
            self.logger.info(f"Campaign updated successfully: {campaign_id}")
            return updated_campaign
            
        except Exception as e:
            self.logger.error(f"Failed to update campaign {campaign_id}: {str(e)}")
            raise
    
    async def delete_campaign(self, campaign_id: UUID) -> bool:
        """Delete a campaign."""
        try:
            self.logger.info(f"Deleting campaign: {campaign_id}")
            
            # Check if campaign exists
            existing_campaign = await self.campaign_repository.get_campaign(campaign_id)
            if not existing_campaign:
                return False
            
            # Delete campaign
            success = await self.campaign_repository.delete_campaign(campaign_id)
            
            if success:
                self.logger.info(f"Campaign deleted successfully: {campaign_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete campaign {campaign_id}: {str(e)}")
            raise
    
    async def start_campaign(self, campaign_id: UUID) -> Optional[CampaignResponse]:
        """Start a campaign."""
        try:
            self.logger.info(f"Starting campaign: {campaign_id}")
            
            # Get campaign
            campaign = await self.campaign_repository.get_campaign(campaign_id)
            if not campaign:
                return None
            
            # Validate campaign can be started
            if campaign.status != "draft":
                raise ValueError(f"Cannot start campaign in status: {campaign.status}")
            
            # Update campaign status
            campaign_update = CampaignUpdate(status="active")
            updated_campaign = await self.campaign_repository.update_campaign(
                campaign_id, 
                campaign_update
            )
            
            # Start campaign execution
            await self._start_campaign_execution(campaign_id)
            
            self.logger.info(f"Campaign started successfully: {campaign_id}")
            return updated_campaign
            
        except Exception as e:
            self.logger.error(f"Failed to start campaign {campaign_id}: {str(e)}")
            raise
    
    async def pause_campaign(self, campaign_id: UUID) -> Optional[CampaignResponse]:
        """Pause a campaign."""
        try:
            self.logger.info(f"Pausing campaign: {campaign_id}")
            
            # Get campaign
            campaign = await self.campaign_repository.get_campaign(campaign_id)
            if not campaign:
                return None
            
            # Validate campaign can be paused
            if campaign.status not in ["active", "running"]:
                raise ValueError(f"Cannot pause campaign in status: {campaign.status}")
            
            # Update campaign status
            campaign_update = CampaignUpdate(status="paused")
            updated_campaign = await self.campaign_repository.update_campaign(
                campaign_id, 
                campaign_update
            )
            
            # Pause campaign execution
            await self._pause_campaign_execution(campaign_id)
            
            self.logger.info(f"Campaign paused successfully: {campaign_id}")
            return updated_campaign
            
        except Exception as e:
            self.logger.error(f"Failed to pause campaign {campaign_id}: {str(e)}")
            raise
    
    async def resume_campaign(self, campaign_id: UUID) -> Optional[CampaignResponse]:
        """Resume a paused campaign."""
        try:
            self.logger.info(f"Resuming campaign: {campaign_id}")
            
            # Get campaign
            campaign = await self.campaign_repository.get_campaign(campaign_id)
            if not campaign:
                return None
            
            # Validate campaign can be resumed
            if campaign.status != "paused":
                raise ValueError(f"Cannot resume campaign in status: {campaign.status}")
            
            # Update campaign status
            campaign_update = CampaignUpdate(status="active")
            updated_campaign = await self.campaign_repository.update_campaign(
                campaign_id, 
                campaign_update
            )
            
            # Resume campaign execution
            await self._resume_campaign_execution(campaign_id)
            
            self.logger.info(f"Campaign resumed successfully: {campaign_id}")
            return updated_campaign
            
        except Exception as e:
            self.logger.error(f"Failed to resume campaign {campaign_id}: {str(e)}")
            raise
    
    async def get_campaign_metrics(self, campaign_id: UUID) -> Optional[Dict[str, Any]]:
        """Get campaign metrics and analytics."""
        try:
            self.logger.info(f"Getting metrics for campaign: {campaign_id}")
            
            # Get campaign
            campaign = await self.campaign_repository.get_campaign(campaign_id)
            if not campaign:
                return None
            
            # Get campaign metrics
            metrics = await self.campaign_repository.get_campaign_metrics(campaign_id)
            
            return {
                "campaign_id": campaign_id,
                "campaign_name": campaign.name,
                "status": campaign.status,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get campaign metrics {campaign_id}: {str(e)}")
            raise
    
    # Workflow management methods
    async def create_workflow(self, workflow_data: WorkflowCreate) -> WorkflowResponse:
        """Create a new workflow."""
        try:
            self.logger.info(f"Creating workflow: {workflow_data.name}")
            
            # Validate workflow definition
            self._validate_workflow_definition(workflow_data.definition)
            
            # Create workflow
            workflow = await self.workflow_repository.create_workflow(workflow_data)
            
            self.logger.info(f"Workflow created successfully: {workflow.id}")
            return workflow
            
        except Exception as e:
            self.logger.error(f"Failed to create workflow: {str(e)}")
            raise
    
    async def get_workflow(self, workflow_id: UUID) -> Optional[WorkflowResponse]:
        """Get a workflow by ID."""
        try:
            self.logger.info(f"Getting workflow: {workflow_id}")
            workflow = await self.workflow_repository.get_workflow(workflow_id)
            return workflow
        except Exception as e:
            self.logger.error(f"Failed to get workflow {workflow_id}: {str(e)}")
            raise
    
    async def list_workflows(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[WorkflowResponse]:
        """List workflows."""
        try:
            self.logger.info(f"Listing workflows: skip={skip}, limit={limit}")
            workflows = await self.workflow_repository.list_workflows(skip=skip, limit=limit)
            return workflows
        except Exception as e:
            self.logger.error(f"Failed to list workflows: {str(e)}")
            raise
    
    def _validate_workflow_definition(self, definition: Dict[str, Any]):
        """Validate workflow definition."""
        try:
            # Check required fields
            if "start_node_id" not in definition:
                raise ValueError("Workflow definition must have start_node_id")
            
            if "nodes" not in definition:
                raise ValueError("Workflow definition must have nodes")
            
            # Check if start node exists
            start_node_id = definition["start_node_id"]
            nodes = definition["nodes"]
            
            if start_node_id not in nodes:
                raise ValueError(f"Start node {start_node_id} not found in workflow")
            
            # Validate each node
            for node_id, node in nodes.items():
                if "type" not in node:
                    raise ValueError(f"Node {node_id} must have a type")
                
                node_type = node["type"]
                if node_type not in ["message", "decision", "action", "ai_response"]:
                    raise ValueError(f"Unknown node type: {node_type}")
            
        except Exception as e:
            raise ValueError(f"Invalid workflow definition: {str(e)}")
    
    async def _start_campaign_execution(self, campaign_id: UUID):
        """Start campaign execution logic."""
        try:
            # This would typically involve:
            # 1. Loading campaign contacts
            # 2. Scheduling campaign execution
            # 3. Setting up monitoring
            # 4. Starting workflow orchestrator
            
            self.logger.info(f"Started campaign execution for: {campaign_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to start campaign execution: {str(e)}")
            raise
    
    async def _pause_campaign_execution(self, campaign_id: UUID):
        """Pause campaign execution logic."""
        try:
            # This would typically involve:
            # 1. Stopping new conversation creation
            # 2. Pausing active workflows
            # 3. Updating monitoring status
            
            self.logger.info(f"Paused campaign execution for: {campaign_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to pause campaign execution: {str(e)}")
            raise
    
    async def _resume_campaign_execution(self, campaign_id: UUID):
        """Resume campaign execution logic."""
        try:
            # This would typically involve:
            # 1. Resuming conversation creation
            # 2. Resuming active workflows
            # 3. Updating monitoring status
            
            self.logger.info(f"Resumed campaign execution for: {campaign_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to resume campaign execution: {str(e)}")
            raise
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            self.logger.info("Cleaning up Campaign Service...")
            
            # Cleanup repositories
            await self.campaign_repository.cleanup()
            await self.workflow_repository.cleanup()
            
            self.logger.info("Campaign Service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}") 