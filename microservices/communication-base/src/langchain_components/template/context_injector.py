"""
Context injector for enriching templates with relevant contextual information.

This module provides a context injector that prepares and injects relevant
context into prompt templates based on conversation history, memory, and
other available information.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set, Union, Tuple

class ContextInjector:
    """
    Context injector for enriching templates with relevant contextual information.
    
    This class prepares and injects various types of context into prompt templates,
    including conversation history, entity information, KB context, and user
    preferences, to provide richer context for the LLM.
    """
    
    def __init__(
        self,
        config_integration: Any = None,
        memory_manager: Any = None,
        entity_store: Any = None,
        rag_coordinator: Any = None,
        profile_manager: Any = None,
        context_truncation_limit: int = 4000
    ):
        """
        Initialize context injector.
        
        Args:
            config_integration: Integration with the config system
            memory_manager: Memory manager for retrieving conversation history
            entity_store: Entity store for accessing known entities
            rag_coordinator: RAG coordinator for retrieving knowledge
            profile_manager: Profile manager for user preferences
            context_truncation_limit: Maximum token limit for context
        """
        self.config_integration = config_integration
        self.memory_manager = memory_manager
        self.entity_store = entity_store
        self.rag_coordinator = rag_coordinator
        self.profile_manager = profile_manager
        self.context_truncation_limit = context_truncation_limit
        self.logger = logging.getLogger(__name__)
    
    def inject_context(
        self,
        template_data: Dict[str, Any],
        user_query: str,
        session_id: str,
        bot_type: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Inject context into a template.
        
        Args:
            template_data: Template data to inject context into
            user_query: Current user query
            session_id: Session identifier
            bot_type: Type of bot
            additional_context: Additional context to inject
            
        Returns:
            Template data with injected context
        """
        # Initialize context variables
        context_variables = additional_context or {}
        
        # Get bot configuration for context settings
        context_settings = self._get_context_settings(bot_type)
        
        # Always include the user query
        context_variables["input"] = user_query
        
        # Inject conversation history if enabled and available
        if context_settings.get("include_history", True) and self.memory_manager:
            try:
                history = self.memory_manager.get_chat_history(session_id, bot_type)
                context_variables["chat_history"] = history
            except Exception as e:
                self.logger.warning(f"Failed to retrieve chat history: {e}")
        
        # Inject memory summary if enabled and available
        if context_settings.get("include_memory_summary", True) and self.memory_manager:
            try:
                memory_summary = self.memory_manager.get_memory_summary(session_id, bot_type)
                context_variables["memory_summary"] = memory_summary
            except Exception as e:
                self.logger.warning(f"Failed to retrieve memory summary: {e}")
        
        # Inject entity information if enabled and available
        if context_settings.get("include_entities", True) and self.entity_store:
            try:
                entities = self._get_relevant_entities(user_query, session_id, bot_type)
                context_variables["entities"] = entities
            except Exception as e:
                self.logger.warning(f"Failed to retrieve entities: {e}")
        
        # Inject RAG context if enabled and available
        if context_settings.get("include_rag", True) and self.rag_coordinator:
            try:
                rag_context = self._get_rag_context(user_query, session_id, bot_type)
                context_variables["knowledge_context"] = rag_context
            except Exception as e:
                self.logger.warning(f"Failed to retrieve RAG context: {e}")
        
        # Inject user profile if enabled and available
        if context_settings.get("include_user_profile", True) and self.profile_manager:
            try:
                user_profile = self.profile_manager.get_user_profile(session_id)
                context_variables["user_profile"] = user_profile
            except Exception as e:
                self.logger.warning(f"Failed to retrieve user profile: {e}")
        
        # Apply context to template
        injected_template = self._apply_context_to_template(template_data, context_variables)
        
        return injected_template
    
    def _get_context_settings(self, bot_type: str) -> Dict[str, Any]:
        """
        Get context settings for a bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Context settings
        """
        # Default settings
        default_settings = {
            "include_history": True,
            "include_memory_summary": True,
            "include_entities": True,
            "include_rag": True,
            "include_user_profile": True,
            "max_history_messages": 10,
            "max_entities": 5,
            "max_rag_chunks": 3
        }
        
        # If no config integration, return defaults
        if not self.config_integration:
            return default_settings
        
        try:
            # Get bot-specific settings
            bot_config = self.config_integration.get_config(bot_type)
            context_settings = bot_config.get("context_settings", {})
            
            # Merge with defaults
            merged_settings = {**default_settings, **context_settings}
            return merged_settings
        except Exception as e:
            self.logger.warning(f"Failed to get context settings: {e}")
            return default_settings
    
    def _get_relevant_entities(
        self,
        user_query: str,
        session_id: str,
        bot_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get entities relevant to the current query.
        
        Args:
            user_query: Current user query
            session_id: Session identifier
            bot_type: Type of bot
            
        Returns:
            List of relevant entities
        """
        if not self.entity_store:
            return []
        
        # Get context settings
        context_settings = self._get_context_settings(bot_type)
        max_entities = context_settings.get("max_entities", 5)
        
        try:
            # Get most important entities from entity store
            entities = self.entity_store.get_important_entities(
                session_id=session_id,
                limit=max_entities
            )
            
            # Format entities for context
            formatted_entities = []
            for entity in entities:
                formatted_entity = {
                    "name": entity.get("name", ""),
                    "type": entity.get("type", ""),
                    "description": entity.get("description", ""),
                    "attributes": entity.get("attributes", {})
                }
                formatted_entities.append(formatted_entity)
            
            return formatted_entities
        except Exception as e:
            self.logger.warning(f"Error retrieving entities: {e}")
            return []
    
    def _get_rag_context(
        self,
        user_query: str,
        session_id: str,
        bot_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get RAG context relevant to the current query.
        
        Args:
            user_query: Current user query
            session_id: Session identifier
            bot_type: Type of bot
            
        Returns:
            RAG context
        """
        if not self.rag_coordinator:
            return []
        
        # Get context settings
        context_settings = self._get_context_settings(bot_type)
        max_chunks = context_settings.get("max_rag_chunks", 3)
        
        try:
            # Get relevant documents from RAG coordinator
            documents = self.rag_coordinator.retrieve_relevant(
                query=user_query,
                session_id=session_id,
                bot_type=bot_type,
                limit=max_chunks
            )
            
            # Format documents for context
            context_chunks = []
            for doc in documents:
                chunk = {
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", ""),
                    "relevance": doc.metadata.get("relevance", 0.0)
                }
                context_chunks.append(chunk)
            
            return context_chunks
        except Exception as e:
            self.logger.warning(f"Error retrieving RAG context: {e}")
            return []
    
    def _apply_context_to_template(
        self,
        template_data: Dict[str, Any],
        context_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply context variables to a template.
        
        Args:
            template_data: Template data
            context_variables: Context variables
            
        Returns:
            Template with context applied
        """
        # Make a copy of the template to avoid modifying the original
        injected_template = template_data.copy()
        
        # Process different template types
        template_type = template_data.get("type", "chat")
        
        if template_type == "chat":
            # For chat templates, we need to handle messages
            messages_data = template_data.get("messages", [])
            injected_messages = []
            
            for message in messages_data:
                # Check if it's a placeholder message
                if message.get("role") == "placeholder":
                    placeholder_type = message.get("placeholder_type", "")
                    
                    # Handle special placeholders
                    if placeholder_type == "chat_history" and "chat_history" in context_variables:
                        # Directly use the chat history
                        continue  # Skip this placeholder, it will be handled by LangChain
                    elif placeholder_type == "agent_scratchpad" and "agent_scratchpad" in context_variables:
                        # Directly use the agent scratchpad
                        continue  # Skip this placeholder, it will be handled by LangChain
                    else:
                        # Generic placeholder (not a special one)
                        if placeholder_type in context_variables:
                            # Create a system message with the content
                            new_message = {
                                "role": "system",
                                "content": str(context_variables[placeholder_type])
                            }
                            injected_messages.append(new_message)
                else:
                    # Get message content
                    content = message.get("content", "")
                    
                    # Replace variables in content
                    for key, value in context_variables.items():
                        if isinstance(value, (str, int, float, bool)):
                            # Simple replacement for primitive types
                            pattern = r"\{" + re.escape(key) + r"\}"
                            content = re.sub(pattern, str(value), content)
                    
                    # Create injected message
                    injected_message = message.copy()
                    injected_message["content"] = content
                    injected_messages.append(injected_message)
            
            # Update template with injected messages
            injected_template["messages"] = injected_messages
            
            # Add context variables to template variables
            if "variables" not in injected_template:
                injected_template["variables"] = {}
            
            for key, value in context_variables.items():
                if key not in injected_template["variables"]:
                    injected_template["variables"][key] = value
        
        else:
            # For other template types, just add context variables
            if "variables" not in injected_template:
                injected_template["variables"] = {}
            
            for key, value in context_variables.items():
                if key not in injected_template["variables"]:
                    injected_template["variables"][key] = value
        
        return injected_template
    
    def truncate_context(self, context: str, max_tokens: Optional[int] = None) -> str:
        """
        Truncate context to fit within token limit.
        
        Args:
            context: Context string to truncate
            max_tokens: Maximum tokens allowed (uses default if None)
            
        Returns:
            Truncated context
        """
        max_tokens = max_tokens or self.context_truncation_limit
        
        # Simple approximation: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        
        if len(context) <= max_chars:
            return context
        
        # Truncate to max_chars and add indicator
        truncated = context[:max_chars]
        return truncated + "... [truncated]"
    
    def get_special_placeholders(self) -> List[str]:
        """
        Get list of special placeholders handled by LangChain.
        
        Returns:
            List of special placeholder names
        """
        return ["chat_history", "agent_scratchpad"]
    
    def prepare_variables_for_prompt(
        self,
        context_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare variables for use in a LangChain prompt.
        
        Args:
            context_variables: Raw context variables
            
        Returns:
            Processed variables suitable for a LangChain prompt
        """
        processed = {}
        
        # Copy simple variables directly
        for key, value in context_variables.items():
            if isinstance(value, (str, int, float, bool)) or key in self.get_special_placeholders():
                processed[key] = value
                continue
            
            # Handle complex types
            if isinstance(value, list):
                # Format lists as bulleted items
                if value and isinstance(value[0], dict):
                    # List of dictionaries
                    items = []
                    for item in value:
                        item_str = self._format_dict_for_prompt(item)
                        items.append(f"• {item_str}")
                    processed[key] = "\n".join(items)
                else:
                    # Simple list
                    items = [f"• {item}" for item in value]
                    processed[key] = "\n".join(items)
            elif isinstance(value, dict):
                # Format dictionary
                processed[key] = self._format_dict_for_prompt(value)
            else:
                # Fallback
                processed[key] = str(value)
        
        return processed
    
    def _format_dict_for_prompt(self, data: Dict[str, Any]) -> str:
        """
        Format a dictionary for inclusion in a prompt.
        
        Args:
            data: Dictionary to format
            
        Returns:
            Formatted string
        """
        lines = []
        
        for key, value in data.items():
            if isinstance(value, dict):
                # Nested dictionary
                nested_str = ", ".join(f"{k}: {v}" for k, v in value.items())
                lines.append(f"{key}: {{{nested_str}}}")
            elif isinstance(value, list):
                # List
                if value:
                    list_str = ", ".join(str(item) for item in value)
                    lines.append(f"{key}: [{list_str}]")
                else:
                    lines.append(f"{key}: []")
            else:
                # Simple value
                lines.append(f"{key}: {value}")
        
        return "; ".join(lines) 