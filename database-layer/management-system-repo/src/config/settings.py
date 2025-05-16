"""
Configuration settings for the Management System Repository Service.

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
    service_name: str = Field("management-system-repo", env="SERVICE_NAME")
    service_version: str = "1.0.0"
    
    # Server Settings
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8080, env="PORT")
    debug: bool = Field(False, env="DEBUG")
    reload: bool = Field(False, env="RELOAD")
    
    # Database Settings
    db_host: str = Field("postgres", env="SYSTEM_DB_HOST")
    db_port: int = Field(5432, env="SYSTEM_DB_PORT")
    db_user: str = Field("postgres", env="SYSTEM_DB_USER")
    db_password: str = Field("password", env="SYSTEM_DB_PASSWORD")
    db_name: str = Field("management_system_repository", env="SYSTEM_DB_NAME")
    db_min_pool_size: int = Field(5, env="DB_MIN_POOL_SIZE")
    db_max_pool_size: int = Field(20, env="DB_MAX_POOL_SIZE")
    
    # Security Settings
    api_key: str = Field("dev_api_key", env="API_KEY")
    allow_cors_origins: list = Field(default_factory=lambda: ["*"])
    jwt_secret: str = Field("dev_secret_key", env="JWT_SECRET")
    
    # Integration Settings
    tenant_service_url: str = Field(
        "http://tenant-mgmt-service:8000", 
        env="TENANT_SERVICE_URL"
    )
    user_service_url: str = Field(
        "http://user-data-service:8000", 
        env="USER_SERVICE_URL"
    )
    task_service_url: str = Field(
        "http://task-repo-service:8000", 
        env="TASK_SERVICE_URL"
    )
    
    # Performance Settings
    cache_ttl: int = Field(300, env="CACHE_TTL")  # 5 minutes
    
    # Add MongoDB configuration
    mongodb_host: str = Field("mongodb-system", env="CONFIG_DB_HOST")
    mongodb_port: int = Field(27017, env="CONFIG_DB_PORT")
    mongodb_user: str = Field("admin", env="CONFIG_DB_USER")
    mongodb_password: str = Field("password", env="CONFIG_DB_PASSWORD")
    mongodb_db: str = Field("config_db", env="CONFIG_DB_NAME")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Service configuration settings
    """
    logger.info("Loading service configuration settings")
    return Settings() 