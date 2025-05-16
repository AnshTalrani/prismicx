"""
Conversation Manager

This module provides the central orchestration layer for conversation flows,
managing the state machine, context, and transitions for different bot types.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import uuid

from src.config.config_integration import ConfigIntegration
from src.models.llm.base_llm_manager import BaseLLMManager
from src.models.adapters.adapter_manager import AdapterManager
from src.langchain_components.rag.langchain_integration import LangChainRAGIntegration
from src.conversation.state.state_machine import ConversationStateMachine
from src.conversation.context.context_store import ContextStore
from src.conversation.transitions.engine import TransitionEngine
from src.conversation.middleware.pipeline import MiddlewarePipeline

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Conversation Manager
    
    Orchestrates the entire conversation lifecycle, including state management,
    context tracking, response generation, and transition handling.
    """
    
    def __init__(
        self,
        config_integration: Optional[ConfigIntegration] = None,
        adapter_manager: Optional[AdapterManager] = None,
        llm_manager: Optional[BaseLLMManager] = None,
        rag_integration: Optional[LangChainRAGIntegration] = None,
    ):
        """
        Initialize the conversation manager.
        
        Args:
            config_integration: Configuration integration instance
            adapter_manager: Adapter manager instance
            llm_manager: LLM manager instance
            rag_integration: RAG integration instance
        """
        self.config_integration = config_integration or ConfigIntegration()
        self.adapter_manager = adapter_manager or AdapterManager()
        self.llm_manager = llm_manager
        self.rag_integration = rag_integration
        
        # Initialize components
        self.context_store = ContextStore(self.config_integration)
        self.state_machines: Dict[str, ConversationStateMachine] = {}
        self.transition_engine = TransitionEngine(self.config_integration)
        self.middleware_pipeline = MiddlewarePipeline(self.config_integration)
        
        # Active conversations
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Conversation manager initialized")
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        user_id: str,
        bot_type: str,
        platform: str = "web",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an incoming message and generate a response.
        
        Args:
            message: The message text
            session_id: Session identifier
            user_id: User identifier
            bot_type: Type of bot (sales, consultancy, support)
            platform: Communication platform (web, email, sms, etc.)
            metadata: Additional metadata about the message
            
        Returns:
            Response information including text and actions
        """
        logger.info(f"Processing message for session {session_id}, bot type {bot_type}")
        
        # Get or create conversation state machine
        state_machine = self._get_state_machine(bot_type)
        
        # Get or initialize conversation context
        context = await self.context_store.get_context(session_id, user_id, bot_type)
        
        # If new conversation, initialize first state
        if not context.get("current_state"):
            initial_state = state_machine.get_initial_state()
            context["current_state"] = initial_state
            context["conversation_start_time"] = datetime.utcnow().isoformat()
            context["platform"] = platform
            await self.context_store.update_context(session_id, context)
        
        # Apply pre-processing middleware
        processed_message, updated_context = await self.middleware_pipeline.apply_pre_processors(
            message=message,
            context=context,
            bot_type=bot_type
        )
        
        # Update context with preprocessor results
        if updated_context:
            await self.context_store.update_context(session_id, updated_context)
            context = updated_context
        
        # Get current state
        current_state_name = context.get("current_state")
        current_state = state_machine.get_state(current_state_name)
        
        if not current_state:
            logger.error(f"Invalid state {current_state_name} for bot type {bot_type}")
            # Fall back to initial state
            current_state_name = state_machine.get_initial_state()
            current_state = state_machine.get_state(current_state_name)
            context["current_state"] = current_state_name
            await self.context_store.update_context(session_id, context)
        
        # Execute state-specific logic
        state_response = await state_machine.execute_state(
            state_name=current_state_name,
            message=processed_message,
            context=context,
            user_id=user_id,
            session_id=session_id
        )
        
        # Update context with state execution results
        if state_response.get("context_updates"):
            for key, value in state_response["context_updates"].items():
                context[key] = value
            await self.context_store.update_context(session_id, context)
        
        # Activate appropriate adapters for this state
        model_id = "default"  # This would be configured or determined from context
        if self.llm_manager and state_response.get("adapters"):
            model = self.llm_manager.get_model(model_id)
            for adapter_name in state_response.get("adapters", []):
                success = self.adapter_manager.activate_adapter(model, adapter_name)
                if not success:
                    logger.warning(f"Failed to activate adapter {adapter_name}")
        
        # Generate response using RAG if available
        response_text = state_response.get("response", "")
        if self.rag_integration and state_response.get("use_rag", False):
            try:
                rag_result = await self.rag_integration.arun_rag_chain(
                    query=processed_message,
                    bot_type=bot_type,
                    session_id=session_id,
                    user_id=user_id,
                    chain_type=state_response.get("rag_chain_type", "stuff")
                )
                response_text = rag_result.get("answer", response_text)
            except Exception as e:
                logger.error(f"Error using RAG: {e}")
                # Continue with the regular response
        
        # Check for transitions
        next_state = await self.transition_engine.evaluate_transitions(
            current_state=current_state_name,
            bot_type=bot_type,
            message=processed_message,
            context=context,
            response=state_response
        )
        
        # If transition detected, update state
        if next_state and next_state != current_state_name:
            logger.info(f"Transitioning from {current_state_name} to {next_state}")
            context["previous_state"] = current_state_name
            context["current_state"] = next_state
            context["state_entry_time"] = datetime.utcnow().isoformat()
            await self.context_store.update_context(session_id, context)
            
            # Execute entry actions for new state
            entry_response = await state_machine.execute_state_entry(
                state_name=next_state,
                context=context,
                user_id=user_id,
                session_id=session_id
            )
            
            # If entry provides a response, use it
            if entry_response.get("response"):
                response_text = entry_response.get("response")
        
        # Apply response post-processing middleware
        final_response, updated_context = await self.middleware_pipeline.apply_post_processors(
            response=response_text,
            original_message=message,
            context=context,
            bot_type=bot_type
        )
        
        # Update context with postprocessor results
        if updated_context:
            await self.context_store.update_context(session_id, updated_context)
        
        # Track this active conversation and update timeout
        self._update_active_conversation(
            session_id=session_id,
            bot_type=bot_type,
            platform=platform,
            state=context.get("current_state")
        )
        
        # Update response information
        response_info = {
            "session_id": session_id,
            "response": final_response,
            "current_state": context.get("current_state"),
            "actions": state_response.get("actions", [])
        }
        
        logger.info(f"Generated response for session {session_id}, state {context.get('current_state')}")
        return response_info
    
    def _get_state_machine(self, bot_type: str) -> ConversationStateMachine:
        """
        Get or create a state machine for the given bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            ConversationStateMachine for the bot type
        """
        if bot_type not in self.state_machines:
            self.state_machines[bot_type] = ConversationStateMachine(bot_type, self.config_integration)
        return self.state_machines[bot_type]
    
    def _update_active_conversation(
        self,
        session_id: str,
        bot_type: str,
        platform: str,
        state: str
    ) -> None:
        """
        Update active conversation tracking.
        
        Args:
            session_id: Session identifier
            bot_type: Type of bot
            platform: Communication platform
            state: Current conversation state
        """
        # Get timeout settings
        config = self.config_integration.get_config(bot_type)
        timeout_config = config.get("conversation.timeouts", {})
        
        # Determine timeout based on bot type and state
        timeout_minutes = 5  # Default 5 minutes
        
        # Sales bot has special timeouts
        if bot_type == "sales":
            if state in ["typing", "appointment_confirmation"]:
                timeout_minutes = 15  # Extended for active engagement
            else:
                timeout_minutes = 7  # Mid-conversation for sales
        # Support bot has tiered timeouts
        elif bot_type == "support":
            if state in ["critical_issue", "payment_issue"]:
                timeout_minutes = 5  # Tier 1 issues
            else:
                timeout_minutes = 15  # Tier 2/3 issues
        # Consultancy bot
        elif bot_type == "consultancy":
            timeout_minutes = 10  # Default for consultancy
        
        # Override with specific state timeout if configured
        state_timeout = timeout_config.get(f"states.{state}", None)
        if state_timeout:
            timeout_minutes = state_timeout
        
        # Set timeout
        timeout = datetime.utcnow().timestamp() + (timeout_minutes * 60)
        
        self.active_conversations[session_id] = {
            "bot_type": bot_type,
            "platform": platform,
            "state": state,
            "timeout": timeout,
            "last_activity": datetime.utcnow().timestamp()
        }
    
    async def check_timeouts(self) -> None:
        """
        Check for timed out conversations and close them appropriately.
        Should be called periodically by a scheduler.
        """
        current_time = datetime.utcnow().timestamp()
        sessions_to_close = []
        
        for session_id, info in self.active_conversations.items():
            if current_time > info.get("timeout", 0):
                sessions_to_close.append((
                    session_id, 
                    info.get("bot_type"), 
                    info.get("platform"),
                    info.get("state")
                ))
        
        # Close timed out sessions
        for session_id, bot_type, platform, state in sessions_to_close:
            await self._close_conversation(session_id, bot_type, platform, state)
            del self.active_conversations[session_id]
    
    async def _close_conversation(
        self,
        session_id: str,
        bot_type: str,
        platform: str,
        state: str
    ) -> None:
        """
        Close a conversation gracefully.
        
        Args:
            session_id: Session identifier
            bot_type: Type of bot
            platform: Communication platform
            state: Current state name
        """
        logger.info(f"Closing conversation {session_id} for bot {bot_type}")
        
        # Get conversation context
        context = await self.context_store.get_context_by_session(session_id)
        if not context:
            return
        
        # Mark conversation as closed
        context["conversation_status"] = "closed"
        context["conversation_end_time"] = datetime.utcnow().isoformat()
        
        # Execute state-specific closing logic
        state_machine = self._get_state_machine(bot_type)
        
        try:
            close_response = await state_machine.execute_state_exit(
                state_name=state,
                context=context,
                session_id=session_id
            )
            
            # Store any final context updates
            if close_response.get("context_updates"):
                for key, value in close_response["context_updates"].items():
                    context[key] = value
            
            # Update context for the closed conversation
            await self.context_store.update_context(session_id, context)
            
            # If there are any closing actions, execute them
            if close_response.get("actions"):
                for action in close_response.get("actions", []):
                    # Execute action based on type
                    if action.get("type") == "notification":
                        # Send notification about conversation closing
                        pass
                    elif action.get("type") == "summary":
                        # Generate and store conversation summary
                        pass
                    # Add more action types as needed
        
        except Exception as e:
            logger.error(f"Error closing conversation {session_id}: {e}")
    
    async def get_active_conversation_count(self) -> Dict[str, int]:
        """
        Get count of active conversations by bot type.
        
        Returns:
            Dictionary with bot types as keys and counts as values
        """
        counts = {}
        for info in self.active_conversations.values():
            bot_type = info.get("bot_type")
            counts[bot_type] = counts.get(bot_type, 0) + 1
        return counts
    
    async def get_conversation_summary(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of the conversation.
        
        Args:
            session_id: Session identifier
            user_id: Optional user identifier
            
        Returns:
            Dictionary with conversation summary
        """
        context = await self.context_store.get_context_by_session(session_id)
        if not context:
            return {"error": "Conversation not found"}
        
        # Simple summary
        summary = {
            "session_id": session_id,
            "user_id": context.get("user_id"),
            "bot_type": context.get("bot_type"),
            "current_state": context.get("current_state"),
            "platform": context.get("platform"),
            "start_time": context.get("conversation_start_time"),
            "end_time": context.get("conversation_end_time"),
            "status": context.get("conversation_status", "active")
        }
        
        # Add more detailed summary if available
        if context.get("summary"):
            summary["details"] = context.get("summary")
        
        return summary 