"""
Model registry for managing all LLM instances across the system.

This module provides a central registry for all LLM managers, allowing
for easy access to the appropriate model based on bot type.
"""

import logging
from typing import Dict, Any, Optional, Type

from src.models.llm.base_llm_manager import BaseLLMManager

class ModelRegistry:
    """Central registry for all LLM managers in the system."""
    
    _instance = None  # Singleton instance
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ModelRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the model registry."""
        if self._initialized:
            return
            
        self.logger = logging.getLogger(self.__class__.__name__)
        self.managers: Dict[str, BaseLLMManager] = {}
        self._initialized = True
        self.logger.info("Model registry initialized")
    
    def register_manager(self, bot_type: str, manager: BaseLLMManager) -> None:
        """
        Register a model manager for a specific bot type.
        
        Args:
            bot_type: The type of bot (consultancy, sales, support)
            manager: The LLM manager instance to register
        """
        self.logger.info(f"Registering model manager for bot type: {bot_type}")
        self.managers[bot_type] = manager
    
    def get_manager(self, bot_type: str) -> Optional[BaseLLMManager]:
        """
        Get the model manager for a specific bot type.
        
        Args:
            bot_type: The type of bot (consultancy, sales, support)
            
        Returns:
            The LLM manager instance if registered, None otherwise
        """
        manager = self.managers.get(bot_type)
        if not manager:
            self.logger.warning(f"No model manager registered for bot type: {bot_type}")
        return manager
    
    def get_all_managers(self) -> Dict[str, BaseLLMManager]:
        """
        Get all registered model managers.
        
        Returns:
            Dictionary of all registered LLM managers
        """
        return self.managers
    
    def unregister_manager(self, bot_type: str) -> None:
        """
        Unregister a model manager.
        
        Args:
            bot_type: The type of bot to unregister
        """
        if bot_type in self.managers:
            self.logger.info(f"Unregistering model manager for bot type: {bot_type}")
            del self.managers[bot_type] 