"""
User Insight Repository

Repository for managing UserInsight documents in MongoDB.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

from ..models.user_insight import UserInsight, Topic, Subtopic

logger = logging.getLogger(__name__)


class UserInsightRepository:
    """Repository for managing UserInsight documents in MongoDB."""

    def __init__(self, mongo_client: AsyncIOMotorClient = None, db_name: str = "user_insights"):
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
            logger.info(f"UserInsightRepository initialized with database {self.db_name}")
        else:
            logger.error("No MongoDB client provided for UserInsightRepository")
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
        collection_name = f'insights_{tenant_id}'
        return self.db[collection_name]
    
    async def find_by_id(self, user_id: str, tenant_id: str) -> Optional[UserInsight]:
        """
        Find a UserInsight by user ID.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            
        Returns:
            UserInsight if found, None otherwise
        """
        collection = self._get_collection(tenant_id)
        data = await collection.find_one({"user_id": user_id})
        
        if data:
            return UserInsight.from_dict(data)
        return None
    
    async def find_users_by_topic(
        self, 
        topic_name: str, 
        filter_criteria: Dict[str, Any],
        page: int = 1, 
        page_size: int = 20,
        tenant_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Find all users with a specific topic and their associated data.
        
        Args:
            topic_name: Topic name to search for
            filter_criteria: Additional filter criteria
            page: Page number
            page_size: Page size
            tenant_id: Tenant identifier
            
        Returns:
            List of users with their topic data
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for find_users_by_topic")
        
        collection = self._get_collection(tenant_id)
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
        
        try:
            results = await collection.aggregate(pipeline).to_list(length=page_size)
            logger.info(f"Found {len(results)} users with topic '{topic_name}'")
            return results
        except Exception as e:
            logger.error(f"Error finding users by topic: {e}")
            raise
    
    async def get_topic_across_users(self, topic_name: str, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get a specific topic across all users.
        
        Args:
            topic_name: Topic name to search for
            tenant_id: Tenant identifier
            
        Returns:
            List of users with the specified topic
        """
        collection = self._get_collection(tenant_id)
        
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
        
        try:
            results = await collection.aggregate(pipeline).to_list(length=None)
            logger.info(f"Found topic '{topic_name}' across {len(results)} users")
            return results
        except Exception as e:
            logger.error(f"Error getting topic across users: {e}")
            raise
    
    async def save(self, insight: UserInsight) -> None:
        """
        Save a UserInsight document.
        
        Args:
            insight: UserInsight to save
        """
        if not insight.tenant_id:
            raise ValueError("insight.tenant_id is required")
        
        collection = self._get_collection(insight.tenant_id)
        
        try:
            await collection.update_one(
                {"user_id": insight.user_id},
                {"$set": insight.to_dict()},
                upsert=True
            )
            logger.info(f"Saved insight for user {insight.user_id}")
        except Exception as e:
            logger.error(f"Error saving insight: {e}")
            raise
    
    async def delete(self, user_id: str, tenant_id: str) -> None:
        """
        Delete a UserInsight by user ID.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
        """
        collection = self._get_collection(tenant_id)
        
        try:
            result = await collection.delete_one({"user_id": user_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted insight for user {user_id}")
            else:
                logger.warning(f"No insight found to delete for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting insight: {e}")
            raise
    
    async def update_topic(self, user_id: str, tenant_id: str, topic_id: str, topic_data: Dict[str, Any]) -> None:
        """
        Update a specific topic for a user.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            topic_id: Topic identifier
            topic_data: Topic data to update
        """
        try:
            # Find the user insight
            insight = await self.find_by_id(user_id, tenant_id)
            if not insight:
                logger.warning(f"No insight found for user {user_id}")
                return
            
            # Find and update the topic
            topic = insight.get_topic(topic_id)
            if not topic:
                logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
                return
            
            # Update topic properties
            for key, value in topic_data.items():
                if key != 'topic_id' and hasattr(topic, key):
                    setattr(topic, key, value)
            
            # Save the updated insight
            await self.save(insight)
            logger.info(f"Updated topic {topic_id} for user {user_id}")
        except Exception as e:
            logger.error(f"Error updating topic: {e}")
            raise
    
    async def update_subtopic(
        self, 
        user_id: str, 
        tenant_id: str, 
        topic_id: str, 
        subtopic_id: str, 
        subtopic_data: Dict[str, Any]
    ) -> None:
        """
        Update a specific subtopic for a user.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            topic_id: Topic identifier
            subtopic_id: Subtopic identifier
            subtopic_data: Subtopic data to update
        """
        try:
            # Find the user insight
            insight = await self.find_by_id(user_id, tenant_id)
            if not insight:
                logger.warning(f"No insight found for user {user_id}")
                return
            
            # Find the topic
            topic = insight.get_topic(topic_id)
            if not topic:
                logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
                return
            
            # Find and update the subtopic
            subtopic = topic.get_subtopic(subtopic_id)
            if not subtopic:
                logger.warning(f"No subtopic found with ID {subtopic_id} in topic {topic_id} for user {user_id}")
                return
            
            # Update subtopic content
            if 'content' in subtopic_data:
                subtopic.update_content(subtopic_data['content'])
            
            # Update other properties
            for key, value in subtopic_data.items():
                if key not in ['subtopic_id', 'content'] and hasattr(subtopic, key):
                    setattr(subtopic, key, value)
            
            # Save the updated insight
            await self.save(insight)
            logger.info(f"Updated subtopic {subtopic_id} in topic {topic_id} for user {user_id}")
        except Exception as e:
            logger.error(f"Error updating subtopic: {e}")
            raise
    
    async def get_all_tenants(self) -> List[str]:
        """
        Get all tenant IDs that have user insights.
        
        Returns:
            List of tenant IDs
        """
        try:
            # Extract tenant IDs from collection names
            collection_names = await self.db.list_collection_names()
            tenant_ids = []
            
            for name in collection_names:
                if name.startswith('insights_'):
                    tenant_id = name[9:]  # Remove 'insights_' prefix
                    tenant_ids.append(tenant_id)
            
            logger.info(f"Found {len(tenant_ids)} tenants with user insights")
            return tenant_ids
        except Exception as e:
            logger.error(f"Error getting all tenants: {e}")
            raise
    
    async def find_all_for_tenant(self, tenant_id: str) -> List[UserInsight]:
        """
        Find all UserInsights for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            List of UserInsight objects
        """
        collection = self._get_collection(tenant_id)
        
        try:
            cursor = collection.find({})
            insights = []
            
            async for document in cursor:
                insights.append(UserInsight.from_dict(document))
            
            logger.info(f"Found {len(insights)} insights for tenant {tenant_id}")
            return insights
        except Exception as e:
            logger.error(f"Error finding all insights for tenant: {e}")
            raise 