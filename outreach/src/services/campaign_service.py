"""
Campaign Service

Handles all business logic related to outreach campaigns.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from src.models.campaign import Campaign

class CampaignService:
    def __init__(self, campaign_repository):
        self.campaign_repo = campaign_repository

    async def create_campaign(self, campaign) -> Campaign:
        # Accept dict or Campaign model
        from src.models.campaign import Campaign as CampaignModel
        if isinstance(campaign, dict):
            campaign = CampaignModel(**campaign)
        campaign = campaign.copy(update={"created_at": datetime.utcnow(), "updated_at": datetime.utcnow()})
        return await self.campaign_repo.create(campaign)
    
    async def get_campaign(self, campaign_id: UUID) -> Optional[Campaign]:
        return await self.campaign_repo.get(campaign_id)

    async def update_campaign(self, campaign_id: UUID, update_data: dict) -> Optional[Campaign]:
        update_data['updated_at'] = datetime.utcnow()
        return await self.campaign_repo.update(campaign_id, update_data)

    async def delete_campaign(self, campaign_id: UUID) -> bool:
        return await self.campaign_repo.delete(campaign_id)
