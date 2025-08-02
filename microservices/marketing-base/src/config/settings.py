"""
Configuration Module

This module provides configuration settings for the marketing-base microservice.
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
    Environment variables should be prefixed with MARKETING_ and use
    uppercase with underscores (e.g., MARKETING_SERVICE_TYPE).
    """
    
    # Service identification
    service_type: str = Field("marketing", env="MARKETING_SERVICE_TYPE")
    service_name: str = Field("marketing-base", env="MARKETING_SERVICE_NAME")
    
    # Server settings
    host: str = Field("0.0.0.0", env="MARKETING_HOST")
    port: int = Field(8000, env="MARKETING_PORT")
    log_level: str = Field("INFO", env="MARKETING_LOG_LEVEL")
    
    # MongoDB settings
    mongodb_uri: str = Field("mongodb://localhost:27017", env="MARKETING_MONGODB_URI")
    mongodb_database: str = Field("marketing", env="MARKETING_MONGODB_DATABASE")
    
    # Redis settings (for caching and queue)
    redis_uri: str = Field("redis://localhost:6379/0", env="MARKETING_REDIS_URI")
    redis_password: Optional[str] = Field(None, env="MARKETING_REDIS_PASSWORD")
    
    # Worker settings
    worker_enabled: bool = Field(True, env="MARKETING_WORKER_ENABLED")
    worker_poll_interval: int = Field(60, env="MARKETING_WORKER_POLL_INTERVAL")
    worker_threads: int = Field(2, env="MARKETING_WORKER_THREADS")
    
    # Email settings
    smtp_host: str = Field("smtp.example.com", env="MARKETING_SMTP_HOST")
    smtp_port: int = Field(587, env="MARKETING_SMTP_PORT")
    smtp_username: str = Field("user@example.com", env="MARKETING_SMTP_USERNAME")
    smtp_password: str = Field("password", env="MARKETING_SMTP_PASSWORD")
    default_sender_email: str = Field("marketing@example.com", env="MARKETING_DEFAULT_SENDER_EMAIL")
    default_sender_name: str = Field("Marketing Team", env="MARKETING_DEFAULT_SENDER_NAME")
    
    # Security settings
    api_key: str = Field("default-api-key", env="MARKETING_API_KEY")
    cors_origins: List[str] = Field(["*"], env="MARKETING_CORS_ORIGINS")
    
    # Features
    enable_ab_testing: bool = Field(True, env="MARKETING_ENABLE_AB_TESTING")
    enable_segmentation: bool = Field(True, env="MARKETING_ENABLE_SEGMENTATION")
    enable_email_campaigns: bool = Field(True, env="MARKETING_ENABLE_EMAIL_CAMPAIGNS")
    
    # Multi-client batch processing settings
    enable_batch_processing: bool = Field(True, env="MARKETING_ENABLE_BATCH_PROCESSING")
    max_client_connections: int = Field(50, env="MARKETING_MAX_CLIENT_CONNECTIONS")
    client_connection_timeout: int = Field(300, env="MARKETING_CLIENT_CONNECTION_TIMEOUT")
    max_client_workers: int = Field(10, env="MARKETING_MAX_CLIENT_WORKERS")
    default_max_concurrent_clients: int = Field(5, env="MARKETING_DEFAULT_MAX_CONCURRENT_CLIENTS")
    batch_processing_interval: int = Field(120, env="MARKETING_BATCH_PROCESSING_INTERVAL")
    max_batch_retries: int = Field(3, env="MARKETING_MAX_BATCH_RETRIES")
    batch_retry_delay: int = Field(300, env="MARKETING_BATCH_RETRY_DELAY")
    
    # Client database settings
    default_client_db_timeout: int = Field(30000, env="MARKETING_DEFAULT_CLIENT_DB_TIMEOUT")
    client_db_retry_writes: bool = Field(True, env="MARKETING_CLIENT_DB_RETRY_WRITES")
    client_db_max_pool_size: int = Field(10, env="MARKETING_CLIENT_DB_MAX_POOL_SIZE")
    
    class Config:
        """Pydantic config class."""
        env_prefix = "MARKETING_"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings.
    
    Uses lru_cache to avoid loading settings multiple times.
    
    Returns:
        Settings object
    """
    return Settings() 