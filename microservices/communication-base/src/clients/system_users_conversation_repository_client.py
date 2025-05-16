"""
Client for interacting with the system users conversation repository.
Handles permanent user data storage for non-campaign-specific conversation data.
"""

import logging
import aiohttp
import json
from typing import Dict, Any, Optional, List

from src.config.config_inheritance import ConfigInheritance

class SystemUsersConversationRepositoryClient:
    """
    Client for the system users conversation repository.
    Manages persistent storage of user conversation data across all bot interactions.
    """
    
    def __init__(self):
        """Initialize the system users conversation repository client."""
        self.config_inheritance = ConfigInheritance()
        self.logger = logging.getLogger(__name__)
        self.base_config = self.config_inheritance.get_base_config()
        self.base_url = self.base_config.get("repository.system_users.url", "http://system-users-repository/api/v1")
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get a user's data from the system repository.
        
        Args:
            user_id: The user ID
            
        Returns:
            User data dictionary
        """
        url = f"{self.base_url}/users/{user_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        self.logger.info(f"User {user_id} not found in system repository")
                        return {}
                    else:
                        self.logger.error(f"Error retrieving user {user_id}: {response.status}")
                        return {}
        except Exception as e:
            self.logger.error(f"Error connecting to system repository: {e}")
            return {}
    
    async def create_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """
        Create a new user in the system repository.
        
        Args:
            user_id: The user ID
            user_data: The user data
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/users"
        
        # Add user_id to the data
        data = user_data.copy()
        data["user_id"] = user_id
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status in (200, 201):
                        return True
                    else:
                        self.logger.error(f"Error creating user {user_id}: {response.status}")
                        return False
        except Exception as e:
            self.logger.error(f"Error connecting to system repository: {e}")
            return False
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """
        Update a user's profile in the system repository.
        
        Args:
            user_id: The user ID
            profile_data: The profile data to update
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/users/{user_id}/profile"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=profile_data) as response:
                    if response.status in (200, 204):
                        return True
                    elif response.status == 404:
                        # User not found, create instead
                        return await self.create_user(user_id, {"profile": profile_data})
                    else:
                        self.logger.error(f"Error updating user {user_id} profile: {response.status}")
                        return False
        except Exception as e:
            self.logger.error(f"Error connecting to system repository: {e}")
            return False
    
    async def store_conversation_metadata(
        self, user_id: str, session_id: str, bot_type: str, metadata: Dict[str, Any]
    ) -> bool:
        """
        Store conversation metadata in the system repository.
        
        Args:
            user_id: The user ID
            session_id: The session ID
            bot_type: The type of bot
            metadata: The metadata to store
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/users/{user_id}/conversations/{session_id}"
        
        # Add bot_type to the metadata
        data = metadata.copy()
        data["bot_type"] = bot_type
        data["session_id"] = session_id
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status in (200, 201):
                        return True
                    else:
                        self.logger.error(f"Error storing conversation metadata for {user_id}: {response.status}")
                        return False
        except Exception as e:
            self.logger.error(f"Error connecting to system repository: {e}")
            return False
    
    async def get_conversation_metadata(
        self, user_id: str, session_id: str, bot_type: str
    ) -> Dict[str, Any]:
        """
        Get conversation metadata from the system repository.
        
        Args:
            user_id: The user ID
            session_id: The session ID
            bot_type: The type of bot
            
        Returns:
            Conversation metadata
        """
        url = f"{self.base_url}/users/{user_id}/conversations/{session_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        self.logger.info(f"Conversation {session_id} not found for user {user_id}")
                        return {}
                    else:
                        self.logger.error(f"Error retrieving conversation metadata: {response.status}")
                        return {}
        except Exception as e:
            self.logger.error(f"Error connecting to system repository: {e}")
            return {}
    
    async def get_user_conversations(
        self, user_id: str, bot_type: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get a user's conversations from the system repository.
        
        Args:
            user_id: The user ID
            bot_type: Optional bot type filter
            limit: Maximum number of conversations to retrieve
            
        Returns:
            List of conversation metadata
        """
        url = f"{self.base_url}/users/{user_id}/conversations"
        params = {"limit": limit}
        
        if bot_type:
            params["bot_type"] = bot_type
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        self.logger.info(f"No conversations found for user {user_id}")
                        return []
                    else:
                        self.logger.error(f"Error retrieving user conversations: {response.status}")
                        return []
        except Exception as e:
            self.logger.error(f"Error connecting to system repository: {e}")
            return [] 