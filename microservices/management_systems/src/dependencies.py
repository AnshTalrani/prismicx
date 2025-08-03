"""
Dependency injection module for the Management Systems microservice.
"""

from functools import lru_cache
from .services.management_service import management_service
from .plugins.manager import PluginManager
from .cache.redis_cache import cache
from .config.settings import get_settings


@lru_cache()
def get_management_service():
    """Get the management service instance."""
    return management_service


@lru_cache()
def get_plugin_manager():
    """Get the plugin manager instance."""
    settings = get_settings()
    return PluginManager(settings)


def get_cache_dependency():
    """Get the cache dependency."""
    return cache


def get_settings_dependency():
    """Get the settings dependency."""
    return get_settings()
