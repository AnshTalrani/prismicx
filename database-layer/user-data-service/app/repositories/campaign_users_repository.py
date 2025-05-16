"""
Campaign Users Repository

Repository for managing campaign users in a separate collection.
This repository handles temporary campaign participants with configurable retention.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
import pymongo

from .system_users_conversation import SystemUsersConversation

logger = logging.getLogger(__name__)


class CampaignUsersRepository:
    """Repository for managing temporary campaign users."""

    def __init__(self, mongo_client: AsyncIOMotorClient = None, db_name: str = "campaign_users"):
        """
        Initialize the repository with MongoDB connection.
        
        Args:
            mongo_client: AsyncIOMotorClient instance
            db_name: Database name (defaults to campaign_users)
        """
        self.client = mongo_client
        self.db_name = db_name
        self.db = None
        # Default TTL of 3 months (90 days) for campaign users
        self.default_ttl_days = int(os.getenv("CAMPAIGN_USERS_TTL_DAYS", "90"))
        self.system_users_repo = None
    
    async def initialize(self, mongo_client: AsyncIOMotorClient = None, system_users_repo: SystemUsersConversation = None):
        """
        Initialize the repository with the MongoDB client.
        
        Args:
            mongo_client: AsyncIOMotorClient instance
            system_users_repo: SystemUsersConversation instance for migration
        """
        if mongo_client:
            self.client = mongo_client
        
        if system_users_repo:
            self.system_users_repo = system_users_repo
        
        if self.client:
            self.db = self.client[self.db_name]
            
            # Create TTL index if it doesn't exist
            for collection_name in await self.db.list_collection_names():
                await self.db[collection_name].create_index(
                    "expiry_date", 
                    expireAfterSeconds=0
                )
            
            logger.info(f"CampaignUsersRepository initialized with database {self.db_name}")
        else:
            logger.error("No MongoDB client provided for CampaignUsersRepository")
            raise ValueError("MongoDB client is required")
    
    def _get_collection(self, campaign_id: str) -> AsyncIOMotorCollection:
        """
        Get the collection for the campaign.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            AsyncIOMotorCollection for the campaign
        """
        collection_name = f'campaign_{campaign_id}'
        collection = self.db[collection_name]
        
        # Ensure TTL index exists
        collection.create_index(
            "expiry_date", 
            expireAfterSeconds=0
        )
        
        return collection
    
    async def find_by_id(self, user_id: str, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a campaign user by user ID.
        
        Args:
            user_id: User identifier
            campaign_id: Campaign identifier
            
        Returns:
            User dict if found, None otherwise
        """
        collection = self._get_collection(campaign_id)
        return await collection.find_one({"user_id": user_id})
    
    async def find_all_by_campaign(
        self,
        campaign_id: str,
        page: int = 1,
        page_size: int = 20,
        filter_criteria: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all users for a campaign.
        
        Args:
            campaign_id: Campaign identifier
            page: Page number
            page_size: Page size
            filter_criteria: Additional filter criteria
            
        Returns:
            List of user dicts
        """
        collection = self._get_collection(campaign_id)
        skip = (page - 1) * page_size
        
        query = filter_criteria or {}
        
        cursor = collection.find(query).skip(skip).limit(page_size)
        return await cursor.to_list(length=page_size)
    
    async def save(
        self,
        user_data: Dict[str, Any],
        campaign_id: str,
        ttl_days: int = None
    ) -> str:
        """
        Save a campaign user.
        
        Args:
            user_data: User data to save
            campaign_id: Campaign identifier
            ttl_days: Optional custom TTL in days
            
        Returns:
            The user ID
        """
        if self.system_users_repo:
            # Check if user is already a system user
            is_system = await self.system_users_repo.is_system_user(
                user_data.get("user_id", str(uuid4()))
            )
            
            if is_system:
                logger.info(f"User {user_data.get('user_id')} is already a system user, skipping campaign storage")
                return user_data.get("user_id")
        
        user_id = user_data.get("user_id", str(uuid4()))
        user_data["user_id"] = user_id
        
        # Set timestamps
        now = datetime.utcnow()
        if "created_at" not in user_data:
            user_data["created_at"] = now
        user_data["updated_at"] = now
        
        # Set expiry date for TTL
        ttl = ttl_days if ttl_days is not None else self.default_ttl_days
        user_data["expiry_date"] = now + timedelta(days=ttl)
        
        # Add campaign identifier
        user_data["campaign_id"] = campaign_id
        
        collection = self._get_collection(campaign_id)
        
        await collection.update_one(
            {"user_id": user_id},
            {"$set": user_data},
            upsert=True
        )
        
        logger.info(f"Saved campaign user {user_id} for campaign {campaign_id} with TTL of {ttl} days")
        return user_id
    
    async def migrate_to_system(self, user_id: str, campaign_id: str) -> bool:
        """
        Migrate a campaign user to system users.
        
        Args:
            user_id: User identifier
            campaign_id: Campaign identifier
            
        Returns:
            True if migrated, False otherwise
        """
        if not self.system_users_repo:
            logger.error("SystemUsersConversation not initialized, cannot migrate user")
            return False
        
        # Get campaign user data
        user_data = await self.find_by_id(user_id, campaign_id)
        if not user_data:
            logger.warning(f"Campaign user {user_id} not found in campaign {campaign_id}")
            return False
        
        # Remove campaign-specific fields
        user_data.pop("campaign_id", None)
        user_data.pop("expiry_date", None)
        
        # Add migration metadata
        user_data["metadata"] = user_data.get("metadata", {})
        user_data["metadata"]["migrated_from_campaign"] = campaign_id
        user_data["metadata"]["migration_date"] = datetime.utcnow().isoformat()
        
        try:
            # Save to system users
            await self.system_users_repo.save(user_data)
            
            # Delete from campaign users
            await self.delete(user_id, campaign_id)
            
            logger.info(f"Migrated user {user_id} from campaign {campaign_id} to system users")
            return True
        except Exception as e:
            logger.error(f"Error migrating user {user_id}: {e}")
            return False
    
    async def delete(self, user_id: str, campaign_id: str) -> bool:
        """
        Delete a campaign user.
        
        Args:
            user_id: User identifier
            campaign_id: Campaign identifier
            
        Returns:
            True if deleted, False otherwise
        """
        collection = self._get_collection(campaign_id)
        
        try:
            result = await collection.delete_one({"user_id": user_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted campaign user {user_id} from campaign {campaign_id}")
                return True
            else:
                logger.warning(f"Campaign user {user_id} not found in campaign {campaign_id}")
                return False
        except Exception as e:
            logger.error(f"Error deleting campaign user {user_id}: {e}")
            return False
    
    async def update(self, user_id: str, campaign_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a campaign user.
        
        Args:
            user_id: User identifier
            campaign_id: Campaign identifier
            update_data: Data to update
            
        Returns:
            True if updated, False otherwise
        """
        collection = self._get_collection(campaign_id)
        
        # Set updated timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            result = await collection.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated campaign user {user_id} in campaign {campaign_id}")
                return True
            elif result.matched_count > 0:
                # Document matched but not modified
                return True
            else:
                logger.warning(f"Campaign user {user_id} not found in campaign {campaign_id}")
                return False
        except Exception as e:
            logger.error(f"Error updating campaign user {user_id}: {e}")
            return False
    
    async def update_ttl(self, user_id: str, campaign_id: str, ttl_days: int) -> bool:
        """
        Update the TTL for a campaign user.
        
        Args:
            user_id: User identifier
            campaign_id: Campaign identifier
            ttl_days: New TTL in days
            
        Returns:
            True if updated, False otherwise
        """
        collection = self._get_collection(campaign_id)
        
        now = datetime.utcnow()
        new_expiry = now + timedelta(days=ttl_days)
        
        try:
            result = await collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "updated_at": now,
                    "expiry_date": new_expiry
                }}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated TTL for campaign user {user_id} to {ttl_days} days")
                return True
            elif result.matched_count > 0:
                # Document matched but not modified
                return True
            else:
                logger.warning(f"Campaign user {user_id} not found in campaign {campaign_id}")
                return False
        except Exception as e:
            logger.error(f"Error updating TTL for campaign user {user_id}: {e}")
            return False 