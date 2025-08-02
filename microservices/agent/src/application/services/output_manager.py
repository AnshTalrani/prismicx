"""
Output Manager for handling completed context results.

Processes outputs from completed contexts and routes them to appropriate destinations.
"""
import logging
import json
import os
from typing import Dict, Any, Optional, List, Callable, Awaitable
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class OutputManager:
    """
    Output Manager is responsible for processing and routing outputs from completed contexts.
    
    Responsibilities:
    - Processing completed context results
    - Routing outputs to appropriate destinations
    - Handling different output types
    - Managing output callbacks
    """
    
    def __init__(self, repository, user_repository=None):
        """
        Initialize Output Manager.
        
        Args:
            repository: Repository for context storage
            user_repository: Repository for user data validation
        """
        self.repository = repository
        self.user_repository = user_repository
        self.output_handlers = {}
        self.callbacks = {}
        self.default_handler = self._default_output_handler
        
        # Register default handlers
        self._register_default_handlers()
        
    def _register_default_handlers(self) -> None:
        """Register default output handlers."""
        # Handler for general API responses
        self.register_handler("api", self._handle_api_output)
        
        # Handler for batch processing outputs
        self.register_handler("batch", self._handle_batch_output)
        
        # Handler for notification outputs
        self.register_handler("notification", self._handle_notification_output)
        
        # Handler for error outputs
        self.register_handler("error", self._handle_error_output)
        
    def register_handler(self, output_type: str, handler: Callable[[str, Dict[str, Any]], Awaitable[bool]]) -> None:
        """
        Register an output handler for a specific output type.
        
        Args:
            output_type: Type of output to handle
            handler: Handler function
        """
        self.output_handlers[output_type] = handler
        logger.debug(f"Registered output handler for type '{output_type}'")
        
    def register_callback(self, context_id: str, callback: Callable) -> None:
        """
        Register a callback for a specific context.
        
        Args:
            context_id: Context ID
            callback: Callback function to call when output is ready
        """
        self.callbacks[context_id] = callback
        logger.debug(f"Registered callback for context {context_id}")
        
    async def process_output(self, context_id: str, context: Dict[str, Any]) -> bool:
        """
        Process output for a completed context.
        
        Args:
            context_id: Context ID
            context: Context data
            
        Returns:
            Success status
        """
        try:
            # Check user validity if possible
            user_id = None
            if "request" in context and "user_id" in context["request"]:
                user_id = context["request"]["user_id"]
                if self.user_repository and user_id:
                    user_exists = await self.user_repository.validate_user_exists(user_id)
                    if not user_exists:
                        logger.warning(f"User {user_id} does not exist in system_users database, but processing output anyway")
            
            # Log the processing
            logger.info(f"Processing output for context {context_id}")
            
            # Get the appropriate handler
            handler = self._get_handler_for_context(context)
            
            if handler:
                # Call the handler
                result = await handler(context_id, context)
                
                # Call registered callback if exists
                if context_id in self.callbacks and result:
                    try:
                        callback = self.callbacks.pop(context_id)
                        await callback(context_id, context)
                    except Exception as e:
                        logger.error(f"Error calling callback for context {context_id}: {str(e)}")
                
                # Update the context with the output status
                if "outputs" not in context:
                    context["outputs"] = []
                    
                context["outputs"].append({
                    "timestamp": asyncio.get_event_loop().time(),
                    "status": "processed" if result else "failed"
                })
                
                # Save the updated context
                success = await self.repository.save(context_id, context)
                
                if success:
                    logger.info(f"Updated context {context_id} with output status")
                else:
                    logger.error(f"Failed to update context {context_id} with output status")
                
                return result
            else:
                logger.warning(f"No handler found for output type '{self._determine_output_type(context)}'")
                return False
                
        except Exception as e:
            logger.error(f"Error processing output for context {context_id}: {str(e)}")
            return False
            
    def _determine_output_type(self, context: Dict[str, Any]) -> str:
        """
        Determine the output type from a context.
        
        Args:
            context: Context data
            
        Returns:
            Output type string
        """
        # Check for explicit output type in tags
        output_type = context.get("tags", {}).get("output_type")
        if output_type:
            return output_type
            
        # Check if this is a batch context
        if context.get("batch_id") or context.get("template", {}).get("type") == "batch":
            return "batch"
            
        # Check if this is an error
        if context.get("status") == "failed" or context.get("results", {}).get("error"):
            return "error"
            
        # Check if this is a notification
        if context.get("tags", {}).get("notification"):
            return "notification"
            
        # Default to API
        return "api"
        
    def _get_handler_for_context(self, context: Dict[str, Any]) -> Callable[[str, Dict[str, Any]], Awaitable[bool]]:
        """
        Get the appropriate handler for a context.
        
        Args:
            context: Context data
            
        Returns:
            Handler function
        """
        # Check for service type first
        service_type = context.get("service_type")
        if service_type and service_type in self.output_handlers:
            return self.output_handlers[service_type]
            
        # Check for template_id next
        template_id = context.get("template_id")
        if template_id and template_id in self.output_handlers:
            return self.output_handlers[template_id]
            
        # Use default handler
        return self.default_handler
        
    async def _handle_api_output(self, context_id: str, context: Dict[str, Any]) -> bool:
        """
        Handle API output.
        
        Args:
            context_id: Context ID
            context: Context data
            
        Returns:
            Success status
        """
        try:
            # For API outputs, we might need to update a response queue or notify clients
            
            # Extract the key results
            results = context.get("results", {})
            request_id = context.get("request", {}).get("id")
            
            # Log successful processing
            logger.info(f"Processed API output for context {context_id} (request {request_id})")
            
            # Here you would implement logic to notify clients or update response queues
            # For now, we just log success
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling API output for context {context_id}: {str(e)}")
            return False
            
    async def _handle_batch_output(self, context_id: str, context: Dict[str, Any]) -> bool:
        """
        Handle batch output.
        
        Args:
            context_id: Context ID
            context: Context data
            
        Returns:
            Success status
        """
        try:
            # For batch outputs, we need to update the batch status
            
            batch_id = context.get("batch_id") or context.get("_id")
            
            # Log successful processing
            logger.info(f"Processed batch output for context {context_id} (batch {batch_id})")
            
            # Here you would implement logic to update batch status
            # For now, we just log success
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling batch output for context {context_id}: {str(e)}")
            return False
            
    async def _handle_notification_output(self, context_id: str, context: Dict[str, Any]) -> bool:
        """
        Handle notification output.
        
        Args:
            context_id: Context ID
            context: Context data
            
        Returns:
            Success status
        """
        try:
            # For notification outputs, we might need to send notifications
            
            notification_type = context.get("tags", {}).get("notification_type", "general")
            destination = context.get("tags", {}).get("notification_destination")
            
            # Log successful processing
            logger.info(f"Processed notification output for context {context_id} (type: {notification_type})")
            
            # Here you would implement logic to send notifications
            # For now, we just log success
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling notification output for context {context_id}: {str(e)}")
            return False
            
    async def _handle_error_output(self, context_id: str, context: Dict[str, Any]) -> bool:
        """
        Handle error output.
        
        Args:
            context_id: Context ID
            context: Context data
            
        Returns:
            Success status
        """
        try:
            # For error outputs, we might need to log errors or notify administrators
            
            error = context.get("results", {}).get("error", "Unknown error")
            
            # Log the error
            logger.error(f"Error in context {context_id}: {error}")
            
            # Here you would implement logic to notify administrators or update error monitoring
            # For now, we just log the error
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling error output for context {context_id}: {str(e)}")
            return False
            
    async def _default_output_handler(self, context_id: str, context: Dict[str, Any]) -> bool:
        """
        Default handler for context outputs.
        
        This handler simply stores the results in the context and returns.
        
        Args:
            context_id: ID of the context
            context: Context data including results
            
        Returns:
            Success status
        """
        try:
            logger.info(f"Default output handler processing context {context_id}")
            
            # Get results
            results = context.get("results", {})
            
            # Just log the results
            logger.info(f"Context {context_id} completed with results: {results}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in default output handler for context {context_id}: {str(e)}")
            return False 