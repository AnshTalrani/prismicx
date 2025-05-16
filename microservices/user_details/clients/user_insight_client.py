import logging
from typing import Dict, Any, List, Optional

from .database_layer_client import DatabaseLayerClient
from models.user_insight import UserInsight, Topic, Subtopic

logger = logging.getLogger(__name__)

class UserInsightClient:
    """
    Client for interacting with the User Insight APIs of the Database Layer service.
    Handles all user insight-related operations through the database layer.
    """
    
    def __init__(self, client: Optional[DatabaseLayerClient] = None):
        """
        Initialize the user insight client.
        
        Args:
            client: DatabaseLayerClient instance (creates a new one if not provided)
        """
        self.client = client or DatabaseLayerClient()
        self.base_path = "/api/insights"
        logger.info("Initialized UserInsightClient")
    
    async def find_by_id(self, user_id: str, tenant_id: str) -> Optional[UserInsight]:
        """
        Find a UserInsight by user ID.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
        
        Returns:
            UserInsight object or None if not found
        """
        try:
            data = await self.client.get(f"{self.base_path}/{user_id}", tenant_id=tenant_id)
            return UserInsight.from_dict(data) if data else None
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
        """
        Find all users with a specific topic and their associated data.
        
        Args:
            topic_name: Name of the topic to search for
            filter_criteria: Additional filter criteria
            page: Page number
            page_size: Page size
            tenant_id: Tenant identifier
        
        Returns:
            List of user insights with the specified topic
        """
        try:
            params = {
                "page": page,
                "page_size": page_size,
                **filter_criteria
            }
            data = await self.client.get(
                f"{self.base_path}/topics/{topic_name}/users", 
                params=params,
                tenant_id=tenant_id
            )
            return data
        except Exception as e:
            logger.error(f"Error finding users by topic: {e}")
            return []
    
    async def save(self, insight: UserInsight) -> None:
        """
        Save a UserInsight document.
        
        Args:
            insight: UserInsight object to save
        """
        if not insight.tenant_id:
            raise ValueError("insight.tenant_id is required")
        
        try:
            # Check if the insight exists
            existing = await self.find_by_id(insight.user_id, insight.tenant_id)
            
            if existing:
                # Update existing insight metadata
                await self.client.put(
                    f"{self.base_path}/{insight.user_id}/metadata",
                    data={"metadata": insight.metadata},
                    tenant_id=insight.tenant_id
                )
                
                # Process each topic in the insight
                for topic in insight.topics:
                    existing_topic = next((t for t in existing.topics if t.topic_id == topic.topic_id), None)
                    
                    if existing_topic:
                        # Update existing topic
                        await self.client.put(
                            f"{self.base_path}/{insight.user_id}/topics/{topic.topic_id}",
                            data={"name": topic.name, "description": topic.description},
                            tenant_id=insight.tenant_id
                        )
                        
                        # Process subtopics
                        for subtopic in topic.subtopics:
                            existing_subtopic = next(
                                (s for s in existing_topic.subtopics if s.subtopic_id == subtopic.subtopic_id), 
                                None
                            )
                            
                            if existing_subtopic:
                                # Update existing subtopic
                                await self.client.put(
                                    f"{self.base_path}/{insight.user_id}/topics/{topic.topic_id}/subtopics/{subtopic.subtopic_id}",
                                    data={"name": subtopic.name, "content": subtopic.content},
                                    tenant_id=insight.tenant_id
                                )
                            else:
                                # Create new subtopic
                                await self.client.post(
                                    f"{self.base_path}/{insight.user_id}/topics/{topic.topic_id}/subtopics",
                                    data={"name": subtopic.name, "content": subtopic.content},
                                    tenant_id=insight.tenant_id
                                )
                    else:
                        # Create new topic
                        new_topic = await self.client.post(
                            f"{self.base_path}/{insight.user_id}/topics",
                            data={"name": topic.name, "description": topic.description},
                            tenant_id=insight.tenant_id
                        )
                        
                        topic_id = new_topic["topic_id"]
                        
                        # Create all subtopics for the new topic
                        for subtopic in topic.subtopics:
                            await self.client.post(
                                f"{self.base_path}/{insight.user_id}/topics/{topic_id}/subtopics",
                                data={"name": subtopic.name, "content": subtopic.content},
                                tenant_id=insight.tenant_id
                            )
            else:
                # Create new insight
                await self.client.post(
                    f"{self.base_path}/{insight.user_id}",
                    data={"metadata": insight.metadata},
                    tenant_id=insight.tenant_id
                )
                
                # Create topics and subtopics
                for topic in insight.topics:
                    new_topic = await self.client.post(
                        f"{self.base_path}/{insight.user_id}/topics",
                        data={"name": topic.name, "description": topic.description},
                        tenant_id=insight.tenant_id
                    )
                    
                    topic_id = new_topic["topic_id"]
                    
                    # Create subtopics
                    for subtopic in topic.subtopics:
                        await self.client.post(
                            f"{self.base_path}/{insight.user_id}/topics/{topic_id}/subtopics",
                            data={"name": subtopic.name, "content": subtopic.content},
                            tenant_id=insight.tenant_id
                        )
        
        except Exception as e:
            logger.error(f"Error saving user insight: {e}")
            raise
    
    async def delete(self, user_id: str, tenant_id: str) -> None:
        """
        Delete a UserInsight by user ID.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
        """
        try:
            await self.client.delete(f"{self.base_path}/{user_id}", tenant_id=tenant_id)
        except Exception as e:
            logger.error(f"Error deleting user insight: {e}")
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
            await self.client.put(
                f"{self.base_path}/{user_id}/topics/{topic_id}",
                data=topic_data,
                tenant_id=tenant_id
            )
        except Exception as e:
            logger.error(f"Error updating topic: {e}")
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
    
    async def find_all_for_tenant(self, tenant_id: str) -> List[UserInsight]:
        """
        Find all user insights for a tenant.
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            List of UserInsight objects
        """
        try:
            data = await self.client.get(f"{self.base_path}/tenant/{tenant_id}/insights", tenant_id=tenant_id)
            return [UserInsight.from_dict(item) for item in data]
        except Exception as e:
            logger.error(f"Error finding all insights for tenant: {e}")
            return []
    
    async def close(self):
        """Close the client connection."""
        await self.client.close() 