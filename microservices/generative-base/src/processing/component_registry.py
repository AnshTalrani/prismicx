"""
Component Registry Module

This module provides a registry for component classes that can be dynamically
loaded and instantiated by name, with support for YAML configuration.
"""

import importlib
import inspect
from typing import Dict, Type, Any, Optional, Callable, Set, List
import structlog
from copy import deepcopy

# Import the configuration loader
from ..common.config_loader import ConfigurationLoader
from ..common.template_renderer import TemplateRenderer

logger = structlog.get_logger(__name__)


class ComponentRegistry:
    """
    Registry for component classes.
    
    This registry maintains a mapping of component names to their classes,
    allowing components to be dynamically loaded and instantiated by name.
    
    It supports automatic discovery and registration of components from
    specified module paths, as well as manual registration and YAML configuration.
    """
    
    def __init__(self, config_loader: Optional[ConfigurationLoader] = None):
        """
        Initialize the component registry.
        
        Args:
            config_loader: Optional configuration loader for YAML configs
        """
        self.components: Dict[str, Type] = {}
        self.config_loader = config_loader
        self.component_configs: Dict[str, Dict[str, Any]] = {}
        self.template_renderer = TemplateRenderer()
        logger.debug("Component registry initialized")
    
    def register(self, name: str, component_class: Type) -> None:
        """
        Register a component class.
        
        Args:
            name: Name under which to register the component
            component_class: The component class to register
        """
        if name in self.components:
            logger.warning("Overriding existing component", name=name)
            
        self.components[name] = component_class
        logger.debug("Component registered", name=name, class_name=component_class.__name__)
    
    def unregister(self, name: str) -> None:
        """
        Unregister a component.
        
        Args:
            name: Name of the component to unregister
        """
        if name in self.components:
            del self.components[name]
            logger.debug("Component unregistered", name=name)
    
    def get(self, name: str) -> Optional[Type]:
        """
        Get a component class by name.
        
        Args:
            name: Name of the component
            
        Returns:
            The component class or None if not found
        """
        component = self.components.get(name)
        
        if component is None:
            logger.warning("Component not found", name=name)
            
        return component
    
    def create(self, name: str, *args, **kwargs) -> Any:
        """
        Create an instance of a component.
        
        Args:
            name: Name of the component
            *args: Positional arguments to pass to the constructor
            **kwargs: Keyword arguments to pass to the constructor
            
        Returns:
            An instance of the component
            
        Raises:
            ValueError: If the component is not found
        """
        component_class = self.get(name)
        
        if component_class is None:
            raise ValueError(f"Component not found: {name}")
        
        try:
            # Apply configuration from YAML if available
            config_kwargs = kwargs.copy()
            if self.config_loader and name in self.component_configs:
                yaml_config = self.component_configs[name].get('config', {})
                # Merge YAML config with provided kwargs (kwargs take precedence)
                for key, value in yaml_config.items():
                    if key not in config_kwargs:
                        config_kwargs[key] = value
            
            # Create the component instance
            instance = component_class(*args, **config_kwargs)
            
            # Apply prompt templates if component has them
            if hasattr(instance, 'set_prompt_templates') and self.component_configs.get(name):
                prompts = self.component_configs[name].get('prompts', {})
                if prompts:
                    instance.set_prompt_templates(prompts)
            
            return instance
            
        except Exception as e:
            logger.error(
                "Failed to create component instance",
                name=name,
                error=str(e),
                exc_info=True
            )
            raise
    
    def create_from_config(self, module_id: str, template_id: Optional[str] = None,
                           context: Optional[Dict[str, Any]] = None,
                           override_config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a component instance from its YAML configuration.
        
        Args:
            module_id: ID of the module to create
            template_id: Optional template ID for template-specific configs
            context: Optional context for dynamic configuration
            override_config: Optional configuration overrides
            
        Returns:
            Configured component instance
            
        Raises:
            ValueError: If the module or template is not found
        """
        if not self.config_loader:
            raise ValueError("Config loader is required for creating components from config")
        
        # Get the module configuration
        module_config = self.config_loader.get_module_config(module_id)
        if not module_config:
            raise ValueError(f"Module configuration not found: {module_id}")
        
        # Determine the component class to use
        component_type = module_config.get('type', module_id)
        component_class = self.get(component_type)
        if not component_class:
            raise ValueError(f"Component class not found for module: {module_id} (type: {component_type})")
        
        # Build the configuration
        config = deepcopy(module_config.get('config', {}))
        
        # Apply template-specific overrides if available
        if template_id and 'templates' in module_config:
            template_config = module_config['templates'].get(template_id, {})
            self._deep_merge(config, template_config)
        
        # Apply manual overrides if provided
        if override_config:
            self._deep_merge(config, override_config)
        
        # Create the instance
        instance = component_class(name=module_id, config=config)
        
        # Set prompt templates if available
        if hasattr(instance, 'set_prompt_templates') and 'prompts' in module_config:
            prompts = module_config.get('prompts', {})
            instance.set_prompt_templates(prompts)
        
        return instance
    
    def register_from_module(self, module_path: str, base_class: Optional[Type] = None, suffix: str = "") -> Set[str]:
        """
        Register components from a module.
        
        Args:
            module_path: Path to the module
            base_class: Base class that components must inherit from
            suffix: Suffix that component class names must have
            
        Returns:
            Set of registered component names
        """
        try:
            module = importlib.import_module(module_path)
            registered = set()
            
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Skip if not derived from base_class (if specified)
                if base_class and not issubclass(obj, base_class):
                    continue
                    
                # Skip if doesn't have the required suffix
                if suffix and not name.endswith(suffix):
                    continue
                    
                # Skip if it's imported from another module
                if obj.__module__ != module_path:
                    continue
                
                # Register with name without suffix if present
                component_name = name
                if suffix and name.endswith(suffix):
                    component_name = name[:-len(suffix)]
                
                self.register(component_name, obj)
                registered.add(component_name)
            
            logger.info(
                "Registered components from module",
                module=module_path,
                count=len(registered)
            )
            
            return registered
            
        except ImportError as e:
            logger.error(
                "Failed to import module for component registration",
                module=module_path,
                error=str(e)
            )
            return set()
    
    def register_from_modules(self, module_paths: List[str], base_class: Optional[Type] = None, suffix: str = "") -> int:
        """
        Register components from multiple modules.
        
        Args:
            module_paths: List of paths to modules
            base_class: Base class that components must inherit from
            suffix: Suffix that component class names must have
            
        Returns:
            Number of registered components
        """
        total_registered = 0
        
        for module_path in module_paths:
            registered = self.register_from_module(module_path, base_class, suffix)
            total_registered += len(registered)
        
        return total_registered
    
    def load_component_configs(self) -> int:
        """
        Load component configurations from the config loader.
        
        Returns:
            Number of component configurations loaded
        """
        if not self.config_loader:
            logger.warning("Config loader not available, skipping component configuration loading")
            return 0
        
        count = 0
        for module_info in self.config_loader.get_enabled_modules():
            module_id = module_info.get('id')
            if not module_id:
                continue
                
            # Load the module configuration
            module_config = self.config_loader.get_module_config(module_id)
            if module_config:
                self.component_configs[module_id] = module_config
                count += 1
                logger.info(f"Loaded configuration for component: {module_id}")
        
        return count
    
    def list_components(self) -> List[str]:
        """
        List all registered component names.
        
        Returns:
            List of component names
        """
        return list(self.components.keys())
    
    def _deep_merge(self, target: Dict, source: Dict) -> None:
        """
        Deep merge source dict into target dict.
        
        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value 