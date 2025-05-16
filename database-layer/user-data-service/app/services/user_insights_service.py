"""
User Insights Service

This service manages the business logic for user insights in the database.
It provides methods for CRUD operations and querying insights by various criteria.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from pymongo.errors import PyMongoError
from pymongo.database import Database
from pymongo.collection import Collection

from app.models.user_insight import UserInsight, Topic, Subtopic

logger = logging.getLogger(__name__)

class UserInsightsService:
    """
    Service for managing user insights in the database.
    
    This service provides methods for creating, retrieving, updating, and deleting
    user insights, as well as specialized queries for topics and subtopics.
    """
    
    def __init__(self, db: Database = None, collection: Collection = None):
        """
        Initialize the user insights service.
        
        Args:
            db: MongoDB database instance
            collection: MongoDB collection instance
        """
        self.db = db
        self.collection = collection
    
    def initialize(self, collection: Collection = None):
        """
        Initialize the database collection for user insights.
        
        Args:
            collection: MongoDB collection for user insights
            
        Returns:
            True if initialization is successful, False otherwise
        """
        try:
            if collection:
                self.collection = collection
                
            # Create indexes for efficient querying if not already exists
            if self.collection:
                self.collection.create_index("user_id", unique=True)
                self.collection.create_index("tenant_id")
                self.collection.create_index("topics.name")
                
                logger.info(f"UserInsightsService initialized with collection {self.collection.name}")
                return True
            else:
                logger.error("No collection provided to UserInsightsService")
                return False
        except PyMongoError as e:
            logger.error(f"Failed to initialize user insights service: {str(e)}")
            return False
    
    def get_user_insight(self, user_id: str, tenant_id: str) -> Optional[UserInsight]:
        """
        Get a user insight by user ID.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            
        Returns:
            UserInsight if found, None otherwise
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return None
            
        try:
            document = self.collection.find_one({"user_id": user_id})
            
            if document:
                return UserInsight.from_dict(document)
            return None
        except PyMongoError as e:
            logger.error(f"Failed to get insight for user {user_id}: {str(e)}")
            return None
    
    def create_user_insight(self, user_id: str, tenant_id: str, metadata: Dict[str, Any] = None) -> Optional[UserInsight]:
        """
        Create a new user insight.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            metadata: Additional metadata
            
        Returns:
            Created UserInsight if successful, None otherwise
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return None
            
        try:
            # Check if the user insight already exists
            existing = self.collection.find_one({"user_id": user_id})
            if existing:
                logger.warning(f"User insight already exists for user {user_id}")
                return UserInsight.from_dict(existing)
            
            # Create a new user insight
            insight = UserInsight(user_id=user_id, tenant_id=tenant_id)
            
            if metadata:
                insight.update_metadata(metadata)
            
            # Save to the database
            self.collection.insert_one(insight.to_dict())
            logger.info(f"Created user insight for user {user_id}")
            
            return insight
        except PyMongoError as e:
            logger.error(f"Failed to create insight for user {user_id}: {str(e)}")
            return None
    
    def update_metadata(self, user_id: str, tenant_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a user insight.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            metadata: Metadata to update
            
        Returns:
            True if update is successful, False otherwise
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return False
            
        try:
            # Get the current document
            document = self.collection.find_one({"user_id": user_id})
            if not document:
                logger.warning(f"No insight found for user {user_id}")
                return False
            
            # Update the metadata
            current_metadata = document.get("metadata", {})
            current_metadata.update(metadata)
            
            # Save back to the database
            result = self.collection.update_one(
                {"user_id": user_id},
                {"$set": {"metadata": current_metadata}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated metadata for user {user_id}")
                return True
            return False
        except PyMongoError as e:
            logger.error(f"Failed to update metadata for user {user_id}: {str(e)}")
            return False
    
    def add_topic(self, user_id: str, tenant_id: str, name: str, description: str) -> Optional[Dict[str, Any]]:
        """
        Add a topic to a user insight.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            name: Topic name
            description: Topic description
            
        Returns:
            Topic data if successful, None otherwise
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return None
            
        try:
            # Get the current document
            document = self.collection.find_one({"user_id": user_id})
            if not document:
                logger.warning(f"No insight found for user {user_id}")
                return None
            
            # Check if a topic with the same name already exists
            topics = document.get("topics", [])
            for topic in topics:
                if topic.get("name") == name:
                    logger.warning(f"Topic '{name}' already exists for user {user_id}")
                    return topic
            
            # Create a new topic
            topic_id = f"t_{str(uuid.uuid4())[:8]}"
            topic = {
                "topic_id": topic_id,
                "name": name,
                "description": description,
                "subtopics": [],
                "created_at": Topic(topic_id=topic_id, name=name, description=description).created_at.isoformat(),
                "updated_at": Topic(topic_id=topic_id, name=name, description=description).updated_at.isoformat()
            }
            
            # Add the topic to the document
            result = self.collection.update_one(
                {"user_id": user_id},
                {"$push": {"topics": topic}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Added topic '{name}' for user {user_id}")
                return topic
            return None
        except PyMongoError as e:
            logger.error(f"Failed to add topic for user {user_id}: {str(e)}")
            return None
    
    def update_topic(self, user_id: str, tenant_id: str, topic_id: str, topic_data: Dict[str, Any]) -> bool:
        """
        Update a topic in a user insight.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            topic_id: Topic identifier
            topic_data: Topic data to update
            
        Returns:
            True if update is successful, False otherwise
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return False
            
        try:
            # Build the update dict
            update_fields = {}
            for key, value in topic_data.items():
                if key not in ["topic_id", "subtopics", "created_at"]:
                    update_fields[f"topics.$.{key}"] = value
            
            # Add updated_at timestamp
            update_fields["topics.$.updated_at"] = Topic(
                topic_id=topic_id, 
                name="", 
                description=""
            ).updated_at.isoformat()
            
            # Update the topic
            result = self.collection.update_one(
                {
                    "user_id": user_id,
                    "topics.topic_id": topic_id
                },
                {"$set": update_fields}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated topic {topic_id} for user {user_id}")
                return True
            logger.warning(f"No changes made to topic {topic_id} for user {user_id}")
            return False
        except PyMongoError as e:
            logger.error(f"Failed to update topic {topic_id} for user {user_id}: {str(e)}")
            return False
    
    def delete_topic(self, user_id: str, tenant_id: str, topic_id: str) -> bool:
        """
        Delete a topic from a user insight.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            topic_id: Topic identifier
            
        Returns:
            True if deletion is successful, False otherwise
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return False
            
        try:
            result = self.collection.update_one(
                {"user_id": user_id},
                {"$pull": {"topics": {"topic_id": topic_id}}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Deleted topic {topic_id} for user {user_id}")
                return True
            logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
            return False
        except PyMongoError as e:
            logger.error(f"Failed to delete topic {topic_id} for user {user_id}: {str(e)}")
            return False
    
    def add_subtopic(
        self, 
        user_id: str, 
        tenant_id: str, 
        topic_id: str,
        name: str, 
        content: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Add a subtopic to a topic.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            topic_id: Topic identifier
            name: Subtopic name
            content: Subtopic content
            
        Returns:
            Subtopic data if successful, None otherwise
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return None
            
        try:
            # Get the current document
            document = self.collection.find_one(
                {
                    "user_id": user_id,
                    "topics.topic_id": topic_id
                }
            )
            
            if not document:
                logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
                return None
            
            # Create a new subtopic
            subtopic_id = f"st_{str(uuid.uuid4())[:8]}"
            subtopic = {
                "subtopic_id": subtopic_id,
                "name": name,
                "content": content,
                "created_at": Subtopic(subtopic_id=subtopic_id, name=name, content=content).created_at.isoformat(),
                "updated_at": Subtopic(subtopic_id=subtopic_id, name=name, content=content).updated_at.isoformat()
            }
            
            # Find the index of the topic
            topics = document.get("topics", [])
            topic_index = None
            
            for i, topic in enumerate(topics):
                if topic.get("topic_id") == topic_id:
                    topic_index = i
                    break
            
            if topic_index is None:
                logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
                return None
            
            # Add the subtopic to the topic
            result = self.collection.update_one(
                {
                    "user_id": user_id,
                    "topics.topic_id": topic_id
                },
                {"$push": {f"topics.{topic_index}.subtopics": subtopic}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Added subtopic '{name}' to topic {topic_id} for user {user_id}")
                return subtopic
            return None
        except PyMongoError as e:
            logger.error(f"Failed to add subtopic to topic {topic_id} for user {user_id}: {str(e)}")
            return None
    
    def update_subtopic(
        self, 
        user_id: str, 
        tenant_id: str, 
        topic_id: str,
        subtopic_id: str, 
        subtopic_data: Dict[str, Any]
    ) -> bool:
        """
        Update a subtopic in a topic.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            topic_id: Topic identifier
            subtopic_id: Subtopic identifier
            subtopic_data: Subtopic data to update
            
        Returns:
            True if update is successful, False otherwise
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return False
            
        try:
            # Get the current document
            document = self.collection.find_one(
                {
                    "user_id": user_id,
                    "topics.topic_id": topic_id
                }
            )
            
            if not document:
                logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
                return False
            
            # Find the topic and subtopic
            topics = document.get("topics", [])
            for i, topic in enumerate(topics):
                if topic.get("topic_id") == topic_id:
                    subtopics = topic.get("subtopics", [])
                    for j, subtopic in enumerate(subtopics):
                        if subtopic.get("subtopic_id") == subtopic_id:
                            # Update the subtopic
                            update_fields = {}
                            for key, value in subtopic_data.items():
                                if key not in ["subtopic_id", "created_at"]:
                                    update_fields[f"topics.{i}.subtopics.{j}.{key}"] = value
                            
                            # Add updated_at timestamp
                            update_fields[f"topics.{i}.subtopics.{j}.updated_at"] = Subtopic(
                                subtopic_id=subtopic_id,
                                name="",
                                content={}
                            ).updated_at.isoformat()
                            
                            result = self.collection.update_one(
                                {"user_id": user_id},
                                {"$set": update_fields}
                            )
                            
                            if result.modified_count > 0:
                                logger.info(f"Updated subtopic {subtopic_id} in topic {topic_id} for user {user_id}")
                                return True
                            logger.warning(f"No changes made to subtopic {subtopic_id} in topic {topic_id} for user {user_id}")
                            return False
            
            logger.warning(f"No subtopic found with ID {subtopic_id} in topic {topic_id} for user {user_id}")
            return False
        except PyMongoError as e:
            logger.error(f"Failed to update subtopic {subtopic_id} in topic {topic_id} for user {user_id}: {str(e)}")
            return False
    
    def delete_subtopic(self, user_id: str, tenant_id: str, topic_id: str, subtopic_id: str) -> bool:
        """
        Delete a subtopic from a topic.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            topic_id: Topic identifier
            subtopic_id: Subtopic identifier
            
        Returns:
            True if deletion is successful, False otherwise
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return False
            
        try:
            # Find the topic and remove the subtopic
            result = self.collection.update_one(
                {
                    "user_id": user_id,
                    "topics.topic_id": topic_id
                },
                {"$pull": {"topics.$.subtopics": {"subtopic_id": subtopic_id}}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Deleted subtopic {subtopic_id} from topic {topic_id} for user {user_id}")
                return True
            logger.warning(f"No subtopic found with ID {subtopic_id} in topic {topic_id} for user {user_id}")
            return False
        except PyMongoError as e:
            logger.error(f"Failed to delete subtopic {subtopic_id} from topic {topic_id} for user {user_id}: {str(e)}")
            return False
    
    def delete_user_insight(self, user_id: str, tenant_id: str) -> bool:
        """
        Delete a user insight.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            
        Returns:
            True if deletion is successful, False otherwise
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return False
            
        try:
            result = self.collection.delete_one({"user_id": user_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted user insight for user {user_id}")
                return True
            logger.warning(f"No insight found for user {user_id}")
            return False
        except PyMongoError as e:
            logger.error(f"Failed to delete insight for user {user_id}: {str(e)}")
            return False
    
    def find_users_by_topic(
        self, 
        topic_name: str, 
        tenant_id: str,
        filter_criteria: Dict[str, Any] = None,
        page: int = 1, 
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find all users with a specific topic.
        
        Args:
            topic_name: Topic name to search for
            tenant_id: Tenant identifier
            filter_criteria: Additional filter criteria
            page: Page number
            page_size: Page size
            
        Returns:
            List of users with their topic data
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return []
            
        try:
            skip = (page - 1) * page_size
            
            # Build the match criteria
            match_criteria = {"topics.name": topic_name}
            if filter_criteria:
                match_criteria.update(filter_criteria)
            
            # Pipeline for aggregation
            pipeline = [
                {"$match": match_criteria},
                {"$project": {
                    "user_id": 1,
                    "tenant_id": 1,
                    "metadata": 1,
                    "topic": {
                        "$filter": {
                            "input": "$topics",
                            "as": "topic",
                            "cond": {"$eq": ["$$topic.name", topic_name]}
                        }
                    }
                }},
                {"$skip": skip},
                {"$limit": page_size}
            ]
            
            results = list(self.collection.aggregate(pipeline))
            logger.info(f"Found {len(results)} users with topic '{topic_name}'")
            return results
        except PyMongoError as e:
            logger.error(f"Failed to find users by topic: {str(e)}")
            return []
    
    def get_topic_across_users(self, topic_name: str, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get a specific topic across all users.
        
        Args:
            topic_name: Topic name to search for
            tenant_id: Tenant identifier
            
        Returns:
            List of users with the specified topic
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return []
            
        try:
            # Pipeline for aggregation
            pipeline = [
                {"$match": {"topics.name": topic_name}},
                {"$project": {
                    "user_id": 1,
                    "topic": {
                        "$filter": {
                            "input": "$topics",
                            "as": "topic",
                            "cond": {"$eq": ["$$topic.name", topic_name]}
                        }
                    }
                }}
            ]
            
            results = list(self.collection.aggregate(pipeline))
            logger.info(f"Found topic '{topic_name}' across {len(results)} users")
            return results
        except PyMongoError as e:
            logger.error(f"Failed to get topic across users: {str(e)}")
            return []
    
    def get_all_tenants(self) -> List[str]:
        """
        Get all tenant IDs that have user insights.
        
        Returns:
            List of tenant IDs
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return []
            
        try:
            results = self.collection.distinct("tenant_id")
            logger.info(f"Found {len(results)} tenants with user insights")
            return results
        except PyMongoError as e:
            logger.error(f"Failed to get all tenants: {str(e)}")
            return []
    
    def find_all_for_tenant(self, tenant_id: str, page: int = 1, page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Find all UserInsights for a tenant with pagination.
        
        Args:
            tenant_id: Tenant identifier
            page: Page number
            page_size: Page size
            
        Returns:
            List of UserInsight data
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return []
            
        try:
            skip = (page - 1) * page_size
            
            cursor = self.collection.find({"tenant_id": tenant_id}).skip(skip).limit(page_size)
            results = []
            
            for document in cursor:
                results.append(document)
            
            logger.info(f"Found {len(results)} insights for tenant {tenant_id} (page {page})")
            return results
        except PyMongoError as e:
            logger.error(f"Failed to find all insights for tenant: {str(e)}")
            return [] 