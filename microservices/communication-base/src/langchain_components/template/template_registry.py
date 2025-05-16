"""
Template registry for managing prompt templates.

This module provides a registry for storing, retrieving, and managing 
prompt templates for different bot types and use cases.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional, Set, Union
from pathlib import Path

from langchain.prompts import (
    ChatPromptTemplate, 
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,
    MessagesPlaceholder
)

class TemplateRegistry:
    """
    Template registry for managing prompt templates.
    
    This class provides a centralized registry for storing, retrieving, and
    managing prompt templates for different bot types and use cases. Templates
    can be loaded from files or configuration and are indexed for efficient
    retrieval.
    """
    
    def __init__(
        self,
        config_integration: Any = None,
        template_dir: Optional[str] = None,
        cache_enabled: bool = True
    ):
        """
        Initialize template registry.
        
        Args:
            config_integration: Integration with the config system
            template_dir: Directory containing template files
            cache_enabled: Whether to cache templates
        """
        self.config_integration = config_integration
        self.template_dir = template_dir
        self.cache_enabled = cache_enabled
        self.logger = logging.getLogger(__name__)
        
        # Template cache by bot type and template name
        self.template_cache: Dict[str, Dict[str, Any]] = {}
        
        # Template metadata by bot type and template name
        self.template_metadata: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # Initialize registry
        self._init_registry()
    
    def _init_registry(self) -> None:
        """
        Initialize registry by loading templates from directory.
        """
        # Load templates from directory if provided
        if self.template_dir and os.path.exists(self.template_dir):
            try:
                self._load_templates_from_directory(self.template_dir)
                self.logger.info(f"Loaded templates from directory: {self.template_dir}")
            except Exception as e:
                self.logger.error(f"Failed to load templates from directory: {e}", exc_info=True)
    
    def _load_templates_from_directory(self, directory: str) -> None:
        """
        Load templates from a directory.
        
        Args:
            directory: Directory containing template files
        """
        # Walk through directory and load templates
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.json', '.yaml', '.yml')):
                    try:
                        file_path = os.path.join(root, file)
                        
                        # Extract bot type from directory structure
                        rel_path = os.path.relpath(root, directory)
                        bot_type = rel_path.split(os.path.sep)[0] if os.path.sep in rel_path else "common"
                        
                        # Load template file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            if file.endswith('.json'):
                                template_data = json.load(f)
                            else:
                                # For YAML files, we need yaml module
                                import yaml
                                template_data = yaml.safe_load(f)
                        
                        # Extract template name from filename
                        template_name = os.path.splitext(file)[0]
                        
                        # Store template
                        self._store_template(bot_type, template_name, template_data)
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to load template from {file}: {e}")
    
    def _store_template(
        self, 
        bot_type: str, 
        template_name: str, 
        template_data: Dict[str, Any]
    ) -> None:
        """
        Store template in registry.
        
        Args:
            bot_type: Type of bot
            template_name: Template name
            template_data: Template data
        """
        # Initialize bot type in cache and metadata if not exists
        if bot_type not in self.template_metadata:
            self.template_metadata[bot_type] = {}
        
        if self.cache_enabled and bot_type not in self.template_cache:
            self.template_cache[bot_type] = {}
        
        # Extract metadata
        metadata = {
            "name": template_name,
            "description": template_data.get("description", ""),
            "type": template_data.get("type", "chat"),
            "tags": template_data.get("tags", []),
            "version": template_data.get("version", "1.0"),
            "created_at": template_data.get("created_at", ""),
            "updated_at": template_data.get("updated_at", ""),
            "author": template_data.get("author", "")
        }
        
        # Store metadata
        self.template_metadata[bot_type][template_name] = metadata
        
        # Store template in cache if enabled
        if self.cache_enabled:
            self.template_cache[bot_type][template_name] = template_data
    
    def get_template(
        self, 
        bot_type: str, 
        template_name: str,
        use_fallback: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get template by bot type and name.
        
        Args:
            bot_type: Type of bot
            template_name: Template name
            use_fallback: Whether to fallback to common templates if bot-specific not found
            
        Returns:
            Template data or None if not found
        """
        # Check cache first if enabled
        if self.cache_enabled:
            # Check bot-specific template
            if bot_type in self.template_cache and template_name in self.template_cache[bot_type]:
                return self.template_cache[bot_type][template_name]
            
            # Check common template if fallback enabled
            if use_fallback and "common" in self.template_cache and template_name in self.template_cache["common"]:
                return self.template_cache["common"][template_name]
        
        # If not in cache or cache disabled, try to load from config
        if self.config_integration:
            try:
                # Get bot-specific template from config
                bot_config = self.config_integration.get_config(bot_type)
                templates = bot_config.get("templates", {})
                
                if template_name in templates:
                    template_data = templates[template_name]
                    
                    # Store in cache if enabled
                    if self.cache_enabled:
                        if bot_type not in self.template_cache:
                            self.template_cache[bot_type] = {}
                        self.template_cache[bot_type][template_name] = template_data
                    
                    return template_data
                
                # Check common templates in config if fallback enabled
                if use_fallback:
                    common_config = self.config_integration.get_config("common")
                    common_templates = common_config.get("templates", {})
                    
                    if template_name in common_templates:
                        template_data = common_templates[template_name]
                        
                        # Store in cache if enabled
                        if self.cache_enabled:
                            if "common" not in self.template_cache:
                                self.template_cache["common"] = {}
                            self.template_cache["common"][template_name] = template_data
                        
                        return template_data
            except Exception as e:
                self.logger.warning(f"Failed to get template from config: {e}")
        
        # If still not found, try to load from file
        if self.template_dir:
            try:
                # Try bot-specific template
                bot_template_path = os.path.join(self.template_dir, bot_type, f"{template_name}.json")
                if os.path.exists(bot_template_path):
                    with open(bot_template_path, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    
                    # Store in cache if enabled
                    if self.cache_enabled:
                        if bot_type not in self.template_cache:
                            self.template_cache[bot_type] = {}
                        self.template_cache[bot_type][template_name] = template_data
                    
                    return template_data
                
                # Try common template if fallback enabled
                if use_fallback:
                    common_template_path = os.path.join(self.template_dir, "common", f"{template_name}.json")
                    if os.path.exists(common_template_path):
                        with open(common_template_path, 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                        
                        # Store in cache if enabled
                        if self.cache_enabled:
                            if "common" not in self.template_cache:
                                self.template_cache["common"] = {}
                            self.template_cache["common"][template_name] = template_data
                        
                        return template_data
            except Exception as e:
                self.logger.warning(f"Failed to load template from file: {e}")
        
        # Template not found
        return None
    
    def get_prompt_template(
        self, 
        bot_type: str, 
        template_name: str,
        use_fallback: bool = True
    ) -> Optional[ChatPromptTemplate]:
        """
        Get a LangChain prompt template by bot type and name.
        
        Args:
            bot_type: Type of bot
            template_name: Template name
            use_fallback: Whether to fallback to common templates if bot-specific not found
            
        Returns:
            LangChain prompt template or None if not found
        """
        # Get template data
        template_data = self.get_template(bot_type, template_name, use_fallback)
        
        if not template_data:
            return None
        
        # Convert to LangChain prompt template
        try:
            return self._create_prompt_template(template_data)
        except Exception as e:
            self.logger.error(f"Failed to create prompt template: {e}", exc_info=True)
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
                    if placeholder_type == "chat_history":
                        messages.append(MessagesPlaceholder(variable_name="chat_history"))
                    elif placeholder_type == "agent_scratchpad":
                        messages.append(MessagesPlaceholder(variable_name="agent_scratchpad"))
                    else:
                        # Generic placeholder
                        messages.append(MessagesPlaceholder(variable_name=placeholder_type))
            
            # Create chat prompt template
            return ChatPromptTemplate.from_messages(messages)
        
        else:
            raise ValueError(f"Unsupported template type: {template_type}")
    
    def get_template_names(self, bot_type: str) -> List[str]:
        """
        Get names of all templates for a bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            List of template names
        """
        # Check metadata
        if bot_type in self.template_metadata:
            return list(self.template_metadata[bot_type].keys())
        
        # Check cache if enabled
        if self.cache_enabled and bot_type in self.template_cache:
            return list(self.template_cache[bot_type].keys())
        
        # Check directory if provided
        if self.template_dir:
            bot_template_dir = os.path.join(self.template_dir, bot_type)
            if os.path.exists(bot_template_dir) and os.path.isdir(bot_template_dir):
                template_names = []
                for file in os.listdir(bot_template_dir):
                    if file.endswith(('.json', '.yaml', '.yml')):
                        template_name = os.path.splitext(file)[0]
                        template_names.append(template_name)
                return template_names
        
        # Check config if available
        if self.config_integration:
            try:
                bot_config = self.config_integration.get_config(bot_type)
                templates = bot_config.get("templates", {})
                return list(templates.keys())
            except Exception:
                pass
        
        return []
    
    def get_template_metadata(
        self, 
        bot_type: str, 
        template_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a template.
        
        Args:
            bot_type: Type of bot
            template_name: Template name
            
        Returns:
            Template metadata or None if not found
        """
        # Check metadata cache
        if bot_type in self.template_metadata and template_name in self.template_metadata[bot_type]:
            return self.template_metadata[bot_type][template_name]
        
        # Try to load template to get metadata
        template_data = self.get_template(bot_type, template_name)
        
        if template_data:
            # Extract metadata
            metadata = {
                "name": template_name,
                "description": template_data.get("description", ""),
                "type": template_data.get("type", "chat"),
                "tags": template_data.get("tags", []),
                "version": template_data.get("version", "1.0"),
                "created_at": template_data.get("created_at", ""),
                "updated_at": template_data.get("updated_at", ""),
                "author": template_data.get("author", "")
            }
            
            # Cache metadata
            if bot_type not in self.template_metadata:
                self.template_metadata[bot_type] = {}
            self.template_metadata[bot_type][template_name] = metadata
            
            return metadata
        
        return None
    
    def register_template(
        self, 
        bot_type: str, 
        template_name: str, 
        template_data: Dict[str, Any]
    ) -> bool:
        """
        Register a new template.
        
        Args:
            bot_type: Type of bot
            template_name: Template name
            template_data: Template data
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Validate template data
            if "type" not in template_data:
                template_data["type"] = "chat"
            
            if template_data["type"] == "chat" and "messages" not in template_data:
                raise ValueError("Chat template must have messages")
            
            # Store template
            self._store_template(bot_type, template_name, template_data)
            
            # Save to file if template directory provided
            if self.template_dir:
                bot_template_dir = os.path.join(self.template_dir, bot_type)
                os.makedirs(bot_template_dir, exist_ok=True)
                
                template_path = os.path.join(bot_template_dir, f"{template_name}.json")
                with open(template_path, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register template: {e}", exc_info=True)
            return False
    
    def update_template(
        self, 
        bot_type: str, 
        template_name: str, 
        template_data: Dict[str, Any]
    ) -> bool:
        """
        Update an existing template.
        
        Args:
            bot_type: Type of bot
            template_name: Template name
            template_data: Updated template data
            
        Returns:
            True if update successful, False otherwise
        """
        # Check if template exists
        existing_template = self.get_template(bot_type, template_name)
        
        if not existing_template:
            self.logger.warning(f"Template not found: {bot_type}/{template_name}")
            return False
        
        # Update template
        return self.register_template(bot_type, template_name, template_data)
    
    def delete_template(self, bot_type: str, template_name: str) -> bool:
        """
        Delete a template.
        
        Args:
            bot_type: Type of bot
            template_name: Template name
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Remove from cache if enabled
            if self.cache_enabled and bot_type in self.template_cache:
                if template_name in self.template_cache[bot_type]:
                    del self.template_cache[bot_type][template_name]
            
            # Remove from metadata
            if bot_type in self.template_metadata:
                if template_name in self.template_metadata[bot_type]:
                    del self.template_metadata[bot_type][template_name]
            
            # Delete file if template directory provided
            if self.template_dir:
                template_path = os.path.join(self.template_dir, bot_type, f"{template_name}.json")
                if os.path.exists(template_path):
                    os.remove(template_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete template: {e}", exc_info=True)
            return False
    
    def find_templates(
        self, 
        tags: Optional[List[str]] = None,
        bot_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find templates by tags and/or bot type.
        
        Args:
            tags: List of tags to filter by
            bot_type: Bot type to filter by
            
        Returns:
            List of matching template metadata
        """
        results = []
        
        # Determine bot types to search
        bot_types = [bot_type] if bot_type else list(self.template_metadata.keys())
        
        # Search templates
        for bt in bot_types:
            if bt in self.template_metadata:
                for template_name, metadata in self.template_metadata[bt].items():
                    # Check if template matches tags
                    if tags:
                        template_tags = metadata.get("tags", [])
                        if not all(tag in template_tags for tag in tags):
                            continue
                    
                    # Add template to results
                    result = metadata.copy()
                    result["bot_type"] = bt
                    results.append(result)
        
        return results
    
    def create_template_directory(self, directory: str) -> bool:
        """
        Create a template directory with standard structure.
        
        Args:
            directory: Template directory path
            
        Returns:
            True if creation successful, False otherwise
        """
        try:
            # Create main directory
            os.makedirs(directory, exist_ok=True)
            
            # Create bot-specific directories
            for bot_type in ["common", "consultancy", "sales", "support"]:
                os.makedirs(os.path.join(directory, bot_type), exist_ok=True)
            
            # Create example template
            example_template = {
                "type": "chat",
                "description": "Example template",
                "tags": ["example"],
                "version": "1.0",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant."
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
            
            example_path = os.path.join(directory, "common", "example.json")
            with open(example_path, 'w', encoding='utf-8') as f:
                json.dump(example_template, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create template directory: {e}", exc_info=True)
            return False
    
    def clear_cache(self) -> None:
        """
        Clear template cache.
        """
        if self.cache_enabled:
            self.template_cache = {}
            self.logger.info("Template cache cleared")
    
    def reload_templates(self) -> None:
        """
        Reload templates from disk.
        """
        # Clear cache
        self.clear_cache()
        
        # Clear metadata
        self.template_metadata = {}
        
        # Reload templates
        self._init_registry()
        self.logger.info("Templates reloaded") 