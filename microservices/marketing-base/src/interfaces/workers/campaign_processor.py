"""
Campaign processor worker.

This module provides a worker process that periodically checks for campaigns
that are scheduled to be sent and processes them.
"""

import asyncio
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import structlog
import os
from prometheus_client import Counter, Gauge, start_http_server

from ...config import get_config
from ...application.services.campaign_service import CampaignService


# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger(__name__)

# Define Prometheus metrics
CAMPAIGNS_PROCESSED = Counter(
    "campaigns_processed_total", 
    "Total number of campaigns processed",
    ["status"]
)
PROCESSING_TIME = Gauge(
    "campaign_processing_seconds",
    "Time spent processing campaigns"
)
PROCESSOR_HEALTH = Gauge(
    "campaign_processor_healthy",
    "Health status of the campaign processor (1=healthy, 0=unhealthy)"
)


class CampaignProcessor:
    """Worker for processing scheduled campaigns."""

    def __init__(self):
        """Initialize the campaign processor worker."""
        self.campaign_service = CampaignService()
        self.config = get_config()
        self.check_interval = getattr(self.config, 'campaign_check_interval', 60)  # seconds
        self.running = False
        self.last_successful_run = datetime.utcnow()
        self.health_threshold_minutes = getattr(self.config, 'health_threshold_minutes', 10)
        self.metrics_port = int(os.environ.get('METRICS_PORT', 8000))
        self._setup_signal_handlers()
        
        # Start Prometheus metrics server
        start_http_server(self.metrics_port)
        logger.info(f"Started metrics server on port {self.metrics_port}")
        
        # Initialize health status
        PROCESSOR_HEALTH.set(1)
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Received shutdown signal, stopping campaign processor")
        self.running = False
    
    def _check_health(self) -> bool:
        """Check health status of the processor.
        
        Returns:
            True if healthy, False otherwise
        """
        # Processor is unhealthy if it hasn't successfully processed campaigns
        # within the configured threshold
        time_since_last_success = datetime.utcnow() - self.last_successful_run
        is_healthy = time_since_last_success.total_seconds() < (self.health_threshold_minutes * 60)
        PROCESSOR_HEALTH.set(1 if is_healthy else 0)
        return is_healthy
    
    async def process_campaigns(self) -> Dict[str, int]:
        """
        Check for and process scheduled campaigns.
        
        Returns:
            Dictionary with count of campaigns processed
        """
        logger.info("Checking for scheduled campaigns")
        start_time = time.time()
        
        try:
            with PROCESSING_TIME.time():
                results = await self.campaign_service.process_scheduled_campaigns()
            
            if results['total'] > 0:
                logger.info(
                    "Processed scheduled campaigns",
                    total=results['total'],
                    success=results['success'],
                    failed=results['failed']
                )
                
                # Update metrics
                CAMPAIGNS_PROCESSED.labels(status="success").inc(results['success'])
                CAMPAIGNS_PROCESSED.labels(status="failed").inc(results['failed'])
            else:
                logger.debug("No campaigns to process")
            
            # Update last successful run timestamp
            self.last_successful_run = datetime.utcnow()
            return results
            
        except Exception as e:
            # Update metrics for unexpected errors
            CAMPAIGNS_PROCESSED.labels(status="error").inc()
            
            logger.exception("Error processing scheduled campaigns", error=str(e))
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'error': str(e)
            }
        finally:
            elapsed = time.time() - start_time
            logger.debug(f"Campaign processing took {elapsed:.2f} seconds")
    
    async def run(self):
        """Run the campaign processor loop."""
        logger.info(
            "Starting campaign processor",
            check_interval=self.check_interval
        )
        
        self.running = True
        
        while self.running:
            start_time = time.time()
            
            # Process scheduled campaigns
            await self.process_campaigns()
            
            # Check health status
            self._check_health()
            
            # Calculate sleep time
            elapsed = time.time() - start_time
            sleep_time = max(0, self.check_interval - elapsed)
            
            if sleep_time > 0 and self.running:
                logger.debug(f"Sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)


async def main():
    """Main entry point for the campaign processor."""
    try:
        processor = CampaignProcessor()
        await processor.run()
    except Exception as e:
        logger.exception("Unhandled exception in campaign processor", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 