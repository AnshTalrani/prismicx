"""
PostgreSQL configuration for multi-tenant database context.

Centralized configuration for PostgreSQL database connections and tenant handling.
"""
import os
from typing import Dict, Any

# PostgreSQL connection settings
DB_HOST = os.getenv("DB_HOST", "postgres-system")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "agent_db")
DB_USERNAME = os.getenv("DB_USERNAME", "agent_service")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_MIN_POOL_SIZE = int(os.getenv("DB_MIN_POOL_SIZE", "5"))
DB_MAX_POOL_SIZE = int(os.getenv("DB_MAX_POOL_SIZE", "20"))
DB_TENANT_AWARE = os.getenv("DB_TENANT_AWARE", "true").lower() == "true"

# Tenant Management Service connection settings
TENANT_MGMT_URL = os.getenv("TENANT_MGMT_URL", "http://tenant-mgmt-service:8501")
TENANT_MGMT_TIMEOUT_MS = int(os.getenv("TENANT_MGMT_TIMEOUT_MS", "5000"))

# Default schema when no tenant context is available
DEFAULT_SCHEMA = "public"

# TTL settings for context cleanup (in seconds)
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

# Table names
CONTEXT_TABLE = "contexts"
BATCH_TABLE = "batch_contexts"
REFERENCE_TABLE = "context_references"

# Query limits
MAX_QUERY_LIMIT = 1000
DEFAULT_QUERY_LIMIT = 100

# Batch processing settings
BATCH_CONCURRENCY = int(os.getenv("BATCH_CONCURRENCY", "5"))
BATCH_RETRY_LIMIT = int(os.getenv("BATCH_RETRY_LIMIT", "3"))
BATCH_RETRY_DELAY = int(os.getenv("BATCH_RETRY_DELAY", "2"))  # seconds

# SQL script for creating context tables in a new tenant schema
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS {schema}.contexts (
    id VARCHAR(100) PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL,
    priority INT DEFAULT 5,
    request JSONB NOT NULL,
    template JSONB NOT NULL,
    results JSONB,
    tags JSONB,
    metadata JSONB,
    parent_id VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS {schema}.batch_contexts (
    id VARCHAR(100) PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    total_items INT DEFAULT 0,
    completed_items INT DEFAULT 0,
    failed_items INT DEFAULT 0,
    skipped_items INT DEFAULT 0,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS {schema}.context_references (
    id SERIAL PRIMARY KEY,
    context_id VARCHAR(100) NOT NULL,
    ref_type VARCHAR(50) NOT NULL,
    ref_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    CONSTRAINT context_ref_unique UNIQUE (context_id, ref_type, ref_id)
);

CREATE INDEX IF NOT EXISTS idx_contexts_status ON {schema}.contexts(status);
CREATE INDEX IF NOT EXISTS idx_contexts_created_at ON {schema}.contexts(created_at);
CREATE INDEX IF NOT EXISTS idx_contexts_parent_id ON {schema}.contexts(parent_id);
CREATE INDEX IF NOT EXISTS idx_batch_contexts_status ON {schema}.batch_contexts(status);
""" 