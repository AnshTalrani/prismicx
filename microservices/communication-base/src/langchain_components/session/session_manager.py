"""
Session management for the communication platform.

This module provides enhanced session management that integrates with LangChain memory
components, manages conversation history, and handles cross-session context.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import asyncio

from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.memory.chat_memory import BaseChatMemory
from langchain.schema import HumanMessage, AIMessage, SystemMessage, BaseMessage
from pydantic import BaseModel, Field

class SessionState(BaseModel):
    """
    Session state model representing the current state of a conversation session.
    """
    session_id: str
    user_id: Optional[str] = None
    bot_type: str
    last_updated: float = Field(default_factory=time.time)
    is_active: bool = True
    history: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    entities: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a message to the session history.
        
        Args:
            role: Role of the message sender (human/ai/system)
            content: Content of the message
            metadata: Additional metadata for the message
        """
        timestamp = time.time()
        self.last_updated = timestamp
        
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }
        
        self.history.append(message)
    
    def to_langchain_messages(self) -> List[BaseMessage]:
        """
        Convert session history to LangChain message format.
        
        Returns:
            List of LangChain messages
        """
        messages = []
        for message in self.history:
            if message["role"] == "human":
                messages.append(HumanMessage(content=message["content"]))
            elif message["role"] == "ai":
                messages.append(AIMessage(content=message["content"]))
            elif message["role"] == "system":
                messages.append(SystemMessage(content=message["content"]))
        
        return messages
    
    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent messages from the history.
        
        Args:
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of recent messages
        """
        return self.history[-limit:] if limit > 0 else []


class SessionManager:
    """
    Enhanced session manager that integrates with LangChain memory components.
    
    This class handles session creation, retrieval, and persistence, while also
    providing integration with LangChain memory components for effective context
    management across interactions.
    """
    
    def __init__(
        self,
        config_integration: Any = None,
        repository_client: Any = None,
        memory_factory: Any = None,
        session_timeout: int = 1800,  # 30 minutes
        max_history_length: int = 100
    ):
        """
        Initialize the session manager.
        
        Args:
            config_integration: Configuration integration service
            repository_client: Repository client for session persistence
            memory_factory: Factory for creating memory components
            session_timeout: Session timeout in seconds
            max_history_length: Maximum number of messages to keep in history
        """
        self.config_integration = config_integration
        self.repository_client = repository_client
        self.memory_factory = memory_factory
        self.session_timeout = session_timeout
        self.max_history_length = max_history_length
        self.logger = logging.getLogger(__name__)
        
        # In-memory session cache
        self.sessions: Dict[str, SessionState] = {}
        
        # Memory components
        self.memories: Dict[str, BaseChatMemory] = {}
    
    async def get_session(self, session_id: str, bot_type: str, user_id: Optional[str] = None) -> SessionState:
        """
        Get an existing session or create a new one.
        
        Args:
            session_id: Session identifier
            bot_type: Type of bot
            user_id: User identifier (optional)
            
        Returns:
            Session state
        """
        # Check if session exists in memory
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            # Check if session is active
            current_time = time.time()
            if current_time - session.last_updated > self.session_timeout:
                # Session expired, reactivate it
                session.is_active = True
                session.last_updated = current_time
                self.logger.info(f"Reactivated expired session: {session_id}")
            
            return session
        
        # Try to load from repository
        if self.repository_client:
            try:
                session_data = await self.repository_client.get_session(session_id)
                if session_data:
                    # Create session from stored data
                    session = SessionState(**session_data)
                    session.is_active = True
                    session.last_updated = time.time()
                    self.sessions[session_id] = session
                    self.logger.info(f"Loaded session from repository: {session_id}")
                    
                    # Initialize memory component for this session
                    await self._init_memory_component(session)
                    
                    return session
            except Exception as e:
                self.logger.error(f"Failed to load session from repository: {e}", exc_info=True)
        
        # Create new session
        session = SessionState(
            session_id=session_id,
            user_id=user_id,
            bot_type=bot_type,
            last_updated=time.time(),
            is_active=True
        )
        
        # Add session to memory cache
        self.sessions[session_id] = session
        
        # Initialize memory component
        await self._init_memory_component(session)
        
        # Add system message with greeting if configured
        if self.config_integration:
            try:
                config = self.config_integration.get_config(bot_type)
                greeting = config.get("session", {}).get("greeting")
                if greeting:
                    session.add_message("system", greeting)
            except Exception as e:
                self.logger.warning(f"Failed to get greeting from config: {e}")
        
        self.logger.info(f"Created new session: {session_id} for bot type: {bot_type}")
        return session
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        bot_type: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to a session.
        
        Args:
            session_id: Session identifier
            role: Role of the message sender (human/ai/system)
            content: Content of the message
            bot_type: Type of bot
            user_id: User identifier (optional)
            metadata: Additional metadata for the message
        """
        # Get or create session
        session = await self.get_session(session_id, bot_type, user_id)
        
        # Add message to session
        session.add_message(role, content, metadata)
        
        # Trim history if needed
        if len(session.history) > self.max_history_length:
            # Remove oldest messages but keep system messages
            new_history = [msg for msg in session.history if msg["role"] == "system"]
            new_history.extend(session.history[-self.max_history_length:])
            session.history = new_history
        
        # Update memory component
        memory_key = f"{session_id}_{bot_type}"
        if memory_key in self.memories:
            memory = self.memories[memory_key]
            # Convert to appropriate message format
            if role == "human":
                memory.chat_memory.add_user_message(content)
            elif role == "ai":
                memory.chat_memory.add_ai_message(content)
        
        # Save session to repository if available
        if self.repository_client:
            try:
                await self.repository_client.save_session(session_id, session.dict())
            except Exception as e:
                self.logger.error(f"Failed to save session: {e}", exc_info=True)
    
    async def get_langchain_memory(
        self,
        session_id: str,
        bot_type: str,
        memory_type: str = "buffer",
        user_id: Optional[str] = None
    ) -> BaseChatMemory:
        """
        Get a LangChain memory component for the session.
        
        Args:
            session_id: Session identifier
            bot_type: Type of bot
            memory_type: Type of memory to use (buffer/summary)
            user_id: User identifier (optional)
            
        Returns:
            LangChain memory component
        """
        memory_key = f"{session_id}_{bot_type}"
        
        # Return cached memory if available
        if memory_key in self.memories:
            return self.memories[memory_key]
        
        # Get or create session
        session = await self.get_session(session_id, bot_type, user_id)
        
        # Initialize memory component
        return await self._init_memory_component(session, memory_type)
    
    async def _init_memory_component(
        self,
        session: SessionState,
        memory_type: Optional[str] = None
    ) -> BaseChatMemory:
        """
        Initialize a LangChain memory component for a session.
        
        Args:
            session: Session state
            memory_type: Type of memory to use (buffer/summary)
            
        Returns:
            LangChain memory component
        """
        memory_key = f"{session.session_id}_{session.bot_type}"
        
        # Get memory configuration for this bot type
        memory_config = self._get_memory_config(session.bot_type)
        
        # Use specified memory type or get from config
        memory_type = memory_type or memory_config.get("type", "buffer")
        
        # Create memory component using factory if available
        if self.memory_factory:
            try:
                memory = self.memory_factory.create_memory(
                    session_id=session.session_id,
                    bot_type=session.bot_type,
                    memory_type=memory_type
                )
                self.memories[memory_key] = memory
                return memory
            except Exception as e:
                self.logger.warning(f"Failed to create memory using factory: {e}")
        
        # Fallback: Create memory directly
        if memory_type == "summary":
            memory = ConversationSummaryMemory(
                llm=self._get_llm_for_summary(session.bot_type),
                max_token_limit=memory_config.get("max_tokens", 2000),
                return_messages=True
            )
        else:  # Default to buffer memory
            memory = ConversationBufferMemory(
                return_messages=True
            )
        
        # Load existing messages
        for msg in session.history:
            if msg["role"] == "human":
                memory.chat_memory.add_user_message(msg["content"])
            elif msg["role"] == "ai":
                memory.chat_memory.add_ai_message(msg["content"])
        
        # Cache and return memory
        self.memories[memory_key] = memory
        return memory
    
    def _get_llm_for_summary(self, bot_type: str) -> Any:
        """
        Get LLM for summarization based on bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            LLM instance for summarization
        """
        # This is a placeholder - in a real implementation, you would
        # retrieve an appropriate LLM from an LLM manager or similar
        from langchain.llms.fake import FakeListLLM
        return FakeListLLM(responses=["Summarized conversation"])
    
    def _get_memory_config(self, bot_type: str) -> Dict[str, Any]:
        """
        Get memory configuration for a bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Memory configuration
        """
        # Default memory configuration
        default_config = {
            "type": "buffer",
            "max_tokens": 2000,
            "summary_interval": 10  # Number of messages after which to generate a summary
        }
        
        # Get bot-specific config if available
        if self.config_integration:
            try:
                config = self.config_integration.get_config(bot_type)
                memory_config = config.get("memory", {})
                
                # Merge with defaults
                merged_config = {**default_config, **memory_config}
                return merged_config
            except Exception as e:
                self.logger.warning(f"Failed to get memory config: {e}")
        
        return default_config
    
    async def get_conversation_summary(self, session_id: str, bot_type: str) -> str:
        """
        Get a summary of the conversation.
        
        Args:
            session_id: Session identifier
            bot_type: Type of bot
            
        Returns:
            Conversation summary
        """
        # Get session
        try:
            session = await self.get_session(session_id, bot_type)
        except Exception as e:
            self.logger.error(f"Failed to get session for summary: {e}")
            return "Unable to generate conversation summary."
        
        # Check if we have a recent summary
        if session.summary and len(session.history) < 5:
            return session.summary
        
        # Get memory configuration
        memory_config = self._get_memory_config(bot_type)
        
        # Use summary memory to generate summary
        try:
            memory = ConversationSummaryMemory(
                llm=self._get_llm_for_summary(bot_type),
                max_token_limit=memory_config.get("max_tokens", 2000),
                return_messages=True
            )
            
            # Load existing messages
            for msg in session.history:
                if msg["role"] == "human":
                    memory.chat_memory.add_user_message(msg["content"])
                elif msg["role"] == "ai":
                    memory.chat_memory.add_ai_message(msg["content"])
            
            # Generate summary
            summary = memory.predict_new_summary(
                memory.chat_memory.messages,
                ""
            )
            
            # Save summary to session
            session.summary = summary
            
            # Persist session if repository available
            if self.repository_client:
                try:
                    await self.repository_client.save_session(session_id, session.dict())
                except Exception as e:
                    self.logger.error(f"Failed to save session with summary: {e}")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate conversation summary: {e}")
            return "Unable to generate conversation summary due to an error."
    
    async def get_session_entities(self, session_id: str, bot_type: str) -> Dict[str, Any]:
        """
        Get entities extracted from a session.
        
        Args:
            session_id: Session identifier
            bot_type: Type of bot
            
        Returns:
            Dictionary of entities
        """
        try:
            session = await self.get_session(session_id, bot_type)
            return session.entities
        except Exception as e:
            self.logger.error(f"Failed to get session entities: {e}")
            return {}
    
    async def update_session_entities(
        self,
        session_id: str,
        bot_type: str,
        entities: Dict[str, Any],
        merge: bool = True
    ) -> None:
        """
        Update entities in a session.
        
        Args:
            session_id: Session identifier
            bot_type: Type of bot
            entities: Entities to update
            merge: Whether to merge with existing entities
        """
        try:
            session = await self.get_session(session_id, bot_type)
            
            if merge:
                # Merge with existing entities (deep merge)
                session.entities = self._deep_merge(session.entities, entities)
            else:
                # Replace entities
                session.entities = entities
            
            # Persist session if repository available
            if self.repository_client:
                try:
                    await self.repository_client.save_session(session_id, session.dict())
                except Exception as e:
                    self.logger.error(f"Failed to save session with updated entities: {e}")
                    
        except Exception as e:
            self.logger.error(f"Failed to update session entities: {e}")
    
    async def get_session_context(self, session_id: str, bot_type: str) -> Dict[str, Any]:
        """
        Get context data from a session.
        
        Args:
            session_id: Session identifier
            bot_type: Type of bot
            
        Returns:
            Session context data
        """
        try:
            session = await self.get_session(session_id, bot_type)
            return session.context
        except Exception as e:
            self.logger.error(f"Failed to get session context: {e}")
            return {}
    
    async def update_session_context(
        self,
        session_id: str,
        bot_type: str,
        context: Dict[str, Any],
        merge: bool = True
    ) -> None:
        """
        Update context data in a session.
        
        Args:
            session_id: Session identifier
            bot_type: Type of bot
            context: Context data to update
            merge: Whether to merge with existing context
        """
        try:
            session = await self.get_session(session_id, bot_type)
            
            if merge:
                # Merge with existing context (deep merge)
                session.context = self._deep_merge(session.context, context)
            else:
                # Replace context
                session.context = context
            
            # Persist session if repository available
            if self.repository_client:
                try:
                    await self.repository_client.save_session(session_id, session.dict())
                except Exception as e:
                    self.logger.error(f"Failed to save session with updated context: {e}")
                    
        except Exception as e:
            self.logger.error(f"Failed to update session context: {e}")
    
    async def end_session(self, session_id: str) -> None:
        """
        End a session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.is_active = False
            
            # Persist session if repository available
            if self.repository_client:
                try:
                    await self.repository_client.save_session(session_id, session.dict())
                except Exception as e:
                    self.logger.error(f"Failed to save ended session: {e}")
            
            # Remove from memory cache
            del self.sessions[session_id]
            
            # Remove associated memory components
            memory_keys = [k for k in self.memories if k.startswith(f"{session_id}_")]
            for key in memory_keys:
                del self.memories[key]
                
            self.logger.info(f"Ended session: {session_id}")
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.last_updated > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.end_session(session_id)
        
        self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        return len(expired_sessions)
    
    def _deep_merge(self, d1: Dict[str, Any], d2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.
        
        Args:
            d1: First dictionary
            d2: Second dictionary
            
        Returns:
            Merged dictionary
        """
        result = d1.copy()
        
        for key, value in d2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result 