"""
Monitoring Module

This module provides functionality for monitoring, metrics collection,
and telemetry for the communication-base service.
"""

import time
from typing import Dict, Any, Optional, Callable
import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import Counter, Histogram, Gauge, Summary, REGISTRY
from prometheus_client.exposition import make_wsgi_app
from wsgiref.simple_server import make_server
import threading
import atexit

# Create logger
logger = structlog.get_logger(__name__)

# Global metrics client
_metrics_client = None


class MetricsClient:
    """
    Metrics client for collecting and exposing application metrics.
    """
    
    def __init__(self, app_name: str, environment: str):
        """
        Initialize the metrics client.
        
        Args:
            app_name: Name of the application
            environment: Environment (development, staging, production)
        """
        self.app_name = app_name
        self.environment = environment
        self.metrics = {}
        self.start_time = time.time()
        
        # Initialize default metrics
        self._initialize_metrics()
        
        logger.info("Metrics client initialized", app_name=app_name, environment=environment)
    
    def _initialize_metrics(self):
        """Initialize default metrics."""
        # API metrics
        self.metrics["api_requests_total"] = Counter(
            "api_requests_total",
            "Total number of API requests",
            ["method", "endpoint", "status"]
        )
        
        self.metrics["api_request_duration_seconds"] = Histogram(
            "api_request_duration_seconds",
            "API request duration in seconds",
            ["method", "endpoint"],
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
        )
        
        # Application metrics
        self.metrics["application_info"] = Gauge(
            "application_info",
            "Application information",
            ["name", "environment", "version"]
        )
        
        self.metrics["application_uptime_seconds"] = Gauge(
            "application_uptime_seconds",
            "Application uptime in seconds"
        )
        
        # Campaign metrics
        self.metrics["campaigns_created_total"] = Counter(
            "campaigns_created_total",
            "Total number of campaigns created",
            ["type"]
        )
        
        self.metrics["campaign_conversations_total"] = Counter(
            "campaign_conversations_total",
            "Total number of conversations in campaigns",
            ["campaign_id", "status"]
        )
        
        # Conversation metrics
        self.metrics["conversation_stage_duration_seconds"] = Histogram(
            "conversation_stage_duration_seconds",
            "Duration of conversation stages in seconds",
            ["stage", "campaign_type"],
            buckets=(1, 5, 15, 30, 60, 300, 900, 1800, 3600, 7200, 14400, 28800, 86400)
        )
        
        self.metrics["conversation_progression_total"] = Counter(
            "conversation_progression_total",
            "Total number of conversation progressions",
            ["from_stage", "to_stage", "campaign_type"]
        )
        
        # Worker metrics
        self.metrics["worker_tasks_processed_total"] = Counter(
            "worker_tasks_processed_total",
            "Total number of tasks processed by workers",
            ["task_type", "status"]
        )
        
        self.metrics["worker_task_duration_seconds"] = Histogram(
            "worker_task_duration_seconds",
            "Duration of worker tasks in seconds",
            ["task_type"],
            buckets=(0.1, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300)
        )
        
        # Set application info
        self.metrics["application_info"].labels(
            name=self.app_name,
            environment=self.environment,
            version="0.1.0"
        ).set(1)
    
    def increment(self, metric_name: str, value: float = 1, labels: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric.
        
        Args:
            metric_name: Name of the metric
            value: Value to increment by
            labels: Labels for the metric
        """
        if metric_name not in self.metrics:
            logger.warning(f"Metric {metric_name} not found")
            return
        
        if labels:
            self.metrics[metric_name].labels(**labels).inc(value)
        else:
            self.metrics[metric_name].inc(value)
    
    def observe(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Observe a value for a histogram or summary metric.
        
        Args:
            metric_name: Name of the metric
            value: Value to observe
            labels: Labels for the metric
        """
        if metric_name not in self.metrics:
            logger.warning(f"Metric {metric_name} not found")
            return
        
        if labels:
            self.metrics[metric_name].labels(**labels).observe(value)
        else:
            self.metrics[metric_name].observe(value)
    
    def set(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Set a gauge metric.
        
        Args:
            metric_name: Name of the metric
            value: Value to set
            labels: Labels for the metric
        """
        if metric_name not in self.metrics:
            logger.warning(f"Metric {metric_name} not found")
            return
        
        if labels:
            self.metrics[metric_name].labels(**labels).set(value)
        else:
            self.metrics[metric_name].set(value)
    
    def update_uptime(self):
        """Update the application uptime metric."""
        uptime = time.time() - self.start_time
        self.metrics["application_uptime_seconds"].set(uptime)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics in a dictionary format.
        
        Returns:
            Dictionary of metrics
        """
        self.update_uptime()
        
        # This is a simplified version - in a real implementation,
        # we would extract the actual metrics from the prometheus client
        return {
            "uptime_seconds": time.time() - self.start_time,
            "application": {
                "name": self.app_name,
                "environment": self.environment
            }
        }


def setup_monitoring(app: FastAPI):
    """
    Set up monitoring for the application.
    
    Args:
        app: FastAPI application
    """
    from src.config.config_manager import get_settings
    
    settings = get_settings()
    
    # Initialize metrics client
    if settings.enable_metrics:
        global _metrics_client
        _metrics_client = MetricsClient(
            app_name=settings.service_name,
            environment=settings.environment
        )
        
        # Add middleware for request metrics
        @app.middleware("http")
        async def metrics_middleware(request: Request, call_next: Callable):
            start_time = time.time()
            
            try:
                response = await call_next(request)
                
                # Record request metrics
                if _metrics_client:
                    duration = time.time() - start_time
                    
                    # Extract path without query parameters
                    path = request.url.path
                    
                    # Record request count
                    _metrics_client.increment(
                        "api_requests_total",
                        1,
                        {
                            "method": request.method,
                            "endpoint": path,
                            "status": str(response.status_code)
                        }
                    )
                    
                    # Record request duration
                    _metrics_client.observe(
                        "api_request_duration_seconds",
                        duration,
                        {
                            "method": request.method,
                            "endpoint": path
                        }
                    )
                
                return response
                
            except Exception as e:
                # Record request metrics for exceptions
                if _metrics_client:
                    duration = time.time() - start_time
                    
                    # Extract path without query parameters
                    path = request.url.path
                    
                    # Record request count
                    _metrics_client.increment(
                        "api_requests_total",
                        1,
                        {
                            "method": request.method,
                            "endpoint": path,
                            "status": "500"
                        }
                    )
                    
                    # Record request duration
                    _metrics_client.observe(
                        "api_request_duration_seconds",
                        duration,
                        {
                            "method": request.method,
                            "endpoint": path
                        }
                    )
                    
                    logger.error(
                        "Error processing request",
                        method=request.method,
                        path=path,
                        error=str(e)
                    )
                
                raise
        
        # Start metrics server if enabled
        if settings.metrics_port != settings.port:
            def start_metrics_server():
                """Start Prometheus metrics server."""
                app = make_wsgi_app()
                httpd = make_server('', settings.metrics_port, app)
                httpd.serve_forever()
            
            # Start metrics server in a separate thread
            thread = threading.Thread(target=start_metrics_server)
            thread.daemon = True
            thread.start()
            
            logger.info(
                "Prometheus metrics server started", 
                port=settings.metrics_port
            )
            
            # Register cleanup on exit
            def cleanup():
                """Cleanup function to stop the metrics server."""
                thread.join(timeout=1.0)
            
            atexit.register(cleanup)
        
        logger.info("Monitoring setup complete")
    else:
        logger.info("Metrics disabled, skipping monitoring setup")


def get_metrics() -> Optional[MetricsClient]:
    """
    Get the metrics client instance.
    
    Returns:
        Metrics client instance or None if metrics are disabled
    """
    return _metrics_client 