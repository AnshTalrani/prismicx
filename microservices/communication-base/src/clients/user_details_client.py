"""
Client for interacting with the User Details microservice.
Provides access to user insights by topic.
"""

import logging
import aiohttp
import json
from typing import Dict, List, Any, Optional

from src.config.config_inheritance import ConfigInheritance

class UserDetailsClient:
    """
    Client for the User Details microservice.
    Provides access to user insights by topic.
    """
    
    def __init__(self):
        """Initialize the User Details client."""
        self.config_inheritance = ConfigInheritance()
        self.logger = logging.getLogger(__name__)
        self.base_config = self.config_inheritance.get_base_config()
        self.base_url = self.base_config.get("services.user_details.url", "http://user-details-service/api/v1")
        self._topics_cache = None
    
    async def get_available_topics(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get a list of available topics that can be queried.
        
        Args:
            force_refresh: Whether to force a refresh of the cache
            
        Returns:
            List of available topics
        """
        # Use cached topics if available and not forcing refresh
        if self._topics_cache is not None and not force_refresh:
            return self._topics_cache
        
        url = f"{self.base_url}/config/default-topics"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        topics = await response.json()
                        self._topics_cache = topics
                        return topics
                    else:
                        self.logger.error(f"Error retrieving available topics: {response.status}")
                        return []
        except Exception as e:
            self.logger.error(f"Error connecting to User Details service: {e}")
            return []
    
    async def get_topic_insights(self, user_id: str, topic_id: str) -> Dict[str, Any]:
        """
        Get insights for a specific topic and user.
        
        Args:
            user_id: The user ID
            topic_id: The topic ID
            
        Returns:
            Topic insights for the user
        """
        url = f"{self.base_url}/insights/{user_id}/topics/{topic_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        self.logger.info(f"No insights found for user {user_id} and topic {topic_id}")
                        return {}
                    else:
                        self.logger.error(f"Error retrieving topic insights: {response.status}")
                        return {}
        except Exception as e:
            self.logger.error(f"Error connecting to User Details service: {e}")
            return {}
    
    async def get_all_user_insights(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all available insights for a user across all topics.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dictionary of topic IDs to topic insights
        """
        # First, get available topics
        topics = await self.get_available_topics()
        
        if not topics:
            return {}
        
        # Then, get insights for each topic
        insights = {}
        for topic in topics:
            topic_id = topic.get("id")
            if not topic_id:
                continue
                
            topic_insights = await self.get_topic_insights(user_id, topic_id)
            if topic_insights:
                insights[topic_id] = topic_insights
        
        return insights
    
    async def get_relevant_insights(
        self, user_id: str, bot_type: str, query: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get insights relevant to a bot type and optional query.
        
        Args:
            user_id: The user ID
            bot_type: The type of bot
            query: Optional query to filter relevant topics
            
        Returns:
            Dictionary of topic IDs to topic insights
        """
        # Get bot-specific configuration
        config = self.config_inheritance.get_config(bot_type)
        relevant_topics = config.get("user_details.relevant_topics", [])
        
        if not relevant_topics:
            self.logger.info(f"No relevant topics configured for bot type {bot_type}")
            return {}
        
        # Get insights for relevant topics
        insights = {}
        for topic_id in relevant_topics:
            topic_insights = await self.get_topic_insights(user_id, topic_id)
            if topic_insights:
                insights[topic_id] = topic_insights
        
        return insights

# Global instance
user_details_client = UserDetailsClient() 