"""
Configuration module for the communication-base microservice.
Loads environment variables and exposes configuration parameters.
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Config:
    COMM_BASE_API_KEY = os.getenv("COMM_BASE_API_KEY")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    # Add other configuration variables as necessary. 

class Settings(BaseSettings):
    api_key: str
    openai_api_key: str
    mongodb_url: str
    environment: str = "development"
    session_timeout: int = 3600  # 1 hour
    cleanup_interval: int = 300   # 5 minutes
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings() 