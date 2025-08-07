"""
Campaign Repository

This module provides database access operations for campaigns,
extending the base repository with campaign-specific queries.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models.database import Campaign, CampaignStatus, CampaignType
from .base import BaseRepository
from ..models.schemas import CampaignCreate, CampaignUpdate

class CampaignRepository(BaseRepository[Campaign, CampaignCreate, CampaignUpdate]):
    """Repository for campaign database operations."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize with database session."""
        super().__init__(Campaign, db_session)
    
    async def get_active_campaigns(self) -> List[Campaign]:
        """Retrieve all active campaigns."""
        result = await self.db.execute(
            select(Campaign).where(Campaign.status == CampaignStatus.ACTIVE)
        )
        return result.scalars().all()
    
    async def get_by_type(
        self, 
        campaign_type: CampaignType, 
        status: Optional[CampaignStatus] = None
    ) -> List[Campaign]:
        """Retrieve campaigns by type and optional status."""
        query = select(Campaign).where(Campaign.campaign_type == campaign_type)
        
        if status:
            query = query.where(Campaign.status == status)
            
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_scheduled_campaigns(self) -> List[Campaign]:
        """Retrieve campaigns that are scheduled to start."""
        from sqlalchemy import func
        
        result = await self.db.execute(
            select(Campaign).where(
                and_(
                    Campaign.status == CampaignStatus.DRAFT,
                    Campaign.start_date <= func.now(),
                    or_(
                        Campaign.end_date.is_(None),
                        Campaign.end_date >= func.now()
                    )
                )
            )
        )
        return result.scalars().all()
    
    async def update_status(
        self, 
        campaign_id: UUID, 
        status: CampaignStatus
    ) -> Optional[Campaign]:
        """Update a campaign's status."""
        campaign = await self.get(campaign_id)
        if not campaign:
            return None
            
        campaign.status = status
        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign
