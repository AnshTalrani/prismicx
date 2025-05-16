"""
User Insight Service

Service layer for managing user insights.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient

from ..models.user_insight import UserInsight, Topic, Subtopic
from ..repositories.user_insight_repository import UserInsightRepository

logger = logging.getLogger(__name__)


class UserInsightService:
    """Service for managing user insights."""

    def __init__(self, mongo_client: AsyncIOMotorClient = None):
        """
        Initialize the service with MongoDB connection.
        
        Args:
            mongo_client: AsyncIOMotorClient instance
        """
        self.repository = UserInsightRepository(mongo_client)
    
    async def initialize(self, mongo_client: AsyncIOMotorClient = None):
        """
        Initialize the service with the MongoDB client.
        
        Args:
            mongo_client: AsyncIOMotorClient instance
        """
        await self.repository.initialize(mongo_client)
        logger.info("UserInsightService initialized")
    
    async def get_user_insight(self, user_id: str, tenant_id: str) -> Optional[UserInsight]:
        """
        Get a user insight by user ID.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            
        Returns:
            UserInsight if found, None otherwise
        """
        return await self.repository.find_by_id(user_id, tenant_id)
    
    async def create_user_insight(self, user_id: str, tenant_id: str, metadata: Dict[str, Any] = None) -> UserInsight:
        """
        Create a new user insight.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            metadata: Additional metadata
            
        Returns:
            Created UserInsight
        """
        insight = UserInsight(user_id=user_id, tenant_id=tenant_id)
        
        if metadata:
            insight.update_metadata(metadata)
        
        await self.repository.save(insight)
        logger.info(f"Created user insight for user {user_id}")
        return insight
    
    async def update_metadata(self, user_id: str, tenant_id: str, metadata: Dict[str, Any]) -> Optional[UserInsight]:
        """
        Update metadata for a user insight.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            metadata: Metadata to update
            
        Returns:
            Updated UserInsight if found, None otherwise
        """
        insight = await self.repository.find_by_id(user_id, tenant_id)
        
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return None
        
        insight.update_metadata(metadata)
        await self.repository.save(insight)
        logger.info(f"Updated metadata for user {user_id}")
        return insight
    
    async def add_topic(
        self, 
        user_id: str, 
        tenant_id: str, 
        name: str, 
        description: str
    ) -> Optional[Topic]:
        """
        Add a topic to a user insight.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            name: Topic name
            description: Topic description
            
        Returns:
            Created Topic if successful, None otherwise
        """
        insight = await self.repository.find_by_id(user_id, tenant_id)
        
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return None
        
        # Check if topic with same name already exists
        existing_topic = insight.get_topic_by_name(name)
        if existing_topic:
            logger.warning(f"Topic '{name}' already exists for user {user_id}")
            return existing_topic
        
        # Create and add the topic
        topic_id = f"t_{str(uuid.uuid4())[:8]}"
        topic = Topic(topic_id=topic_id, name=name, description=description)
        insight.add_topic(topic)
        
        await self.repository.save(insight)
        logger.info(f"Added topic '{name}' for user {user_id}")
        return topic
    
    async def update_topic(
        self, 
        user_id: str, 
        tenant_id: str, 
        topic_id: str, 
        topic_data: Dict[str, Any]
    ) -> Optional[Topic]:
        """
        Update a topic in a user insight.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            topic_id: Topic identifier
            topic_data: Topic data to update
            
        Returns:
            Updated Topic if successful, None otherwise
        """
        insight = await self.repository.find_by_id(user_id, tenant_id)
        
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return None
        
        topic = insight.get_topic(topic_id)
        if not topic:
            logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
            return None
        
        # Update topic properties
        for key, value in topic_data.items():
            if key != 'topic_id' and hasattr(topic, key):
                setattr(topic, key, value)
        
        await self.repository.save(insight)
        logger.info(f"Updated topic {topic_id} for user {user_id}")
        return topic
    
    async def delete_topic(self, user_id: str, tenant_id: str, topic_id: str) -> bool:
        """
        Delete a topic from a user insight.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            topic_id: Topic identifier
            
        Returns:
            True if successful, False otherwise
        """
        insight = await self.repository.find_by_id(user_id, tenant_id)
        
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return False
        
        topic = insight.get_topic(topic_id)
        if not topic:
            logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
            return False
        
        insight.remove_topic(topic_id)
        await self.repository.save(insight)
        logger.info(f"Deleted topic {topic_id} for user {user_id}")
        return True
    
    async def add_subtopic(
        self, 
        user_id: str, 
        tenant_id: str, 
        topic_id: str, 
        name: str, 
        content: Dict[str, Any]
    ) -> Optional[Subtopic]:
        """
        Add a subtopic to a topic.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            topic_id: Topic identifier
            name: Subtopic name
            content: Subtopic content
            
        Returns:
            Created Subtopic if successful, None otherwise
        """
        insight = await self.repository.find_by_id(user_id, tenant_id)
        
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return None
        
        topic = insight.get_topic(topic_id)
        if not topic:
            logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
            return None
        
        # Create and add the subtopic
        subtopic_id = f"st_{str(uuid.uuid4())[:8]}"
        subtopic = Subtopic(subtopic_id=subtopic_id, name=name, content=content)
        topic.add_subtopic(subtopic)
        
        await self.repository.save(insight)
        logger.info(f"Added subtopic '{name}' to topic {topic_id} for user {user_id}")
        return subtopic
    
    async def update_subtopic(
        self, 
        user_id: str, 
        tenant_id: str, 
        topic_id: str, 
        subtopic_id: str, 
        subtopic_data: Dict[str, Any]
    ) -> Optional[Subtopic]:
        """
        Update a subtopic in a topic.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            topic_id: Topic identifier
            subtopic_id: Subtopic identifier
            subtopic_data: Subtopic data to update
            
        Returns:
            Updated Subtopic if successful, None otherwise
        """
        await self.repository.update_subtopic(
            user_id=user_id,
            tenant_id=tenant_id,
            topic_id=topic_id,
            subtopic_id=subtopic_id,
            subtopic_data=subtopic_data
        )
        
        # Get the updated insight
        insight = await self.repository.find_by_id(user_id, tenant_id)
        if not insight:
            return None
        
        topic = insight.get_topic(topic_id)
        if not topic:
            return None
        
        return topic.get_subtopic(subtopic_id)
    
    async def delete_subtopic(self, user_id: str, tenant_id: str, topic_id: str, subtopic_id: str) -> bool:
        """
        Delete a subtopic from a topic.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            topic_id: Topic identifier
            subtopic_id: Subtopic identifier
            
        Returns:
            True if successful, False otherwise
        """
        insight = await self.repository.find_by_id(user_id, tenant_id)
        
        if not insight:
            logger.warning(f"No insight found for user {user_id}")
            return False
        
        topic = insight.get_topic(topic_id)
        if not topic:
            logger.warning(f"No topic found with ID {topic_id} for user {user_id}")
            return False
        
        subtopic = topic.get_subtopic(subtopic_id)
        if not subtopic:
            logger.warning(f"No subtopic found with ID {subtopic_id} in topic {topic_id}")
            return False
        
        topic.remove_subtopic(subtopic_id)
        await self.repository.save(insight)
        logger.info(f"Deleted subtopic {subtopic_id} from topic {topic_id} for user {user_id}")
        return True
    
    async def delete_user_insight(self, user_id: str, tenant_id: str) -> bool:
        """
        Delete a user insight.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.repository.delete(user_id, tenant_id)
            logger.info(f"Deleted user insight for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user insight: {e}")
            return False
    
    async def find_users_by_topic(
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
        return await self.repository.find_users_by_topic(
            topic_name=topic_name,
            filter_criteria=filter_criteria or {},
            page=page,
            page_size=page_size,
            tenant_id=tenant_id
        )
    
    async def get_topic_across_users(self, topic_name: str, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get a specific topic across all users.
        
        Args:
            topic_name: Topic name to search for
            tenant_id: Tenant identifier
            
        Returns:
            List of users with the specified topic
        """
        return await self.repository.get_topic_across_users(topic_name, tenant_id)
    
    async def get_all_tenants(self) -> List[str]:
        """
        Get all tenant IDs that have user insights.
        
        Returns:
            List of tenant IDs
        """
        return await self.repository.get_all_tenants()
    
    async def find_all_for_tenant(self, tenant_id: str) -> List[UserInsight]:
        """
        Find all UserInsights for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            List of UserInsight objects
        """
        return await self.repository.find_all_for_tenant(tenant_id) 