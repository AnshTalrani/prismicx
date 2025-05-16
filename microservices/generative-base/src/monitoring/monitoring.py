"""
Monitoring Module

This module implements monitoring and metrics collection for the generative-base microservice.
"""

from typing import Dict, Any, Optional
import time
from datetime import datetime
import structlog
from prometheus_client import Counter, Histogram, Gauge, Summary
from prometheus_client.metrics import MetricWrapperBase

# Configure structured logging
logger = structlog.get_logger(__name__)

class MonitoringMetrics:
    """
    Monitoring metrics for the generative-base microservice.
    
    This class manages:
    - Task processing metrics
    - Resource utilization metrics
    - Error and performance metrics
    - Custom business metrics
    """
    
    def __init__(self):
        """Initialize monitoring metrics."""
        # Task Processing Metrics
        self.tasks_total = Counter(
            'generative_tasks_total',
            'Total number of tasks processed',
            ['status', 'task_type']
        )
        
        self.task_duration = Histogram(
            'generative_task_duration_seconds',
            'Time taken to process tasks',
            ['task_type'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
        )
        
        # Resource Metrics
        self.memory_usage = Gauge(
            'generative_memory_bytes',
            'Memory usage in bytes'
        )
        
        self.cpu_usage = Gauge(
            'generative_cpu_percent',
            'CPU usage percentage'
        )
        
        # Error Metrics
        self.errors_total = Counter(
            'generative_errors_total',
            'Total number of errors',
            ['error_type', 'task_type']
        )
        
        # Performance Metrics
        self.queue_size = Gauge(
            'generative_queue_size',
            'Current size of the task queue'
        )
        
        self.processing_time = Summary(
            'generative_processing_time_seconds',
            'Time spent in processing',
            ['stage']
        )
        
        # Business Metrics
        self.template_usage = Counter(
            'generative_template_usage_total',
            'Number of times each template is used',
            ['template_id', 'version']
        )
        
        self.output_size = Histogram(
            'generative_output_size_bytes',
            'Size of generated outputs',
            ['output_type'],
            buckets=(100, 500, 1000, 5000, 10000, 50000, 100000)
        )
        
        logger.info("Monitoring metrics initialized")
    
    def record_task_start(self, task_id: str, task_type: str):
        """
        Record the start of a task.
        
        Args:
            task_id: Unique identifier for the task
            task_type: Type of the task
        """
        self.tasks_total.labels(status='started', task_type=task_type).inc()
        logger.info(
            "Task started",
            task_id=task_id,
            task_type=task_type
        )
    
    def record_task_completion(self, task_id: str, task_type: str, duration: float):
        """
        Record the completion of a task.
        
        Args:
            task_id: Unique identifier for the task
            task_type: Type of the task
            duration: Time taken to process the task
        """
        self.tasks_total.labels(status='completed', task_type=task_type).inc()
        self.task_duration.labels(task_type=task_type).observe(duration)
        logger.info(
            "Task completed",
            task_id=task_id,
            task_type=task_type,
            duration=duration
        )
    
    def record_task_error(self, task_id: str, task_type: str, error_type: str):
        """
        Record a task error.
        
        Args:
            task_id: Unique identifier for the task
            task_type: Type of the task
            error_type: Type of error that occurred
        """
        self.tasks_total.labels(status='error', task_type=task_type).inc()
        self.errors_total.labels(error_type=error_type, task_type=task_type).inc()
        logger.error(
            "Task error",
            task_id=task_id,
            task_type=task_type,
            error_type=error_type
        )
    
    def update_resource_metrics(self, memory_bytes: int, cpu_percent: float):
        """
        Update resource utilization metrics.
        
        Args:
            memory_bytes: Current memory usage in bytes
            cpu_percent: Current CPU usage percentage
        """
        self.memory_usage.set(memory_bytes)
        self.cpu_usage.set(cpu_percent)
    
    def update_queue_metrics(self, queue_size: int):
        """
        Update queue metrics.
        
        Args:
            queue_size: Current size of the task queue
        """
        self.queue_size.set(queue_size)
    
    def record_processing_time(self, stage: str, duration: float):
        """
        Record processing time for a specific stage.
        
        Args:
            stage: Name of the processing stage
            duration: Time taken for the stage
        """
        self.processing_time.labels(stage=stage).observe(duration)
    
    def record_template_usage(self, template_id: str, version: str):
        """
        Record template usage.
        
        Args:
            template_id: ID of the template used
            version: Version of the template
        """
        self.template_usage.labels(
            template_id=template_id,
            version=version
        ).inc()
    
    def record_output_size(self, output_type: str, size_bytes: int):
        """
        Record the size of generated output.
        
        Args:
            output_type: Type of the output
            size_bytes: Size of the output in bytes
        """
        self.output_size.labels(output_type=output_type).observe(size_bytes)

# Global metrics instance
metrics = MonitoringMetrics() 