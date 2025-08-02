"""
Settings module for the analysis-base microservice.

This module defines default settings and configuration values for the
analysis-base microservice, which can be overridden by environment
variables or configuration files.
"""
import os
from typing import Any, Dict, List

# Application settings
APP_NAME = "analysis-base"
APP_VERSION = "0.1.0"
ENV = os.getenv("ENVIRONMENT", "development")
DEBUG = ENV == "development"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
    
    # Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/analysis_db")
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
DATABASE_TIMEOUT = int(os.getenv("DATABASE_TIMEOUT", "30"))

# Redis settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_TIMEOUT = int(os.getenv("REDIS_TIMEOUT", "10"))

# Celery settings
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
    
    # API settings
API_PREFIX = "/api/v1"
API_TITLE = "Analysis Base API"
API_DESCRIPTION = "API for the analysis-base microservice"
API_VERSION = "v1"
API_DOCS_URL = "/docs"
API_REDOC_URL = "/redoc"

# CORS settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_HEADERS = ["*"]

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "analysis-base-secret-key")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
ALGORITHM = "HS256"

# Database Layer Client settings
DATABASE_LAYER_URL = os.getenv("DATABASE_LAYER_URL", "http://database-layer:8000")
DATABASE_LAYER_TIMEOUT = int(os.getenv("DATABASE_LAYER_TIMEOUT", "30"))
DATABASE_LAYER_API_KEY = os.getenv("DATABASE_LAYER_API_KEY", "")

# Analysis settings
DEFAULT_CONTEXT_LIMIT = int(os.getenv("DEFAULT_CONTEXT_LIMIT", "100"))
MAX_CONTEXT_LIMIT = int(os.getenv("MAX_CONTEXT_LIMIT", "1000"))
CONTEXT_POLL_INTERVAL = int(os.getenv("CONTEXT_POLL_INTERVAL", "5"))  # seconds
MAX_PROCESSING_TIME = int(os.getenv("MAX_PROCESSING_TIME", "300"))  # seconds
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# Pipeline settings
PIPELINE_TIMEOUT = int(os.getenv("PIPELINE_TIMEOUT", "60"))  # seconds
PIPELINE_SPECS_DIR = os.getenv("PIPELINE_SPECS_DIR", "specs/pipelines")

# Model settings
MODEL_SPECS_DIR = os.getenv("MODEL_SPECS_DIR", "specs/models")
DECISION_TREE_SPECS_DIR = os.getenv("DECISION_TREE_SPECS_DIR", "specs/decision_trees")

# Default modules to load
DEFAULT_MODULES = [
    "src.modules.data_ingestion.components",
    "src.modules.descriptive_module.components",
    "src.modules.diagnostic_module.components",
    "src.modules.predictive_module.components",
    "src.modules.prescriptive_module.components"
]

# Default analysis type pipelines
DEFAULT_ANALYSIS_PIPELINES: Dict[str, Dict[str, Any]] = {
    "descriptive": {
        "id": "descriptive",
        "name": "Descriptive Analysis Pipeline",
        "description": "Pipeline for descriptive analysis",
        "components": []
    },
    "diagnostic": {
        "id": "diagnostic",
        "name": "Diagnostic Analysis Pipeline",
        "description": "Pipeline for diagnostic analysis",
        "components": []
    },
    "predictive": {
        "id": "predictive",
        "name": "Predictive Analysis Pipeline",
        "description": "Pipeline for predictive analysis",
        "components": []
    },
    "prescriptive": {
        "id": "prescriptive",
        "name": "Prescriptive Analysis Pipeline",
        "description": "Pipeline for prescriptive analysis",
        "components": []
    }
}

# Build default configuration dict
default_config: Dict[str, Any] = {
    "app": {
        "name": APP_NAME,
        "version": APP_VERSION,
        "env": ENV,
        "debug": DEBUG,
        "log_level": LOG_LEVEL
    },
    "server": {
        "host": HOST,
        "port": PORT
    },
    "database": {
        "url": DATABASE_URL,
        "pool_size": DATABASE_POOL_SIZE,
        "max_overflow": DATABASE_MAX_OVERFLOW,
        "timeout": DATABASE_TIMEOUT
    },
    "redis": {
        "url": REDIS_URL,
        "timeout": REDIS_TIMEOUT
    },
    "celery": {
        "broker_url": CELERY_BROKER_URL,
        "result_backend": CELERY_RESULT_BACKEND,
        "task_serializer": CELERY_TASK_SERIALIZER,
        "result_serializer": CELERY_RESULT_SERIALIZER,
        "accept_content": CELERY_ACCEPT_CONTENT,
        "timezone": CELERY_TIMEZONE,
        "enable_utc": CELERY_ENABLE_UTC
    },
    "api": {
        "prefix": API_PREFIX,
        "title": API_TITLE,
        "description": API_DESCRIPTION,
        "version": API_VERSION,
        "docs_url": API_DOCS_URL,
        "redoc_url": API_REDOC_URL
    },
    "cors": {
        "origins": CORS_ORIGINS,
        "methods": CORS_METHODS,
        "headers": CORS_HEADERS
    },
    "security": {
        "secret_key": SECRET_KEY,
        "access_token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
        "algorithm": ALGORITHM
    },
    "database_layer": {
        "url": DATABASE_LAYER_URL,
        "timeout": DATABASE_LAYER_TIMEOUT,
        "api_key": DATABASE_LAYER_API_KEY
    },
    "analysis": {
        "default_context_limit": DEFAULT_CONTEXT_LIMIT,
        "max_context_limit": MAX_CONTEXT_LIMIT,
        "context_poll_interval": CONTEXT_POLL_INTERVAL,
        "max_processing_time": MAX_PROCESSING_TIME,
        "max_retries": MAX_RETRIES
    },
    "pipeline": {
        "timeout": PIPELINE_TIMEOUT,
        "specs_dir": PIPELINE_SPECS_DIR,
        "default_pipelines": DEFAULT_ANALYSIS_PIPELINES
    },
    "model": {
        "specs_dir": MODEL_SPECS_DIR,
        "decision_tree_specs_dir": DECISION_TREE_SPECS_DIR
    },
    "modules": {
        "default_modules": DEFAULT_MODULES
    }
} 