"""
Pipeline module for the analysis-base microservice.

This module provides classes for creating and executing pipelines of
processing components. Pipelines define a sequence of processing steps
to be applied to data.
"""
import logging
from typing import Any, Dict, List, Optional, Union

from src.processing.components.base import BaseComponent
from src.processing.component_registry import get_registry


class Pipeline:
    """
    A pipeline of processing components.
    
    A pipeline represents a sequence of processing steps to be applied
    to data. Each step is a component that processes the data and
    produces output for the next component in the pipeline.
    
    Attributes:
        pipeline_id (str): Unique identifier for the pipeline
        name (str): Human-readable name for the pipeline
        description (str): Description of the pipeline's purpose
        components (List[BaseComponent]): List of component instances in the pipeline
        logger (logging.Logger): Logger for the pipeline
    """
    
    def __init__(
        self, 
        pipeline_id: str,
        name: str,
        description: str = "",
        components: Optional[List[BaseComponent]] = None
    ):
        """
        Initialize a pipeline.
        
        Args:
            pipeline_id: Unique identifier for the pipeline
            name: Human-readable name for the pipeline
            description: Description of the pipeline's purpose
            components: List of component instances in the pipeline
        """
        self.pipeline_id = pipeline_id
        self.name = name
        self.description = description
        self.components = components or []
        self.logger = logging.getLogger(f"pipeline.{pipeline_id}")
    
    def add_component(self, component: BaseComponent) -> None:
        """
        Add a component to the pipeline.
        
        Args:
            component: Component to add
        """
        self.components.append(component)
        self.logger.debug(f"Added component {component.__class__.__name__} to pipeline")
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data through the pipeline.
        
        Args:
            context: Context to process
            
        Returns:
            Dict[str, Any]: Processed context
            
        Raises:
            Exception: If any component processing fails
        """
        processed_context = context.copy()
        
        # Add pipeline metadata to context
        processed_context.setdefault("_metadata", {}).setdefault("pipeline", {})
        processed_context["_metadata"]["pipeline"]["id"] = self.pipeline_id
        processed_context["_metadata"]["pipeline"]["name"] = self.name
        
        # Process through each component
        for i, component in enumerate(self.components):
            try:
                # Log start of component processing
                self.logger.debug(
                    f"Processing component {i+1}/{len(self.components)}: "
                    f"{component.__class__.__name__}"
                )
                
                # Process context through component
                processed_context = await component.process(processed_context)
                
                # Validate that component returned a context
                if processed_context is None:
                    raise ValueError(
                        f"Component {component.__class__.__name__} returned None"
                    )
                
                # Add component processing metadata
                processed_context.setdefault("_metadata", {}).setdefault("components", []).append({
                    "component_id": getattr(component, "component_id", str(i)),
                    "component_type": component.__class__.__name__,
                    "order": i
                })
                
            except Exception as e:
                # Log error and reraise
                self.logger.error(
                    f"Error in component {component.__class__.__name__}: {str(e)}"
                )
                raise
        
        return processed_context


class PipelineFactory:
    """
    Factory for creating pipelines from specifications.
    
    This class provides methods to create pipelines based on
    configuration or specifications.
    """
    
    def __init__(self):
        """Initialize the pipeline factory."""
        self.logger = logging.getLogger("pipeline_factory")
        self.registry = get_registry()
    
    def create_pipeline_from_spec(self, spec: Dict[str, Any]) -> Pipeline:
        """
        Create a pipeline from a specification.
        
        Args:
            spec: Pipeline specification
            
        Returns:
            Pipeline: The created pipeline
            
        Raises:
            ValueError: If the specification is invalid
        """
        # Extract pipeline details
        pipeline_id = spec.get("id")
        name = spec.get("name")
        description = spec.get("description", "")
        components_spec = spec.get("components", [])
        
        # Validate pipeline spec
        if not pipeline_id or not name:
            raise ValueError(
                "Invalid pipeline specification: missing required fields 'id' and/or 'name'"
            )
        
        # Create pipeline
        pipeline = Pipeline(pipeline_id, name, description)
        
        # Add components
        for component_spec in components_spec:
            component = self.registry.create_component_from_spec(component_spec)
            pipeline.add_component(component)
        
        self.logger.info(
            f"Created pipeline {name} (id: {pipeline_id}) with {len(pipeline.components)} components"
        )
        
        return pipeline
    
    def create_pipeline_for_analysis_type(
        self, 
        analysis_type: str,
        configuration: Optional[Dict[str, Any]] = None
    ) -> Pipeline:
        """
        Create a pipeline for a specific analysis type.
        
        Args:
            analysis_type: Type of analysis (e.g., "descriptive", "diagnostic")
            configuration: Configuration for the pipeline
            
        Returns:
            Pipeline: The created pipeline
            
        Raises:
            ValueError: If the analysis type is not supported
        """
        # This is a placeholder implementation. In a real implementation,
        # this would load pipeline specifications based on the analysis type.
        
        if analysis_type == "descriptive":
            return self._create_descriptive_pipeline(configuration)
        elif analysis_type == "diagnostic":
            return self._create_diagnostic_pipeline(configuration)
        elif analysis_type == "predictive":
            return self._create_predictive_pipeline(configuration)
        elif analysis_type == "prescriptive":
            return self._create_prescriptive_pipeline(configuration)
        else:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")
    
    def _create_descriptive_pipeline(self, configuration: Optional[Dict[str, Any]] = None) -> Pipeline:
        """
        Create a descriptive analysis pipeline.
        
        Args:
            configuration: Configuration for the pipeline
            
        Returns:
            Pipeline: The created pipeline
        """
        # This is a placeholder implementation. In a real implementation,
        # this would create a pipeline with components for descriptive analysis.
        
        pipeline = Pipeline(
            pipeline_id="descriptive",
            name="Descriptive Analysis Pipeline",
            description="Pipeline for descriptive analysis"
        )
        
        # In a real implementation, we would add components to the pipeline here
        
        return pipeline
    
    def _create_diagnostic_pipeline(self, configuration: Optional[Dict[str, Any]] = None) -> Pipeline:
        """
        Create a diagnostic analysis pipeline.
        
        Args:
            configuration: Configuration for the pipeline
            
        Returns:
            Pipeline: The created pipeline
        """
        # This is a placeholder implementation. In a real implementation,
        # this would create a pipeline with components for diagnostic analysis.
        
        pipeline = Pipeline(
            pipeline_id="diagnostic",
            name="Diagnostic Analysis Pipeline",
            description="Pipeline for diagnostic analysis"
        )
        
        # In a real implementation, we would add components to the pipeline here
        
        return pipeline
    
    def _create_predictive_pipeline(self, configuration: Optional[Dict[str, Any]] = None) -> Pipeline:
        """
        Create a predictive analysis pipeline.
        
        Args:
            configuration: Configuration for the pipeline
            
        Returns:
            Pipeline: The created pipeline
        """
        # This is a placeholder implementation. In a real implementation,
        # this would create a pipeline with components for predictive analysis.
        
        pipeline = Pipeline(
            pipeline_id="predictive",
            name="Predictive Analysis Pipeline",
            description="Pipeline for predictive analysis"
        )
        
        # In a real implementation, we would add components to the pipeline here
        
        return pipeline
    
    def _create_prescriptive_pipeline(self, configuration: Optional[Dict[str, Any]] = None) -> Pipeline:
        """
        Create a prescriptive analysis pipeline.
        
        Args:
            configuration: Configuration for the pipeline
            
        Returns:
            Pipeline: The created pipeline
        """
        # This is a placeholder implementation. In a real implementation,
        # this would create a pipeline with components for prescriptive analysis.
        
        pipeline = Pipeline(
            pipeline_id="prescriptive",
            name="Prescriptive Analysis Pipeline",
            description="Pipeline for prescriptive analysis"
        )
        
        # In a real implementation, we would add components to the pipeline here
            
            return pipeline