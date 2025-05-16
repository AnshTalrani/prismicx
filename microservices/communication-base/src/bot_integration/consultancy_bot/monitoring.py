"""
Monitoring utilities for Consultancy Bot.

Provides functionality for tracking performance metrics, usage patterns,
error logging, and system health indicators for the consultancy bot.
"""

import os
import time
import json
import logging
import threading
import statistics
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Union, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
import structlog

logger = structlog.get_logger(__name__)

class MetricType(Enum):
    """Types of metrics that can be tracked"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class MetricValue:
    """Container for a metric value with metadata"""
    value: Union[int, float]
    timestamp: float = field(default_factory=time.time)
    dimensions: Dict[str, str] = field(default_factory=dict)

@dataclass
class MetricSummary:
    """Summary statistics for a collected metric"""
    count: int = 0
    sum: float = 0
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    p95: Optional[float] = None  # 95th percentile
    last_value: Optional[float] = None
    last_updated: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {k: v for k, v in asdict(self).items() if v is not None}

class MetricsRegistry:
    """
    Registry for tracking various metrics about the bot's performance and usage.
    
    Supports different metric types like counters, gauges, histograms, and timers.
    All metrics can be tagged with dimensions for flexible querying.
    """
    
    def __init__(self, capacity: int = 1000, retention_hours: int = 24):
        """
        Initialize the metrics registry.
        
        Args:
            capacity: Maximum number of data points to store per metric 
            retention_hours: Hours to retain metric data
        """
        self.metrics: Dict[str, List[MetricValue]] = {}
        self.metric_types: Dict[str, MetricType] = {}
        self.capacity = capacity
        self.retention_seconds = retention_hours * 3600
        self.lock = threading.Lock()
        
        # Start background cleanup thread
        self._start_cleanup_thread()
        
        logger.info("Metrics registry initialized", 
                  capacity=capacity, 
                  retention_hours=retention_hours)
    
    def _start_cleanup_thread(self) -> None:
        """Start background thread for periodic cleanup"""
        def cleanup_task():
            while True:
                time.sleep(3600)  # Run once per hour
                try:
                    self._cleanup_old_metrics()
                except Exception as e:
                    logger.error("Error in metrics cleanup", error=str(e))
        
        cleanup_thread = threading.Thread(
            target=cleanup_task, 
            daemon=True,
            name="metrics-cleanup"
        )
        cleanup_thread.start()
    
    def _cleanup_old_metrics(self) -> None:
        """Remove metrics older than retention period"""
        if not self.retention_seconds:
            return
            
        cutoff = time.time() - self.retention_seconds
        deleted_count = 0
        
        with self.lock:
            for metric_name, values in list(self.metrics.items()):
                # Filter out old values
                new_values = [v for v in values if v.timestamp >= cutoff]
                deleted_count += len(values) - len(new_values)
                
                if not new_values:
                    # Remove metric entirely if no values remain
                    del self.metrics[metric_name]
                    del self.metric_types[metric_name]
                else:
                    # Update with filtered values
                    self.metrics[metric_name] = new_values
                    
        if deleted_count > 0:
            logger.info("Cleaned up old metrics", deleted_count=deleted_count)
    
    def register_metric(self, name: str, metric_type: MetricType) -> None:
        """
        Register a new metric type.
        
        Args:
            name: Metric name
            metric_type: Type of metric
        """
        with self.lock:
            # Check if already exists with a different type
            if name in self.metric_types and self.metric_types[name] != metric_type:
                logger.warning(
                    "Changing metric type", 
                    metric=name, 
                    old_type=self.metric_types[name].value,
                    new_type=metric_type.value
                )
            
            self.metric_types[name] = metric_type
            if name not in self.metrics:
                self.metrics[name] = []
    
    def _record_value(
        self, 
        name: str, 
        value: Union[int, float], 
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a value for a metric.
        
        Args:
            name: Metric name
            value: Value to record
            dimensions: Additional dimensions to tag the metric
        """
        if dimensions is None:
            dimensions = {}
            
        with self.lock:
            if name not in self.metrics:
                logger.warning("Recording to unregistered metric", metric=name)
                # Assume it's a counter if not registered
                self.metric_types[name] = MetricType.COUNTER
                self.metrics[name] = []
                
            # Create new metric value 
            metric_value = MetricValue(
                value=value,
                dimensions=dimensions.copy()
            )
            
            # Add to the list
            self.metrics[name].append(metric_value)
            
            # Enforce capacity limit
            if len(self.metrics[name]) > self.capacity:
                self.metrics[name] = self.metrics[name][-self.capacity:]
    
    def increment(
        self, 
        name: str, 
        value: Union[int, float] = 1, 
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Amount to increment by
            dimensions: Additional dimensions to tag the metric
        """
        self.register_metric(name, MetricType.COUNTER)
        self._record_value(name, value, dimensions)
    
    def gauge(
        self, 
        name: str, 
        value: Union[int, float], 
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge metric value.
        
        Args:
            name: Metric name
            value: Current gauge value
            dimensions: Additional dimensions to tag the metric
        """
        self.register_metric(name, MetricType.GAUGE)
        self._record_value(name, value, dimensions)
    
    def histogram(
        self, 
        name: str, 
        value: Union[int, float], 
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a value in a histogram metric.
        
        Args:
            name: Metric name
            value: Value to record
            dimensions: Additional dimensions to tag the metric
        """
        self.register_metric(name, MetricType.HISTOGRAM)
        self._record_value(name, value, dimensions)
    
    def timer_start(self, name: str, dimensions: Optional[Dict[str, str]] = None) -> Callable[[], float]:
        """
        Start a timer and return a function to stop it.
        
        Args:
            name: Metric name
            dimensions: Additional dimensions to tag the metric
            
        Returns:
            Function that stops the timer and returns elapsed time
        """
        self.register_metric(name, MetricType.TIMER)
        start_time = time.time()
        
        def stop_timer():
            elapsed = time.time() - start_time
            self._record_value(name, elapsed, dimensions)
            return elapsed
            
        return stop_timer
    
    def with_timer(self, name: str, dimensions: Optional[Dict[str, str]] = None):
        """
        Context manager for timing a block of code.
        
        Args:
            name: Metric name
            dimensions: Additional dimensions to tag the metric
            
        Example:
            ```python
            with metrics.with_timer("process_time", {"module": "nlp"}):
                # Code to time
                process_text()
            ```
        """
        class TimerContext:
            def __init__(self, registry, metric_name, dims):
                self.registry = registry
                self.metric_name = metric_name
                self.dimensions = dims
                self.start_time = None
                
            def __enter__(self):
                self.start_time = time.time()
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                elapsed = time.time() - self.start_time
                self.registry._record_value(self.metric_name, elapsed, self.dimensions)
                
        return TimerContext(self, name, dimensions)
    
    def get_metric_summary(
        self, 
        name: str, 
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        dimensions: Optional[Dict[str, str]] = None
    ) -> Optional[MetricSummary]:
        """
        Get summary statistics for a metric.
        
        Args:
            name: Metric name
            start_time: Optional start time filter (timestamp)
            end_time: Optional end time filter (timestamp)
            dimensions: Optional dimension filters
            
        Returns:
            Summary statistics or None if metric doesn't exist
        """
        with self.lock:
            if name not in self.metrics:
                return None
                
            values = self.metrics[name]
            
            # Apply time filters
            if start_time is not None:
                values = [v for v in values if v.timestamp >= start_time]
            if end_time is not None:
                values = [v for v in values if v.timestamp <= end_time]
                
            # Apply dimension filters
            if dimensions:
                values = [
                    v for v in values if all(
                        k in v.dimensions and v.dimensions[k] == val 
                        for k, val in dimensions.items()
                    )
                ]
                
            if not values:
                return MetricSummary()
                
            # Extract raw values
            raw_values = [v.value for v in values]
            
            # Calculate statistics
            summary = MetricSummary(
                count=len(raw_values),
                sum=sum(raw_values),
                min=min(raw_values),
                max=max(raw_values),
                mean=statistics.mean(raw_values),
                last_value=values[-1].value,
                last_updated=values[-1].timestamp
            )
            
            # Calculate median and percentiles if enough data
            if len(raw_values) >= 2:
                summary.median = statistics.median(raw_values)
            if len(raw_values) >= 20:  # Need enough samples for percentile
                sorted_values = sorted(raw_values)
                idx = int(len(sorted_values) * 0.95)
                summary.p95 = sorted_values[idx]
                
            return summary
            
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summaries for all metrics.
        
        Returns:
            Dictionary of metric names to their summaries
        """
        result = {}
        
        with self.lock:
            for name in self.metrics:
                summary = self.get_metric_summary(name)
                if summary:
                    result[name] = {
                        "type": self.metric_types[name].value,
                        "summary": summary.to_dict()
                    }
                    
        return result
    
    def get_distinct_dimensions(self, name: str) -> Dict[str, Set[str]]:
        """
        Get all distinct dimension values for a metric.
        
        Args:
            name: Metric name
            
        Returns:
            Dictionary of dimension names to sets of values
        """
        result: Dict[str, Set[str]] = {}
        
        with self.lock:
            if name not in self.metrics:
                return {}
                
            for value in self.metrics[name]:
                for dim_name, dim_value in value.dimensions.items():
                    if dim_name not in result:
                        result[dim_name] = set()
                    result[dim_name].add(dim_value)
                    
        return result
    
    def export_data(
        self, 
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Export all metrics data for persistence or analysis.
        
        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            Dictionary with all metrics data
        """
        export = {
            "timestamp": time.time(),
            "metrics": {},
            "types": {}
        }
        
        with self.lock:
            for name, values in self.metrics.items():
                # Apply time filters
                filtered_values = values
                if start_time is not None:
                    filtered_values = [v for v in filtered_values if v.timestamp >= start_time]
                if end_time is not None:
                    filtered_values = [v for v in filtered_values if v.timestamp <= end_time]
                
                # Convert to serializable format
                export["metrics"][name] = [
                    {
                        "value": v.value,
                        "timestamp": v.timestamp,
                        "dimensions": v.dimensions
                    }
                    for v in filtered_values
                ]
                
                # Record type
                export["types"][name] = self.metric_types[name].value
                
        return export
    
    def import_data(self, data: Dict[str, Any]) -> None:
        """
        Import metrics data from a previous export.
        
        Args:
            data: Data dictionary from export_data
        """
        with self.lock:
            # Import metric types
            for name, type_str in data.get("types", {}).items():
                try:
                    metric_type = MetricType(type_str)
                    self.metric_types[name] = metric_type
                except ValueError:
                    logger.warning("Unknown metric type during import", metric=name, type=type_str)
            
            # Import metric values
            for name, values in data.get("metrics", {}).items():
                if name not in self.metrics:
                    self.metrics[name] = []
                    
                for value_data in values:
                    try:
                        metric_value = MetricValue(
                            value=value_data["value"],
                            timestamp=value_data["timestamp"],
                            dimensions=value_data.get("dimensions", {})
                        )
                        self.metrics[name].append(metric_value)
                    except (KeyError, TypeError) as e:
                        logger.warning("Error importing metric value", 
                                     metric=name, error=str(e))
                        
                # Enforce capacity limit
                if len(self.metrics[name]) > self.capacity:
                    self.metrics[name] = self.metrics[name][-self.capacity:]

class BotActivityMonitor:
    """
    High-level monitoring for bot activity and health.
    
    Provides methods to track:
    - Request processing times
    - Success/failure rates
    - User engagement metrics
    - Component performance
    - Error tracking
    """
    
    def __init__(self, metrics: Optional[MetricsRegistry] = None):
        """
        Initialize the bot monitor.
        
        Args:
            metrics: Optional existing metrics registry to use
        """
        self.metrics = metrics or MetricsRegistry()
        self.session_starts: Dict[str, float] = {}
        self.error_counts: Dict[str, int] = {}
        
        logger.info("Bot activity monitor initialized")
    
    def track_request(
        self, 
        request_type: str,
        conversation_id: str,
        dimensions: Optional[Dict[str, str]] = None
    ) -> Callable[[], None]:
        """
        Track a request with timing.
        
        Args:
            request_type: Type of request 
            conversation_id: ID of the conversation
            dimensions: Additional dimensions
            
        Returns:
            Function to call when request completes
        """
        if dimensions is None:
            dimensions = {}
            
        dims = {
            "request_type": request_type,
            "conversation_id": conversation_id,
            **dimensions
        }
        
        # Track request count
        self.metrics.increment("bot.requests.count", dimensions=dims)
        
        # Start timer for request duration
        stop_timer = self.metrics.timer_start("bot.requests.duration", dimensions=dims)
        
        def complete_tracking(success: bool = True, error_type: Optional[str] = None):
            # Record request duration
            elapsed = stop_timer()
            
            # Track success/failure
            if success:
                self.metrics.increment("bot.requests.success", dimensions=dims)
            else:
                error_dims = dims.copy()
                if error_type:
                    error_dims["error_type"] = error_type
                self.metrics.increment("bot.requests.failure", dimensions=error_dims)
                
                # Track error counts
                error_key = error_type or "unknown"
                self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
                if self.error_counts[error_key] % 10 == 0:  # Log every 10th error
                    logger.warning(
                        "Error threshold reached",
                        error_type=error_key,
                        count=self.error_counts[error_key]
                    )
            
            return elapsed
            
        return complete_tracking
    
    def track_session_start(self, session_id: str, user_id: Optional[str] = None) -> None:
        """
        Track the start of a user session.
        
        Args:
            session_id: Unique session identifier
            user_id: Optional user identifier
        """
        dimensions = {"session_id": session_id}
        if user_id:
            dimensions["user_id"] = user_id
            
        self.session_starts[session_id] = time.time()
        self.metrics.increment("bot.sessions.started", dimensions=dimensions)
    
    def track_session_end(
        self, 
        session_id: str, 
        messages_count: int = 0,
        user_id: Optional[str] = None
    ) -> None:
        """
        Track the end of a user session.
        
        Args:
            session_id: Unique session identifier
            messages_count: Number of messages in the session
            user_id: Optional user identifier
        """
        dimensions = {"session_id": session_id}
        if user_id:
            dimensions["user_id"] = user_id
            
        self.metrics.increment("bot.sessions.ended", dimensions=dimensions)
        self.metrics.histogram("bot.sessions.message_count", messages_count, dimensions=dimensions)
        
        # Calculate session duration if start was tracked
        if session_id in self.session_starts:
            duration = time.time() - self.session_starts[session_id]
            self.metrics.histogram("bot.sessions.duration", duration, dimensions=dimensions)
            del self.session_starts[session_id]
    
    def track_component_execution(
        self, 
        component_name: str, 
        dimensions: Optional[Dict[str, str]] = None
    ):
        """
        Context manager to track component execution time.
        
        Args:
            component_name: Name of the component 
            dimensions: Additional dimensions
            
        Returns:
            Context manager for timing
        """
        if dimensions is None:
            dimensions = {}
            
        dims = {
            "component": component_name,
            **dimensions
        }
        
        return self.metrics.with_timer("bot.component.execution_time", dims)
    
    def track_nlp_metrics(
        self, 
        text_length: int,
        processing_time: float,
        features_extracted: int,
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Track NLP processing metrics.
        
        Args:
            text_length: Length of processed text
            processing_time: Time taken for processing 
            features_extracted: Number of features extracted
            dimensions: Additional dimensions
        """
        if dimensions is None:
            dimensions = {}
            
        self.metrics.histogram("bot.nlp.text_length", text_length, dimensions)
        self.metrics.histogram("bot.nlp.processing_time", processing_time, dimensions)
        self.metrics.histogram("bot.nlp.processing_speed", 
                              text_length / max(processing_time, 0.001), 
                              dimensions)
        self.metrics.histogram("bot.nlp.features_extracted", features_extracted, dimensions)
    
    def track_memory_usage(
        self, 
        memory_mb: float,
        component: Optional[str] = None
    ) -> None:
        """
        Track memory usage.
        
        Args:
            memory_mb: Memory usage in MB
            component: Optional component name
        """
        dimensions = {}
        if component:
            dimensions["component"] = component
            
        self.metrics.gauge("bot.system.memory_usage", memory_mb, dimensions)
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get current health status of the bot.
        
        Returns:
            Dictionary with health metrics
        """
        last_hour = time.time() - 3600
        
        # Get request metrics for last hour
        requests = self.metrics.get_metric_summary("bot.requests.count", start_time=last_hour)
        successes = self.metrics.get_metric_summary("bot.requests.success", start_time=last_hour)
        failures = self.metrics.get_metric_summary("bot.requests.failure", start_time=last_hour)
        duration = self.metrics.get_metric_summary("bot.requests.duration", start_time=last_hour)
        
        # Calculate success rate
        total_requests = (requests.count if requests else 0)
        total_success = (successes.count if successes else 0)
        success_rate = (total_success / total_requests) if total_requests > 0 else 1.0
        
        # Get latest memory usage
        memory = self.metrics.get_metric_summary("bot.system.memory_usage")
        
        return {
            "timestamp": time.time(),
            "status": "healthy" if success_rate >= 0.95 else "degraded",
            "request_count_1h": total_requests,
            "success_rate_1h": success_rate,
            "avg_request_duration_ms": (duration.mean * 1000) if duration and duration.mean else None,
            "p95_request_duration_ms": (duration.p95 * 1000) if duration and duration.p95 else None,
            "memory_usage_mb": memory.last_value if memory else None,
            "error_counts": self.error_counts.copy()
        }
    
def get_bot_monitor(enabled: bool = True) -> BotActivityMonitor:
    """Factory function to get a bot monitor instance"""
    if not enabled:
        logger.info("Bot monitoring disabled")
        return BotActivityMonitor(MetricsRegistry(capacity=1))  # Minimal registry
        
    return BotActivityMonitor() 