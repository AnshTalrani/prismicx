"""
Memory factory for creating and configuring LangChain memory components.

This module provides a factory for creating different types of LangChain
memory components based on configuration, with appropriate fallbacks.
"""

import logging
from typing import Dict, Any, Optional, Union, List

from langchain.memory import (
    ConversationBufferMemory,
    ConversationSummaryMemory,
    ConversationBufferWindowMemory,
    ConversationTokenBufferMemory,
    CombinedMemory,
    ConversationEntityMemory
)
from langchain.memory.chat_memory import BaseChatMemory
from langchain.schema import BaseRetriever

class MemoryFactory:
    """
    Factory for creating LangChain memory components.
    
    This class is responsible for creating and configuring different types
    of LangChain memory components based on bot configuration, with appropriate
    integration points and fallback mechanisms.
    """
    
    def __init__(
        self,
        config_integration: Any = None,
        llm_manager: Any = None,
        entity_store: Any = None,
    ):
        """
        Initialize memory factory.
        
        Args:
            config_integration: Integration with the config system
            llm_manager: LLM manager for accessing language models
            entity_store: Entity store for entity memory
        """
        self.config_integration = config_integration
        self.llm_manager = llm_manager
        self.entity_store = entity_store
        self.logger = logging.getLogger(__name__)
        
        # Cache of created memories
        self.memories: Dict[str, BaseChatMemory] = {}
    
    def create_memory(
        self,
        session_id: str,
        bot_type: str,
        memory_type: Optional[str] = None,
        return_messages: bool = True,
        **kwargs
    ) -> BaseChatMemory:
        """
        Create a LangChain memory component.
        
        Args:
            session_id: Session identifier
            bot_type: Type of bot
            memory_type: Type of memory to create (buffer/summary/window/token/entity/combined)
            return_messages: Whether to return messages or strings
            **kwargs: Additional parameters for memory initialization
            
        Returns:
            LangChain memory component
        """
        # Get memory configuration for this bot type
        memory_config = self._get_memory_config(bot_type)
        
        # Generate cache key
        cache_key = f"{session_id}_{bot_type}_{memory_type or memory_config.get('type', 'buffer')}"
        
        # Return cached memory if available
        if cache_key in self.memories:
            return self.memories[cache_key]
        
        # Use specified memory type or get from config
        memory_type = memory_type or memory_config.get("type", "buffer")
        
        # Create memory based on type
        try:
            if memory_type == "combined":
                memory = self._create_combined_memory(session_id, bot_type, memory_config, return_messages, **kwargs)
            elif memory_type == "summary":
                memory = self._create_summary_memory(bot_type, memory_config, return_messages, **kwargs)
            elif memory_type == "window":
                memory = self._create_window_memory(memory_config, return_messages, **kwargs)
            elif memory_type == "token":
                memory = self._create_token_memory(bot_type, memory_config, return_messages, **kwargs)
            elif memory_type == "entity":
                memory = self._create_entity_memory(bot_type, session_id, memory_config, return_messages, **kwargs)
            else:  # Default to buffer memory
                memory = self._create_buffer_memory(memory_config, return_messages, **kwargs)
            
            # Cache and return memory
            self.memories[cache_key] = memory
            return memory
            
        except Exception as e:
            self.logger.error(f"Failed to create {memory_type} memory: {e}", exc_info=True)
            
            # Fall back to buffer memory
            try:
                memory = ConversationBufferMemory(return_messages=return_messages)
                
                # Cache and return fallback memory
                self.memories[cache_key] = memory
                return memory
                
            except Exception as fallback_error:
                self.logger.error(f"Failed to create fallback memory: {fallback_error}")
                raise
    
    def _create_buffer_memory(
        self,
        memory_config: Dict[str, Any],
        return_messages: bool = True,
        **kwargs
    ) -> ConversationBufferMemory:
        """
        Create a buffer memory component.
        
        Args:
            memory_config: Memory configuration
            return_messages: Whether to return messages or strings
            **kwargs: Additional parameters
            
        Returns:
            Buffer memory component
        """
        return ConversationBufferMemory(
            return_messages=return_messages,
            memory_key=kwargs.get("memory_key", "chat_history"),
            input_key=kwargs.get("input_key", "input"),
            output_key=kwargs.get("output_key", "output")
        )
    
    def _create_summary_memory(
        self,
        bot_type: str,
        memory_config: Dict[str, Any],
        return_messages: bool = True,
        **kwargs
    ) -> ConversationSummaryMemory:
        """
        Create a summary memory component.
        
        Args:
            bot_type: Type of bot
            memory_config: Memory configuration
            return_messages: Whether to return messages or strings
            **kwargs: Additional parameters
            
        Returns:
            Summary memory component
        """
        # Get LLM for summarization
        llm = self._get_llm(bot_type, "summarization")
        
        return ConversationSummaryMemory(
            llm=llm,
            return_messages=return_messages,
            memory_key=kwargs.get("memory_key", "chat_history"),
            input_key=kwargs.get("input_key", "input"),
            output_key=kwargs.get("output_key", "output"),
            max_token_limit=memory_config.get("max_tokens", 2000)
        )
    
    def _create_window_memory(
        self,
        memory_config: Dict[str, Any],
        return_messages: bool = True,
        **kwargs
    ) -> ConversationBufferWindowMemory:
        """
        Create a window memory component.
        
        Args:
            memory_config: Memory configuration
            return_messages: Whether to return messages or strings
            **kwargs: Additional parameters
            
        Returns:
            Window memory component
        """
        k = memory_config.get("window_size", 5)
        
        return ConversationBufferWindowMemory(
            k=k,
            return_messages=return_messages,
            memory_key=kwargs.get("memory_key", "chat_history"),
            input_key=kwargs.get("input_key", "input"),
            output_key=kwargs.get("output_key", "output")
        )
    
    def _create_token_memory(
        self,
        bot_type: str,
        memory_config: Dict[str, Any],
        return_messages: bool = True,
        **kwargs
    ) -> ConversationTokenBufferMemory:
        """
        Create a token buffer memory component.
        
        Args:
            bot_type: Type of bot
            memory_config: Memory configuration
            return_messages: Whether to return messages or strings
            **kwargs: Additional parameters
            
        Returns:
            Token buffer memory component
        """
        # Get LLM for token counting
        llm = self._get_llm(bot_type, "token_counting")
        
        max_token_limit = memory_config.get("max_tokens", 2000)
        
        return ConversationTokenBufferMemory(
            llm=llm,
            max_token_limit=max_token_limit,
            return_messages=return_messages,
            memory_key=kwargs.get("memory_key", "chat_history"),
            input_key=kwargs.get("input_key", "input"),
            output_key=kwargs.get("output_key", "output")
        )
    
    def _create_entity_memory(
        self,
        bot_type: str,
        session_id: str,
        memory_config: Dict[str, Any],
        return_messages: bool = True,
        **kwargs
    ) -> ConversationEntityMemory:
        """
        Create an entity memory component.
        
        Args:
            bot_type: Type of bot
            session_id: Session identifier
            memory_config: Memory configuration
            return_messages: Whether to return messages or strings
            **kwargs: Additional parameters
            
        Returns:
            Entity memory component
        """
        # Get LLM for entity extraction
        llm = self._get_llm(bot_type, "entity_extraction")
        
        # Use a custom entity store if available
        if self.entity_store:
            store = self.entity_store.get_store(session_id, bot_type)
        else:
            # Use default entity store
            store = {}
        
        return ConversationEntityMemory(
            llm=llm,
            return_messages=return_messages,
            entity_cache=store,
            memory_key=kwargs.get("memory_key", "chat_history"),
            input_key=kwargs.get("input_key", "input"),
            output_key=kwargs.get("output_key", "output"),
            k=memory_config.get("entity_history_size", 3)
        )
    
    def _create_combined_memory(
        self,
        session_id: str,
        bot_type: str,
        memory_config: Dict[str, Any],
        return_messages: bool = True,
        **kwargs
    ) -> CombinedMemory:
        """
        Create a combined memory component.
        
        Args:
            session_id: Session identifier
            bot_type: Type of bot
            memory_config: Memory configuration
            return_messages: Whether to return messages or strings
            **kwargs: Additional parameters
            
        Returns:
            Combined memory component
        """
        # Determine which memory types to combine
        memory_types = memory_config.get("combined_types", ["buffer", "entity"])
        
        # Create memory components
        memories = []
        
        for memory_type in memory_types:
            try:
                # Use a different memory key for each component
                memory_key = f"{memory_type}_history"
                
                # Create memory component
                memory = self.create_memory(
                    session_id=session_id,
                    bot_type=bot_type,
                    memory_type=memory_type,
                    return_messages=return_messages,
                    memory_key=memory_key,
                    **kwargs
                )
                
                memories.append(memory)
                
            except Exception as e:
                self.logger.warning(f"Failed to create {memory_type} memory for combined memory: {e}")
        
        # Fall back to buffer memory if no memories created
        if not memories:
            memories.append(self._create_buffer_memory(memory_config, return_messages, **kwargs))
        
        # Create combined memory
        return CombinedMemory(memories=memories)
    
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
            "window_size": 5,
            "entity_history_size": 3,
            "combined_types": ["buffer", "entity"],
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
    
    def _get_llm(self, bot_type: str, purpose: str) -> Any:
        """
        Get an LLM instance for a specific purpose.
        
        Args:
            bot_type: Type of bot
            purpose: Purpose of the LLM (summarization, entity_extraction, etc.)
            
        Returns:
            LLM instance
        """
        # Use LLM manager if available
        if self.llm_manager:
            try:
                return self.llm_manager.get_model(bot_type, model_type=purpose)
            except Exception as e:
                self.logger.warning(f"Failed to get LLM from manager: {e}")
        
        # Fallback: Return a fake LLM
        from langchain.llms.fake import FakeListLLM
        return FakeListLLM(responses=["Placeholder response"])
    
    def get_memory(
        self,
        session_id: str,
        bot_type: str,
        memory_type: Optional[str] = None
    ) -> Optional[BaseChatMemory]:
        """
        Get a cached memory component.
        
        Args:
            session_id: Session identifier
            bot_type: Type of bot
            memory_type: Type of memory
            
        Returns:
            Cached memory component or None if not found
        """
        # Get memory configuration for this bot type
        memory_config = self._get_memory_config(bot_type)
        
        # Generate cache key
        memory_type = memory_type or memory_config.get("type", "buffer")
        cache_key = f"{session_id}_{bot_type}_{memory_type}"
        
        # Return cached memory if available
        return self.memories.get(cache_key)
    
    def clear_memory_cache(self) -> None:
        """
        Clear the memory cache.
        """
        self.memories = {}
        self.logger.info("Memory cache cleared")
    
    def invalidate_memory(self, cache_key: str) -> None:
        """
        Invalidate a specific memory in the cache.
        
        Args:
            cache_key: Key of the memory to invalidate
        """
        if cache_key in self.memories:
            del self.memories[cache_key]
            self.logger.info(f"Memory {cache_key} invalidated in cache") 