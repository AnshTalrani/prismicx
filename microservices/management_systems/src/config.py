"""
Configuration settings for the Management Systems microservice.

This module provides configuration settings for the service, loaded from
environment variables with sensible defaults.
"""

import os
from typing import List, Dict, Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings."""
    
    # Service Info
    app_name: str = "management-systems"
    app_version: str = "1.0.0"
    
    # Server Settings
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    debug: bool = Field(False, env="DEBUG")
    reload: bool = Field(False, env="RELOAD")
    
    # Security Settings
    api_key: str = Field("dev_api_key", env="API_KEY")
    jwt_secret: str = Field("dev_secret_key", env="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS Settings
    cors_origins: List[str] = Field(["*"], env="CORS_ORIGINS")
    
    # Database Layer Service URLs
    management_system_repo_url: str = Field(
        "http://management-system-repo:8080", 
        env="MANAGEMENT_SYSTEM_REPO_URL"
    )
    management_system_repo_api_key: str = Field(
        "dev_api_key", 
        env="MANAGEMENT_SYSTEM_REPO_API_KEY"
    )
    tenant_mgmt_service_url: str = Field(
        "http://tenant-mgmt-service:8000", 
        env="TENANT_MGMT_SERVICE_URL"
    )
    tenant_mgmt_service_api_key: str = Field(
        "dev_api_key", 
        env="TENANT_MGMT_SERVICE_API_KEY"
    )
    user_data_service_url: str = Field(
        "http://user-data-service:8000", 
        env="USER_DATA_SERVICE_URL"
    )
    user_data_service_api_key: str = Field(
        "dev_api_key", 
        env="USER_DATA_SERVICE_API_KEY"
    )
    task_repo_service_url: str = Field(
        "http://task-repo-service:8000", 
        env="TASK_REPO_SERVICE_URL"
    )
    task_repo_service_api_key: str = Field(
        "dev_api_key", 
        env="TASK_REPO_SERVICE_API_KEY"
    )
    
    # Plugin Settings
    plugins_dir: str = Field("plugins", env="PLUGINS_DIR")
    active_plugins: List[str] = Field(["config_service"], env="ACTIVE_PLUGINS")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Create a global instance
settings = Settings()

def get_settings() -> Settings:
    """
    Get application settings.
    
    Returns:
        Application settings
    """
    return settings 