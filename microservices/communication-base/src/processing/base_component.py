"""
Base Component Module

This module provides the base class for all processing components used in the
communication processing pipeline. Components handle specific tasks like
data transformation, content generation, or campaign analytics.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
import structlog
from src.common.monitoring import Metrics

logger = structlog.get_logger(__name__)

class BaseComponent(ABC):
    """
    Base class for all processing components in the communication pipeline.
    
    Components are modular processing units that can be assembled into pipelines
    to perform complex processing tasks. Each component has a specific function
    (e.g., data transformation, content generation) and can be configured with
    parameters to customize its behavior.
    """
    
    def __init__(
        self, 
        component_id: str,
        component_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        metrics: Optional[Metrics] = None
    ):
        """
        Initialize the base component.
        
        Args:
            component_id: Unique identifier for this component instance
            component_type: Type of component (used for registry and metrics)
            parameters: Configuration parameters for the component
            metrics: Optional metrics collector
        """
        self.component_id = component_id
        self.component_type = component_type
        self.parameters = parameters or {}
        self.metrics = metrics
        
        # Component state
        self.is_initialized = False
        self.is_enabled = True
        
        logger.info(
            "Component created", 
            component_id=component_id, 
            component_type=component_type
        )
    
    @abstractmethod
    async def process(
        self, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process input data and return the processed result.
        
        This is the main method that must be implemented by all components.
        It takes input data and context, processes it according to the component's
        function, and returns a result.
        
        Args:
            input_data: The data to be processed
            context: Additional context information for processing
            
        Returns:
            Processed data as a dictionary
            
        Raises:
            NotImplementedError: If the component doesn't implement this method
        """
        raise NotImplementedError("Component must implement process method")
    
    async def initialize(self) -> bool:
        """
        Initialize the component with necessary resources.
        
        This method should be called before the component is used for processing.
        It can be overridden by derived classes to perform resource initialization,
        like loading models or connecting to external services.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        self.is_initialized = True
        return True
    
    async def shutdown(self) -> bool:
        """
        Release resources used by the component.
        
        This method should be called when the component is no longer needed.
        It can be overridden by derived classes to perform cleanup tasks like
        closing connections or releasing memory.
        
        Returns:
            True if shutdown was successful, False otherwise
        """
        self.is_initialized = False
        return True
    
    def validate_parameters(self) -> List[str]:
        """
        Validate component parameters.
        
        This method should be overridden by derived classes to validate
        the parameters provided during initialization.
        
        Returns:
            List of error messages (empty if all parameters are valid)
        """
        return []
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get component information.
        
        Returns:
            Dictionary with component information
        """
        return {
            "component_id": self.component_id,
            "component_type": self.component_type,
            "parameters": self.parameters,
            "is_initialized": self.is_initialized,
            "is_enabled": self.is_enabled
        }
    
    def _track_metric(
        self, 
        name: str, 
        value: Union[float, int], 
        metric_type: str = "counter",
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Track a metric using the metrics collector.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric (counter, gauge, histogram)
            labels: Optional labels for the metric
        """
        if not self.metrics:
            return
            
        default_labels = {
            "component_id": self.component_id,
            "component_type": self.component_type
        }
        
        # Merge default labels with provided labels
        merged_labels = {**default_labels, **(labels or {})}
        
        # Track the metric based on type
        if metric_type == "counter":
            self.metrics.increment(name, value, merged_labels)
        elif metric_type == "gauge":
            self.metrics.gauge(name, value, merged_labels)
        elif metric_type == "histogram":
            self.metrics.observe(name, value, merged_labels)
        else:
            logger.warning(
                "Unknown metric type", 
                metric_type=metric_type, 
                name=name
            ) 