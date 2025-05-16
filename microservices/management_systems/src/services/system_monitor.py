"""
Service for collecting and managing system information.
"""
import logging
import httpx
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.system_info import (
    ServiceHealth,
    ServiceMetrics,
    TenantUsage,
    SystemOverview,
    ServiceConfig,
    CacheConfig
)
from ..cache.redis_cache import cache

logger = logging.getLogger(__name__)

class SystemMonitor:
    """System monitoring and information collection service."""
    
    def __init__(self):
        """Initialize system monitor."""
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.services = {
            "config-service": "http://config-service:8000",
            "tenant-mgmt-service": "http://tenant-mgmt-service:8000",
            "user-data-service": "http://user-data-service:8000",
            "task-repo-service": "http://task-repo-service:8000"
        }
        
    async def close(self):
        """Cleanup resources."""
        await self.http_client.aclose()
        
    async def get_service_health(self, service_name: str) -> ServiceHealth:
        """Get health status for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            ServiceHealth: Health status information
        """
        cache_key = cache.get_key("health", service_name)
        cached = await cache.get(cache_key)
        if cached:
            return ServiceHealth(**cached)
            
        try:
            start_time = datetime.now()
            response = await self.http_client.get(f"{self.services[service_name]}/health")
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            health = ServiceHealth(
                service_name=service_name,
                status="healthy" if response.status_code == 200 else "unhealthy",
                last_check=datetime.now(),
                uptime=response.json().get("uptime", 0),
                response_time=response_time,
                error_count=response.json().get("error_count", 0),
                warning_count=response.json().get("warning_count", 0)
            )
            
            await cache.set(cache_key, health.dict(), CacheConfig.HEALTH_CACHE_TTL)
            return health
            
        except Exception as e:
            logger.error(f"Error getting health for {service_name}: {str(e)}")
            return ServiceHealth(
                service_name=service_name,
                status="unhealthy",
                last_check=datetime.now(),
                uptime=0,
                response_time=0,
                error_count=1,
                warning_count=0
            )
            
    async def get_service_metrics(self, service_name: str) -> ServiceMetrics:
        """Get metrics for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            ServiceMetrics: Service metrics information
        """
        cache_key = cache.get_key("metrics", service_name)
        cached = await cache.get(cache_key)
        if cached:
            return ServiceMetrics(**cached)
            
        try:
            response = await self.http_client.get(f"{self.services[service_name]}/metrics")
            metrics = ServiceMetrics(
                service_name=service_name,
                cpu_usage=response.json().get("cpu_usage", 0),
                memory_usage=response.json().get("memory_usage", 0),
                request_count=response.json().get("request_count", 0),
                error_rate=response.json().get("error_rate", 0),
                average_response_time=response.json().get("avg_response_time", 0),
                timestamp=datetime.now()
            )
            
            await cache.set(cache_key, metrics.dict(), CacheConfig.METRICS_CACHE_TTL)
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics for {service_name}: {str(e)}")
            return ServiceMetrics(
                service_name=service_name,
                cpu_usage=0,
                memory_usage=0,
                request_count=0,
                error_rate=0,
                average_response_time=0,
                timestamp=datetime.now()
            )
            
    async def get_tenant_usage(self, tenant_id: str) -> TenantUsage:
        """Get usage metrics for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            TenantUsage: Tenant usage information
        """
        cache_key = cache.get_key("tenant", tenant_id)
        cached = await cache.get(cache_key)
        if cached:
            return TenantUsage(**cached)
            
        try:
            response = await self.http_client.get(
                f"{self.services['tenant-mgmt-service']}/api/v1/tenants/{tenant_id}/usage"
            )
            usage = TenantUsage(**response.json())
            await cache.set(cache_key, usage.dict(), CacheConfig.TENANT_CACHE_TTL)
            return usage
            
        except Exception as e:
            logger.error(f"Error getting usage for tenant {tenant_id}: {str(e)}")
            return None
            
    async def get_system_overview(self) -> SystemOverview:
        """Get overall system overview.
        
        Returns:
            SystemOverview: System overview information
        """
        cache_key = "system:overview"
        cached = await cache.get(cache_key)
        if cached:
            return SystemOverview(**cached)
            
        try:
            # Collect health status for all services
            health_statuses = await asyncio.gather(*[
                self.get_service_health(service)
                for service in self.services
            ])
            
            # Get tenant statistics
            tenant_stats = await self.http_client.get(
                f"{self.services['tenant-mgmt-service']}/api/v1/tenants/stats"
            )
            
            overview = SystemOverview(
                total_tenants=tenant_stats.json().get("total", 0),
                active_tenants=tenant_stats.json().get("active", 0),
                total_users=tenant_stats.json().get("total_users", 0),
                total_storage=tenant_stats.json().get("total_storage", 0),
                total_api_calls=tenant_stats.json().get("total_api_calls", 0),
                services_healthy=sum(1 for h in health_statuses if h.status == "healthy"),
                services_total=len(self.services),
                last_updated=datetime.now()
            )
            
            await cache.set(cache_key, overview.dict(), CacheConfig.OVERVIEW_CACHE_TTL)
            return overview
            
        except Exception as e:
            logger.error(f"Error getting system overview: {str(e)}")
            return SystemOverview(
                total_tenants=0,
                active_tenants=0,
                total_users=0,
                total_storage=0,
                total_api_calls=0,
                services_healthy=0,
                services_total=len(self.services),
                last_updated=datetime.now()
            )
            
    async def get_service_config(self, service_name: str) -> ServiceConfig:
        """Get configuration for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            ServiceConfig: Service configuration information
        """
        cache_key = cache.get_key("config", service_name)
        cached = await cache.get(cache_key)
        if cached:
            return ServiceConfig(**cached)
            
        try:
            response = await self.http_client.get(f"{self.services[service_name]}/config")
            config = ServiceConfig(**response.json())
            await cache.set(cache_key, config.dict(), CacheConfig.CONFIG_CACHE_TTL)
            return config
            
        except Exception as e:
            logger.error(f"Error getting config for {service_name}: {str(e)}")
            return None

# Global monitor instance
monitor = SystemMonitor() 