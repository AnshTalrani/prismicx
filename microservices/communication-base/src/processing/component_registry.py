"""
Component Registry Module

This module provides a registry for managing and accessing processing components.
The registry allows components to be registered, retrieved, and managed centrally.
"""

from typing import Dict, Any, Optional, List, Type
import structlog

from src.processing.base_component import BaseComponent

logger = structlog.get_logger(__name__)

class ComponentRegistry:
    """
    Registry for managing processing components.
    
    The ComponentRegistry provides a central place to register, retrieve, and
    manage components in the processing pipeline. It ensures components are
    properly tracked and accessible throughout the application.
    """
    
    def __init__(self):
        """
        Initialize the component registry.
        """
        self._components: Dict[str, BaseComponent] = {}
        logger.info("Component registry initialized")
    
    def register_component(self, component: BaseComponent) -> None:
        """
        Register a component in the registry.
        
        Args:
            component: The component to register
            
        Raises:
            ValueError: If a component with the same ID is already registered
        """
        component_id = component.component_id
        
        if component_id in self._components:
            raise ValueError(f"Component with ID '{component_id}' is already registered")
        
        self._components[component_id] = component
        logger.info(
            "Component registered", 
            component_id=component_id, 
            component_type=component.component_type
        )
    
    def get_component(self, component_id: str) -> Optional[BaseComponent]:
        """
        Get a component by ID.
        
        Args:
            component_id: ID of the component to retrieve
            
        Returns:
            The component if found, None otherwise
        """
        component = self._components.get(component_id)
        
        if not component:
            logger.warning("Component not found", component_id=component_id)
            
        return component
    
    def get_component_by_type(self, component_type: str) -> Optional[BaseComponent]:
        """
        Get the first component of a specific type.
        
        Args:
            component_type: Type of component to retrieve
            
        Returns:
            The first component of the specified type if found, None otherwise
        """
        for component in self._components.values():
            if component.component_type == component_type:
                return component
                
        logger.warning("No component found of type", component_type=component_type)
        return None
    
    def get_components_by_type(self, component_type: str) -> List[BaseComponent]:
        """
        Get all components of a specific type.
        
        Args:
            component_type: Type of components to retrieve
            
        Returns:
            List of components of the specified type
        """
        components = [
            component for component in self._components.values()
            if component.component_type == component_type
        ]
        
        return components
    
    def get_all_components(self) -> Dict[str, BaseComponent]:
        """
        Get all registered components.
        
        Returns:
            Dictionary of component IDs to components
        """
        return self._components.copy()
    
    def unregister_component(self, component_id: str) -> bool:
        """
        Unregister a component from the registry.
        
        Args:
            component_id: ID of the component to unregister
            
        Returns:
            True if the component was unregistered, False if not found
        """
        if component_id in self._components:
            self._components.pop(component_id)
            logger.info("Component unregistered", component_id=component_id)
            return True
            
        logger.warning(
            "Cannot unregister component, not found", 
            component_id=component_id
        )
        return False
    
    async def initialize_all(self) -> Dict[str, bool]:
        """
        Initialize all registered components.
        
        Returns:
            Dictionary mapping component IDs to initialization success status
        """
        results = {}
        
        for component_id, component in self._components.items():
            try:
                success = await component.initialize()
                results[component_id] = success
                
                if success:
                    logger.info("Component initialized", component_id=component_id)
                else:
                    logger.warning(
                        "Component initialization failed", 
                        component_id=component_id
                    )
                    
            except Exception as e:
                logger.error(
                    "Error initializing component", 
                    component_id=component_id, 
                    error=str(e)
                )
                results[component_id] = False
        
        return results
    
    async def shutdown_all(self) -> Dict[str, bool]:
        """
        Shutdown all registered components.
        
        Returns:
            Dictionary mapping component IDs to shutdown success status
        """
        results = {}
        
        for component_id, component in self._components.items():
            try:
                await component.shutdown()
                results[component_id] = True
                logger.info("Component shutdown", component_id=component_id)
                
            except Exception as e:
                logger.error(
                    "Error shutting down component", 
                    component_id=component_id, 
                    error=str(e)
                )
                results[component_id] = False
        
        return results
    
    def get_registry_info(self) -> Dict[str, Any]:
        """
        Get information about the registry and its components.
        
        Returns:
            Dictionary with registry information
        """
        components_info = {}
        for component_id, component in self._components.items():
            try:
                components_info[component_id] = {
                    "type": component.component_type,
                    "info": component.get_info()
                }
            except Exception as e:
                components_info[component_id] = {
                    "type": component.component_type,
                    "error": str(e)
                }
        
        return {
            "component_count": len(self._components),
            "components": components_info
        } 