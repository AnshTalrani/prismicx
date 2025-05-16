"""
Component registry for the analysis-base microservice.

This module provides a registry for component classes, allowing components
to be dynamically loaded and instantiated based on string identifiers or
specifications. It supports versioning and configuration management.
"""
import importlib
import logging
from typing import Any, Dict, List, Optional, Type, Union, cast

from src.processing.components.base import BaseComponent
from src.processing.components.contracts.base_contracts import ComponentContract


class ComponentRegistry:
    """
    Registry for component classes.
    
    This class maintains a registry of component classes and provides
    methods to register, retrieve, and instantiate components based on
    identifiers or specifications.
    
    Attributes:
        logger (logging.Logger): Logger for the registry
        components (Dict[str, Dict[str, Type[BaseComponent]]]): Registry of component classes,
            organized by component type and name
    """
    
    def __init__(self):
        """Initialize the component registry."""
        self.logger = logging.getLogger(__name__)
        self.components: Dict[str, Dict[str, Type[BaseComponent]]] = {
            "collector": {},
            "transformer": {},
            "feature_extractor": {},
            "analyzer": {},
            "predictor": {},
            "recommender": {},
        }
    
    def register_component(
        self, 
        component_type: str, 
        name: str, 
        component_class: Type[BaseComponent],
        version: str = "latest"
    ) -> None:
        """
        Register a component class.
        
        Args:
            component_type: Type of the component (e.g., "collector", "analyzer")
            name: Name of the component
            component_class: Component class to register
            version: Version of the component (default: "latest")
            
        Raises:
            ValueError: If the component type is invalid
        """
        if component_type not in self.components:
            raise ValueError(f"Invalid component type: {component_type}")
        
        # Register the component
        if name not in self.components[component_type]:
            self.components[component_type][name] = {}
        
        self.components[component_type][name][version] = component_class
        self.logger.info(
            f"Registered component: {component_type}.{name} (version: {version})"
        )
    
    def get_component_class(
        self, 
        component_type: str, 
        name: str,
        version: str = "latest"
    ) -> Type[BaseComponent]:
        """
        Get a component class by type, name, and version.
        
        Args:
            component_type: Type of the component
            name: Name of the component
            version: Version of the component (default: "latest")
            
        Returns:
            Type[BaseComponent]: The component class
            
        Raises:
            ValueError: If the component is not found
        """
        if (
            component_type not in self.components
            or name not in self.components[component_type]
            or version not in self.components[component_type][name]
        ):
            raise ValueError(
                f"Component not found: {component_type}.{name} (version: {version})"
            )
        
        return self.components[component_type][name][version]
    
    def create_component(
        self, 
        component_type: str, 
        name: str,
        configuration: Optional[Dict[str, Any]] = None,
        version: str = "latest",
        component_id: Optional[str] = None
    ) -> BaseComponent:
        """
        Create a component instance.
        
        Args:
            component_type: Type of the component
            name: Name of the component
            configuration: Component configuration
            version: Version of the component (default: "latest")
            component_id: Unique identifier for the component
            
        Returns:
            BaseComponent: The component instance
        """
        component_class = self.get_component_class(component_type, name, version)
        return component_class(component_id=component_id, configuration=configuration)
    
    def create_component_from_spec(self, spec: Dict[str, Any]) -> BaseComponent:
        """
        Create a component instance from a specification.
        
        Args:
            spec: Component specification
            
        Returns:
            BaseComponent: The component instance
            
        Raises:
            ValueError: If the specification is invalid
        """
        # Extract component details from specification
        component_type = spec.get("type")
        name = spec.get("name")
        version = spec.get("version", "latest")
        configuration = spec.get("configuration", {})
        component_id = spec.get("id")
        
        # Validate specification
        if not component_type or not name:
            raise ValueError(
                "Invalid component specification: "
                "missing required fields 'type' and/or 'name'"
            )
        
        # Create and return the component
        return self.create_component(
            component_type, name, configuration, version, component_id
        )
    
    def load_components_from_module(self, module_path: str) -> None:
        """
        Load and register component classes from a module.
        
        Args:
            module_path: Path to the module
            
        Raises:
            ImportError: If the module cannot be imported
        """
        try:
            module = importlib.import_module(module_path)
            
            # Find all BaseComponent subclasses in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # Check if it's a BaseComponent subclass (but not BaseComponent itself)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseComponent)
                    and attr is not BaseComponent
                ):
                    # Determine component type based on implemented contracts
                    component_type = self._determine_component_type(attr)
                    
                    if component_type:
                        # Extract name from class name (e.g., DataCollectorComponent -> DataCollector)
                        name = attr.__name__
                        if name.endswith("Component"):
                            name = name[:-9]
                        
                        # Register the component
                        self.register_component(component_type, name, attr)
            
            self.logger.info(f"Loaded components from module: {module_path}")
            
        except ImportError as e:
            self.logger.error(f"Failed to import module {module_path}: {e}")
            raise
    
    def _determine_component_type(self, component_class: Type[BaseComponent]) -> Optional[str]:
        """
        Determine the type of a component class based on implemented contracts.
        
        Args:
            component_class: The component class
            
        Returns:
            Optional[str]: The component type, or None if not determined
        """
        # Check for each contract type
        from src.processing.components.contracts.base_contracts import (
            CollectorContract,
            TransformerContract,
            FeatureExtractorContract,
            AnalyzerContract,
            PredictorContract,
            RecommenderContract,
        )
        
        if issubclass(component_class, CollectorContract):
            return "collector"
        elif issubclass(component_class, TransformerContract):
            return "transformer"
        elif issubclass(component_class, FeatureExtractorContract):
            return "feature_extractor"
        elif issubclass(component_class, AnalyzerContract):
            return "analyzer"
        elif issubclass(component_class, PredictorContract):
            return "predictor"
        elif issubclass(component_class, RecommenderContract):
            return "recommender"
        
        return None


# Create a singleton instance
registry = ComponentRegistry()

def get_registry() -> ComponentRegistry:
    """
    Get the component registry instance.
    
    Returns:
        ComponentRegistry: The component registry instance
    """
    return registry 