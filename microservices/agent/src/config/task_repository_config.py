"""
Task Repository configuration.

Centralized configuration for the Task Repository service integration.
"""
import os
from typing import Dict, Any

# Task Repository Service connection settings
TASK_SERVICE_URL = os.getenv("TASK_REPO_URL", "http://task-repo-service:8503")
TASK_SERVICE_API_KEY = os.getenv("TASK_REPO_API_KEY", "dev_api_key")
SERVICE_ID = os.getenv("SERVICE_ID", "agent-service")

# TTL settings for auto-deletion (in seconds)
COMPLETED_CONTEXT_TTL = int(os.getenv("COMPLETED_CONTEXT_TTL", str(86400)))  # 24 hours
FAILED_CONTEXT_TTL = int(os.getenv("FAILED_CONTEXT_TTL", str(604800)))  # 7 days
DEFAULT_CONTEXT_TTL = int(os.getenv("DEFAULT_CONTEXT_TTL", str(2592000)))  # 30 days

# Default context status tags
DEFAULT_STATUS_TAGS: Dict[str, Dict[str, Any]] = {
    "created": {
        "action": "log",
        "description": "Context has been created"
    },
    "processing": {
        "action": "log",
        "description": "Context is being processed"
    },
    "completed": {
        "action": "route_to_output",
        "description": "Context processing has completed successfully",
        "delete_after": COMPLETED_CONTEXT_TTL
    },
    "failed": {
        "action": "log_error",
        "description": "Context processing has failed",
        "delete_after": FAILED_CONTEXT_TTL
    },
    "pending": {
        "action": "queue",
        "description": "Context is waiting for processing"
    }
}

# Query limits
MAX_QUERY_LIMIT = 1000
DEFAULT_QUERY_LIMIT = 100

# Batch processing settings
BATCH_CONCURRENCY = int(os.getenv("BATCH_CONCURRENCY", "5"))
BATCH_RETRY_LIMIT = int(os.getenv("BATCH_RETRY_LIMIT", "3"))
BATCH_RETRY_DELAY = int(os.getenv("BATCH_RETRY_DELAY", "2"))  # seconds 