"""
Configuration module for the Communication Base Microservice.

This module provides configuration management, validation, and integration
for the communication base microservice. It includes components for loading
and accessing bot-specific configurations.
"""

from src.config.bot_config_manager import ConfigManager
from src.config.config_integration import ConfigIntegration, config_integration
from src.config.bot_configs import get_bot_config, initialize_config_system

__all__ = [
    'ConfigManager',
    'ConfigIntegration',
    'config_integration',
    'get_bot_config',
    'initialize_config_system'
] 