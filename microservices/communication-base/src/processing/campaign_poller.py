"""
Campaign Poller Module

This module provides a campaign polling mechanism to retrieve batches of campaigns
from the repository for processing.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import structlog

from src.clients.campaign_users_repository_client import CampaignUsersRepositoryClient

logger = structlog.get_logger(__name__)

class CampaignPoller:
    """
    Campaign Poller for retrieving batches of campaigns for processing.
    
    This class is responsible for efficiently polling the repository
    for pending campaigns and managing the batch processing flow.
    """
    
    def __init__(self, repository: CampaignUsersRepositoryClient, batch_size: int = 10, 
                poll_interval: float = 5.0):
        """
        Initialize the campaign poller.
        
        Args:
            repository: Campaign Users Repository client
            batch_size: Maximum number of campaigns to retrieve in one batch
            poll_interval: Time in seconds between polling attempts when no campaigns are found
        """
        self.repository = repository
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.is_running = False
        logger.info("Campaign poller initialized", batch_size=batch_size, 
                   poll_interval=poll_interval)
    
    async def get_next_campaign(self) -> Optional[Dict[str, Any]]:
        """
        Get the next available campaign for processing.
        
        Returns:
            Campaign data dictionary or None if no campaigns are available
        """
        campaigns = await self.repository.get_pending_campaigns(limit=1)
        if campaigns:
            campaign = campaigns[0]
            # Mark as processing
            await self.repository.update_campaign_status(
                campaign["id"], 
                "processing",
                started_at=datetime.utcnow()
            )
            logger.info("Retrieved campaign for processing", campaign_id=campaign["id"])
            return campaign
        return None
    
    async def get_batch_campaigns(self) -> List[Dict[str, Any]]:
        """
        Get a batch of campaigns for processing.
        
        Returns:
            List of campaign data dictionaries
        """
        pending_campaigns = await self.repository.get_pending_campaigns(limit=self.batch_size)
        processed_campaigns = []
        
        for campaign in pending_campaigns:
            # Mark as processing
            success = await self.repository.update_campaign_status(
                campaign["id"], 
                "processing",
                started_at=datetime.utcnow()
            )
            
            if success:
                processed_campaigns.append(campaign)
                logger.debug("Marked campaign as processing", campaign_id=campaign["id"])
            
        if processed_campaigns:
            logger.info(f"Retrieved batch of {len(processed_campaigns)} campaigns")
        
        return processed_campaigns
    
    async def poll_campaigns(self) -> List[Dict[str, Any]]:
        """
        Poll for campaigns, waiting if none are available.
        
        Returns:
            List of campaign data dictionaries
        """
        self.is_running = True
        
        while self.is_running:
            campaigns = await self.get_batch_campaigns()
            
            if campaigns:
                return campaigns
            
            # No campaigns found, wait before polling again
            logger.debug(f"No pending campaigns found, waiting {self.poll_interval} seconds")
            await asyncio.sleep(self.poll_interval)
        
        return []
    
    async def mark_campaign_completed(self, campaign_id: str, 
                                     results: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark a campaign as completed.
        
        Args:
            campaign_id: ID of the campaign to mark as completed
            results: Optional results from processing
            
        Returns:
            True if successful, False otherwise
        """
        return await self.repository.update_campaign_status(
            campaign_id,
            "completed",
            completed_at=datetime.utcnow(),
            results=results
        )
    
    async def mark_campaign_failed(self, campaign_id: str, error: str) -> bool:
        """
        Mark a campaign as failed.
        
        Args:
            campaign_id: ID of the campaign to mark as failed
            error: Error message
            
        Returns:
            True if successful, False otherwise
        """
        return await self.repository.update_campaign_status(
            campaign_id,
            "failed",
            completed_at=datetime.utcnow(),
            error=error
        )
    
    def stop(self):
        """Stop the polling process."""
        self.is_running = False
        logger.info("Campaign poller stopped") 