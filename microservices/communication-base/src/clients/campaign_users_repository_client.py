"""
Client for interacting with the campaign users repository.
Handles campaign-specific user data storage and retrieval.
"""

import logging
import aiohttp
import json
from typing import Dict, Any, Optional, List

from src.config.config_inheritance import ConfigInheritance

class CampaignUsersRepositoryClient:
    """
    Client for the campaign users repository.
    Manages persistent storage of campaign-specific user data.
    """
    
    def __init__(self):
        """Initialize the campaign users repository client."""
        self.config_inheritance = ConfigInheritance()
        self.logger = logging.getLogger(__name__)
        self.base_config = self.config_inheritance.get_base_config()
        self.base_url = self.base_config.get("repository.campaign_users.url", "http://campaign-users-repository/api/v1")
    
    async def get_campaign_user(self, user_id: str, campaign_id: str) -> Dict[str, Any]:
        """
        Get a user's campaign-specific data.
        
        Args:
            user_id: The user ID
            campaign_id: The campaign ID
            
        Returns:
            Campaign-specific user data
        """
        url = f"{self.base_url}/campaigns/{campaign_id}/users/{user_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        self.logger.info(f"User {user_id} not found in campaign {campaign_id}")
                        return {}
                    else:
                        self.logger.error(f"Error retrieving campaign user {user_id}: {response.status}")
                        return {}
        except Exception as e:
            self.logger.error(f"Error connecting to campaign repository: {e}")
            return {}
    
    async def create_campaign_user(self, user_id: str, campaign_id: str, user_data: Dict[str, Any]) -> bool:
        """
        Create a new user in a campaign.
        
        Args:
            user_id: The user ID
            campaign_id: The campaign ID
            user_data: The user data
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/campaigns/{campaign_id}/users"
        
        # Add user_id to the data
        data = user_data.copy()
        data["user_id"] = user_id
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status in (200, 201):
                        return True
                    else:
                        self.logger.error(f"Error creating campaign user {user_id}: {response.status}")
                        return False
        except Exception as e:
            self.logger.error(f"Error connecting to campaign repository: {e}")
            return False
    
    async def update_campaign_user_profile(
        self, user_id: str, campaign_id: str, profile_data: Dict[str, Any]
    ) -> bool:
        """
        Update a user's campaign-specific profile.
        
        Args:
            user_id: The user ID
            campaign_id: The campaign ID
            profile_data: The profile data to update
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/campaigns/{campaign_id}/users/{user_id}/profile"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=profile_data) as response:
                    if response.status in (200, 204):
                        return True
                    elif response.status == 404:
                        # User not found in campaign, create instead
                        return await self.create_campaign_user(user_id, campaign_id, {"profile": profile_data})
                    else:
                        self.logger.error(f"Error updating campaign user {user_id} profile: {response.status}")
                        return False
        except Exception as e:
            self.logger.error(f"Error connecting to campaign repository: {e}")
            return False
    
    async def store_campaign_conversation_metadata(
        self, user_id: str, session_id: str, campaign_id: str, metadata: Dict[str, Any]
    ) -> bool:
        """
        Store campaign conversation metadata.
        
        Args:
            user_id: The user ID
            session_id: The session ID
            campaign_id: The campaign ID
            metadata: The metadata to store
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/campaigns/{campaign_id}/users/{user_id}/conversations/{session_id}"
        
        # Add session_id and campaign_id to the metadata
        data = metadata.copy()
        data["session_id"] = session_id
        data["campaign_id"] = campaign_id
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status in (200, 201):
                        return True
                    else:
                        self.logger.error(f"Error storing campaign conversation metadata: {response.status}")
                        return False
        except Exception as e:
            self.logger.error(f"Error connecting to campaign repository: {e}")
            return False
    
    async def get_campaign_conversation_metadata(
        self, user_id: str, session_id: str, campaign_id: str
    ) -> Dict[str, Any]:
        """
        Get campaign conversation metadata.
        
        Args:
            user_id: The user ID
            session_id: The session ID
            campaign_id: The campaign ID
            
        Returns:
            Campaign conversation metadata
        """
        url = f"{self.base_url}/campaigns/{campaign_id}/users/{user_id}/conversations/{session_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        self.logger.info(f"Campaign conversation {session_id} not found")
                        return {}
                    else:
                        self.logger.error(f"Error retrieving campaign conversation metadata: {response.status}")
                        return {}
        except Exception as e:
            self.logger.error(f"Error connecting to campaign repository: {e}")
            return {}
    
    async def get_user_campaign_conversations(
        self, user_id: str, campaign_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get a user's conversations for a specific campaign.
        
        Args:
            user_id: The user ID
            campaign_id: The campaign ID
            limit: Maximum number of conversations to retrieve
            
        Returns:
            List of campaign conversation metadata
        """
        url = f"{self.base_url}/campaigns/{campaign_id}/users/{user_id}/conversations"
        params = {"limit": limit}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        self.logger.info(f"No campaign conversations found")
                        return []
                    else:
                        self.logger.error(f"Error retrieving campaign conversations: {response.status}")
                        return []
        except Exception as e:
            self.logger.error(f"Error connecting to campaign repository: {e}")
            return []
    
    async def get_campaign_users(self, campaign_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get users for a specific campaign.
        
        Args:
            campaign_id: The campaign ID
            limit: Maximum number of users to retrieve
            offset: Offset for pagination
            
        Returns:
            List of campaign users
        """
        url = f"{self.base_url}/campaigns/{campaign_id}/users"
        params = {"limit": limit, "offset": offset}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        self.logger.info(f"No users found for campaign {campaign_id}")
                        return []
                    else:
                        self.logger.error(f"Error retrieving campaign users: {response.status}")
                        return []
        except Exception as e:
            self.logger.error(f"Error connecting to campaign repository: {e}")
            return [] 