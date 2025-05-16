"""
User Extension Service

This module provides the service layer for managing user extensions.
It handles the business logic for creating, reading, updating, and deleting
user extensions in the MongoDB database.
"""

import logging
from typing import List, Dict, Any, Optional
from bson import ObjectId
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.models.user_extension import UserExtension

logger = logging.getLogger(__name__)

class UserExtensionService:
    """
    Service for managing user extensions in the database.
    
    This service provides methods for CRUD operations on user extensions,
    ensuring proper tenant isolation and data integrity.
    """
    
    def __init__(self, db: Database, collection: Collection):
        """
        Initialize the UserExtensionService.
        
        Args:
            db: MongoDB database instance
            collection: MongoDB collection for user extensions
        """
        self.db = db
        self.collection = collection
        self.initialized = False
    
    def initialize(self, collection: Collection) -> None:
        """
        Initialize the service and set up necessary indexes.
        
        Args:
            collection: MongoDB collection for user extensions
        """
        try:
            # Set up indexes for efficient querying
            collection.create_index([("user_id", 1), ("tenant_id", 1)])
            collection.create_index([("extension_type", 1), ("tenant_id", 1)])
            self.initialized = True
            logger.info("UserExtensionService initialized with indexes")
        except PyMongoError as e:
            logger.error(f"Failed to initialize UserExtensionService: {str(e)}")
            self.initialized = False
    
    def _check_initialized(self) -> bool:
        """
        Check if the service is properly initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        if not self.initialized:
            logger.error("UserExtensionService not initialized")
            return False
        return True
    
    def get_extension_by_id(self, user_id: str, tenant_id: str, extension_id: str) -> Optional[UserExtension]:
        """
        Get a specific extension by its ID.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            extension_id: Extension identifier
            
        Returns:
            UserExtension if found, None otherwise
        """
        if not self._check_initialized():
            return None
        
        try:
            document = self.collection.find_one({
                "_id": ObjectId(extension_id),
                "user_id": user_id,
                "tenant_id": tenant_id
            })
            
            if document:
                return UserExtension.from_document(document)
            return None
        except PyMongoError as e:
            logger.error(f"Error retrieving extension {extension_id}: {str(e)}")
            return None
    
    def get_extensions_by_user(self, user_id: str, tenant_id: str) -> List[UserExtension]:
        """
        Get all extensions for a specific user.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            
        Returns:
            List of user extensions
        """
        if not self._check_initialized():
            return []
        
        try:
            documents = self.collection.find({
                "user_id": user_id,
                "tenant_id": tenant_id
            })
            
            return [UserExtension.from_document(doc) for doc in documents]
        except PyMongoError as e:
            logger.error(f"Error retrieving extensions for user {user_id}: {str(e)}")
            return []
    
    def get_extensions_by_type(self, user_id: str, tenant_id: str, extension_type: str) -> List[UserExtension]:
        """
        Get all extensions of a specific type for a user.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            extension_type: Type of the extension
            
        Returns:
            List of user extensions
        """
        if not self._check_initialized():
            return []
        
        try:
            documents = self.collection.find({
                "user_id": user_id,
                "tenant_id": tenant_id,
                "extension_type": extension_type
            })
            
            return [UserExtension.from_document(doc) for doc in documents]
        except PyMongoError as e:
            logger.error(f"Error retrieving extensions of type {extension_type} for user {user_id}: {str(e)}")
            return []
    
    def create_extension(
        self,
        user_id: str,
        tenant_id: str,
        extension_type: str,
        metrics: Dict[str, Any],
        practicality: Dict[str, Any]
    ) -> Optional[UserExtension]:
        """
        Create a new user extension.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            extension_type: Type of the extension
            metrics: Extension metrics
            practicality: Extension practicality data
            
        Returns:
            Created UserExtension if successful, None otherwise
        """
        if not self._check_initialized():
            return None
        
        extension = UserExtension(
            id=str(ObjectId()),
            user_id=user_id,
            tenant_id=tenant_id,
            extension_type=extension_type,
            metrics=metrics,
            practicality=practicality
        )
        
        try:
            document = extension.to_document()
            result = self.collection.insert_one(document)
            
            if result.inserted_id:
                # Update the ID field with the generated ObjectId
                extension.id = str(result.inserted_id)
                return extension
            return None
        except PyMongoError as e:
            logger.error(f"Error creating extension for user {user_id}: {str(e)}")
            return None
    
    def update_extension(
        self,
        user_id: str,
        tenant_id: str,
        extension_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Update an existing user extension.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            extension_id: Extension identifier
            update_data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        if not self._check_initialized():
            return False
        
        try:
            # Prepare update document
            update_doc = {"$set": {}}
            
            # Add fields to update
            for key, value in update_data.items():
                if key not in ["id", "user_id", "tenant_id"]:  # Don't allow updating these fields
                    update_doc["$set"][key] = value
            
            if not update_doc["$set"]:
                logger.warning("No valid fields to update")
                return False
            
            result = self.collection.update_one(
                {
                    "_id": ObjectId(extension_id),
                    "user_id": user_id,
                    "tenant_id": tenant_id
                },
                update_doc
            )
            
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error updating extension {extension_id}: {str(e)}")
            return False
    
    def delete_extension(self, user_id: str, tenant_id: str, extension_id: str) -> bool:
        """
        Delete a user extension.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            extension_id: Extension identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self._check_initialized():
            return False
        
        try:
            result = self.collection.delete_one({
                "_id": ObjectId(extension_id),
                "user_id": user_id,
                "tenant_id": tenant_id
            })
            
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Error deleting extension {extension_id}: {str(e)}")
            return False
    
    def find_all_for_tenant(self, tenant_id: str, page: int = 1, page_size: int = 20) -> List[UserExtension]:
        """
        Find all extensions for a specific tenant with pagination.
        
        Args:
            tenant_id: Tenant identifier
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            List of user extensions
        """
        if not self._check_initialized():
            return []
        
        try:
            skip = (page - 1) * page_size
            
            documents = self.collection.find(
                {"tenant_id": tenant_id}
            ).skip(skip).limit(page_size)
            
            return [UserExtension.from_document(doc) for doc in documents]
        except PyMongoError as e:
            logger.error(f"Error retrieving extensions for tenant {tenant_id}: {str(e)}")
            return [] 