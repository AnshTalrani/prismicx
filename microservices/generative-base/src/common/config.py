"""
Configuration Module

This module provides configuration settings for the application.
Settings are loaded from environment variables with reasonable defaults.
"""

import os
from functools import lru_cache
from typing import Optional, Dict, Any, List

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """
    Application configuration settings.
    
    Attributes are loaded from environment variables with defaults.
    Environment variables should be prefixed with GENERATIVE_ and use
    uppercase with underscores (e.g., GENERATIVE_SERVICE_TYPE).
    """
    
    # Service identification
    service_type: str = Field("default", env="GENERATIVE_SERVICE_TYPE")
    service_name: str = Field("generative-base", env="GENERATIVE_SERVICE_NAME")
    
    # PostgreSQL settings
    postgres_uri: str = Field("postgresql://postgres:postgres@postgres-service:5432/generative", env="GENERATIVE_POSTGRES_URI")
    postgres_database: str = Field("generative", env="GENERATIVE_POSTGRES_DATABASE")
    
    # Task Repository settings
    task_repo_url: str = Field("http://task-repo-service:8000", env="GENERATIVE_TASK_REPO_URL")
    
    # Worker settings
    max_processing_attempts: int = Field(3, env="GENERATIVE_MAX_PROCESSING_ATTEMPTS")
    retry_delay: int = Field(60, env="GENERATIVE_RETRY_DELAY")  # seconds
    poll_interval: float = Field(1.0, env="GENERATIVE_POLL_INTERVAL")  # seconds
    
    # Batch processing settings
    batch_processing_enabled: bool = Field(True, env="GENERATIVE_BATCH_PROCESSING_ENABLED")
    batch_size: int = Field(10, env="GENERATIVE_BATCH_SIZE")
    batch_wait_time: int = Field(5, env="GENERATIVE_BATCH_WAIT_TIME")  # seconds
    
    # API settings
    host: str = Field("0.0.0.0", env="GENERATIVE_HOST")
    port: int = Field(8000, env="GENERATIVE_PORT")
    debug: bool = Field(False, env="GENERATIVE_DEBUG")
    
    # Logging settings
    log_level: str = Field("INFO", env="GENERATIVE_LOG_LEVEL")
    
    # Component-specific settings
    component_settings: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        """Initialize settings with component-specific configurations."""
        super().__init__(**kwargs)
        
        # Load component-specific settings from environment
        self._load_component_settings()
    
    def _load_component_settings(self):
        """
        Load component-specific settings from environment variables.
        
        Component settings are prefixed with GENERATIVE_COMPONENT_ followed
        by the component name in uppercase. For example:
        GENERATIVE_COMPONENT_TEMPLATE_CACHE_SIZE=100
        """
        component_prefix = "GENERATIVE_COMPONENT_"
        
        # Process all environment variables
        for key, value in os.environ.items():
            if key.startswith(component_prefix):
                # Extract component name and setting
                parts = key[len(component_prefix):].split("_", 1)
                if len(parts) == 2:
                    component_name = parts[0].lower()
                    setting_name = parts[1].lower()
                    
                    # Create component dictionary if it doesn't exist
                    if component_name not in self.component_settings:
                        self.component_settings[component_name] = {}
                    
                    # Convert value to appropriate type
                    if value.lower() in ("true", "yes", "1"):
                        typed_value = True
                    elif value.lower() in ("false", "no", "0"):
                        typed_value = False
                    elif value.isdigit():
                        typed_value = int(value)
                    elif value.replace(".", "", 1).isdigit():
                        typed_value = float(value)
                    else:
                        typed_value = value
                    
                    # Store setting
                    self.component_settings[component_name][setting_name] = typed_value


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings instance with configuration values
    """
    return Settings()