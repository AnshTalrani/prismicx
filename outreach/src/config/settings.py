"""
Application settings and configuration.

This module handles loading and validating all environment variables
and application settings.
"""

import os
from typing import Dict, List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = "Outreach System"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # Database settings
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # API settings
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    
    # Authentication settings
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # AI Model settings
    # ASR (Whisper) settings
    whisper_model_size: str = Field(default="base", env="WHISPER_MODEL_SIZE")
    whisper_device: str = Field(default="cpu", env="WHISPER_DEVICE")
    whisper_language: Optional[str] = Field(default=None, env="WHISPER_LANGUAGE")
    
    # LLM settings
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-sonnet", env="ANTHROPIC_MODEL")
    
    # TTS (Kokoro) settings
    kokoro_model_path: Optional[str] = Field(default=None, env="KOKORO_MODEL_PATH")
    kokoro_device: str = Field(default="cpu", env="KOKORO_DEVICE")
    kokoro_voice_profile: str = Field(default="default", env="KOKORO_VOICE_PROFILE")
    
    # Emotion detection settings
    emotion_model_path: Optional[str] = Field(default=None, env="EMOTION_MODEL_PATH")
    emotion_confidence_threshold: float = Field(default=0.7, env="EMOTION_CONFIDENCE_THRESHOLD")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Monitoring settings
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # File storage settings
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    
    # Feature flags
    enable_realtime: bool = Field(default=True, env="ENABLE_REALTIME")
    enable_analytics: bool = Field(default=True, env="ENABLE_ANALYTICS")
    enable_notifications: bool = Field(default=True, env="ENABLE_NOTIFICATIONS")
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


# Feature flags for easy access
class FeatureFlags:
    """Feature flags for conditional functionality."""
    
    @property
    def realtime_enabled(self) -> bool:
        return settings.enable_realtime
    
    @property
    def analytics_enabled(self) -> bool:
        return settings.enable_analytics
    
    @property
    def notifications_enabled(self) -> bool:
        return settings.enable_notifications


feature_flags = FeatureFlags()
