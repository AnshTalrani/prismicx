"""
Configuration module for the Expert Base microservice.

This module loads configuration from environment variables and provides
a central place for accessing configuration settings.
"""

import os
from pydantic import BaseSettings
from typing import Optional, List, Dict, Any
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_KEY: str = "dev_expert_base_key"
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: Optional[str] = None
    
    # Vector DB Configuration
    VECTOR_DB_TYPE: str = "chroma"
    VECTOR_DB_HOST: str = "localhost"
    VECTOR_DB_PORT: int = 8000
    
    # Model Server Configuration
    MODEL_SERVER_URL: str = "http://localhost:8080"
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    
    # Redis Configuration
    REDIS_URL: Optional[str] = None
    
    # Paths
    CONFIG_PATH: str = os.path.join(os.path.dirname(__file__), "..", "..", "config")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()


def get_expert_config_path() -> str:
    """Get the path to the expert configuration files."""
    return os.path.join(settings.CONFIG_PATH, "experts") 