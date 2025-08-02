"""
Configuration settings for the marketing microservice.

This module provides configuration settings and defaults for the application.
"""

import logging
import os
import socket
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class Config:
    """
    Configuration settings for the marketing microservice.
    
    This class provides access to configuration settings from environment variables
    with sensible defaults.
    """
    
    def __init__(self):
        """Initialize configuration with values from environment variables."""
        # Database settings
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.mongodb_database = os.getenv("MONGODB_DATABASE", "marketing")
        
        # SMTP settings
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "25"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ["true", "1", "yes"]
        
        # Email settings
        self.email_from = os.getenv("EMAIL_FROM", "noreply@example.com")
        
        # API settings
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.debug = os.getenv("DEBUG", "false").lower() in ["true", "1", "yes"]
        self.api_key = os.getenv("API_KEY", "")
        
        # Central task repository settings
        self.central_task_repo_uri = os.getenv(
            "CENTRAL_TASK_REPO_URI", 
            "mongodb://admin:password@task-repository:27017/"
        )
        self.central_task_repo_db = os.getenv("CENTRAL_TASK_REPO_DB", "agent_tasks")
        self.central_task_collection = os.getenv("CENTRAL_TASK_COLLECTION", "marketing_tasks")
        
        # Worker settings
        self.worker_id = os.getenv("WORKER_ID", f"marketing-{socket.gethostname()}-{uuid.uuid4().hex[:8]}")
        self.task_check_interval = int(os.getenv("TASK_CHECK_INTERVAL", "30"))
        self.campaign_check_interval = int(os.getenv("CAMPAIGN_CHECK_INTERVAL", "60"))
        self.service_id = os.getenv("SERVICE_ID", f"marketing-{socket.gethostname()}")
        
        # Template directory
        self.template_dir = os.getenv("TEMPLATE_DIR", "templates")
        
        # Logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # Rate limiting
        self.daily_email_limit = int(os.getenv('DAILY_EMAIL_LIMIT', '1000'))
        
        # Initialize logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        )
        
    def dict(self) -> Dict[str, Any]:
        """
        Get configuration as a dictionary.
        
        Returns:
            Dictionary of configuration values
        """
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }
    
    def __str__(self) -> str:
        """
        Return string representation of configuration.
        
        Excludes sensitive information like passwords.
        """
        return (
            f"Config("
            f"mongodb_uri='{self._mask_uri(self.mongodb_uri)}', "
            f"mongodb_database='{self.mongodb_database}', "
            f"smtp_host='{self.smtp_host}', "
            f"smtp_port={self.smtp_port}, "
            f"smtp_username='{self.smtp_username}', "
            f"smtp_use_tls={self.smtp_use_tls}, "
            f"email_from='{self.email_from}', "
            f"host='{self.host}', "
            f"port={self.port}, "
            f"debug={self.debug}, "
            f"api_key='{self.api_key}', "
            f"central_task_repo_uri='{self.central_task_repo_uri}', "
            f"central_task_repo_db='{self.central_task_repo_db}', "
            f"central_task_collection='{self.central_task_collection}', "
            f"worker_id='{self.worker_id}', "
            f"task_check_interval={self.task_check_interval}, "
            f"campaign_check_interval={self.campaign_check_interval}, "
            f"service_id='{self.service_id}', "
            f"template_dir='{self.template_dir}', "
            f"log_level='{self.log_level}', "
            f"daily_email_limit={self.daily_email_limit}"
            f")"
        )
    
    def _mask_uri(self, uri: str) -> str:
        """
        Mask sensitive information in a URI.
        
        Args:
            uri: URI to mask
            
        Returns:
            Masked URI with password replaced by asterisks
        """
        try:
            if '@' in uri:
                prefix = uri.split('@')[0]
                if ':' in prefix:
                    username_part = prefix.split(':')[0]
                    return f"{username_part}:****@{uri.split('@')[1]}"
            return uri
        except Exception:
            return uri

# Singleton configuration instance
_config: Optional[Config] = None

def get_config() -> Config:
    """
    Get the configuration singleton.
    
    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config()
        logger.info(f"Loaded configuration: {_config}")
    return _config 