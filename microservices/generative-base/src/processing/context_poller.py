"""
Context Poller Module

This module provides functionality to poll for pending contexts
from the repository based on various criteria.
"""

import asyncio
import structlog
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid

from ..adapters.repository import Repository
from ..common.config import Settings
from ..common.config_loader import ConfigurationLoader

# Configure structured logging
logger = structlog.get_logger(__name__)

class ContextPoller:
    """
    Context Poller for retrieving pending contexts from the repository.
    
    This class:
    - Manages fetching of pending contexts for processing
    - Provides both single and batch context polling
    - Applies business rules for context selection and prioritization
    - Supports template-based flow selection
    """
    
    def __init__(self, repository: Repository, settings: Settings, 
                 config_loader: Optional[ConfigurationLoader] = None):
        """
        Initialize the context poller.
        
        Args:
            repository: Data repository
            settings: Application configuration settings
            config_loader: Optional configuration loader for YAML settings
        """
        self.repository = repository
        self.settings = settings
        self.config_loader = config_loader
        self.service_type = settings.service_type
        
        # Polling settings
        self.max_attempts = settings.max_processing_attempts
        self.retry_delay = settings.retry_delay
        self.poll_interval = settings.poll_interval
        
        # Controls for batch polling with wait time
        self.batch_accumulating = False
        self.batch_start_time = None
        self.batch_contexts = []
        self.batch_template_id = None
        
        # Load configuration-based settings if available
        self._load_config_settings()
        
        logger.info(
            "Context poller initialized",
            service_type=self.service_type,
            max_attempts=self.max_attempts,
            retry_delay=self.retry_delay
        )
    
    def _load_config_settings(self):
        """Load settings from configuration if available."""
        if self.config_loader:
            # Get system configuration
            system_config = self.config_loader.get_system_config()
            
            # Override settings from config if available
            self.max_attempts = system_config.get(
                'max_processing_attempts', self.max_attempts)
            self.retry_delay = system_config.get(
                'retry_delay_seconds', self.retry_delay)
            self.poll_interval = system_config.get(
                'poll_interval', self.poll_interval)
            
            logger.info(
                "Loaded configuration settings",
                max_attempts=self.max_attempts,
                retry_delay=self.retry_delay,
                poll_interval=self.poll_interval
            )
    
    async def get_next_context(self) -> Optional[Dict[str, Any]]:
        """
        Get the next pending context for processing.
        
        Returns:
            A context document or None if no pending contexts are available
        """
        # Build filter for pending contexts matching service type
        query_filter = {
            "status": "pending",
            "service_type": self.service_type,
            "$or": [
                {"attempts": {"$lt": self.max_attempts}},
                {"attempts": {"$exists": False}}
            ]
        }
        
        # Add retry delay check if needed
        if self.retry_delay > 0:
            retry_threshold = datetime.utcnow() - timedelta(seconds=self.retry_delay)
            query_filter["$or"] = [
                {"last_attempt": {"$lt": retry_threshold.isoformat()}},
                {"last_attempt": {"$exists": False}}
            ]
        
        # Sort by priority and created time
        sort_criteria = [
            ("priority", -1),  # Higher priority first
            ("created_at", 1)   # Older contexts first
        ]
        
        # Fetch one context
        context = await self.repository.find_one_and_update_context(
            query_filter=query_filter,
            update={
                "$inc": {"attempts": 1},
                "$set": {"last_attempt": datetime.utcnow().isoformat()}
            },
            sort=sort_criteria
        )
        
        if context:
            logger.debug(
                "Retrieved context for processing",
                context_id=str(context.get("_id")),
                template_id=context.get("template_id"),
                attempt=context.get("attempts", 1)
            )
        
        return context
    
    async def get_context_for_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a pending context for a specific template.
        
        Args:
            template_id: The template ID to match
            
        Returns:
            A context document or None if no matching pending contexts are available
        """
        # Build filter for pending contexts matching service type and template
        query_filter = {
            "status": "pending",
            "service_type": self.service_type,
            "template_id": template_id,
            "$or": [
                {"attempts": {"$lt": self.max_attempts}},
                {"attempts": {"$exists": False}}
            ]
        }
        
        # Add retry delay check if needed
        if self.retry_delay > 0:
            retry_threshold = datetime.utcnow() - timedelta(seconds=self.retry_delay)
            query_filter["$or"] = [
                {"last_attempt": {"$lt": retry_threshold.isoformat()}},
                {"last_attempt": {"$exists": False}}
            ]
        
        # Sort by priority and created time
        sort_criteria = [
            ("priority", -1),  # Higher priority first
            ("created_at", 1)   # Older contexts first
        ]
        
        # Fetch one context
        context = await self.repository.find_one_and_update_context(
            query_filter=query_filter,
            update={
                "$inc": {"attempts": 1},
                "$set": {"last_attempt": datetime.utcnow().isoformat()}
            },
            sort=sort_criteria
        )
        
        return context
    
    async def get_next_context_and_flow(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get the next pending context and determine its flow.
        
        Returns:
            Tuple of (context, flow_id) or (None, None) if no contexts available
        """
        context = await self.get_next_context()
        if not context:
            return None, None
        
        # Determine the flow ID based on the template ID
        template_id = context.get("template_id")
        flow_id = None
        
        if self.config_loader and template_id:
            flow_config = self.config_loader.get_flow_for_template(template_id)
            if flow_config:
                flow_id = flow_config.get('id')
        
        return context, flow_id
    
    async def get_batch_contexts(
        self, 
        batch_size: int = 10, 
        wait_time: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get a batch of pending contexts for processing.
        
        This method attempts to gather a batch of contexts that share the same template
        to enable more efficient batch processing. It may wait up to the specified
        wait_time to collect a full batch.
        
        Args:
            batch_size: Maximum number of contexts to include in the batch
            wait_time: Maximum time to wait in seconds to gather a full batch
            
        Returns:
            A list of context documents for batch processing
        """
        # If we're already accumulating a batch, check if we should return it
        if self.batch_accumulating:
            current_size = len(self.batch_contexts)
            elapsed_time = (datetime.utcnow() - self.batch_start_time).total_seconds()
            
            # Return accumulated batch if it's full or we've waited long enough
            if current_size >= batch_size or elapsed_time >= wait_time:
                result = self.batch_contexts
                self._reset_batch_state()
                return result
        
        # Start a new batch accumulation if none is in progress
        if not self.batch_accumulating:
            self.batch_accumulating = True
            self.batch_start_time = datetime.utcnow()
            self.batch_contexts = []
            
            # Get the first context to determine the template
            first_context = await self.get_next_context()
            if first_context:
                self.batch_contexts.append(first_context)
                self.batch_template_id = first_context.get("template_id")
                
                # Try to immediately get more contexts with same template
                await self._fill_batch(batch_size)
        else:
            # Continue filling an existing batch
            await self._fill_batch(batch_size)
        
        # Check if we should return what we have so far
        current_size = len(self.batch_contexts)
        elapsed_time = (datetime.utcnow() - self.batch_start_time).total_seconds()
        
        if current_size > 0 and (current_size >= batch_size or elapsed_time >= wait_time):
            result = self.batch_contexts
            self._reset_batch_state()
            return result
        
        # Return empty list if no contexts found
        return []
    
    async def get_batch_contexts_for_flow(
        self, 
        batch_size: int = 10, 
        wait_time: int = 5
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get a batch of pending contexts for processing and determine their flow.
        
        Args:
            batch_size: Maximum number of contexts to include in the batch
            wait_time: Maximum time to wait in seconds to gather a full batch
            
        Returns:
            Tuple of (contexts, flow_id) or ([], None) if no contexts available
        """
        contexts = await self.get_batch_contexts(batch_size, wait_time)
        if not contexts:
            return [], None
        
        # Determine the flow ID based on the template ID from the first context
        template_id = contexts[0].get("template_id")
        flow_id = None
        
        if self.config_loader and template_id:
            flow_config = self.config_loader.get_flow_for_template(template_id)
            if flow_config:
                flow_id = flow_config.get('id')
        
        return contexts, flow_id
    
    async def _fill_batch(self, batch_size: int):
        """
        Fill a batch with additional contexts that match the template.
        
        Args:
            batch_size: Maximum number of contexts in the batch
        """
        # Stop if batch is already full
        if len(self.batch_contexts) >= batch_size:
            return
            
        # Build filter for pending contexts with matching template_id
        query_filter = {
            "status": "pending",
            "service_type": self.service_type,
            "template_id": self.batch_template_id,
            "$or": [
                {"attempts": {"$lt": self.max_attempts}},
                {"attempts": {"$exists": False}}
            ]
        }
        
        # Add retry delay check if needed
        if self.retry_delay > 0:
            retry_threshold = datetime.utcnow() - timedelta(seconds=self.retry_delay)
            query_filter["$or"] = [
                {"last_attempt": {"$lt": retry_threshold.isoformat()}},
                {"last_attempt": {"$exists": False}}
            ]
        
        # Sort by priority and created time
        sort_criteria = [
            ("priority", -1),  # Higher priority first
            ("created_at", 1)   # Older contexts first
        ]
        
        # How many more contexts we need
        remaining = batch_size - len(self.batch_contexts)
        
        # Fetch additional contexts
        contexts = await self.repository.find_and_update_contexts(
            query_filter=query_filter,
            update={
                "$inc": {"attempts": 1},
                "$set": {"last_attempt": datetime.utcnow().isoformat()}
            },
            sort=sort_criteria,
            limit=remaining
        )
        
        # Add to batch
        if contexts:
            self.batch_contexts.extend(contexts)
            logger.debug(
                "Added contexts to batch",
                template_id=self.batch_template_id,
                added_count=len(contexts),
                total_count=len(self.batch_contexts)
            )
    
    def _reset_batch_state(self):
        """Reset the batch accumulation state."""
        self.batch_accumulating = False
        self.batch_start_time = None
        self.batch_contexts = []
        self.batch_template_id = None


