"""
Shared knowledge base for cross-bot integration.

This module provides access to shared knowledge between different bot types,
enabling seamless knowledge sharing and consistent responses across the platform.
"""

import logging
from typing import Dict, Any, List, Optional, Union

from src.config.config_inheritance import ConfigInheritance

class SharedKnowledge:
    """
    Provides access to shared knowledge between different bot types.
    
    This class manages access to shared knowledge bases, ensuring consistent
    information across different bot types while respecting access controls
    and privacy settings defined in configuration.
    """
    
    def __init__(self):
        """Initialize the shared knowledge manager."""
        self.logger = logging.getLogger(__name__)
        self.config_inheritance = ConfigInheritance()
    
    def get_shared_knowledge(self, knowledge_type: str) -> Dict[str, Any]:
        """
        Get shared knowledge of a specific type from the base configuration.
        
        Args:
            knowledge_type: Type of knowledge to retrieve
            
        Returns:
            Dictionary containing the requested knowledge
        """
        try:
            # Access shared knowledge through base config
            base_config = self.config_inheritance.get_base_config()
            shared_knowledge = base_config.get("shared_knowledge", {})
            
            return shared_knowledge.get(knowledge_type, {})
        except Exception as e:
            self.logger.error(f"Error retrieving shared knowledge '{knowledge_type}': {e}")
            return {}
    
    def get_bot_specific_knowledge(self, bot_type: str, knowledge_type: str) -> Dict[str, Any]:
        """
        Get bot-specific knowledge of a specified type.
        
        Args:
            bot_type: Type of bot
            knowledge_type: Type of knowledge to retrieve
            
        Returns:
            Dictionary containing the requested knowledge
        """
        try:
            # Get bot-specific config
            bot_config = self.config_inheritance.get_config(bot_type)
            
            # Get knowledge from bot config
            bot_knowledge = bot_config.get("knowledge", {})
            
            return bot_knowledge.get(knowledge_type, {})
        except Exception as e:
            self.logger.error(f"Error retrieving bot-specific knowledge '{knowledge_type}' for {bot_type}: {e}")
            return {}
    
    def get_merged_knowledge(self, bot_type: str, knowledge_type: str) -> Dict[str, Any]:
        """
        Get merged knowledge combining shared and bot-specific knowledge.
        
        Args:
            bot_type: Type of bot
            knowledge_type: Type of knowledge to retrieve
            
        Returns:
            Dictionary containing merged knowledge
        """
        try:
            # Get shared knowledge
            shared = self.get_shared_knowledge(knowledge_type)
            
            # Get bot-specific knowledge
            bot_specific = self.get_bot_specific_knowledge(bot_type, knowledge_type)
            
            # Merge with bot-specific knowledge taking precedence
            merged = {**shared, **bot_specific}
            
            return merged
        except Exception as e:
            self.logger.error(f"Error merging knowledge '{knowledge_type}' for {bot_type}: {e}")
            return {}
    
    def is_knowledge_accessible(self, bot_type: str, knowledge_type: str) -> bool:
        """
        Check if a specific knowledge type is accessible to a bot.
        
        Args:
            bot_type: Type of bot
            knowledge_type: Type of knowledge to check
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            # Get base config
            base_config = self.config_inheritance.get_base_config()
            
            # Get access control settings
            access_control = base_config.get("shared_knowledge_access", {})
            
            # If no access control defined, default to accessible
            if not access_control:
                return True
            
            # Check for specific knowledge type access control
            type_access = access_control.get(knowledge_type, {})
            
            # If no specific access control for this type, check global
            if not type_access:
                # Check global access control
                allowed_bots = access_control.get("allowed_bots", [])
                
                # If allowed_bots is empty, all bots have access
                if not allowed_bots:
                    return True
                
                # Check if this bot is allowed
                return bot_type in allowed_bots
            
            # Check type-specific access control
            allowed_bots = type_access.get("allowed_bots", [])
            
            # If allowed_bots is empty, all bots have access
            if not allowed_bots:
                return True
            
            # Check if this bot is allowed
            return bot_type in allowed_bots
        
        except Exception as e:
            self.logger.error(f"Error checking knowledge access for '{knowledge_type}' by {bot_type}: {e}")
            # Default to accessible on error
            return True
    
    def get_accessible_knowledge_types(self, bot_type: str) -> List[str]:
        """
        Get list of knowledge types accessible to a specific bot.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            List of accessible knowledge types
        """
        try:
            # Get base config
            base_config = self.config_inheritance.get_base_config()
            
            # Get all shared knowledge types
            shared_knowledge = base_config.get("shared_knowledge", {})
            all_types = list(shared_knowledge.keys())
            
            # Filter to accessible types
            accessible_types = [
                k_type for k_type in all_types
                if self.is_knowledge_accessible(bot_type, k_type)
            ]
            
            return accessible_types
        
        except Exception as e:
            self.logger.error(f"Error getting accessible knowledge types for {bot_type}: {e}")
            return []
    
    def get_all_accessible_knowledge(self, bot_type: str) -> Dict[str, Any]:
        """
        Get all knowledge accessible to a specific bot.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Dictionary containing all accessible knowledge
        """
        try:
            # Get accessible knowledge types
            accessible_types = self.get_accessible_knowledge_types(bot_type)
            
            # Build combined knowledge dictionary
            combined_knowledge = {}
            
            for k_type in accessible_types:
                combined_knowledge[k_type] = self.get_merged_knowledge(bot_type, k_type)
            
            return combined_knowledge
        
        except Exception as e:
            self.logger.error(f"Error getting all accessible knowledge for {bot_type}: {e}")
            return {}
    
    def share_knowledge_between_bots(
        self, 
        source_bot: str, 
        target_bot: str, 
        knowledge_type: str,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Share specific knowledge from one bot to another.
        
        This method can be used during bot handoffs to ensure the target bot
        has access to relevant context and knowledge.
        
        Args:
            source_bot: Source bot type
            target_bot: Target bot type
            knowledge_type: Type of knowledge to share
            session_id: Optional session ID for session-specific knowledge
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if knowledge type is accessible to source bot
            if not self.is_knowledge_accessible(source_bot, knowledge_type):
                self.logger.warning(
                    f"Knowledge type '{knowledge_type}' is not accessible to source bot {source_bot}"
                )
                return False
            
            # Check if knowledge type is accessible to target bot
            if not self.is_knowledge_accessible(target_bot, knowledge_type):
                self.logger.warning(
                    f"Knowledge type '{knowledge_type}' is not accessible to target bot {target_bot}"
                )
                return False
            
            # Get knowledge from source bot
            source_knowledge = self.get_merged_knowledge(source_bot, knowledge_type)
            
            # In a real implementation, this would involve updating session-specific
            # context or temporary storage for the target bot to access
            # Since we're implementing a basic version, we'll just log the event
            
            self.logger.info(
                f"Shared knowledge '{knowledge_type}' from {source_bot} to {target_bot} "
                f"(session: {session_id if session_id else 'none'})"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                f"Error sharing knowledge '{knowledge_type}' from {source_bot} to {target_bot}: {e}"
            )
            return False


# Create singleton instance
shared_knowledge = SharedKnowledge() 