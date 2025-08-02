"""Service factory for creating service implementations."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Type, TypeVar, Generic, Optional, Set, List, Callable

from ..config.config_manager import ConfigManager

T = TypeVar('T')


class ServiceFactory(Generic[T], ABC):
    """Abstract service factory for creating service implementations."""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize service factory.
        
        Args:
            config_manager: Configuration manager
        """
        self.config = config_manager
        self._implementations: Dict[str, Type[T]] = {}
    
    def register_implementation(self, name: str, implementation_class: Type[T]) -> None:
        """
        Register a service implementation.
        
        Args:
            name: Implementation name
            implementation_class: Implementation class
        """
        self._implementations[name] = implementation_class
    
    def get_implementation_types(self) -> Set[str]:
        """
        Get available implementation types.
        
        Returns:
            Set of implementation names
        """
        return set(self._implementations.keys())
    
    def create(
        self,
        implementation_type: Optional[str] = None,
        **kwargs
    ) -> T:
        """
        Create a service implementation.
        
        Args:
            implementation_type: Optional implementation type, defaults to config value
            **kwargs: Additional constructor arguments
            
        Returns:
            Service implementation
            
        Raises:
            ValueError: If implementation type is not registered
        """
        impl_type = implementation_type or self._get_default_implementation_type()
        
        if impl_type not in self._implementations:
            registered_types = ", ".join(self._implementations.keys())
            raise ValueError(
                f"Unknown implementation type: {impl_type}. "
                f"Registered types: {registered_types}"
            )
        
        implementation_class = self._implementations[impl_type]
        return self._create_implementation(implementation_class, **kwargs)
    
    @abstractmethod
    def _get_default_implementation_type(self) -> str:
        """
        Get the default implementation type from configuration.
        
        Returns:
            Default implementation type
        """
        pass
    
    @abstractmethod
    def _create_implementation(self, implementation_class: Type[T], **kwargs) -> T:
        """
        Create a service implementation.
        
        Args:
            implementation_class: Implementation class
            **kwargs: Additional constructor arguments
            
        Returns:
            Service implementation
        """
        pass


class ServiceFactoryRegistry:
    """Registry for service factories."""
    
    def __init__(self):
        """Initialize service factory registry."""
        self._factories: Dict[Type, ServiceFactory] = {}
    
    def register_factory(self, service_type: Type, factory: ServiceFactory) -> None:
        """
        Register a service factory.
        
        Args:
            service_type: Service interface type
            factory: Service factory
        """
        self._factories[service_type] = factory
    
    def get_factory(self, service_type: Type[T]) -> ServiceFactory[T]:
        """
        Get a service factory.
        
        Args:
            service_type: Service interface type
            
        Returns:
            Service factory
            
        Raises:
            KeyError: If factory is not registered
        """
        if service_type not in self._factories:
            raise KeyError(f"Factory not registered for type: {service_type.__name__}")
        
        return self._factories[service_type]
    
    def has_factory(self, service_type: Type) -> bool:
        """
        Check if a factory is registered.
        
        Args:
            service_type: Service interface type
            
        Returns:
            True if factory is registered, False otherwise
        """
        return service_type in self._factories


# Global factory registry
registry = ServiceFactoryRegistry()


def register_factory(service_type: Type, factory: ServiceFactory) -> None:
    """
    Register a service factory.
    
    Args:
        service_type: Service interface type
        factory: Service factory
    """
    registry.register_factory(service_type, factory)


def create_service(
    service_type: Type[T],
    implementation_type: Optional[str] = None,
    **kwargs
) -> T:
    """
    Create a service implementation.
    
    Args:
        service_type: Service interface type
        implementation_type: Optional implementation type
        **kwargs: Additional constructor arguments
        
    Returns:
        Service implementation
    """
    factory = registry.get_factory(service_type)
    return factory.create(implementation_type, **kwargs)


def register_factories(config_manager: ConfigManager) -> None:
    """
    Register all service factories.
    
    Args:
        config_manager: Configuration manager
    """
    # Import factories here to avoid circular imports
    # Example: (these would be implemented in their respective files)
    # from .factories.analytics_factory import AnalyticsServiceFactory
    # from .factories.cache_factory import CacheServiceFactory
    # etc.
    
    # Then register them with the registry
    # Example:
    # register_factory(IAnalyticsService, AnalyticsServiceFactory(config_manager))
    # register_factory(ICacheService, CacheServiceFactory(config_manager))
    # etc.
    
    # This function would be called during application startup 