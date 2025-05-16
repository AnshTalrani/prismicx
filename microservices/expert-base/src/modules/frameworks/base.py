"""
Base expert framework for the Expert Base microservice.

This module provides the base expert framework that all domain-specific
expert frameworks extend.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from loguru import logger


class BaseExpertFramework(ABC):
    """
    Base class for all expert frameworks.
    
    This class defines the interface and common functionality for all expert
    frameworks. Domain-specific frameworks should extend this class.
    """
    
    def __init__(self, framework_id: str, config: Dict[str, Any]):
        """
        Initialize the expert framework.
        
        Args:
            framework_id: The ID of the framework.
            config: The configuration for the framework.
        """
        self.framework_id = framework_id
        self.config = config
        self.capabilities = config.get("capabilities", [])
        self.modes = config.get("modes", {})
        
        logger.info(f"Initialized expert framework: {framework_id}")
    
    @abstractmethod
    async def get_prompt_template(self, intent: str) -> str:
        """
        Get a prompt template for the given intent.
        
        Args:
            intent: The intent to get a prompt template for.
            
        Returns:
            A prompt template string.
        """
        pass
    
    def get_supported_intents(self) -> List[str]:
        """
        Get the intents supported by this framework.
        
        Returns:
            A list of supported intents.
        """
        return list(self.modes.keys())
    
    def get_mode_config(self, intent: str) -> Dict[str, Any]:
        """
        Get the mode configuration for the given intent.
        
        Args:
            intent: The intent to get the mode configuration for.
            
        Returns:
            The mode configuration.
            
        Raises:
            ValueError: If the intent is not supported.
        """
        if intent not in self.modes:
            raise ValueError(f"Intent '{intent}' not supported by framework '{self.framework_id}'")
        
        return self.modes[intent]
    
    def get_knowledge_filters(self, intent: str) -> Dict[str, Any]:
        """
        Get the knowledge filters for the given intent.
        
        Args:
            intent: The intent to get knowledge filters for.
            
        Returns:
            The knowledge filters.
        """
        mode_config = self.get_mode_config(intent)
        return mode_config.get("knowledge_filters", {})
    
    def get_prompt_parameters(self, intent: str, user_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the parameters to use in a prompt template.
        
        Args:
            intent: The intent to get parameters for.
            user_parameters: The user-provided parameters.
            
        Returns:
            The parameters to use in a prompt template.
        """
        # Get the mode configuration
        mode_config = self.get_mode_config(intent)
        
        # Get the default parameters from the mode configuration
        default_params = mode_config.get("parameters", {})
        
        # Merge with user parameters
        merged_params = {**default_params, **user_parameters}
        
        return merged_params
    
    def supports_intent(self, intent: str) -> bool:
        """
        Check if the framework supports the given intent.
        
        Args:
            intent: The intent to check.
            
        Returns:
            True if the intent is supported, False otherwise.
        """
        return intent in self.modes
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of this framework.
        
        Returns:
            The capabilities.
        """
        return {
            "framework_id": self.framework_id,
            "supported_intents": self.get_supported_intents(),
            "capabilities": self.capabilities
        } 