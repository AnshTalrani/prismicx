"""
Session-aware memory implementation that persists across user sessions.

This module provides a specialized memory implementation that integrates with
the session management system to persist memory across user sessions.
"""

import logging
from typing import Dict, Any, List, Optional

from langchain.memory import ConversationSummaryMemory
from langchain.schema import BaseMessage

class SessionMemory(ConversationSummaryMemory):
    """
    Session-aware memory implementation that persists across user sessions.
    
    This class extends ConversationSummaryMemory to provide integration with 
    the session management system, allowing memory to be persisted across sessions
    and loaded based on configuration settings.
    """
    
    def __init__(
        self, 
        llm: Any,
        session_manager: Any,
        session_id: str,
        bot_type: str,
        max_token_limit: int = 1000,
        memory_key: str = "chat_history",
        human_prefix: str = "Human",
        ai_prefix: str = "AI",
        **kwargs
    ):
        """
        Initialize session-aware memory.
        
        Args:
            llm: LLM for summarization
            session_manager: Session management service
            session_id: Session identifier
            bot_type: Type of bot
            max_token_limit: Maximum token limit for memory
            memory_key: Key to use for memory in chain inputs/outputs
            human_prefix: Prefix for human messages
            ai_prefix: Prefix for AI messages
        """
        super().__init__(
            llm=llm,
            memory_key=memory_key,
            human_prefix=human_prefix,
            ai_prefix=ai_prefix,
            max_token_limit=max_token_limit,
            return_messages=True,
            **kwargs
        )
        self.session_manager = session_manager
        self.session_id = session_id
        self.bot_type = bot_type
        self.logger = logging.getLogger(__name__)
        
        # Load existing memory if available
        self._load_from_session()
    
    def _load_from_session(self) -> None:
        """
        Load memory from session if available.
        """
        try:
            session_memory = self.session_manager.get_session_memory(self.session_id)
            if session_memory:
                self.chat_memory = session_memory
                self.logger.info(f"Loaded memory from session {self.session_id}")
        except Exception as e:
            self.logger.warning(f"Failed to load memory from session: {e}")
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """
        Save context from this conversation turn and persist to session.
        
        Args:
            inputs: Input values
            outputs: Output values
        """
        super().save_context(inputs, outputs)
        
        # Save to session
        try:
            self.session_manager.store_session_memory(
                self.session_id, 
                self.chat_memory
            )
            self.logger.debug(f"Saved memory to session {self.session_id}")
        except Exception as e:
            self.logger.warning(f"Failed to save memory to session: {e}")
    
    def clear(self) -> None:
        """
        Clear memory and remove from session.
        """
        super().clear()
        
        # Clear from session
        try:
            self.session_manager.clear_session_memory(self.session_id)
            self.logger.info(f"Cleared memory from session {self.session_id}")
        except Exception as e:
            self.logger.warning(f"Failed to clear memory from session: {e}")
    
    def get_historical_summary(self) -> str:
        """
        Get a summary of the conversation history.
        
        Returns:
            A string summary of the conversation history
        """
        # Use the built-in summarization capability
        buffer = super().load_memory_variables({})
        if isinstance(buffer[self.memory_key], List) and buffer[self.memory_key]:
            # Join messages into a string summary
            summary_messages = []
            for message in buffer[self.memory_key]:
                if isinstance(message, BaseMessage):
                    prefix = self.human_prefix if message.type == "human" else self.ai_prefix
                    summary_messages.append(f"{prefix}: {message.content}")
                else:
                    summary_messages.append(str(message))
            
            return "\n".join(summary_messages)
        else:
            return "" 