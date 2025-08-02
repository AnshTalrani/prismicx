"""
Monitoring Module

This module provides monitoring functionality for the application.
It includes metrics collection, performance tracking, and health checks.
"""

import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import structlog
import asyncio

# Configure structured logging
logger = structlog.get_logger(__name__)

class Monitoring:
    """
    Monitoring service for tracking application metrics and health.
    
    This class:
    - Collects performance metrics
    - Tracks component execution times
    - Monitors resource usage
    - Provides health check information
    """
    
    def __init__(self):
        """Initialize the monitoring service."""
        self.metrics = {
            "startup_time": datetime.utcnow().isoformat(),
            "requests": {
                "total": 0,
                "success": 0,
                "error": 0,
                "latency_ms_avg": 0
            },
            "processing": {
                "contexts_processed": 0,
                "batch_processed": 0,
                "failed_contexts": 0,
                "avg_processing_time_ms": 0
            },
            "components": {},
            "health": {
                "status": "starting",
                "last_check": datetime.utcnow().isoformat(),
                "details": {}
            }
        }
        
        # Performance tracking
        self._latency_sum = 0
        self._processing_time_sum = 0
        
        logger.info("Monitoring service initialized")
    
    def track_request(self, success: bool, latency_ms: float) -> None:
        """
        Track an API request.
        
        Args:
            success: Whether the request was successful
            latency_ms: Request latency in milliseconds
        """
        self.metrics["requests"]["total"] += 1
        
        if success:
            self.metrics["requests"]["success"] += 1
        else:
            self.metrics["requests"]["error"] += 1
        
        # Update average latency
        self._latency_sum += latency_ms
        self.metrics["requests"]["latency_ms_avg"] = round(
            self._latency_sum / self.metrics["requests"]["total"], 2
        )
    
    def track_processing(self, success: bool, processing_time_ms: float, is_batch: bool = False) -> None:
        """
        Track context processing.
        
        Args:
            success: Whether processing was successful
            processing_time_ms: Processing time in milliseconds
            is_batch: Whether this was batch processing
        """
        self.metrics["processing"]["contexts_processed"] += 1
        
        if not success:
            self.metrics["processing"]["failed_contexts"] += 1
            
        if is_batch:
            self.metrics["processing"]["batch_processed"] += 1
        
        # Update average processing time
        self._processing_time_sum += processing_time_ms
        self.metrics["processing"]["avg_processing_time_ms"] = round(
            self._processing_time_sum / self.metrics["processing"]["contexts_processed"], 2
        )
    
    def track_component(self, component_name: str, execution_time_ms: float, success: bool) -> None:
        """
        Track component execution.
        
        Args:
            component_name: Name of the component
            execution_time_ms: Execution time in milliseconds
            success: Whether execution was successful
        """
        if component_name not in self.metrics["components"]:
            self.metrics["components"][component_name] = {
                "executions": 0,
                "failures": 0,
                "avg_execution_time_ms": 0,
                "execution_time_sum": 0
            }
        
        component_metrics = self.metrics["components"][component_name]
        component_metrics["executions"] += 1
        
        if not success:
            component_metrics["failures"] += 1
        
        # Update average execution time
        component_metrics["execution_time_sum"] += execution_time_ms
        component_metrics["avg_execution_time_ms"] = round(
            component_metrics["execution_time_sum"] / component_metrics["executions"], 2
        )
    
    def update_health(self, status: str, details: Dict[str, Any]) -> None:
        """
        Update health status.
        
        Args:
            status: Health status (healthy, degraded, unhealthy)
            details: Health check details
        """
        self.metrics["health"]["status"] = status
        self.metrics["health"]["last_check"] = datetime.utcnow().isoformat()
        self.metrics["health"]["details"] = details
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics.
        
        Returns:
            Dictionary of metrics
        """
        # Add a timestamp for when metrics were collected
        metrics = self.metrics.copy()
        metrics["timestamp"] = datetime.utcnow().isoformat()
        return metrics
    
    async def run_periodic_health_check(self, check_interval: int, health_check_fn: Callable) -> None:
        """
        Run periodic health checks.
        
        Args:
            check_interval: Check interval in seconds
            health_check_fn: Health check function
        """
        while True:
            try:
                health_result = await health_check_fn()
                self.update_health(
                    status=health_result.get("status", "unknown"),
                    details=health_result.get("details", {})
                )
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                self.update_health(
                    status="unhealthy",
                    details={"error": str(e)}
                )
            
            # Wait for next check
            await asyncio.sleep(check_interval)

# Singleton instance
monitoring = Monitoring() 