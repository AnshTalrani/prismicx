import os
import logging
from typing import List, Dict, Any, Optional

from models.extension import UserExtension, Practicality, Factor
from clients.user_extension_client import UserExtensionClient

logger = logging.getLogger(__name__)


class UserExtensionRepository:
    """Repository for managing UserExtension objects via the Database Layer."""

    def __init__(self):
        """Initialize the repository with the UserExtensionClient."""
        logger.info("Initializing UserExtensionRepository with Database Layer client")
        
        try:
            self.client = UserExtensionClient()
            logger.info("Successfully connected to Database Layer User Extension service")
        except Exception as e:
            logger.error(f"Failed to initialize UserExtensionClient: {e}")
            raise
    
    async def find_by_id(self, extension_id: str, tenant_id: str) -> Optional[UserExtension]:
        """Find a UserExtension by extension_id."""
        try:
            return await self.client.find_by_id(extension_id, tenant_id)
        except Exception as e:
            logger.error(f"Error finding user extension by ID: {e}")
            return None
    
    async def find_by_user_id(self, user_id: str, tenant_id: str) -> List[UserExtension]:
        """Find all extensions for a user."""
        try:
            return await self.client.find_by_user_id(user_id, tenant_id)
        except Exception as e:
            logger.error(f"Error finding extensions by user ID: {e}")
            return []
    
    async def find_by_type(self, extension_type: str, tenant_id: str, page: int = 1, page_size: int = 20) -> List[UserExtension]:
        """
        Find all extensions of a specific type.
        
        Args:
            extension_type: The type of extension to find
            tenant_id: Tenant identifier
            page: Page number
            page_size: Page size
            
        Returns:
            A list of extension objects
        """
        try:
            return await self.client.find_by_type(extension_type, tenant_id, page, page_size)
        except Exception as e:
            logger.error(f"Error finding extensions by type: {e}")
            return []
    
    async def save(self, extension: UserExtension) -> None:
        """Save a UserExtension object."""
        try:
            await self.client.save(extension)
            logger.info(f"Saved extension {extension.extension_id}")
        except Exception as e:
            logger.error(f"Error saving extension: {e}")
            raise
    
    async def delete(self, extension_id: str, tenant_id: str) -> None:
        """Delete a UserExtension by extension_id."""
        try:
            await self.client.delete(extension_id, tenant_id)
            logger.info(f"Deleted extension {extension_id}")
        except Exception as e:
            logger.error(f"Error deleting extension: {e}")
            raise
    
    async def delete_by_user_id(self, user_id: str, tenant_id: str) -> None:
        """Delete all extensions for a user."""
        try:
            await self.client.delete_by_user_id(user_id, tenant_id)
            logger.info(f"Deleted all extensions for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting extensions by user ID: {e}")
            raise
    
    async def close(self):
        """Close the client connection."""
        await self.client.close()
        logger.info("Closed UserExtensionClient connection")
    
    async def update(self, extension: UserExtension) -> bool:
        """
        Update an existing extension.
        
        Args:
            extension: The extension to update
        
        Returns:
            True if the update was successful, False otherwise
        """
        try:
            # The save method in the client handles both creation and updates
            await self.save(extension)
            return True
        except Exception as e:
            logger.error(f"Error updating extension: {e}")
            return False
    
    async def get_all_tenants(self) -> List[str]:
        """Get all tenant IDs."""
        try:
            return await self.client.get_all_tenants()
        except Exception as e:
            logger.error(f"Error getting all tenants: {e}")
            return []
    
    async def find_all_for_tenant(self, tenant_id: str, page: int = 1, page_size: int = 20) -> List[UserExtension]:
        """Find all user extensions for a tenant."""
        try:
            return await self.client.find_all_for_tenant(tenant_id, page, page_size)
        except Exception as e:
            logger.error(f"Error finding all extensions for tenant: {e}")
            return [] 