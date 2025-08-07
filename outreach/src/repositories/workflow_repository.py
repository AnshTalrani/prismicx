"""
Workflow Repository

This module provides database access operations for workflows,
extending the base repository with workflow-specific queries.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.database import Workflow
from src.repositories.base import BaseRepository
from src.models.schemas import WorkflowCreate, WorkflowDefinition

class WorkflowRepository(BaseRepository[Workflow, WorkflowCreate, dict]):
    """Repository for workflow database operations."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize with database session."""
        super().__init__(Workflow, db_session)
    
    async def get_by_name(self, name: str) -> Optional[Workflow]:
        """Retrieve a workflow by name."""
        result = await self.db.execute(
            select(Workflow).where(Workflow.name == name)
        )
        return result.scalars().first()
    
    async def get_active_workflows(self) -> List[Workflow]:
        """Retrieve all active workflows."""
        result = await self.db.execute(
            select(Workflow).where(Workflow.is_active == True)
        )
        return result.scalars().all()
    
    async def get_latest_version(self, name: str) -> Optional[Workflow]:
        """Retrieve the latest version of a workflow by name."""
        result = await self.db.execute(
            select(Workflow)
            .where(Workflow.name == name)
            .order_by(Workflow.version.desc())
            .limit(1)
        )
        return result.scalars().first()
    
    async def create_version(
        self, 
        workflow_data: WorkflowCreate,
        version: Optional[int] = None
    ) -> Workflow:
        """Create a new version of a workflow."""
        # If version is not provided, get the latest version and increment
        if version is None:
            latest = await self.get_latest_version(workflow_data.name)
            version = latest.version + 1 if latest else 1
        
        # Create new workflow version
        workflow_dict = workflow_data.dict()
        workflow_dict["version"] = version
        
        return await super().create(workflow_dict)
    
    async def get_workflow_definition(
        self, 
        workflow_id: UUID
    ) -> Optional[WorkflowDefinition]:
        """Get the workflow definition for a workflow."""
        workflow = await self.get(workflow_id)
        if not workflow:
            return None
            
        return WorkflowDefinition(**workflow.definition)
    
    async def update_workflow_definition(
        self, 
        workflow_id: UUID, 
        definition: WorkflowDefinition
    ) -> Optional[Workflow]:
        """Update a workflow's definition."""
        workflow = await self.get(workflow_id)
        if not workflow:
            return None
            
        workflow.definition = definition.dict()
        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)
        return workflow
