"""
Template compiler for processing templates and generating LangChain prompts.

This module provides a compiler that processes templates with injected context
and converts them into LangChain-compatible format for use in chains and agents.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple

from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,
    MessagesPlaceholder
)
from langchain.schema import BaseMessage, AIMessage, HumanMessage, SystemMessage

class TemplateCompiler:
    """
    Template compiler for processing templates and generating LangChain prompts.
    
    This class compiles template data into LangChain-compatible formats,
    including prompt templates, message sequences, and raw prompt strings.
    """
    
    def __init__(
        self,
        template_registry: Any = None,
        context_injector: Any = None,
        config_integration: Any = None
    ):
        """
        Initialize template compiler.
        
        Args:
            template_registry: Registry for template lookup
            context_injector: Injector for adding context to templates
            config_integration: Integration with the config system
        """
        self.template_registry = template_registry
        self.context_injector = context_injector
        self.config_integration = config_integration
        self.logger = logging.getLogger(__name__)
    
    def compile_template(
        self,
        bot_type: str,
        template_name: str,
        user_query: str,
        session_id: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Optional[ChatPromptTemplate]:
        """
        Compile a template into a LangChain prompt template.
        
        Args:
            bot_type: Type of bot
            template_name: Template name
            user_query: Current user query
            session_id: Session identifier
            additional_context: Additional context to inject
            
        Returns:
            LangChain prompt template or None if compilation fails
        """
        try:
            # Get template data from registry
            template_data = self._get_template_data(bot_type, template_name)
            
            if not template_data:
                self.logger.warning(f"Template not found: {bot_type}/{template_name}")
                return None
            
            # Inject context if injector available
            if self.context_injector:
                template_data = self.context_injector.inject_context(
                    template_data=template_data,
                    user_query=user_query,
                    session_id=session_id,
                    bot_type=bot_type,
                    additional_context=additional_context
                )
            
            # Convert to LangChain prompt template
            return self._create_prompt_template(template_data)
            
        except Exception as e:
            self.logger.error(f"Failed to compile template: {e}", exc_info=True)
            return None
    
    def compile_template_with_messages(
        self,
        bot_type: str,
        template_name: str,
        user_query: str,
        session_id: str,
        chat_history: Optional[List[BaseMessage]] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Optional[ChatPromptTemplate]:
        """
        Compile a template with chat history messages.
        
        Args:
            bot_type: Type of bot
            template_name: Template name
            user_query: Current user query
            session_id: Session identifier
            chat_history: List of previous chat messages
            additional_context: Additional context to inject
            
        Returns:
            LangChain prompt template with chat history or None if compilation fails
        """
        # Add chat history to context
        context = additional_context or {}
        if chat_history:
            context["chat_history"] = chat_history
        
        # Compile template with chat history
        return self.compile_template(
            bot_type=bot_type,
            template_name=template_name,
            user_query=user_query,
            session_id=session_id,
            additional_context=context
        )
    
    def _get_template_data(
        self,
        bot_type: str,
        template_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get template data from registry or config.
        
        Args:
            bot_type: Type of bot
            template_name: Template name
            
        Returns:
            Template data or None if not found
        """
        # Try to get from registry first
        if self.template_registry:
            template_data = self.template_registry.get_template(bot_type, template_name)
            if template_data:
                return template_data
        
        # Try to get from config if registry failed
        if self.config_integration:
            try:
                bot_config = self.config_integration.get_config(bot_type)
                templates = bot_config.get("templates", {})
                
                if template_name in templates:
                    return templates[template_name]
                
                # Try common templates
                common_config = self.config_integration.get_config("common")
                common_templates = common_config.get("templates", {})
                
                if template_name in common_templates:
                    return common_templates[template_name]
            except Exception as e:
                self.logger.warning(f"Failed to get template from config: {e}")
        
        return None
    
    def _create_prompt_template(self, template_data: Dict[str, Any]) -> ChatPromptTemplate:
        """
        Create a LangChain prompt template from template data.
        
        Args:
            template_data: Template data
            
        Returns:
            LangChain prompt template
            
        Raises:
            ValueError: If template data is invalid
        """
        # Get template type
        template_type = template_data.get("type", "chat")
        
        if template_type == "chat":
            # Get messages
            messages_data = template_data.get("messages", [])
            
            if not messages_data:
                raise ValueError("Chat template must have messages")
            
            # Convert to LangChain message templates
            messages = []
            
            for message in messages_data:
                role = message.get("role", "")
                content = message.get("content", "")
                
                if role == "system":
                    messages.append(SystemMessagePromptTemplate.from_template(content))
                elif role == "human":
                    messages.append(HumanMessagePromptTemplate.from_template(content))
                elif role == "ai":
                    messages.append(AIMessagePromptTemplate.from_template(content))
                elif role == "placeholder":
                    # Handle special placeholders
                    placeholder_type = message.get("placeholder_type", "")
                    if placeholder_type:
                        messages.append(MessagesPlaceholder(variable_name=placeholder_type))
            
            # Create chat prompt template
            return ChatPromptTemplate.from_messages(messages)
        
        else:
            raise ValueError(f"Unsupported template type: {template_type}")
    
    def create_message_list(
        self,
        template_data: Dict[str, Any],
        context_variables: Dict[str, Any]
    ) -> List[BaseMessage]:
        """
        Create a list of LangChain messages from template data.
        
        Args:
            template_data: Template data
            context_variables: Context variables for template
            
        Returns:
            List of LangChain messages
            
        Raises:
            ValueError: If template data is invalid
        """
        # Get template type
        template_type = template_data.get("type", "chat")
        
        if template_type != "chat":
            raise ValueError(f"Cannot create message list from {template_type} template")
        
        # Get messages
        messages_data = template_data.get("messages", [])
        
        if not messages_data:
            raise ValueError("Chat template must have messages")
        
        # Convert to LangChain messages
        messages = []
        
        for message in messages_data:
            role = message.get("role", "")
            content = message.get("content", "")
            
            # Replace variables in content
            for key, value in context_variables.items():
                if isinstance(value, (str, int, float, bool)):
                    # Simple replacement for primitive types
                    content = content.replace(f"{{{key}}}", str(value))
            
            if role == "system":
                messages.append(SystemMessage(content=content))
            elif role == "human":
                messages.append(HumanMessage(content=content))
            elif role == "ai":
                messages.append(AIMessage(content=content))
            elif role == "placeholder":
                # Handle placeholders
                placeholder_type = message.get("placeholder_type", "")
                if placeholder_type in context_variables:
                    # Handle special placeholders
                    if placeholder_type == "chat_history":
                        if isinstance(context_variables[placeholder_type], list):
                            messages.extend(context_variables[placeholder_type])
                    else:
                        # Treat as system message
                        messages.append(SystemMessage(content=str(context_variables[placeholder_type])))
        
        return messages
    
    def render_template_to_string(
        self,
        template_data: Dict[str, Any],
        context_variables: Dict[str, Any]
    ) -> str:
        """
        Render a template to a string using context variables.
        
        Args:
            template_data: Template data
            context_variables: Context variables for template
            
        Returns:
            Rendered template string
            
        Raises:
            ValueError: If template data is invalid
        """
        # Get template type
        template_type = template_data.get("type", "chat")
        
        rendered_parts = []
        
        if template_type == "chat":
            # Get messages
            messages_data = template_data.get("messages", [])
            
            for message in messages_data:
                role = message.get("role", "")
                content = message.get("content", "")
                
                # Skip placeholders in string rendering
                if role == "placeholder":
                    placeholder_type = message.get("placeholder_type", "")
                    if placeholder_type in context_variables and isinstance(context_variables[placeholder_type], str):
                        rendered_parts.append(f"{context_variables[placeholder_type]}")
                    continue
                
                # Replace variables in content
                for key, value in context_variables.items():
                    if isinstance(value, (str, int, float, bool)):
                        # Simple replacement for primitive types
                        content = content.replace(f"{{{key}}}", str(value))
                
                # Add to rendered parts
                if role == "system":
                    rendered_parts.append(f"System: {content}")
                elif role == "human":
                    rendered_parts.append(f"Human: {content}")
                elif role == "ai":
                    rendered_parts.append(f"AI: {content}")
        
        else:
            # For non-chat templates, just use the raw template content
            raw_template = template_data.get("content", "")
            
            # Replace variables in content
            for key, value in context_variables.items():
                if isinstance(value, (str, int, float, bool)):
                    # Simple replacement for primitive types
                    raw_template = raw_template.replace(f"{{{key}}}", str(value))
            
            rendered_parts.append(raw_template)
        
        return "\n\n".join(rendered_parts)
    
    def get_default_template(
        self,
        bot_type: str,
        template_type: str = "conversation"
    ) -> Dict[str, Any]:
        """
        Get default template for a bot type and template type.
        
        Args:
            bot_type: Type of bot
            template_type: Type of template
            
        Returns:
            Default template data
        """
        if template_type == "conversation":
            return {
                "type": "chat",
                "description": f"Default conversation template for {bot_type}",
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are a {bot_type} bot. Provide helpful and accurate information."
                    },
                    {
                        "role": "placeholder",
                        "placeholder_type": "chat_history"
                    },
                    {
                        "role": "human",
                        "content": "{input}"
                    }
                ]
            }
        elif template_type == "agent":
            return {
                "type": "chat",
                "description": f"Default agent template for {bot_type}",
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are a {bot_type} agent with access to tools. Use the tools to help the user."
                    },
                    {
                        "role": "placeholder",
                        "placeholder_type": "chat_history"
                    },
                    {
                        "role": "human",
                        "content": "{input}"
                    },
                    {
                        "role": "placeholder",
                        "placeholder_type": "agent_scratchpad"
                    }
                ]
            }
        else:
            # Generic template
            return {
                "type": "chat",
                "description": f"Generic template for {bot_type}",
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are a {bot_type} assistant."
                    },
                    {
                        "role": "human",
                        "content": "{input}"
                    }
                ]
            }
    
    def register_template_from_messages(
        self,
        bot_type: str,
        template_name: str,
        messages: List[Dict[str, str]],
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Register a new template from message list.
        
        Args:
            bot_type: Type of bot
            template_name: Template name
            messages: List of message dictionaries with role and content
            description: Template description
            tags: List of tags
            
        Returns:
            True if registration successful, False otherwise
        """
        template_data = {
            "type": "chat",
            "description": description,
            "tags": tags or [],
            "messages": messages
        }
        
        # Register via registry if available
        if self.template_registry:
            return self.template_registry.register_template(
                bot_type=bot_type,
                template_name=template_name,
                template_data=template_data
            )
        
        # Otherwise, log error
        self.logger.error("Cannot register template: No template registry available")
        return False 