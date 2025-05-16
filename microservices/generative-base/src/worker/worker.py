"""
Worker Module

This module manages the worker lifecycle and task processing for the generative-base microservice.
"""

from typing import Dict, Any, Optional
import asyncio
import structlog
from celery import Celery
from celery.signals import worker_ready, worker_shutdown
from tenacity import retry, stop_after_attempt, wait_exponential
import time

from src.config import settings
from src.repository import repository
from src.monitoring.monitoring import metrics

# Configure structured logging
logger = structlog.get_logger(__name__)

# Configure Celery
celery_app = Celery(
    'generative_worker',
    broker=settings.redis.uri,
    backend=settings.redis.uri
)

# Configure task settings
celery_app.conf.update(
    task_default_priority=5,
    task_queue_max_priority=10,
    task_annotations={
        'process_task': {
            'rate_limit': '10/m',
            'max_retries': 3,
            'default_retry_delay': 60
        }
    }
)

@celery_app.task(bind=True, max_retries=3)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def process_task(self, task_id: str, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a task with monitoring and error handling.
    
    Args:
        task_id: Unique identifier for the task
        task_type: Type of task to process
        task_data: Task-specific data
        
    Returns:
        Dict containing task results
    """
    start_time = time.time()
    
    try:
        # Record task start
        metrics.record_task_start(task_id, task_type)
        
        # Store task context
        repository.store_task_context(task_id, {
            'task_type': task_type,
            'status': 'processing',
            'start_time': start_time
        })
        
        # Process based on task type
        if task_type == 'template_generation':
            result = process_template_generation(task_data)
        elif task_type == 'content_generation':
            result = process_content_generation(task_data)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
        
        # Record template usage if applicable
        if 'template_id' in task_data:
            metrics.record_template_usage(
                task_data['template_id'],
                task_data.get('version', 'latest')
            )
        
        # Record output size
        if 'output' in result:
            metrics.record_output_size(
                task_type,
                len(str(result['output']).encode('utf-8'))
            )
        
        # Record task completion
        duration = time.time() - start_time
        metrics.record_task_completion(task_id, task_type, duration)
        
        # Store results
        repository.store_task_results(task_id, result)
        
        return result
        
    except Exception as e:
        # Record error
        metrics.record_task_error(task_id, task_type, type(e).__name__)
        
        # Update task context with error
        repository.store_task_context(task_id, {
            'status': 'error',
            'error': str(e),
            'error_type': type(e).__name__
        })
        
        # Retry if appropriate
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        else:
            logger.error(
                "Task failed permanently",
                task_id=task_id,
                task_type=task_type,
                error=str(e)
            )
            raise

@celery_app.signals.worker_ready.connect
def on_worker_ready(**kwargs):
    """Handle worker ready signal."""
    logger.info("Worker is ready to process tasks")
    metrics.update_queue_metrics(0)  # Initialize queue metrics

@celery_app.signals.worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    """Handle worker shutdown signal."""
    logger.info("Worker is shutting down")
    repository.close()  # Clean up repository connections

def process_template_generation(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process template generation task.
    
    Args:
        task_data: Template generation parameters
        
    Returns:
        Dict containing generation results
    """
    # Implementation specific to template generation
    pass

def process_content_generation(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process content generation task.
    
    Args:
        task_data: Content generation parameters
        
    Returns:
        Dict containing generation results
    """
    # Implementation specific to content generation
    pass 