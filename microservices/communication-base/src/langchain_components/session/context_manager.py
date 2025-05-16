"""
Session context manager for tracking conversation history and state.
Manages message history, extracts key information, and maintains conversation context.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from uuid import uuid4

from src.config.config_inheritance import ConfigInheritance
from src.models.session.session_manager import SessionManager
from src.langchain_components.nlp.hybrid_processor import hybrid_processor
from src.langchain_components.storage.entity_repository_manager import entity_repository_manager

class ContextManager:
    """
    Session context manager for conversation tracking and state management.
    Maintains message history, extracts key entities, and persists state.
    """
    
    def __init__(self):
        """Initialize the context manager."""
        self.config_inheritance = ConfigInheritance()
        self.session_manager = SessionManager()
        self.logger = logging.getLogger(__name__)
        
        # In-memory cache for active contexts
        self._active_contexts = {}
        
        # Cache expiry settings
        self._cache_timeout = 30  # minutes
        self._cleanup_task = None
    
    async def initialize(self):
        """Initialize the context manager and start cleanup task."""
        # Start the cleanup task to periodically check for expired contexts
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_contexts())
    
    async def get_context(self, session_id: str, bot_type: str) -> Dict[str, Any]:
        """
        Get the current context for a session.
        
        Args:
            session_id: The session identifier
            bot_type: The type of bot
            
        Returns:
            The session context dictionary
        """
        # Check in-memory cache first
        cache_key = f"{session_id}:{bot_type}"
        if cache_key in self._active_contexts:
            context = self._active_contexts[cache_key]
            # Refresh last accessed time
            context["_meta"]["last_accessed"] = datetime.utcnow()
            return context
        
        # Not in cache, try to load from storage
        try:
            context = await self.session_manager.get_session_data(session_id, bot_type)
            
            # If no context exists, create a new one
            if not context:
                context = self._create_new_context(session_id, bot_type)
            
            # Add to cache
            context["_meta"] = {
                "last_accessed": datetime.utcnow(),
                "created": datetime.utcnow()
            }
            self._active_contexts[cache_key] = context
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting context for session {session_id}: {e}")
            # Return a new context if retrieval fails
            context = self._create_new_context(session_id, bot_type)
            
            # Add to cache
            context["_meta"] = {
                "last_accessed": datetime.utcnow(),
                "created": datetime.utcnow()
            }
            self._active_contexts[cache_key] = context
            
            return context
    
    def _create_new_context(self, session_id: str, bot_type: str) -> Dict[str, Any]:
        """Create a new context for a session."""
        config = self.config_inheritance.get_config(bot_type)
        
        # Get max history length from config
        max_history_length = config.get("session.max_history_length", 10)
        
        return {
            "session_id": session_id,
            "bot_type": bot_type,
            "history": [],
            "entities": {},
            "conversation_state": {
                "stage": "initial",
                "topic": None,
                "last_entity_update": None
            },
            "user_info": {},
            "system_flags": {},
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "message_count": 0,
                "max_history_length": max_history_length
            }
        }
    
    async def add_message(
        self, 
        session_id: str, 
        bot_type: str, 
        message: str, 
        is_user: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a message to the session context.
        
        Args:
            session_id: The session identifier
            bot_type: The type of bot
            message: The message content
            is_user: Whether the message is from the user (True) or bot (False)
            metadata: Additional message metadata
            
        Returns:
            The updated context
        """
        # Get current context
        context = await self.get_context(session_id, bot_type)
        
        # Create message entry
        timestamp = datetime.utcnow().isoformat()
        message_id = str(uuid4())
        
        message_entry = {
            "id": message_id,
            "timestamp": timestamp,
            "content": message,
            "is_user": is_user,
            "metadata": metadata or {}
        }
        
        # Add message to history
        context["history"].append(message_entry)
        
        # Update message count
        context["metadata"]["message_count"] += 1
        
        # Trim history if it exceeds max length
        max_length = context["metadata"]["max_history_length"]
        if len(context["history"]) > max_length:
            context["history"] = context["history"][-max_length:]
        
        # Process user message for entities if from user
        if is_user:
            await self._process_user_message(context, message, bot_type)
        
        # Save context
        await self._save_context(context)
        
        return context
    
    async def _process_user_message(
        self, context: Dict[str, Any], message: str, bot_type: str
    ) -> None:
        """
        Process a user message to extract entities and update context.
        
        Args:
            context: The session context
            message: The user message
            bot_type: The type of bot
        """
        try:
            # Process message with NLP processor
            extracted_info = await hybrid_processor.process_message(message, bot_type)
            
            if not extracted_info:
                return
            
            # Update entities in context
            if "entities" in extracted_info:
                # Get current entities
                current_entities = context.get("entities", {})
                
                # Merge new entities (updating timestamps)
                for entity_type, entities in extracted_info["entities"].items():
                    if entity_type not in current_entities:
                        current_entities[entity_type] = {}
                    
                    # Add/update entities with timestamp
                    for entity_name, entity_data in entities.items():
                        entity_data["last_updated"] = datetime.utcnow().isoformat()
                        current_entities[entity_type][entity_name] = entity_data
                
                # Update context
                context["entities"] = current_entities
                context["conversation_state"]["last_entity_update"] = datetime.utcnow().isoformat()
                
                # Store entities in repository if configured
                await self._store_entities(context["session_id"], bot_type, extracted_info["entities"])
            
            # Update conversation state if intent is present
            if "intent" in extracted_info:
                # Update conversation state based on intent
                intent = extracted_info["intent"]
                
                if "topic" in intent:
                    context["conversation_state"]["topic"] = intent["topic"]
                
                if "stage" in intent:
                    context["conversation_state"]["stage"] = intent["stage"]
                
                # Add any other intent properties to conversation state
                for key, value in intent.items():
                    if key not in ["topic", "stage"]:
                        context["conversation_state"][key] = value
        
        except Exception as e:
            self.logger.error(f"Error processing user message: {e}")
    
    async def _store_entities(
        self, session_id: str, bot_type: str, entities: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Store extracted entities in the entity repository.
        
        Args:
            session_id: The session identifier
            bot_type: The type of bot
            entities: Dictionary of entities by type
        """
        # Get config
        config = self.config_inheritance.get_config(bot_type)
        
        # Check if entity storage is enabled
        if not config.get("session.store_entities", True):
            return
        
        try:
            # Store entities by type
            for entity_type, entities_by_name in entities.items():
                for entity_name, entity_data in entities_by_name.items():
                    await entity_repository_manager.store_entity(
                        session_id=session_id,
                        bot_type=bot_type,
                        entity_type=entity_type,
                        entity_name=entity_name,
                        entity_data=entity_data
                    )
        except Exception as e:
            self.logger.error(f"Error storing entities: {e}")
    
    async def update_context(
        self, session_id: str, bot_type: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update specific fields in the context.
        
        Args:
            session_id: The session identifier
            bot_type: The type of bot
            updates: Dictionary of updates to apply
            
        Returns:
            Updated context
        """
        # Get current context
        context = await self.get_context(session_id, bot_type)
        
        # Apply updates at top level only
        for key, value in updates.items():
            if key not in ["_meta"]:  # Protect internal fields
                context[key] = value
        
        # Save context
        await self._save_context(context)
        
        return context
    
    async def merge_entities(
        self, session_id: str, bot_type: str, entities: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge entities into the context.
        
        Args:
            session_id: The session identifier
            bot_type: The type of bot
            entities: Dictionary of entities by type
            
        Returns:
            Updated context
        """
        # Get current context
        context = await self.get_context(session_id, bot_type)
        
        # Get current entities
        current_entities = context.get("entities", {})
        
        # Merge new entities
        for entity_type, entity_dict in entities.items():
            if entity_type not in current_entities:
                current_entities[entity_type] = {}
            
            # Add/update entities
            for entity_name, entity_data in entity_dict.items():
                entity_data["last_updated"] = datetime.utcnow().isoformat()
                current_entities[entity_type][entity_name] = entity_data
        
        # Update context
        context["entities"] = current_entities
        context["conversation_state"]["last_entity_update"] = datetime.utcnow().isoformat()
        
        # Save context
        await self._save_context(context)
        
        # Store entities in repository
        await self._store_entities(session_id, bot_type, entities)
        
        return context
    
    async def get_message_history(
        self, session_id: str, bot_type: str, limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        Get message history for a session.
        
        Args:
            session_id: The session identifier
            bot_type: The type of bot
            limit: Maximum number of messages to return (newest first)
            
        Returns:
            List of message entries
        """
        context = await self.get_context(session_id, bot_type)
        history = context.get("history", [])
        
        if limit:
            return history[-limit:]
        
        return history
    
    async def clear_history(self, session_id: str, bot_type: str) -> Dict[str, Any]:
        """
        Clear message history for a session.
        
        Args:
            session_id: The session identifier
            bot_type: The type of bot
            
        Returns:
            Updated context
        """
        context = await self.get_context(session_id, bot_type)
        
        # Clear history
        context["history"] = []
        context["metadata"]["message_count"] = 0
        
        # Save context
        await self._save_context(context)
        
        return context
    
    async def _save_context(self, context: Dict[str, Any]) -> None:
        """
        Save context to persistent storage.
        
        Args:
            context: The context to save
        """
        try:
            # Create a copy of the context without metadata
            save_context = context.copy()
            
            # Remove internal metadata
            if "_meta" in save_context:
                del save_context["_meta"]
            
            # Save to session manager
            session_id = context["session_id"]
            bot_type = context["bot_type"]
            
            await self.session_manager.update_session_data(session_id, bot_type, save_context)
            
        except Exception as e:
            self.logger.error(f"Error saving context: {e}")
    
    async def _cleanup_expired_contexts(self) -> None:
        """Periodically clean up expired contexts from memory."""
        while True:
            try:
                # Sleep for a while
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Get current time
                now = datetime.utcnow()
                
                # Find expired contexts
                expired_keys = []
                for key, context in self._active_contexts.items():
                    last_accessed = context["_meta"]["last_accessed"]
                    timeout = timedelta(minutes=self._cache_timeout)
                    
                    if now - last_accessed > timeout:
                        expired_keys.append(key)
                
                # Remove expired contexts
                for key in expired_keys:
                    del self._active_contexts[key]
                    
                if expired_keys:
                    self.logger.debug(f"Cleaned up {len(expired_keys)} expired contexts")
                    
            except Exception as e:
                self.logger.error(f"Error in context cleanup: {e}")
    
    async def get_formatted_history(
        self, session_id: str, bot_type: str, limit: int = None, include_metadata: bool = False
    ) -> str:
        """
        Get formatted conversation history.
        
        Args:
            session_id: The session identifier
            bot_type: The type of bot
            limit: Maximum number of messages to return
            include_metadata: Whether to include message metadata
            
        Returns:
            Formatted conversation history as a string
        """
        # Get message history
        history = await self.get_message_history(session_id, bot_type, limit)
        
        # Format messages
        formatted_messages = []
        for msg in history:
            # Format timestamp
            try:
                timestamp = datetime.fromisoformat(msg["timestamp"])
                time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                time_str = msg["timestamp"]
            
            # Format sender
            sender = "User" if msg["is_user"] else "Bot"
            
            # Format message
            if include_metadata and msg.get("metadata"):
                metadata_str = json.dumps(msg["metadata"])
                formatted_msg = f"[{time_str}] {sender}: {msg['content']} (Metadata: {metadata_str})"
            else:
                formatted_msg = f"[{time_str}] {sender}: {msg['content']}"
            
            formatted_messages.append(formatted_msg)
        
        # Join messages
        return "\n".join(formatted_messages)
    
    async def get_context_summary(self, session_id: str, bot_type: str) -> Dict[str, Any]:
        """
        Get a summary of the current context.
        
        Args:
            session_id: The session identifier
            bot_type: The type of bot
            
        Returns:
            Context summary
        """
        context = await self.get_context(session_id, bot_type)
        
        # Create a summary
        summary = {
            "session_id": context["session_id"],
            "bot_type": context["bot_type"],
            "message_count": context["metadata"]["message_count"],
            "conversation_state": context["conversation_state"],
            "entity_count": {
                entity_type: len(entities)
                for entity_type, entities in context.get("entities", {}).items()
            },
            "user_info": context.get("user_info", {})
        }
        
        return summary

# Global instance
context_manager = ContextManager() 