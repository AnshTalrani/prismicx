"""
Expert Registry for the Expert Base microservice.

This module provides functionality for loading and managing expert configurations.
"""

import os
import json
import yaml
from typing import Dict, List, Any, Optional, Set
from loguru import logger

from src.common.exceptions import ExpertNotFoundException, ConfigurationException
from src.modules.frameworks.base import BaseExpertFramework
from src.modules.frameworks.instagram import InstagramExpertFramework


class ExpertRegistry:
    """
    Registry for expert configurations and frameworks.
    
    This class manages the registration, loading, and retrieval of expert
    configurations and frameworks.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the expert registry.
        
        Args:
            config_path: Optional path to the expert configuration file.
                         If not provided, uses the default path from environment
                         variables or a default location.
        """
        self.experts = {}
        self.expert_frameworks = {}
        self.config_path = config_path or os.environ.get("EXPERT_CONFIG_PATH", "config/experts.yaml")
        
        logger.info(f"Initialized Expert Registry with config path: {self.config_path}")

    async def load_configurations(self) -> None:
        """
        Load expert configurations from the configuration file.
        
        This method loads the expert configurations from the specified YAML file
        and initializes the expert frameworks.
        
        Raises:
            ConfigurationException: If the configuration file cannot be loaded
                                   or contains invalid data.
        """
        logger.info(f"Loading expert configurations from {self.config_path}")
        
        try:
            # Load expert configurations
            with open(self.config_path, "r") as file:
                configurations = yaml.safe_load(file)
            
            logger.info(f"Loaded configurations for {len(configurations)} experts")
            
            # Store configurations
            self.experts = configurations
            
            # Initialize expert frameworks
            for expert_id, config in self.experts.items():
                self._initialize_framework(expert_id, config)
            
            logger.info("Expert Registry configurations loaded successfully")
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {self.config_path}. Creating empty registry.")
            self.experts = {}
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            error_msg = f"Failed to parse configuration file: {e}"
            logger.error(error_msg)
            raise ConfigurationException(error_msg)
        except Exception as e:
            error_msg = f"Failed to load expert configurations: {e}"
            logger.error(error_msg)
            raise ConfigurationException(error_msg)
    
    def _initialize_framework(self, expert_id: str, config: Dict[str, Any]):
        """
        Initialize an expert framework for the given expert ID and configuration.
        
        Args:
            expert_id: The ID of the expert.
            config: The expert configuration.
        """
        try:
            # Create appropriate framework based on expert ID
            if expert_id == "instagram":
                framework = InstagramExpertFramework(expert_id, config)
                self.expert_frameworks[expert_id] = framework
                logger.info(f"Initialized Instagram Expert Framework")
            elif expert_id == "etsy":
                # Placeholder for Etsy framework
                # framework = EtsyExpertFramework(expert_id, config)
                logger.info(f"Etsy Expert Framework not yet implemented")
            elif expert_id == "marketing":
                # Placeholder for Marketing framework
                # framework = MarketingExpertFramework(expert_id, config)
                logger.info(f"Marketing Expert Framework not yet implemented")
            elif expert_id == "branding":
                # Placeholder for Branding framework
                # framework = BrandingExpertFramework(expert_id, config)
                logger.info(f"Branding Expert Framework not yet implemented")
            else:
                logger.warning(f"No specialized framework available for expert ID: {expert_id}")
        except Exception as e:
            logger.error(f"Error initializing framework for expert ID {expert_id}: {e}")
    
    def has_expert(self, expert_id: str) -> bool:
        """
        Check if the expert exists in the registry.
        
        Args:
            expert_id: The ID of the expert to check.
            
        Returns:
            True if the expert exists, False otherwise.
        """
        return expert_id in self.experts
    
    def supports_intent(self, expert_id: str, intent: str) -> bool:
        """
        Check if the expert supports the given intent.
        
        Args:
            expert_id: The ID of the expert to check.
            intent: The intent to check.
            
        Returns:
            True if the expert supports the intent, False otherwise.
        """
        if not self.has_expert(expert_id):
            return False
        
        # Check if the framework is initialized
        if expert_id in self.expert_frameworks:
            return self.expert_frameworks[expert_id].supports_intent(intent)
        
        # Fallback to configuration check
        modes = self.experts[expert_id].get("modes", {})
        return intent in modes
    
    def get_core_config(self, expert_id: str) -> Dict[str, Any]:
        """
        Get the core configuration for the expert.
        
        Args:
            expert_id: The ID of the expert.
            
        Returns:
            The core configuration for the expert.
            
        Raises:
            ExpertNotFoundException: If the expert is not found.
        """
        if not self.has_expert(expert_id):
            raise ExpertNotFoundException(expert_id)
        
        return self.experts[expert_id].get("core_config", {})
    
    def get_mode_config(self, expert_id: str, intent: str) -> Dict[str, Any]:
        """
        Get the mode configuration for the expert and intent.
        
        Args:
            expert_id: The ID of the expert.
            intent: The intent to get the mode configuration for.
            
        Returns:
            The mode configuration for the expert and intent.
            
        Raises:
            ExpertNotFoundException: If the expert is not found.
        """
        if not self.has_expert(expert_id):
            raise ExpertNotFoundException(expert_id)
        
        modes = self.experts[expert_id].get("modes", {})
        return modes.get(intent, {})
    
    async def get_prompt_template(self, expert_id: str, intent: str) -> str:
        """
        Get a prompt template for the expert and intent.
        
        Args:
            expert_id: The ID of the expert.
            intent: The intent to get a prompt template for.
            
        Returns:
            A prompt template string.
            
        Raises:
            ExpertNotFoundException: If the expert is not found.
        """
        if not self.has_expert(expert_id):
            raise ExpertNotFoundException(expert_id)
        
        # If the framework is initialized, use it
        if expert_id in self.expert_frameworks:
            return await self.expert_frameworks[expert_id].get_prompt_template(intent)
        
        # Otherwise, return a default template
        logger.warning(f"No framework available for expert ID: {expert_id}, using default template")
        return self._get_default_template(expert_id, intent)
    
    def _get_default_template(self, expert_id: str, intent: str) -> str:
        """
        Get a default template for the expert and intent.
        
        Args:
            expert_id: The ID of the expert.
            intent: The intent to get a template for.
            
        Returns:
            A default template string.
        """
        if intent == "generate":
            return f"""
You are a {expert_id} expert. Your task is to generate content based on the provided parameters.

CONTEXT:
{{knowledge_context}}

PARAMETERS:
{{parameters}}

CONTENT SEED (if applicable):
{{content_seed}}

Generate content:
"""
        elif intent == "analyze":
            return f"""
You are a {expert_id} expert. Your task is to analyze the given content and provide insights.

CONTEXT:
{{knowledge_context}}

PARAMETERS:
{{parameters}}

CONTENT TO ANALYZE:
{{content}}

Provide analysis:
"""
        elif intent == "review":
            return f"""
You are a {expert_id} expert. Your task is to review the given content and provide feedback.

CONTEXT:
{{knowledge_context}}

PARAMETERS:
{{parameters}}

CONTENT TO REVIEW:
{{content}}

Provide review:
"""
        else:
            return f"""
You are a {expert_id} expert. Your task is to process the given content according to your expertise.

CONTEXT:
{{knowledge_context}}

PARAMETERS:
{{parameters}}

CONTENT:
{{content}}

Provide your response:
"""
    
    def get_capabilities(self, expert_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get capabilities for a specific expert or all experts.
        
        Args:
            expert_id: Optional ID of the expert to get capabilities for.
                     If not provided, returns capabilities for all experts.
            
        Returns:
            Dictionary of expert capabilities.
            
        Raises:
            ExpertNotFoundException: If the specified expert is not found.
        """
        if expert_id is not None:
            if not self.has_expert(expert_id):
                raise ExpertNotFoundException(expert_id)
            
            # If the framework is initialized, use it
            if expert_id in self.expert_frameworks:
                return {expert_id: self.expert_frameworks[expert_id].get_capabilities()}
            
            # Otherwise, build capabilities from configuration
            expert_config = self.experts[expert_id]
            core_config = expert_config.get("core_config", {})
            
            return {
                expert_id: {
                    "supported_intents": list(expert_config.get("modes", {}).keys()),
                    "capabilities": core_config.get("capabilities", [])
                }
            }
        else:
            # Get capabilities for all experts
            capabilities = {}
            
            for expert_id in self.experts:
                # If the framework is initialized, use it
                if expert_id in self.expert_frameworks:
                    capabilities[expert_id] = self.expert_frameworks[expert_id].get_capabilities()
                else:
                    # Otherwise, build capabilities from configuration
                    expert_config = self.experts[expert_id]
                    core_config = expert_config.get("core_config", {})
                    
                    capabilities[expert_id] = {
                        "supported_intents": list(expert_config.get("modes", {}).keys()),
                        "capabilities": core_config.get("capabilities", [])
                    }
            
            return capabilities
    
    async def refresh_configurations(self) -> None:
        """
        Refresh the expert configurations from the configuration file.
        
        This method is useful for updating configurations without restarting the service.
        
        Raises:
            ConfigurationException: If the configuration file cannot be loaded
                                   or contains invalid data.
        """
        logger.info("Refreshing expert configurations")
        await self.load_configurations()
    
    async def add_expert(self, expert_id: str, configuration: Dict[str, Any]) -> None:
        """
        Add a new expert to the registry.
        
        Args:
            expert_id: The ID of the expert to add.
            configuration: The configuration for the expert.
            
        Raises:
            ConfigurationException: If the configuration is invalid.
        """
        logger.info(f"Adding expert '{expert_id}' to registry")
        
        # Validate the configuration before adding
        if 'core_config' not in configuration:
            raise ConfigurationException(f"Missing 'core_config' for expert '{expert_id}'")
        
        if 'modes' not in configuration:
            raise ConfigurationException(f"Missing 'modes' for expert '{expert_id}'")
        
        # Add the expert to the registry
        self.experts[expert_id] = configuration
        
        # Optionally persist the updated configuration
        # await self._persist_configurations()
    
    async def remove_expert(self, expert_id: str) -> None:
        """
        Remove an expert from the registry.
        
        Args:
            expert_id: The ID of the expert to remove.
            
        Raises:
            ExpertNotFoundException: If the expert is not found.
        """
        if not self.has_expert(expert_id):
            raise ExpertNotFoundException(expert_id)
        
        logger.info(f"Removing expert '{expert_id}' from registry")
        del self.experts[expert_id]
        
        # Optionally persist the updated configuration
        # await self._persist_configurations()
    
    async def update_expert(self, expert_id: str, configuration: Dict[str, Any]) -> None:
        """
        Update an existing expert in the registry.
        
        Args:
            expert_id: The ID of the expert to update.
            configuration: The updated configuration for the expert.
            
        Raises:
            ExpertNotFoundException: If the expert is not found.
            ConfigurationException: If the configuration is invalid.
        """
        if not self.has_expert(expert_id):
            raise ExpertNotFoundException(expert_id)
        
        logger.info(f"Updating expert '{expert_id}' in registry")
        
        # Validate the configuration before updating
        if 'core_config' not in configuration:
            raise ConfigurationException(f"Missing 'core_config' for expert '{expert_id}'")
        
        if 'modes' not in configuration:
            raise ConfigurationException(f"Missing 'modes' for expert '{expert_id}'")
        
        # Update the expert in the registry
        self.experts[expert_id] = configuration
        
        # Optionally persist the updated configuration
        # await self._persist_configurations()
    
    # Helper method to persist configurations to file
    # This could be implemented if needed to save changes
    # async def _persist_configurations(self) -> None:
    #     """
    #     Persist the current configurations to the configuration file.
    #     """
    #     try:
    #         if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
    #             with open(self.config_path, 'w') as file:
    #                 yaml.dump(self.experts, file)
    #         elif self.config_path.endswith('.json'):
    #             with open(self.config_path, 'w') as file:
    #                 json.dump(self.experts, file, indent=2)
    #     except Exception as e:
    #         logger.error(f"Failed to persist expert configurations: {e}") 