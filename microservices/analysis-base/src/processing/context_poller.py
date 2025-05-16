"""
Context Poller Module

This module provides functionality to poll for pending contexts
from the repository based on various criteria.
"""

import asyncio
import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid

from ..repository.repository import Repository
from ..config.settings import Settings

# Configure structured logging
logger = structlog.get_logger(__name__)

class ContextPoller:
    """
    Context Poller for retrieving pending contexts from the repository.
    
    This class:
    - Manages fetching of pending contexts for processing
    - Provides both single and batch context polling
    - Applies business rules for context selection and prioritization
    """
    
    def __init__(self, repository: Repository, settings: Settings):
        """
        Initialize the context poller.
        
        Args:
            repository: Data repository
            settings: Application configuration settings
        """
        self.repository = repository
        self.settings = settings
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
        
        logger.info(
            "Context poller initialized",
            service_type=self.service_type,
            max_attempts=self.max_attempts,
            retry_delay=self.retry_delay
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
        
        # Limit to the number of additional contexts needed
        limit = batch_size - len(self.batch_contexts)
        
        # Sort by priority and created time
        sort_criteria = [
            ("priority", -1),  # Higher priority first
            ("created_at", 1)   # Older contexts first
        ]
        
        # Find the additional contexts
        contexts = await self.repository.find_and_update_contexts(
            query_filter=query_filter,
            update={
                "$inc": {"attempts": 1},
                "$set": {"last_attempt": datetime.utcnow().isoformat()}
            },
            sort=sort_criteria,
            limit=limit
        )
        
        if contexts:
            logger.debug(
                "Retrieved additional contexts for batch",
                count=len(contexts),
                template_id=self.batch_template_id
            )
            
            # Add to our accumulating batch
            self.batch_contexts.extend(contexts)
    
    def _reset_batch_state(self):
        """Reset the batch accumulation state."""
        self.batch_accumulating = False
        self.batch_start_time = None
        self.batch_contexts = []
        self.batch_template_id = None 