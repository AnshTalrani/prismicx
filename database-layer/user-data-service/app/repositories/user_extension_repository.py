"""
User Extension Repository

Repository for managing UserExtension documents in MongoDB.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

from ..models.user_extension import UserExtension, Practicality, Factor

logger = logging.getLogger(__name__)


class UserExtensionRepository:
    """Repository for managing UserExtension documents in MongoDB."""

    def __init__(self, mongo_client: AsyncIOMotorClient = None, db_name: str = "user_extensions"):
        """
        Initialize the repository with MongoDB connection.
        
        Args:
            mongo_client: AsyncIOMotorClient instance
            db_name: Database name
        """
        self.client = mongo_client
        self.db_name = db_name
        self.db = None
    
    async def initialize(self, mongo_client: AsyncIOMotorClient = None):
        """
        Initialize the repository with the MongoDB client.
        
        Args:
            mongo_client: AsyncIOMotorClient instance
        """
        if mongo_client:
            self.client = mongo_client
        
        if self.client:
            self.db = self.client[self.db_name]
            logger.info(f"UserExtensionRepository initialized with database {self.db_name}")
        else:
            logger.error("No MongoDB client provided for UserExtensionRepository")
            raise ValueError("MongoDB client is required")
    
    def _get_collection(self, tenant_id: str) -> AsyncIOMotorCollection:
        """
        Get the collection for the tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            AsyncIOMotorCollection for the tenant
        """
        # Using tenant_id to create separate collections for each tenant
        collection_name = f'extensions_{tenant_id}'
        return self.db[collection_name]
    
    async def find_by_id(self, extension_id: str, tenant_id: str) -> Optional[UserExtension]:
        """
        Find a UserExtension by its ID.
        
        Args:
            extension_id: Extension identifier
            tenant_id: Tenant identifier
            
        Returns:
            UserExtension if found, None otherwise
        """
        collection = self._get_collection(tenant_id)
        data = await collection.find_one({"extension_id": extension_id})
        
        if data:
            return UserExtension.from_dict(data)
        return None
    
    async def find_by_user_id(self, user_id: str, tenant_id: str) -> List[UserExtension]:
        """
        Find all UserExtensions for a user.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            
        Returns:
            List of UserExtension objects
        """
        collection = self._get_collection(tenant_id)
        cursor = collection.find({"user_id": user_id})
        
        extensions = []
        async for document in cursor:
            extensions.append(UserExtension.from_dict(document))
        
        return extensions
    
    async def find_by_type(self, extension_type: str, tenant_id: str, page: int = 1, page_size: int = 20) -> List[UserExtension]:
        """
        Find all UserExtensions of a specific type.
        
        Args:
            extension_type: Extension type to filter by
            tenant_id: Tenant identifier
            page: Page number
            page_size: Page size
            
        Returns:
            List of UserExtension objects
        """
        collection = self._get_collection(tenant_id)
        skip = (page - 1) * page_size
        
        cursor = collection.find({"extension_type": extension_type}).skip(skip).limit(page_size)
        
        extensions = []
        async for document in cursor:
            extensions.append(UserExtension.from_dict(document))
        
        return extensions
    
    async def save(self, extension: UserExtension) -> None:
        """
        Save a UserExtension document.
        
        Args:
            extension: UserExtension to save
        """
        if not extension.tenant_id:
            raise ValueError("extension.tenant_id is required")
        
        collection = self._get_collection(extension.tenant_id)
        
        try:
            await collection.update_one(
                {"extension_id": extension.extension_id},
                {"$set": extension.to_dict()},
                upsert=True
            )
            logger.info(f"Saved extension {extension.extension_id} for user {extension.user_id}")
        except Exception as e:
            logger.error(f"Error saving extension: {e}")
            raise
    
    async def delete(self, extension_id: str, tenant_id: str) -> None:
        """
        Delete a UserExtension by its ID.
        
        Args:
            extension_id: Extension identifier
            tenant_id: Tenant identifier
        """
        collection = self._get_collection(tenant_id)
        
        try:
            result = await collection.delete_one({"extension_id": extension_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted extension {extension_id}")
            else:
                logger.warning(f"No extension found to delete with ID {extension_id}")
        except Exception as e:
            logger.error(f"Error deleting extension: {e}")
            raise
    
    async def update_metrics(self, extension_id: str, tenant_id: str, metrics: Dict[str, Any]) -> None:
        """
        Update the metrics of a UserExtension.
        
        Args:
            extension_id: Extension identifier
            tenant_id: Tenant identifier
            metrics: Metrics to update
        """
        try:
            # Find the extension
            extension = await self.find_by_id(extension_id, tenant_id)
            if not extension:
                logger.warning(f"No extension found with ID {extension_id}")
                return
            
            # Update metrics
            extension.update_metrics(metrics)
            
            # Save the updated extension
            await self.save(extension)
            logger.info(f"Updated metrics for extension {extension_id}")
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            raise
    
    async def update_practicality(self, extension_id: str, tenant_id: str, practicality_data: Dict[str, Any]) -> None:
        """
        Update the practicality of a UserExtension.
        
        Args:
            extension_id: Extension identifier
            tenant_id: Tenant identifier
            practicality_data: Practicality data to update
        """
        try:
            # Find the extension
            extension = await self.find_by_id(extension_id, tenant_id)
            if not extension:
                logger.warning(f"No extension found with ID {extension_id}")
                return
            
            # Create or update practicality
            if not extension.practicality:
                if 'practicality_id' not in practicality_data:
                    practicality_data['practicality_id'] = f"p_{extension_id}"
                
                practicality = Practicality.from_dict(practicality_data)
                extension.set_practicality(practicality)
            else:
                # Update existing practicality
                for key, value in practicality_data.items():
                    if key != 'practicality_id' and hasattr(extension.practicality, key):
                        setattr(extension.practicality, key, value)
            
            # Save the updated extension
            await self.save(extension)
            logger.info(f"Updated practicality for extension {extension_id}")
        except Exception as e:
            logger.error(f"Error updating practicality: {e}")
            raise
    
    async def add_factor(self, extension_id: str, tenant_id: str, factor_data: Dict[str, Any]) -> None:
        """
        Add a factor to the practicality of a UserExtension.
        
        Args:
            extension_id: Extension identifier
            tenant_id: Tenant identifier
            factor_data: Factor data to add
        """
        try:
            # Find the extension
            extension = await self.find_by_id(extension_id, tenant_id)
            if not extension:
                logger.warning(f"No extension found with ID {extension_id}")
                return
            
            # Ensure practicality exists
            if not extension.practicality:
                practicality = Practicality(
                    practicality_id=f"p_{extension_id}",
                    score=0.0,
                    description="Practicality metrics"
                )
                extension.set_practicality(practicality)
            
            # Create and add factor
            factor = Factor.from_dict(factor_data)
            extension.practicality.add_factor(factor)
            
            # Save the updated extension
            await self.save(extension)
            logger.info(f"Added factor {factor.factor_id} to extension {extension_id}")
        except Exception as e:
            logger.error(f"Error adding factor: {e}")
            raise
    
    async def remove_factor(self, extension_id: str, tenant_id: str, factor_id: str) -> None:
        """
        Remove a factor from the practicality of a UserExtension.
        
        Args:
            extension_id: Extension identifier
            tenant_id: Tenant identifier
            factor_id: Factor identifier
        """
        try:
            # Find the extension
            extension = await self.find_by_id(extension_id, tenant_id)
            if not extension:
                logger.warning(f"No extension found with ID {extension_id}")
                return
            
            # Ensure practicality exists
            if not extension.practicality:
                logger.warning(f"No practicality found for extension {extension_id}")
                return
            
            # Remove the factor
            extension.practicality.remove_factor(factor_id)
            
            # Save the updated extension
            await self.save(extension)
            logger.info(f"Removed factor {factor_id} from extension {extension_id}")
        except Exception as e:
            logger.error(f"Error removing factor: {e}")
            raise
    
    async def get_all_tenants(self) -> List[str]:
        """
        Get all tenant IDs that have user extensions.
        
        Returns:
            List of tenant IDs
        """
        try:
            # Extract tenant IDs from collection names
            collection_names = await self.db.list_collection_names()
            tenant_ids = []
            
            for name in collection_names:
                if name.startswith('extensions_'):
                    tenant_id = name[11:]  # Remove 'extensions_' prefix
                    tenant_ids.append(tenant_id)
            
            logger.info(f"Found {len(tenant_ids)} tenants with user extensions")
            return tenant_ids
        except Exception as e:
            logger.error(f"Error getting all tenants: {e}")
            raise
    
    async def find_all_for_tenant(self, tenant_id: str, page: int = 1, page_size: int = 100) -> List[UserExtension]:
        """
        Find all UserExtensions for a tenant with pagination.
        
        Args:
            tenant_id: Tenant identifier
            page: Page number
            page_size: Page size
            
        Returns:
            List of UserExtension objects
        """
        collection = self._get_collection(tenant_id)
        skip = (page - 1) * page_size
        
        try:
            cursor = collection.find({}).skip(skip).limit(page_size)
            extensions = []
            
            async for document in cursor:
                extensions.append(UserExtension.from_dict(document))
            
            logger.info(f"Found {len(extensions)} extensions for tenant {tenant_id} (page {page})")
            return extensions
        except Exception as e:
            logger.error(f"Error finding all extensions for tenant: {e}")
            raise 