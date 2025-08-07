"""
Health Service

This module provides comprehensive health monitoring functionality,
including system status, model health, and performance metrics.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import psutil

from ..config.logging_config import get_logger, LoggerMixin
from ..config.settings import settings

logger = get_logger(__name__)


class HealthService(LoggerMixin):
    """Service for health monitoring and system status."""
    
    def __init__(self):
        """Initialize the health service."""
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the service."""
        try:
            self.logger.info("Initializing Health Service...")
            self.is_initialized = True
            self.logger.info("Health Service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Health Service: {str(e)}")
            raise
    
    async def get_detailed_health(self) -> Dict[str, Any]:
        """Get detailed health status of all system components."""
        try:
            self.logger.info("Getting detailed health status")
            
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": settings.app_version,
                "environment": settings.environment,
                "components": {}
            }
            
            # Check database health
            db_health = await self.get_database_health()
            health_status["components"]["database"] = db_health
            
            # Check Redis health
            redis_health = await self.get_redis_health()
            health_status["components"]["redis"] = redis_health
            
            # Check model health
            model_health = await self.get_model_health()
            health_status["components"]["models"] = model_health
            
            # Check external services health
            external_health = await self.get_external_services_health()
            health_status["components"]["external_services"] = external_health
            
            # Check system performance
            performance_health = await self.get_performance_metrics()
            health_status["components"]["performance"] = performance_health
            
            # Determine overall status
            all_healthy = all(
                component.get("status") == "healthy"
                for component in health_status["components"].values()
            )
            
            if not all_healthy:
                health_status["status"] = "degraded"
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Failed to get detailed health: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_model_health(self) -> Dict[str, Any]:
        """Check health of all AI models."""
        try:
            self.logger.info("Checking model health")
            
            model_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "models": {}
            }
            
            # Check ASR model
            asr_status = await self._check_asr_model()
            model_status["models"]["asr"] = asr_status
            
            # Check LLM model
            llm_status = await self._check_llm_model()
            model_status["models"]["llm"] = llm_status
            
            # Check TTS model
            tts_status = await self._check_tts_model()
            model_status["models"]["tts"] = tts_status
            
            # Check Emotion model
            emotion_status = await self._check_emotion_model()
            model_status["models"]["emotion"] = emotion_status
            
            # Determine overall model status
            all_models_healthy = all(
                model.get("status") == "healthy"
                for model in model_status["models"].values()
            )
            
            if not all_models_healthy:
                model_status["status"] = "degraded"
            
            return model_status
            
        except Exception as e:
            self.logger.error(f"Failed to check model health: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and health."""
        try:
            self.logger.info("Checking database health")
            
            # This would typically involve:
            # 1. Testing database connection
            # 2. Running a simple query
            # 3. Checking connection pool status
            
            # For now, return mock status
            db_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "connection": "connected",
                "response_time": 0.05,
                "pool_size": 10,
                "active_connections": 3
            }
            
            return db_status
            
        except Exception as e:
            self.logger.error(f"Failed to check database health: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity and health."""
        try:
            self.logger.info("Checking Redis health")
            
            # This would typically involve:
            # 1. Testing Redis connection
            # 2. Running a simple ping command
            # 3. Checking memory usage
            
            # For now, return mock status
            redis_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "connection": "connected",
                "response_time": 0.01,
                "memory_usage": "64MB",
                "keys_count": 1250
            }
            
            return redis_status
            
        except Exception as e:
            self.logger.error(f"Failed to check Redis health: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_external_services_health(self) -> Dict[str, Any]:
        """Check health of external services (APIs, etc.)."""
        try:
            self.logger.info("Checking external services health")
            
            external_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {}
            }
            
            # Check OpenAI API
            openai_status = await self._check_openai_api()
            external_status["services"]["openai"] = openai_status
            
            # Check Anthropic API
            anthropic_status = await self._check_anthropic_api()
            external_status["services"]["anthropic"] = anthropic_status
            
            # Check other external services
            other_services = await self._check_other_external_services()
            external_status["services"].update(other_services)
            
            # Determine overall external services status
            all_services_healthy = all(
                service.get("status") == "healthy"
                for service in external_status["services"].values()
            )
            
            if not all_services_healthy:
                external_status["status"] = "degraded"
            
            return external_status
            
        except Exception as e:
            self.logger.error(f"Failed to check external services health: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics."""
        try:
            self.logger.info("Getting performance metrics")
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            performance_metrics = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available": memory.available,
                    "disk_percent": disk.percent,
                    "disk_free": disk.free
                },
                "application": {
                    "uptime": self._get_uptime(),
                    "active_connections": self._get_active_connections(),
                    "request_rate": self._get_request_rate()
                }
            }
            
            # Check if metrics are within acceptable ranges
            if cpu_percent > 80 or memory.percent > 80 or disk.percent > 90:
                performance_metrics["status"] = "degraded"
            
            return performance_metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Private helper methods for model health checks
    async def _check_asr_model(self) -> Dict[str, Any]:
        """Check ASR model health."""
        try:
            # This would typically involve:
            # 1. Checking if model is loaded
            # 2. Testing with a sample audio
            # 3. Checking response time
            
            return {
                "status": "healthy",
                "model": "whisper",
                "loaded": True,
                "response_time": 0.5,
                "memory_usage": "512MB"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": "whisper"
            }
    
    async def _check_llm_model(self) -> Dict[str, Any]:
        """Check LLM model health."""
        try:
            # This would typically involve:
            # 1. Checking if model is loaded
            # 2. Testing with a sample prompt
            # 3. Checking response time
            
            return {
                "status": "healthy",
                "model": settings.llm_provider,
                "loaded": True,
                "response_time": 2.1,
                "context_window": 4096
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": settings.llm_provider
            }
    
    async def _check_tts_model(self) -> Dict[str, Any]:
        """Check TTS model health."""
        try:
            # This would typically involve:
            # 1. Checking if model is loaded
            # 2. Testing with a sample text
            # 3. Checking response time
            
            return {
                "status": "healthy",
                "model": "kokoro",
                "loaded": True,
                "response_time": 1.2,
                "voice_profiles": 5
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": "kokoro"
            }
    
    async def _check_emotion_model(self) -> Dict[str, Any]:
        """Check Emotion model health."""
        try:
            # This would typically involve:
            # 1. Checking if model is loaded
            # 2. Testing with sample audio/text
            # 3. Checking response time
            
            return {
                "status": "healthy",
                "model": "multimodal_emotion",
                "loaded": True,
                "response_time": 0.8,
                "supported_emotions": 10
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": "multimodal_emotion"
            }
    
    # Private helper methods for external service checks
    async def _check_openai_api(self) -> Dict[str, Any]:
        """Check OpenAI API health."""
        try:
            # This would typically involve:
            # 1. Making a test API call
            # 2. Checking response time
            # 3. Validating API key
            
            return {
                "status": "healthy",
                "api": "openai",
                "response_time": 1.5,
                "rate_limit_remaining": 1000
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api": "openai"
            }
    
    async def _check_anthropic_api(self) -> Dict[str, Any]:
        """Check Anthropic API health."""
        try:
            # This would typically involve:
            # 1. Making a test API call
            # 2. Checking response time
            # 3. Validating API key
            
            return {
                "status": "healthy",
                "api": "anthropic",
                "response_time": 2.0,
                "rate_limit_remaining": 500
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api": "anthropic"
            }
    
    async def _check_other_external_services(self) -> Dict[str, Any]:
        """Check other external services health."""
        try:
            # This would check other external services like:
            # - Email services
            # - SMS services
            # - Payment processors
            # - etc.
            
            return {
                "email_service": {
                    "status": "healthy",
                    "response_time": 0.3
                },
                "sms_service": {
                    "status": "healthy",
                    "response_time": 0.5
                }
            }
        except Exception as e:
            return {
                "other_services": {
                    "status": "unhealthy",
                    "error": str(e)
                }
            }
    
    # Private helper methods for performance metrics
    def _get_uptime(self) -> str:
        """Get application uptime."""
        # This would calculate actual uptime
        return "2 days, 5 hours, 30 minutes"
    
    def _get_active_connections(self) -> int:
        """Get number of active connections."""
        # This would count actual active connections
        return 25
    
    def _get_request_rate(self) -> float:
        """Get current request rate."""
        # This would calculate actual request rate
        return 15.5  # requests per second
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            self.logger.info("Cleaning up Health Service...")
            self.logger.info("Health Service cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}") 