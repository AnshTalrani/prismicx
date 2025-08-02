"""
Template service for managing email templates.

This module provides business logic for creating, retrieving, updating,
and managing email templates for marketing campaigns.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

from src.config import get_config

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for managing email templates."""

    def __init__(self, mongo_client: Optional[MongoClient] = None):
        """
        Initialize the template service.
        
        Args:
            mongo_client: Optional MongoDB client. If not provided, a new client
                will be created using the configuration.
        """
        self.config = get_config()
        self._client = mongo_client or MongoClient(self.config.mongodb_uri)
        self._db = self._client[self.config.mongodb_database]
        self._collection = self._db['templates']
        
        # Create indexes
        self._ensure_indexes()
    
    def _ensure_indexes(self) -> None:
        """Ensure all necessary indexes exist on the templates collection."""
        indexes = [
            [("id", ASCENDING)],
            [("name", ASCENDING)],
            [("created_at", DESCENDING)],
            [("updated_at", DESCENDING)],
            [("tags", ASCENDING)]
        ]
        
        for index in indexes:
            self._collection.create_index(index)
    
    def create_template(
        self,
        name: str,
        html: str,
        text: str,
        subject: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        custom_attributes: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new email template.
        
        Args:
            name: Template name
            html: HTML version of the template
            text: Plain text version of the template
            subject: Default subject line for the template
            description: Optional template description
            tags: Optional list of tags for template categorization
            custom_attributes: Optional custom template attributes
            
        Returns:
            ID of the created template
            
        Raises:
            PyMongoError: If there's an error communicating with MongoDB
        """
        try:
            template_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            template_data = {
                "id": template_id,
                "name": name,
                "html": html,
                "text": text,
                "subject": subject,
                "description": description or "",
                "tags": tags or [],
                "custom_attributes": custom_attributes or {},
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            
            self._collection.insert_one(template_data)
            
            return template_id
        except PyMongoError as e:
            logger.error(f"Failed to create template: {e}")
            raise
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a template by ID.
        
        Args:
            template_id: ID of the template to retrieve
            
        Returns:
            Template data if found, None otherwise
            
        Raises:
            PyMongoError: If there's an error communicating with MongoDB
        """
        try:
            template_data = self._collection.find_one({"id": template_id})
            return template_data
        except PyMongoError as e:
            logger.error(f"Failed to retrieve template {template_id}: {e}")
            raise
    
    def update_template(
        self,
        template_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update an existing template.
        
        Args:
            template_id: ID of the template to update
            updates: Dictionary of fields to update
            
        Returns:
            True if the template was updated, False otherwise
            
        Raises:
            PyMongoError: If there's an error communicating with MongoDB
        """
        try:
            # Add updated timestamp
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = self._collection.update_one(
                {"id": template_id},
                {"$set": updates}
            )
            
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to update template {template_id}: {e}")
            raise
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.
        
        Args:
            template_id: ID of the template to delete
            
        Returns:
            True if the template was deleted, False otherwise
            
        Raises:
            PyMongoError: If there's an error communicating with MongoDB
        """
        try:
            result = self._collection.delete_one({"id": template_id})
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to delete template {template_id}: {e}")
            raise
    
    def list_templates(
        self,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 50,
        sort_by: str = "created_at",
        sort_direction: int = DESCENDING
    ) -> List[Dict[str, Any]]:
        """
        List templates with optional filtering and sorting.
        
        Args:
            tags: Optional list of tags to filter by
            skip: Number of templates to skip (pagination)
            limit: Maximum number of templates to return
            sort_by: Field to sort by
            sort_direction: Sort direction (ASCENDING or DESCENDING)
            
        Returns:
            List of templates matching the criteria
            
        Raises:
            PyMongoError: If there's an error communicating with MongoDB
        """
        try:
            query = {}
            
            if tags:
                query["tags"] = {"$all": tags}
            
            cursor = self._collection.find(query)
            cursor = cursor.sort(sort_by, sort_direction)
            cursor = cursor.skip(skip).limit(limit)
            
            return list(cursor)
        except PyMongoError as e:
            logger.error(f"Failed to list templates: {e}")
            raise
    
    def count_templates(self, tags: Optional[List[str]] = None) -> int:
        """
        Count templates with optional filtering.
        
        Args:
            tags: Optional list of tags to filter by
            
        Returns:
            Number of templates matching the criteria
            
        Raises:
            PyMongoError: If there's an error communicating with MongoDB
        """
        try:
            query = {}
            
            if tags:
                query["tags"] = {"$all": tags}
            
            return self._collection.count_documents(query)
        except PyMongoError as e:
            logger.error(f"Failed to count templates: {e}")
            raise
    
    def close(self) -> None:
        """Close the MongoDB client connection."""
        if self._client:
            self._client.close() 