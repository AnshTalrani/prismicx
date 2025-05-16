"""
Configuration settings for the Task Repository Service.

This module provides configuration settings for the service, loaded from
environment variables or default values.
"""

import os
import logging
from functools import lru_cache
from pydantic import BaseSettings, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Service configuration settings."""
    
    # Service Info
    service_name: str = Field("task-repo-service", env="SERVICE_NAME")
    service_version: str = "1.0.0"
    
    # Server Settings
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8503, env="PORT")
    debug: bool = Field(False, env="DEBUG")
    reload: bool = Field(False, env="RELOAD")
    
    # MongoDB Settings
    mongodb_uri: str = Field(
        "mongodb://task_service:password@mongodb-system:27017/task_repository", 
        env="MONGODB_URI"
    )
    mongodb_database: str = Field("task_repository", env="MONGODB_DATABASE")
    mongodb_tasks_collection: str = Field("tasks", env="MONGODB_TASKS_COLLECTION")
    mongodb_min_pool_size: int = Field(5, env="MONGODB_MIN_POOL_SIZE")
    mongodb_max_pool_size: int = Field(20, env="MONGODB_MAX_POOL_SIZE")
    
    # Security Settings
    api_key: str = Field("dev_api_key", env="API_KEY")
    allow_cors_origins: list = Field(default_factory=lambda: ["*"])
    
    # Task Settings
    default_task_limit: int = Field(10, env="DEFAULT_TASK_LIMIT")
    task_cleanup_days: int = Field(30, env="TASK_CLEANUP_DAYS")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings instance
    """
    settings = Settings()
    logger.info(f"Loaded settings for {settings.service_name} v{settings.service_version}")
    return settings 