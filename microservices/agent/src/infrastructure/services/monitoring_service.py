"""Interface for monitoring service."""
from typing import Dict, Any, Optional, List
from datetime import datetime
from abc import ABC, abstractmethod


class IMonitoringService(ABC):
    """Interface for monitoring service."""
    
    @abstractmethod
    async def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Record a metric value.
        
        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for the metric
            timestamp: Optional timestamp for the metric
        """
        pass
    
    @abstractmethod
    async def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Counter name
            value: Amount to increment by
            tags: Optional tags for the counter
        """
        pass
    
    @abstractmethod
    async def record_gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a gauge metric value.
        
        Args:
            name: Gauge name
            value: Gauge value
            tags: Optional tags for the gauge
        """
        pass
    
    @abstractmethod
    async def record_histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a histogram value.
        
        Args:
            name: Histogram name
            value: Value to record
            tags: Optional tags for the histogram
        """
        pass
    
    @abstractmethod
    async def record_timing(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a timing value.
        
        Args:
            name: Timing name
            value: Time value in seconds
            tags: Optional tags for the timing
        """
        pass
    
    @abstractmethod
    async def record_event(
        self,
        name: str,
        properties: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record an event.
        
        Args:
            name: Event name
            properties: Optional event properties
            tags: Optional tags for the event
        """
        pass
    
    @abstractmethod
    async def record_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record an error.
        
        Args:
            error: Exception to record
            context: Optional error context
            tags: Optional tags for the error
        """
        pass
    
    @abstractmethod
    async def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a request metric.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            tags: Optional tags for the request
        """
        pass
    
    @abstractmethod
    async def record_batch_operation(
        self,
        operation: str,
        item_count: int,
        success_count: int,
        failure_count: int,
        duration_ms: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a batch operation metric.
        
        Args:
            operation: Operation name
            item_count: Total number of items
            success_count: Number of successful items
            failure_count: Number of failed items
            duration_ms: Operation duration in milliseconds
            tags: Optional tags for the operation
        """
        pass
    
    @abstractmethod
    async def get_metric_value(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> float:
        """
        Get the value of a metric.
        
        Args:
            name: Metric name
            tags: Optional tags to filter by
            start_time: Optional start time for the query
            end_time: Optional end time for the query
            
        Returns:
            Metric value
        """
        pass
    
    @abstractmethod
    async def get_metric_history(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        interval: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the history of a metric.
        
        Args:
            name: Metric name
            tags: Optional tags to filter by
            start_time: Optional start time for the query
            end_time: Optional end time for the query
            interval: Optional time interval for aggregation
            
        Returns:
            List of metric values over time
        """
        pass 