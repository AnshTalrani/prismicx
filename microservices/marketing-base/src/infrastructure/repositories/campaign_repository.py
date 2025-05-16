"""
Campaign repository.

This module provides a repository for storing and retrieving campaign data.
"""

import logging
from datetime import datetime
import asyncio
from typing import Dict, List, Optional, Any, Union

from ..models.campaign import Campaign, CampaignStatus
from ..database import Database

logger = logging.getLogger(__name__)


class CampaignRepository:
    """Repository for campaign data storage and retrieval."""

    def __init__(self, database: Optional[Database] = None):
        """Initialize the campaign repository.

        Args:
            database: Database connection.
        """
        self.database = database or Database()
        self.collection = "campaigns"
        self.max_retries = 3
        self.retry_delay = 0.5  # seconds

    async def _execute_with_retry(self, operation, *args, **kwargs):
        """Execute a database operation with retry logic.
        
        Args:
            operation: Async function to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: After max retries are exhausted
        """
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                retries += 1
                if retries < self.max_retries:
                    delay = self.retry_delay * (2 ** (retries - 1))  # Exponential backoff
                    logger.warning(
                        f"Database operation failed (attempt {retries}/{self.max_retries}), "
                        f"retrying in {delay:.2f}s: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Database operation failed after {self.max_retries} attempts: {str(e)}")
        
        # Re-raise the last error after max retries
        raise last_error

    async def save(self, campaign: Campaign) -> Campaign:
        """Save a campaign to the database.

        Args:
            campaign: Campaign to save.

        Returns:
            Saved campaign.
        """
        # Convert to dictionary for storage
        campaign_dict = campaign.to_dict()
        
        # Update timestamps
        campaign_dict["updated_at"] = datetime.utcnow()
        
        # Save to database with retry
        await self._execute_with_retry(
            self.database.upsert,
            collection=self.collection,
            id=campaign.id,
            data=campaign_dict
        )
        
        logger.debug(f"Saved campaign {campaign.id}")
        return campaign

    async def get_by_id(self, campaign_id: str) -> Optional[Campaign]:
        """Get a campaign by ID.

        Args:
            campaign_id: Campaign ID.

        Returns:
            Campaign if found, None otherwise.
        """
        campaign_dict = await self._execute_with_retry(
            self.database.get_by_id,
            collection=self.collection,
            id=campaign_id
        )
        
        if not campaign_dict:
            return None
        
        return Campaign.from_dict(campaign_dict)

    async def delete(self, campaign_id: str) -> bool:
        """Delete a campaign.

        Args:
            campaign_id: Campaign ID.

        Returns:
            True if deleted, False otherwise.
        """
        result = await self._execute_with_retry(
            self.database.delete,
            collection=self.collection,
            id=campaign_id
        )
        
        if result:
            logger.debug(f"Deleted campaign {campaign_id}")
        
        return result

    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[CampaignStatus] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> List[Campaign]:
        """List campaigns with filtering.

        Args:
            limit: Maximum number of campaigns to return.
            offset: Number of campaigns to skip.
            status: Filter by status.
            tags: Filter by tags.
            search: Search term for campaign name or description.

        Returns:
            List of campaigns.
        """
        # Build query
        query = {}
        
        if status:
            query["status"] = status.name
        
        if tags:
            query["tags"] = {"$in": tags}
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        # Execute query
        campaign_dicts = await self.database.find(
            collection=self.collection,
            query=query,
            limit=limit,
            offset=offset,
            sort={"created_at": -1}
        )
        
        # Convert to Campaign objects
        campaigns = [Campaign.from_dict(c) for c in campaign_dicts]
        
        return campaigns

    async def count(
        self,
        status: Optional[CampaignStatus] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> int:
        """Count campaigns with filtering.

        Args:
            status: Filter by status.
            tags: Filter by tags.
            search: Search term for campaign name or description.

        Returns:
            Count of matching campaigns.
        """
        # Build query
        query = {}
        
        if status:
            query["status"] = status.name
        
        if tags:
            query["tags"] = {"$in": tags}
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        # Execute count
        return await self.database.count(
            collection=self.collection,
            query=query
        )

    async def get_scheduled_campaigns(self, before_time: datetime) -> List[Campaign]:
        """Get campaigns scheduled to run before a specified time.

        Args:
            before_time: Get campaigns scheduled before this time.

        Returns:
            List of campaigns to process.
        """
        query = {
            "status": CampaignStatus.SCHEDULED.name,
            "scheduled_at": {"$lte": before_time}
        }
        
        campaign_dicts = await self.database.find(
            collection=self.collection,
            query=query,
            sort={"scheduled_at": 1}
        )
        
        campaigns = [Campaign.from_dict(c) for c in campaign_dicts]
        
        return campaigns

    async def update_recipient_status(
        self,
        campaign_id: str,
        tracking_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a recipient's status within a campaign.

        Args:
            campaign_id: Campaign ID.
            tracking_id: Recipient tracking ID.
            updates: Fields to update.

        Returns:
            True if updated, False otherwise.
        """
        # Build the update query for the nested recipient
        update_query = {
            "$set": {f"recipients.$.{key}": value for key, value in updates.items()}
        }
        
        # Execute update
        result = await self.database.update_array_element(
            collection=self.collection,
            id=campaign_id,
            array_field="recipients",
            element_query={"tracking_id": tracking_id},
            update=update_query
        )
        
        return result

    async def find(
        self,
        query: Dict[str, Any],
        limit: int = 100,
        offset: int = 0,
        sort: Optional[Dict[str, int]] = None
    ) -> List[Campaign]:
        """Find campaigns by custom query.

        Args:
            query: MongoDB query dictionary.
            limit: Maximum number of campaigns to return.
            offset: Number of campaigns to skip.
            sort: Sort criteria.

        Returns:
            List of campaigns matching the query.
        """
        # Use default sort if not specified
        if sort is None:
            sort = {"updated_at": -1}
        
        # Execute query with retry
        campaign_dicts = await self._execute_with_retry(
            self.database.find,
            collection=self.collection,
            query=query,
            limit=limit,
            offset=offset,
            sort=sort
        )
        
        # Convert to Campaign objects
        campaigns = [Campaign.from_dict(c) for c in campaign_dicts]
        
        logger.debug(f"Found {len(campaigns)} campaigns with query: {query}")
        return campaigns 