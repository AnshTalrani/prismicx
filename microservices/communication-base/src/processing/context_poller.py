"""
Context Poller Module

This module provides functionality for polling campaign contexts from the database.
It helps the worker service retrieve batches of campaigns for processing.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
import structlog

from src.config.settings import Settings
from src.repository.repository import Repository
from src.common.monitoring import Metrics

logger = structlog.get_logger(__name__)

class ContextPoller:
    """
    Polls for campaign contexts to be processed.
    
    This class is responsible for:
    - Retrieving pending campaigns from the repository
    - Managing batch sizes and polling intervals
    - Providing campaigns to the worker service
    """
    
    def __init__(
        self, 
        repository: Repository, 
        settings: Settings,
        metrics: Optional[Metrics] = None
    ):
        """
        Initialize the context poller.
        
        Args:
            repository: Repository for data access
            settings: Application settings
            metrics: Optional metrics collector
        """
        self.repository = repository
        self.settings = settings
        self.metrics = metrics
        
        # Default batch size and polling configuration
        self.batch_size = settings.poller_batch_size
        self.min_poll_interval = settings.poller_min_interval_seconds
        self.max_poll_interval = settings.poller_max_interval_seconds
        self.current_poll_interval = self.min_poll_interval
        
        logger.info(
            "Context poller initialized",
            batch_size=self.batch_size,
            min_poll_interval=self.min_poll_interval,
            max_poll_interval=self.max_poll_interval
        )
    
    async def get_next_context(self) -> Optional[Dict[str, Any]]:
        """
        Get the next campaign context to process.
        
        Returns:
            Campaign context or None if no pending campaigns
        """
        start_time = time.time()
        try:
            # Get the next pending campaign
            campaign = await self.repository.get_next_campaign()
            
            # Track metrics
            if self.metrics:
                self.metrics.observe("context_poll_time", time.time() - start_time)
                if campaign:
                    self.metrics.increment("contexts_retrieved_total")
                
            if campaign:
                logger.debug("Retrieved next campaign context", campaign_id=campaign.get("id"))
            else:
                logger.debug("No pending campaign contexts available")
                # Adjust polling interval (back-off strategy)
                self._adjust_poll_interval(False)
                
            return campaign
        except Exception as e:
            logger.error("Error retrieving next campaign context", error=str(e))
            if self.metrics:
                self.metrics.increment("context_poll_errors_total")
            return None
    
    async def get_batch_contexts(self) -> List[Dict[str, Any]]:
        """
        Get a batch of campaign contexts to process.
        
        Returns:
            List of campaign contexts
        """
        start_time = time.time()
        try:
            # Get a batch of pending campaigns
            campaigns = await self.repository.get_batch_campaigns(self.batch_size)
            
            # Track metrics
            if self.metrics:
                self.metrics.observe("context_poll_time", time.time() - start_time)
                self.metrics.observe("batch_size", len(campaigns))
                self.metrics.increment("contexts_retrieved_total", value=len(campaigns))
            
            # Adjust polling interval based on results
            if campaigns:
                logger.debug("Retrieved batch of campaign contexts", count=len(campaigns))
                # If we got results, reduce poll interval to minimum
                self._adjust_poll_interval(True)
            else:
                logger.debug("No pending campaign contexts available for batch")
                # If no results, increase poll interval (back-off strategy)
                self._adjust_poll_interval(False)
            
            return campaigns
        except Exception as e:
            logger.error("Error retrieving batch of campaign contexts", error=str(e))
            if self.metrics:
                self.metrics.increment("context_poll_errors_total")
            return []
    
    def _adjust_poll_interval(self, has_results: bool) -> None:
        """
        Adjust the polling interval based on query results.
        
        Args:
            has_results: Whether the last query returned results
        """
        if has_results:
            # Reset to minimum interval if we have results
            self.current_poll_interval = self.min_poll_interval
        else:
            # Increase interval (with cap) if no results
            self.current_poll_interval = min(
                self.current_poll_interval * 1.5,  # Increase by 50%
                self.max_poll_interval
            )
    
    async def wait_for_next_poll(self) -> None:
        """
        Wait for the next polling interval.
        """
        await asyncio.sleep(self.current_poll_interval)
    
    async def poll_campaigns(self) -> List[Dict[str, Any]]:
        """
        Poll for campaigns and wait if none are available.
        
        Returns:
            List of campaign contexts
        """
        campaigns = await self.get_batch_contexts()
        
        if not campaigns:
            await self.wait_for_next_poll()
            
        return campaigns
    
    async def get_campaigns_by_status(
        self, 
        status: str, 
        limit: int = 100, 
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get campaigns with a specific status.
        
        Args:
            status: Status to filter by
            limit: Maximum number of results
            skip: Number of results to skip
            
        Returns:
            List of campaign contexts
        """
        try:
            # Get campaigns with the specified status
            campaigns = await self.repository.get_campaigns(
                status=status,
                limit=limit,
                skip=skip
            )
            
            if self.metrics:
                self.metrics.increment("contexts_retrieved_total", value=len(campaigns))
            
            logger.debug(
                "Retrieved campaigns by status", 
                status=status, 
                count=len(campaigns)
            )
            
            return campaigns
        except Exception as e:
            logger.error(
                "Error retrieving campaigns by status", 
                status=status, 
                error=str(e)
            )
            if self.metrics:
                self.metrics.increment("context_poll_errors_total")
            return [] 