"""
Settings Module

This module provides the Settings model that defines the configuration
options for the communication-base service.
"""

from pydantic import BaseSettings, Field
from typing import Optional, Dict, Any


class Settings(BaseSettings):
    """
    Settings for the communication-base service.
    
    This class defines all the configuration options available for the service,
    with their default values and validation rules.
    """
    # Service identification
    service_name: str = "communication-base"
    version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    
    # MongoDB settings
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "communication_base"
    mongodb_user: Optional[str] = None
    mongodb_password: Optional[str] = None
    mongodb_connection_timeout_ms: int = 5000
    mongodb_max_pool_size: int = 10
    
    # Agent batch request settings
    batch_collection_name: str = "agent_batch_requests"
    servicetype: str = "communication"
    
    # Campaign settings
    campaign_poll_interval_seconds: int = 60
    worker_count: int = 2
    max_retries: int = 3
    max_campaign_recipients: int = 10000
    campaign_timeout_minutes: int = 1440  # 24 hours
    
    # Worker settings
    worker_processing_interval_seconds: int = 5
    worker_max_concurrent_conversations: int = 10
    worker_batch_size: int = 50
    worker_retry_delay_minutes: int = 5
    worker_error_retry_max: int = 3
    
    # Metrics and monitoring
    enable_metrics: bool = True
    metrics_format: str = "prometheus"
    
    # Performance settings
    batch_size: int = 100
    max_concurrent_operations: int = 20
    
    class Config:
        """Configuration for the Settings model."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = ""
        
        # Allow environment variables to override the values
        env_nested_delimiter = "__"
        
        # Additional attributes that can be set via environment variables
        extra = "ignore"

_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """
    Get application settings singleton.
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings 