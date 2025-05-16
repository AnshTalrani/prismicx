"""
Middleware Pipeline

This module provides a pipeline for applying middleware processors to messages
and responses during conversation processing.
"""

import logging
from typing import Dict, Any, List, Tuple, Callable, Awaitable, Optional
import asyncio

from src.config.config_integration import ConfigIntegration

logger = logging.getLogger(__name__)

# Type definitions for middleware processors
PreProcessorType = Callable[[str, Dict[str, Any], str], Awaitable[Tuple[str, Optional[Dict[str, Any]]]]]
PostProcessorType = Callable[[str, str, Dict[str, Any], str], Awaitable[Tuple[str, Optional[Dict[str, Any]]]]]

class MiddlewarePipeline:
    """
    Middleware Pipeline
    
    Manages the application of middleware processors to messages and responses,
    enabling extensible pre and post-processing in the conversation flow.
    """
    
    def __init__(self, config_integration: ConfigIntegration):
        """
        Initialize the middleware pipeline.
        
        Args:
            config_integration: Configuration integration instance
        """
        self.config_integration = config_integration
        self.pre_processors: Dict[str, List[PreProcessorType]] = {
            "sales": [],
            "consultancy": [], 
            "support": [],
            "all": []  # Applied to all bot types
        }
        self.post_processors: Dict[str, List[PostProcessorType]] = {
            "sales": [],
            "consultancy": [],
            "support": [],
            "all": []  # Applied to all bot types
        }
        
        # Load middleware configuration
        self._load_middleware_config()
        
        logger.info("Middleware pipeline initialized")
    
    def _load_middleware_config(self) -> None:
        """
        Load middleware configuration from config integration.
        This determines which processors are enabled for each bot type.
        """
        try:
            middleware_config = self.config_integration.get_config_section("middleware")
            if not middleware_config:
                logger.warning("No middleware configuration found, using defaults")
                return
                
            # Configure enabled processors based on config
            # Implementation would depend on actual middleware processors available
            logger.info("Middleware configuration loaded")
        except Exception as e:
            logger.error(f"Error loading middleware configuration: {e}")
    
    def register_pre_processor(
        self, 
        processor: PreProcessorType, 
        bot_types: List[str] = ["all"]
    ) -> None:
        """
        Register a pre-processor for specified bot types.
        
        Args:
            processor: The pre-processor function
            bot_types: List of bot types to apply this processor to
        """
        for bot_type in bot_types:
            if bot_type in self.pre_processors:
                self.pre_processors[bot_type].append(processor)
                logger.info(f"Registered pre-processor for bot type {bot_type}")
            else:
                logger.warning(f"Unknown bot type {bot_type} for pre-processor")
    
    def register_post_processor(
        self, 
        processor: PostProcessorType, 
        bot_types: List[str] = ["all"]
    ) -> None:
        """
        Register a post-processor for specified bot types.
        
        Args:
            processor: The post-processor function
            bot_types: List of bot types to apply this processor to
        """
        for bot_type in bot_types:
            if bot_type in self.post_processors:
                self.post_processors[bot_type].append(processor)
                logger.info(f"Registered post-processor for bot type {bot_type}")
            else:
                logger.warning(f"Unknown bot type {bot_type} for post-processor")
    
    async def apply_pre_processors(
        self,
        message: str,
        context: Dict[str, Any],
        bot_type: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Apply all relevant pre-processors to a message.
        
        Args:
            message: The original message
            context: The conversation context
            bot_type: The type of bot
            
        Returns:
            Tuple of (processed_message, updated_context)
        """
        processed_message = message
        current_context = context.copy()
        
        try:
            # Apply general processors first
            for processor in self.pre_processors["all"]:
                processed_message, context_updates = await processor(
                    processed_message, current_context, bot_type
                )
                if context_updates:
                    current_context.update(context_updates)
            
            # Then apply bot-specific processors
            if bot_type in self.pre_processors:
                for processor in self.pre_processors[bot_type]:
                    processed_message, context_updates = await processor(
                        processed_message, current_context, bot_type
                    )
                    if context_updates:
                        current_context.update(context_updates)
            
            logger.info(f"Applied pre-processors for bot type {bot_type}")
            return processed_message, current_context
        except Exception as e:
            logger.error(f"Error applying pre-processors: {e}")
            # Return original message and context in case of error
            return message, context
    
    async def apply_post_processors(
        self,
        response: str,
        original_message: str,
        context: Dict[str, Any],
        bot_type: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Apply all relevant post-processors to a response.
        
        Args:
            response: The generated response
            original_message: The original user message
            context: The conversation context
            bot_type: The type of bot
            
        Returns:
            Tuple of (processed_response, updated_context)
        """
        processed_response = response
        current_context = context.copy()
        
        try:
            # Apply general processors first
            for processor in self.post_processors["all"]:
                processed_response, context_updates = await processor(
                    processed_response, original_message, current_context, bot_type
                )
                if context_updates:
                    current_context.update(context_updates)
            
            # Then apply bot-specific processors
            if bot_type in self.post_processors:
                for processor in self.post_processors[bot_type]:
                    processed_response, context_updates = await processor(
                        processed_response, original_message, current_context, bot_type
                    )
                    if context_updates:
                        current_context.update(context_updates)
            
            logger.info(f"Applied post-processors for bot type {bot_type}")
            return processed_response, current_context
        except Exception as e:
            logger.error(f"Error applying post-processors: {e}")
            # Return original response and context in case of error
            return response, context 