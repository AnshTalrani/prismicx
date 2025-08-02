import os
import logging
from typing import List, Dict, Any, Optional

from models.user_insight import UserInsight, Topic, Subtopic
from clients.user_insight_client import UserInsightClient

logger = logging.getLogger(__name__)


class UserInsightRepository:
    """Repository for managing UserInsight documents via the Database Layer."""

    def __init__(self):
        """Initialize the repository with the UserInsightClient."""
        logger.info("Initializing UserInsightRepository with Database Layer client")
        
        try:
            self.client = UserInsightClient()
            logger.info("Successfully connected to Database Layer User Insight service")
        except Exception as e:
            logger.error(f"Failed to initialize UserInsightClient: {e}")
            raise
    
    async def find_by_id(self, user_id: str, tenant_id: str) -> Optional[UserInsight]:
        """Find a UserInsight by userID."""
        try:
            return await self.client.find_by_id(user_id, tenant_id)
        except Exception as e:
            logger.error(f"Error finding user insight by ID: {e}")
            return None
    
    async def find_users_by_topic(
        self, 
        topic_name: str, 
        filter_criteria: Dict[str, Any],
        page: int = 1, 
        page_size: int = 20,
        tenant_id: str = None
    ) -> List[Dict[str, Any]]:
        """Find all users with a specific topic and their associated data."""
        if not tenant_id:
            raise ValueError("tenant_id is required for find_users_by_topic")
        
        try:
            return await self.client.find_users_by_topic(
                topic_name, 
                filter_criteria, 
                page, 
                page_size, 
                tenant_id
            )
        except Exception as e:
            logger.error(f"Error finding users by topic: {e}")
            return []
    
    async def get_topic_across_users(self, topic_name: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Get a specific topic across all users."""
        # This functionality is implemented through find_users_by_topic in the database layer
        try:
            return await self.client.find_users_by_topic(
                topic_name, 
                {}, 
                1,  # page
                100,  # page_size - using a larger size to get more results
                tenant_id
            )
        except Exception as e:
            logger.error(f"Error getting topic across users: {e}")
            return []
    
    async def save(self, insight: UserInsight) -> None:
        """Save a UserInsight document."""
        if not insight.tenant_id:
            raise ValueError("insight.tenant_id is required")
        
        try:
            await self.client.save(insight)
            logger.info(f"Saved insight for user {insight.user_id}")
        except Exception as e:
            logger.error(f"Error saving insight: {e}")
            raise
    
    async def delete(self, user_id: str, tenant_id: str) -> None:
        """Delete a UserInsight by userID."""
        try:
            await self.client.delete(user_id, tenant_id)
            logger.info(f"Deleted insight for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting insight: {e}")
            raise
    
    async def update_topic(self, user_id: str, tenant_id: str, topic_id: str, topic_data: Dict[str, Any]) -> None:
        """Update a specific topic for a user."""
        try:
            await self.client.update_topic(user_id, tenant_id, topic_id, topic_data)
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
        """Update a specific subtopic for a user."""
        try:
            # This operation is handled through the client's save method with detailed logic there
            # Get the current insight
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
            
            # Update subtopic properties
            for key, value in subtopic_data.items():
                if key != 'subtopic_id' and hasattr(subtopic, key):
                    setattr(subtopic, key, value)
            
            # Save the updated insight
            await self.save(insight)
            logger.info(f"Updated subtopic {subtopic_id} in topic {topic_id} for user {user_id}")
        except Exception as e:
            logger.error(f"Error updating subtopic: {e}")
            raise
    
    async def close(self):
        """Close the client connection."""
        await self.client.close()
        logger.info("Closed UserInsightClient connection")
    
    async def get_all_tenants(self) -> List[str]:
        """Get all tenant IDs."""
        try:
            return await self.client.get_all_tenants()
        except Exception as e:
            logger.error(f"Error getting all tenants: {e}")
            return []
    
    async def find_all_for_tenant(self, tenant_id: str) -> List[UserInsight]:
        """Find all user insights for a tenant."""
        try:
            return await self.client.find_all_for_tenant(tenant_id)
        except Exception as e:
            logger.error(f"Error finding all insights for tenant: {e}")
            return [] 