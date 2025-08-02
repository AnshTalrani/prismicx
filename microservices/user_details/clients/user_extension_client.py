import logging
from typing import Dict, Any, List, Optional

from .database_layer_client import DatabaseLayerClient
from models.extension import UserExtension, Practicality, Factor

logger = logging.getLogger(__name__)

class UserExtensionClient:
    """
    Client for interacting with the User Extension APIs of the Database Layer service.
    Handles all user extension-related operations through the database layer.
    """
    
    def __init__(self, client: Optional[DatabaseLayerClient] = None):
        """
        Initialize the user extension client.
        
        Args:
            client: DatabaseLayerClient instance (creates a new one if not provided)
        """
        self.client = client or DatabaseLayerClient()
        self.base_path = "/api/extensions"
        logger.info("Initialized UserExtensionClient")
    
    async def find_by_id(self, extension_id: str, tenant_id: str) -> Optional[UserExtension]:
        """
        Find a UserExtension by extension ID.
        
        Args:
            extension_id: Extension identifier
            tenant_id: Tenant identifier
        
        Returns:
            UserExtension object or None if not found
        """
        try:
            data = await self.client.get(f"{self.base_path}/extension/{extension_id}", tenant_id=tenant_id)
            return UserExtension.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Error finding user extension by ID: {e}")
            return None
    
    async def find_by_user_id(self, user_id: str, tenant_id: str) -> List[UserExtension]:
        """
        Find all extensions for a user.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
        
        Returns:
            List of UserExtension objects
        """
        try:
            data = await self.client.get(f"{self.base_path}/user/{user_id}", tenant_id=tenant_id)
            return [UserExtension.from_dict(item) for item in data]
        except Exception as e:
            logger.error(f"Error finding extensions by user ID: {e}")
            return []
    
    async def find_by_type(self, extension_type: str, tenant_id: str, page: int = 1, page_size: int = 20) -> List[UserExtension]:
        """
        Find all extensions of a specific type.
        
        Args:
            extension_type: Type of extension
            tenant_id: Tenant identifier
            page: Page number
            page_size: Page size
        
        Returns:
            List of UserExtension objects
        """
        try:
            params = {
                "page": page,
                "page_size": page_size
            }
            data = await self.client.get(
                f"{self.base_path}/type/{extension_type}", 
                params=params,
                tenant_id=tenant_id
            )
            return [UserExtension.from_dict(item) for item in data]
        except Exception as e:
            logger.error(f"Error finding extensions by type: {e}")
            return []
    
    async def save(self, extension: UserExtension) -> None:
        """
        Save a UserExtension object.
        
        Args:
            extension: UserExtension object to save
        """
        if not extension.tenant_id:
            raise ValueError("extension.tenant_id is required")
        
        try:
            # Check if the extension exists
            existing = await self.find_by_id(extension.extension_id, extension.tenant_id)
            
            if existing:
                # Update existing extension metrics
                await self.client.put(
                    f"{self.base_path}/extension/{extension.extension_id}/metrics",
                    data={"metrics": extension.metrics},
                    tenant_id=extension.tenant_id
                )
                
                # Update practicality if it exists
                if extension.practicality:
                    await self.client.put(
                        f"{self.base_path}/extension/{extension.extension_id}/practicality",
                        data={"practicality": extension.practicality.to_dict()},
                        tenant_id=extension.tenant_id
                    )
                    
                    # Update factors
                    for factor in extension.practicality.factors:
                        await self.client.post(
                            f"{self.base_path}/extension/{extension.extension_id}/factor",
                            data={
                                "name": factor.name,
                                "value": factor.value,
                                "weight": factor.weight
                            },
                            tenant_id=extension.tenant_id
                        )
            else:
                # Create new extension
                practicality_data = None
                if extension.practicality:
                    practicality_data = extension.practicality.to_dict()
                
                await self.client.post(
                    f"{self.base_path}/",
                    data={
                        "user_id": extension.user_id,
                        "extension_type": extension.extension_type,
                        "metrics": extension.metrics,
                        "practicality": practicality_data
                    },
                    tenant_id=extension.tenant_id
                )
        except Exception as e:
            logger.error(f"Error saving user extension: {e}")
            raise
    
    async def delete(self, extension_id: str, tenant_id: str) -> None:
        """
        Delete a UserExtension by extension ID.
        
        Args:
            extension_id: Extension identifier
            tenant_id: Tenant identifier
        """
        try:
            await self.client.delete(f"{self.base_path}/extension/{extension_id}", tenant_id=tenant_id)
        except Exception as e:
            logger.error(f"Error deleting user extension: {e}")
            raise
    
    async def delete_by_user_id(self, user_id: str, tenant_id: str) -> None:
        """
        Delete all extensions for a user.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
        """
        try:
            # Get all extensions for the user
            extensions = await self.find_by_user_id(user_id, tenant_id)
            
            # Delete each extension
            for extension in extensions:
                await self.delete(extension.extension_id, tenant_id)
        except Exception as e:
            logger.error(f"Error deleting extensions by user ID: {e}")
            raise
    
    async def get_all_tenants(self) -> List[str]:
        """
        Get a list of all tenant IDs.
        
        Returns:
            List of tenant IDs
        """
        try:
            data = await self.client.get(f"{self.base_path}/tenants")
            return data
        except Exception as e:
            logger.error(f"Error getting all tenants: {e}")
            return []
    
    async def find_all_for_tenant(self, tenant_id: str, page: int = 1, page_size: int = 20) -> List[UserExtension]:
        """
        Find all user extensions for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            page: Page number
            page_size: Page size
        
        Returns:
            List of UserExtension objects
        """
        try:
            params = {
                "page": page,
                "page_size": page_size
            }
            data = await self.client.get(
                f"{self.base_path}/tenant/{tenant_id}/extensions", 
                params=params,
                tenant_id=tenant_id
            )
            return [UserExtension.from_dict(item) for item in data]
        except Exception as e:
            logger.error(f"Error finding all extensions for tenant: {e}")
            return []
    
    async def close(self):
        """Close the client connection."""
        await self.client.close() 