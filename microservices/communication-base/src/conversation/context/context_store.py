"""
Conversation Context Store

This module provides storage and retrieval for conversation context,
ensuring persistence and efficient access to conversation state.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from src.config.config_integration import ConfigIntegration

logger = logging.getLogger(__name__)

class ContextStore:
    """
    Context Store for conversation context management.
    
    This class handles the storage, retrieval, and update of conversation
    context, ensuring proper state management across turns and sessions.
    """
    
    def __init__(self, config_integration: ConfigIntegration):
        """
        Initialize the context store.
        
        Args:
            config_integration: Configuration integration instance
        """
        self.config_integration = config_integration
        self.in_memory_contexts: Dict[str, Dict[str, Any]] = {}
        self.user_session_mapping: Dict[str, List[str]] = {}
        
        # Flag for using persistence (would connect to real database in production)
        self.use_persistence = True
        
        logger.info("Context store initialized")
    
    async def get_context(
        self,
        session_id: str,
        user_id: str,
        bot_type: str
    ) -> Dict[str, Any]:
        """
        Get or create context for a session.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            bot_type: Type of bot
            
        Returns:
            Context dictionary for the session
        """
        # Try to get existing context
        context = await self.get_context_by_session(session_id)
        
        if context:
            # Update last access time
            context["last_accessed"] = datetime.utcnow().isoformat()
            return context
        
        # Create new context
        context = {
            "session_id": session_id,
            "user_id": user_id,
            "bot_type": bot_type,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
            "conversation_status": "active",
            "messages": [],
            "entities": {},
            "user_info": await self._load_user_info(user_id, bot_type)
        }
        
        # Store context
        await self.save_context(session_id, context)
        
        # Update user-session mapping
        if user_id not in self.user_session_mapping:
            self.user_session_mapping[user_id] = []
        
        if session_id not in self.user_session_mapping[user_id]:
            self.user_session_mapping[user_id].append(session_id)
        
        logger.info(f"Created new context for session {session_id}, user {user_id}, bot {bot_type}")
        return context
    
    async def get_context_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get context by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Context dictionary or None if not found
        """
        # Check in-memory cache first
        if session_id in self.in_memory_contexts:
            return self.in_memory_contexts[session_id]
        
        # If using persistence, try to load from storage
        if self.use_persistence:
            context = await self._load_context_from_persistence(session_id)
            if context:
                # Cache in memory
                self.in_memory_contexts[session_id] = context
                return context
        
        return None
    
    async def get_contexts_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all contexts for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of context dictionaries
        """
        contexts = []
        
        # Get session IDs for this user
        session_ids = self.user_session_mapping.get(user_id, [])
        
        # Get context for each session
        for session_id in session_ids:
            context = await self.get_context_by_session(session_id)
            if context:
                contexts.append(context)
        
        return contexts
    
    async def update_context(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update context for a session.
        
        Args:
            session_id: Session identifier
            updates: Dictionary of updates to apply
            
        Returns:
            True if successful, False otherwise
        """
        # Get existing context
        context = await self.get_context_by_session(session_id)
        
        if not context:
            logger.error(f"Cannot update context: session {session_id} not found")
            return False
        
        # Apply updates
        context.update(updates)
        
        # Update last access time
        context["last_accessed"] = datetime.utcnow().isoformat()
        
        # Save updated context
        await self.save_context(session_id, context)
        
        logger.info(f"Updated context for session {session_id}")
        return True
    
    async def save_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """
        Save context for a session.
        
        Args:
            session_id: Session identifier
            context: Context dictionary
            
        Returns:
            True if successful, False otherwise
        """
        # Update in-memory cache
        self.in_memory_contexts[session_id] = context
        
        # If using persistence, save to storage
        if self.use_persistence:
            success = await self._save_context_to_persistence(session_id, context)
            if not success:
                logger.error(f"Failed to persist context for session {session_id}")
                return False
        
        return True
    
    async def add_message_to_context(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """
        Add a message to the conversation history in context.
        
        Args:
            session_id: Session identifier
            message: Message dictionary
            
        Returns:
            True if successful, False otherwise
        """
        # Get existing context
        context = await self.get_context_by_session(session_id)
        
        if not context:
            logger.error(f"Cannot add message: session {session_id} not found")
            return False
        
        # Add message to history
        if "messages" not in context:
            context["messages"] = []
        
        context["messages"].append(message)
        
        # Limit message history if needed
        max_messages = 100  # Configurable
        if len(context["messages"]) > max_messages:
            # If too many messages, keep most recent and create summary
            if "message_summary" not in context:
                context["message_summary"] = []
            
            # Summarize oldest messages (first half of excess)
            excess = len(context["messages"]) - max_messages
            messages_to_summarize = context["messages"][:excess]
            
            # Create simple summary (would be more sophisticated in production)
            summary = {
                "count": len(messages_to_summarize),
                "time_range": [
                    messages_to_summarize[0].get("timestamp", ""),
                    messages_to_summarize[-1].get("timestamp", "")
                ]
            }
            
            context["message_summary"].append(summary)
            
            # Keep only the most recent messages
            context["messages"] = context["messages"][excess:]
        
        # Save updated context
        await self.save_context(session_id, context)
        
        return True
    
    async def clear_context(self, session_id: str) -> bool:
        """
        Clear context for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        # Remove from in-memory cache
        if session_id in self.in_memory_contexts:
            del self.in_memory_contexts[session_id]
        
        # If using persistence, remove from storage
        if self.use_persistence:
            success = await self._delete_context_from_persistence(session_id)
            if not success:
                logger.error(f"Failed to delete persisted context for session {session_id}")
                return False
        
        # Update user-session mapping
        for user_id, sessions in self.user_session_mapping.items():
            if session_id in sessions:
                sessions.remove(session_id)
        
        logger.info(f"Cleared context for session {session_id}")
        return True
    
    async def _load_user_info(
        self,
        user_id: str,
        bot_type: str
    ) -> Dict[str, Any]:
        """
        Load user information for context.
        
        Args:
            user_id: User identifier
            bot_type: Type of bot
            
        Returns:
            User information dictionary
        """
        # This would connect to a user database in production
        # For now, return dummy data
        return {
            "user_id": user_id,
            "preferences": {
                "language": "en",
                "notification_channel": "email"
            },
            "history": {
                "previous_interactions": 0,
                "last_interaction": None
            }
        }
    
    async def _load_context_from_persistence(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load context from persistent storage.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Context dictionary or None if not found
        """
        # This would connect to a database in production
        # For now, just simulate a delay
        await asyncio.sleep(0.01)
        
        # Simulate not found
        logger.info(f"No persisted context found for session {session_id}")
        return None
    
    async def _save_context_to_persistence(
        self,
        session_id: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Save context to persistent storage.
        
        Args:
            session_id: Session identifier
            context: Context dictionary
            
        Returns:
            True if successful, False otherwise
        """
        # This would connect to a database in production
        # For now, just simulate a delay
        await asyncio.sleep(0.01)
        
        # Simulate success
        logger.info(f"Persisted context for session {session_id}")
        return True
    
    async def _delete_context_from_persistence(
        self,
        session_id: str
    ) -> bool:
        """
        Delete context from persistent storage.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        # This would connect to a database in production
        # For now, just simulate a delay
        await asyncio.sleep(0.01)
        
        # Simulate success
        logger.info(f"Deleted persisted context for session {session_id}")
        return True 