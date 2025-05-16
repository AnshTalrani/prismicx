"""
Communication Base Microservice - Main Entry Point

This module serves as the main entry point for the Communication Base microservice,
which handles campaign processing from agent batch requests, conversation state management,
and worker-based message processing.
"""

import asyncio
import signal
import sys
from typing import Set

import structlog

from src.config.config_manager import get_settings
from src.config.monitoring import get_metrics, setup_monitoring
from src.clients.system_users_repository_client import SystemUsersRepositoryClient
from src.clients.campaign_users_repository_client import CampaignUsersRepositoryClient
from src.storage.entity_repository_manager import EntityRepositoryManager
from src.service.campaign_manager import CampaignManager
from src.service.campaign_poller import CampaignPoller
from src.service.worker_service import WorkerService
from src.multitenant import (
    TenantService, 
    get_database_adapter,
    get_communication_config
)


# Configure logger
logger = structlog.get_logger()

# Get settings
settings = get_settings()

# Initialize repositories and services
system_users_repo = SystemUsersRepositoryClient()
campaign_users_repo = CampaignUsersRepositoryClient()
entity_repo_manager = EntityRepositoryManager()
campaign_manager = CampaignManager(system_users_repo)
campaign_poller = CampaignPoller(system_users_repo, campaign_manager)
worker_service = WorkerService(campaign_manager, system_users_repo)

# Store running tasks
running_tasks: Set[asyncio.Task] = set()


async def startup():
    """Initialize services and start background tasks."""
    # Setup monitoring
    metrics = get_metrics()
    metrics.register_counter("campaigns_processed", "Number of campaigns processed")
    metrics.register_counter("batch_requests_processed", "Number of batch requests processed")
    metrics.register_gauge("active_workers", "Number of active workers")
    
    # Initialize multitenant components
    logger.info("Initializing multitenant components")
    tenant_service = TenantService()
    db_adapter = get_database_adapter()
    comm_config = get_communication_config()
    
    # Initialize repository clients
    logger.info("Initializing repository clients")
    await system_users_repo.initialize()
    await campaign_users_repo.initialize()
    await entity_repo_manager.initialize()
    
    # Initialize services
    logger.info("Initializing services")
    await campaign_manager.initialize()
    await campaign_poller.initialize()
    await worker_service.initialize()
    
    # Start background tasks
    logger.info("Starting background tasks")
    start_background_tasks()
    
    logger.info("Communication Base microservice started (worker-only mode)")
    
    # Keep the main task running
    while True:
        await asyncio.sleep(60)
        logger.debug(
            "Service status", 
            running_tasks=len(running_tasks), 
            active_workers=worker_service.active_workers
        )


async def shutdown():
    """Cleanup resources and stop background tasks."""
    logger.info("Shutting down microservice")
    
    # Stop the campaign poller
    await campaign_poller.stop()
    
    # Stop the worker service
    await worker_service.stop()
    
    # Cancel all running tasks
    for task in running_tasks:
        task.cancel()
        
    # Wait for all tasks to complete with a timeout
    if running_tasks:
        await asyncio.wait(running_tasks, timeout=5.0)
    
    # Close repository connections
    await system_users_repo.close()
    await campaign_users_repo.close()
    
    logger.info("Microservice shutdown complete")


def start_background_tasks():
    """Start all background tasks and track them."""
    # Start campaign poller task
    poller_task = asyncio.create_task(campaign_poller.run())
    poller_task.add_done_callback(task_done_callback)
    running_tasks.add(poller_task)
    
    # Start worker service task
    worker_task = asyncio.create_task(worker_service.run())
    worker_task.add_done_callback(task_done_callback)
    running_tasks.add(worker_task)
    
    logger.info(f"Started {len(running_tasks)} background tasks")


def task_done_callback(task: asyncio.Task):
    """Callback for when a task is done. Removes it from the set of running tasks."""
    running_tasks.discard(task)
    
    # Check for exceptions
    if not task.cancelled() and task.exception():
        logger.error(
            "Background task raised an exception",
            exception=str(task.exception())
        )
        # Restart the task if it wasn't cancelled and we're still running
        if len(running_tasks) > 0:  # If we still have other tasks, we're not shutting down
            start_background_tasks()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    
    # Set up signal handlers for graceful shutdown
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown())
        )
    
    # Run the main task
    try:
        loop.run_until_complete(startup())
    except asyncio.CancelledError:
        pass
    finally:
        loop.run_until_complete(shutdown())
        loop.close() 