"""
User Context Service

Service for managing user context including system users and campaign users.
Provides a unified interface for both user types with intelligent routing.
"""

import logging
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient

from ..repositories.system_users_conversation import SystemUsersConversation
from ..repositories.campaign_users_repository import CampaignUsersRepository

logger = logging.getLogger(__name__)


class UserContextService:
    """Service for managing user context data in both system and campaign repositories."""
    
    def __init__(self):
        """Initialize the user context service."""
        self.system_users_repo = SystemUsersConversation()
        self.campaign_users_repo = CampaignUsersRepository()
        self.initialized = False
    
    async def initialize(self, mongo_client: AsyncIOMotorClient):
        """
        Initialize the service with MongoDB connection.
        
        Args:
            mongo_client: AsyncIOMotorClient instance
        """
        if self.initialized:
            return
        
        logger.info("Initializing UserContextService")
        
        # Initialize repositories
        await self.system_users_repo.initialize(mongo_client)
        await self.campaign_users_repo.initialize(mongo_client, self.system_users_repo)
        
        self.initialized = True
        logger.info("UserContextService initialized successfully")
    
    async def close(self):
        """Close database connections."""
        await self.system_users_repo.close()
        logger.info("UserContextService connections closed")
    
    async def get_user_context(self, user_id: str, tenant_id: str = None, campaign_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Get user context from the appropriate repository.
        
        Prioritizes system users over campaign users.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier (for system users)
            campaign_id: Campaign identifier (for campaign users)
            
        Returns:
            User context dict if found, None otherwise
        """
        user_data = None
        
        # Check system users first if tenant_id is provided
        if tenant_id:
            user_data = await self.system_users_repo.find_by_id(user_id, tenant_id)
            if user_data:
                logger.debug(f"Found user {user_id} in system users")
                return user_data
        
        # Check campaign users if campaign_id is provided
        if campaign_id:
            user_data = await self.campaign_users_repo.find_by_id(user_id, campaign_id)
            if user_data:
                logger.debug(f"Found user {user_id} in campaign {campaign_id}")
                return user_data
        
        # Check if user is a system user without tenant filtering
        is_system = await self.system_users_repo.is_system_user(user_id)
        if is_system:
            logger.debug(f"User {user_id} is a system user but data not accessible with provided tenant_id")
            
        return None
    
    async def save_user_context(
        self,
        user_data: Dict[str, Any],
        tenant_id: str = None,
        campaign_id: str = None,
        ttl_days: int = None
    ) -> str:
        """
        Save user context to the appropriate repository.
        
        Prioritizes system users over campaign users.
        
        Args:
            user_data: User data to save
            tenant_id: Tenant identifier (for system users)
            campaign_id: Campaign identifier (for campaign users)
            ttl_days: Optional TTL for campaign users
            
        Returns:
            The user ID
        """
        # Check if user is already a system user
        user_id = user_data.get("user_id")
        if user_id:
            is_system = await self.system_users_repo.is_system_user(user_id)
            if is_system:
                # If system user and tenant_id provided, update system user
                if tenant_id:
                    user_data["tenant_id"] = tenant_id
                    return await self.system_users_repo.save(user_data)
                logger.info(f"User {user_id} is a system user but no tenant_id provided")
        
        # If tenant_id provided, save to system users
        if tenant_id:
            user_data["tenant_id"] = tenant_id
            return await self.system_users_repo.save(user_data)
        
        # If campaign_id provided, save to campaign users
        if campaign_id:
            return await self.campaign_users_repo.save(user_data, campaign_id, ttl_days)
        
        raise ValueError("Either tenant_id or campaign_id must be provided")
    
    async def update_user_context(
        self,
        user_id: str,
        update_data: Dict[str, Any],
        tenant_id: str = None,
        campaign_id: str = None
    ) -> bool:
        """
        Update user context in the appropriate repository.
        
        Prioritizes system users over campaign users.
        
        Args:
            user_id: User identifier
            update_data: Data to update
            tenant_id: Tenant identifier (for system users)
            campaign_id: Campaign identifier (for campaign users)
            
        Returns:
            True if updated, False otherwise
        """
        # Check if user is already a system user
        is_system = await self.system_users_repo.is_system_user(user_id)
        
        # If system user and tenant_id provided, update system user
        if is_system and tenant_id:
            return await self.system_users_repo.update(user_id, tenant_id, update_data)
        
        # If campaign_id provided, update campaign user
        if campaign_id:
            return await self.campaign_users_repo.update(user_id, campaign_id, update_data)
        
        return False
    
    async def delete_user_context(
        self,
        user_id: str,
        tenant_id: str = None,
        campaign_id: str = None
    ) -> bool:
        """
        Delete user context from the appropriate repository.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier (for system users)
            campaign_id: Campaign identifier (for campaign users)
            
        Returns:
            True if deleted, False otherwise
        """
        result = False
        
        # Delete from system users if tenant_id provided
        if tenant_id:
            system_result = await self.system_users_repo.delete(user_id, tenant_id)
            result = result or system_result
        
        # Delete from campaign users if campaign_id provided
        if campaign_id:
            campaign_result = await self.campaign_users_repo.delete(user_id, campaign_id)
            result = result or campaign_result
        
        return result
    
    async def migrate_to_system(
        self,
        user_id: str,
        campaign_id: str,
        tenant_id: str
    ) -> bool:
        """
        Migrate a campaign user to system users.
        
        Args:
            user_id: User identifier
            campaign_id: Campaign identifier
            tenant_id: Target tenant identifier
            
        Returns:
            True if migrated, False otherwise
        """
        # Get campaign user data
        user_data = await self.campaign_users_repo.find_by_id(user_id, campaign_id)
        if not user_data:
            logger.warning(f"Campaign user {user_id} not found in campaign {campaign_id}")
            return False
        
        # Remove campaign-specific fields
        user_data.pop("campaign_id", None)
        user_data.pop("expiry_date", None)
        
        # Add tenant_id
        user_data["tenant_id"] = tenant_id
        
        # Add migration metadata
        user_data["metadata"] = user_data.get("metadata", {})
        user_data["metadata"]["migrated_from_campaign"] = campaign_id
        
        try:
            # Save to system users
            await self.system_users_repo.save(user_data)
            
            # Delete from campaign users
            await self.campaign_users_repo.delete(user_id, campaign_id)
            
            logger.info(f"Migrated user {user_id} from campaign {campaign_id} to system tenant {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"Error migrating user {user_id}: {e}")
            return False
    
    async def get_all_campaign_users(
        self,
        campaign_id: str,
        page: int = 1,
        page_size: int = 20,
        filter_criteria: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all users for a campaign.
        
        Args:
            campaign_id: Campaign identifier
            page: Page number
            page_size: Page size
            filter_criteria: Additional filter criteria
            
        Returns:
            List of user data
        """
        return await self.campaign_users_repo.find_all_by_campaign(
            campaign_id,
            page,
            page_size,
            filter_criteria
        )
    
    async def get_all_system_users(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get all system users for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            page: Page number
            page_size: Page size
            
        Returns:
            List of user data
        """
        return await self.system_users_repo.find_all_by_tenant(
            tenant_id,
            page,
            page_size
        )
    
    async def update_campaign_ttl(
        self,
        user_id: str,
        campaign_id: str,
        ttl_days: int
    ) -> bool:
        """
        Update the TTL for a campaign user.
        
        Args:
            user_id: User identifier
            campaign_id: Campaign identifier
            ttl_days: New TTL in days
            
        Returns:
            True if updated, False otherwise
        """
        return await self.campaign_users_repo.update_ttl(user_id, campaign_id, ttl_days) 