"""
Settings module for the management systems API.
"""
import os
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings."""
    # API settings
    api_title: str = "Management Systems API"
    api_description: str = "API for management systems and tenant instances"
    api_version: str = "1.0.0"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    
    # CORS settings
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    
    # Cache settings
    cache_ttl: int = 300  # 5 minutes
    
    # Database Layer Service URLs
    management_system_repo_url: str = Field(
        os.getenv("MANAGEMENT_SYSTEM_REPO_URL", "http://management-system-repo:8080"),
        env="MANAGEMENT_SYSTEM_REPO_URL"
    )
    management_system_repo_api_key: str = Field(
        os.getenv("MANAGEMENT_SYSTEM_REPO_API_KEY", "dev_api_key"),
        env="MANAGEMENT_SYSTEM_REPO_API_KEY"
    )
    tenant_mgmt_service_url: str = Field(
        os.getenv("TENANT_MGMT_SERVICE_URL", "http://tenant-mgmt-service:8000"),
        env="TENANT_MGMT_SERVICE_URL"
    )
    tenant_mgmt_service_api_key: str = Field(
        os.getenv("TENANT_MGMT_SERVICE_API_KEY", "dev_api_key"),
        env="TENANT_MGMT_SERVICE_API_KEY"
    )
    user_data_service_url: str = Field(
        os.getenv("USER_DATA_SERVICE_URL", "http://user-data-service:8000"),
        env="USER_DATA_SERVICE_URL"
    )
    user_data_service_api_key: str = Field(
        os.getenv("USER_DATA_SERVICE_API_KEY", "dev_api_key"),
        env="USER_DATA_SERVICE_API_KEY"
    )
    task_repo_service_url: str = Field(
        os.getenv("TASK_REPO_SERVICE_URL", "http://task-repo-service:8000"),
        env="TASK_REPO_SERVICE_URL"
    )
    task_repo_service_api_key: str = Field(
        os.getenv("TASK_REPO_SERVICE_API_KEY", "dev_api_key"),
        env="TASK_REPO_SERVICE_API_KEY"
    )
    
    # Redis settings
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    
    # Plugin settings
    plugins_enabled: bool = True
    plugins_watch: bool = True
    plugins_dir: str = "../plugins"
    
    @property
    def redis_url(self) -> str:
        """Get the Redis URL for the configured Redis instance."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings singleton."""
    return Settings() 