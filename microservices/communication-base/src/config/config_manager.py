"""Compatibility shim.
This module provides `ConfigManager` under the import path `src.config.config_manager`
so legacy code continues to work. It simply re-exports the class from
`configuration_manager.py`.
"""

from src.config.configuration_manager import ConfigManager  # noqa: F401
