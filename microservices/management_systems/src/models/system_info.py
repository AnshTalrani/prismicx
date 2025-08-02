"""
Models for system information and metrics.
"""
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ServiceHealth(BaseModel):
    """Health status of a service."""
    service_name: str
    status: str  # "healthy", "unhealthy", "degraded"
    last_check: datetime
    uptime: float  # in seconds
    response_time: float  # in milliseconds
    error_count: int
    warning_count: int

class ServiceMetrics(BaseModel):
    """Metrics for a service."""
    service_name: str
    cpu_usage: float  # percentage
    memory_usage: float  # percentage
    request_count: int
    error_rate: float
    average_response_time: float
    timestamp: datetime

class TenantUsage(BaseModel):
    """Usage metrics for a tenant."""
    tenant_id: str
    tenant_name: str
    active_users: int
    storage_used: float  # in MB
    api_calls_count: int
    last_activity: datetime
    subscription_status: str

class SystemOverview(BaseModel):
    """Overall system overview."""
    total_tenants: int
    active_tenants: int
    total_users: int
    total_storage: float  # in MB
    total_api_calls: int
    services_healthy: int
    services_total: int
    last_updated: datetime

class ServiceConfig(BaseModel):
    """Service configuration information."""
    service_name: str
    version: str
    environment: str
    config_timestamp: datetime
    settings: Dict[str, str]
    dependencies: List[str]
    endpoints: List[str]

class CacheConfig:
    """Cache configuration for system information."""
    HEALTH_CACHE_TTL = 60  # 1 minute
    METRICS_CACHE_TTL = 300  # 5 minutes
    TENANT_CACHE_TTL = 600  # 10 minutes
    OVERVIEW_CACHE_TTL = 300  # 5 minutes
    CONFIG_CACHE_TTL = 3600  # 1 hour 