"""
Monitoring Module

This module provides utilities for monitoring and metrics collection.
"""

from typing import Dict, Any, Optional, Union
import time
import structlog

logger = structlog.get_logger(__name__)

# Global metrics instance
_metrics_instance = None

def get_metrics() -> 'Metrics':
    """
    Get the global metrics instance.
    
    Returns:
        Metrics instance
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = Metrics()
    return _metrics_instance

class Metrics:
    """
    Simple metrics collection class.
    
    This class provides basic methods for tracking counters, gauges, histograms,
    and timers. In a production environment, this would be replaced with a more
    robust metrics system like Prometheus or StatsD.
    """
    
    def __init__(self):
        """Initialize the metrics collection."""
        self._counters = {}
        self._gauges = {}
        self._histograms = {}
        self._counter_descriptions = {}
        self._gauge_descriptions = {}
        self._histogram_descriptions = {}
        
        logger.info("Metrics collection initialized")
    
    def register_counter(self, name: str, description: str) -> None:
        """
        Register a counter metric.
        
        Args:
            name: Name of the counter
            description: Description of what the counter tracks
        """
        if name not in self._counters:
            self._counters[name] = 0
            self._counter_descriptions[name] = description
    
    def register_gauge(self, name: str, description: str) -> None:
        """
        Register a gauge metric.
        
        Args:
            name: Name of the gauge
            description: Description of what the gauge tracks
        """
        if name not in self._gauges:
            self._gauges[name] = 0
            self._gauge_descriptions[name] = description
    
    def register_histogram(self, name: str, description: str) -> None:
        """
        Register a histogram metric.
        
        Args:
            name: Name of the histogram
            description: Description of what the histogram tracks
        """
        if name not in self._histograms:
            self._histograms[name] = []
            self._histogram_descriptions[name] = description
    
    def increment(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter.
        
        Args:
            name: Name of the counter
            value: Value to increment by
            labels: Optional labels for the metric
        """
        if name not in self._counters:
            self.register_counter(name, "Auto-registered counter")
        
        self._counters[name] += value
        
        if labels:
            label_str = ", ".join(f"{k}={v}" for k, v in labels.items())
            logger.debug(f"Incremented counter {name} by {value}", labels=label_str)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Set a gauge value.
        
        Args:
            name: Name of the gauge
            value: Value to set
            labels: Optional labels for the metric
        """
        if name not in self._gauges:
            self.register_gauge(name, "Auto-registered gauge")
        
        self._gauges[name] = value
        
        if labels:
            label_str = ", ".join(f"{k}={v}" for k, v in labels.items())
            logger.debug(f"Set gauge {name} to {value}", labels=label_str)
    
    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Observe a value for a histogram.
        
        Args:
            name: Name of the histogram
            value: Value to observe
            labels: Optional labels for the metric
        """
        if name not in self._histograms:
            self.register_histogram(name, "Auto-registered histogram")
        
        self._histograms[name].append(value)
        
        if labels:
            label_str = ", ".join(f"{k}={v}" for k, v in labels.items())
            logger.debug(f"Observed {value} for histogram {name}", labels=label_str)
    
    def start_timer(self, name: str) -> float:
        """
        Start a timer.
        
        Args:
            name: Name of the timer
            
        Returns:
            Start time in seconds
        """
        return time.time()
    
    def stop_timer(self, name: str, start_time: float, labels: Optional[Dict[str, str]] = None) -> float:
        """
        Stop a timer and record the duration.
        
        Args:
            name: Name of the timer
            start_time: Start time from start_timer
            labels: Optional labels for the metric
            
        Returns:
            Duration in seconds
        """
        duration = time.time() - start_time
        self.observe(name, duration, labels)
        return duration
    
    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all metrics as a dictionary.
        
        Returns:
            Dictionary of all metrics
        """
        metrics = {
            "counters": {name: {"value": value, "description": self._counter_descriptions.get(name, "")} 
                         for name, value in self._counters.items()},
            "gauges": {name: {"value": value, "description": self._gauge_descriptions.get(name, "")} 
                      for name, value in self._gauges.items()},
            "histograms": {name: {"values": values, "description": self._histogram_descriptions.get(name, "")} 
                          for name, values in self._histograms.items()}
        }
        return metrics 