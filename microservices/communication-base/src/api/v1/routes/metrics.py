"""
Metrics API Routes

This module provides API endpoints for retrieving service metrics.
"""

from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime, timedelta

from src.config.config_manager import get_settings
from src.config.monitoring import get_metrics
from src.config.settings import Settings
from src.repository.campaign_state_repository import CampaignStateRepository
from src.repository.conversation_state_repository import ConversationStateRepository

# Create logger
logger = structlog.get_logger(__name__)

# Create router
router = APIRouter()

# Dependencies
async def get_repositories():
    """Dependency to get repository instances."""
    campaign_repo = CampaignStateRepository()
    conversation_repo = ConversationStateRepository()
    
    await campaign_repo.initialize()
    await conversation_repo.initialize()
    
    return campaign_repo, conversation_repo

@router.get("/", response_model=Dict[str, Any])
async def get_all_metrics(
    time_range: Optional[str] = Query("1h", description="Time range for metrics (e.g., 15m, 1h, 24h, 7d)"),
    repos=Depends(get_repositories),
    settings: Settings = Depends(get_settings)
):
    """
    Get overall service metrics.
    
    Args:
        time_range: Time range for metrics (e.g., 15m, 1h, 24h, 7d)
        
    Returns:
        Service metrics
    """
    campaign_repo, conversation_repo = repos
    
    # Parse time range
    end_time = datetime.utcnow()
    start_time = parse_time_range(end_time, time_range)
    
    try:
        # Get campaign metrics
        campaign_metrics = await get_campaign_metrics(campaign_repo, start_time, end_time)
        
        # Get conversation metrics
        conversation_metrics = await get_conversation_metrics(conversation_repo, start_time, end_time)
        
        # Get system metrics
        system_metrics = get_system_metrics()
        
        # Combine all metrics
        metrics = {
            "timestamp": end_time.isoformat(),
            "time_range": time_range,
            "campaigns": campaign_metrics,
            "conversations": conversation_metrics,
            "system": system_metrics
        }
        
        logger.info("Metrics retrieved", time_range=time_range)
        
        return metrics
        
    except Exception as e:
        logger.error("Error getting metrics", error=str(e))
        return {
            "timestamp": end_time.isoformat(),
            "time_range": time_range,
            "error": str(e)
        }

@router.get("/campaigns", response_model=Dict[str, Any])
async def get_only_campaign_metrics(
    time_range: Optional[str] = Query("1h", description="Time range for metrics (e.g., 15m, 1h, 24h, 7d)"),
    repos=Depends(get_repositories)
):
    """
    Get campaign-specific metrics.
    
    Args:
        time_range: Time range for metrics (e.g., 15m, 1h, 24h, 7d)
        
    Returns:
        Campaign metrics
    """
    campaign_repo, _ = repos
    
    # Parse time range
    end_time = datetime.utcnow()
    start_time = parse_time_range(end_time, time_range)
    
    try:
        # Get campaign metrics
        campaign_metrics = await get_campaign_metrics(campaign_repo, start_time, end_time)
        
        metrics = {
            "timestamp": end_time.isoformat(),
            "time_range": time_range,
            "campaigns": campaign_metrics
        }
        
        logger.info("Campaign metrics retrieved", time_range=time_range)
        
        return metrics
        
    except Exception as e:
        logger.error("Error getting campaign metrics", error=str(e))
        return {
            "timestamp": end_time.isoformat(),
            "time_range": time_range,
            "error": str(e)
        }

@router.get("/conversations", response_model=Dict[str, Any])
async def get_only_conversation_metrics(
    time_range: Optional[str] = Query("1h", description="Time range for metrics (e.g., 15m, 1h, 24h, 7d)"),
    repos=Depends(get_repositories)
):
    """
    Get conversation-specific metrics.
    
    Args:
        time_range: Time range for metrics (e.g., 15m, 1h, 24h, 7d)
        
    Returns:
        Conversation metrics
    """
    _, conversation_repo = repos
    
    # Parse time range
    end_time = datetime.utcnow()
    start_time = parse_time_range(end_time, time_range)
    
    try:
        # Get conversation metrics
        conversation_metrics = await get_conversation_metrics(conversation_repo, start_time, end_time)
        
        metrics = {
            "timestamp": end_time.isoformat(),
            "time_range": time_range,
            "conversations": conversation_metrics
        }
        
        logger.info("Conversation metrics retrieved", time_range=time_range)
        
        return metrics
        
    except Exception as e:
        logger.error("Error getting conversation metrics", error=str(e))
        return {
            "timestamp": end_time.isoformat(),
            "time_range": time_range,
            "error": str(e)
        }

@router.get("/system", response_model=Dict[str, Any])
async def get_only_system_metrics():
    """
    Get system metrics.
    
    Returns:
        System metrics
    """
    try:
        # Get system metrics
        system_metrics = get_system_metrics()
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": system_metrics
        }
        
        logger.info("System metrics retrieved")
        
        return metrics
        
    except Exception as e:
        logger.error("Error getting system metrics", error=str(e))
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# Helper functions
def parse_time_range(end_time: datetime, time_range: str) -> datetime:
    """
    Parse time range string into a start time.
    
    Args:
        end_time: End time for the range
        time_range: Time range string (e.g., 15m, 1h, 24h, 7d)
        
    Returns:
        Start time for the range
    """
    unit = time_range[-1]
    try:
        value = int(time_range[:-1])
    except ValueError:
        # Default to 1 hour if invalid format
        return end_time - timedelta(hours=1)
    
    if unit == 'm':
        return end_time - timedelta(minutes=value)
    elif unit == 'h':
        return end_time - timedelta(hours=value)
    elif unit == 'd':
        return end_time - timedelta(days=value)
    else:
        # Default to 1 hour if invalid unit
        return end_time - timedelta(hours=1)

async def get_campaign_metrics(
    campaign_repo: CampaignStateRepository, 
    start_time: datetime, 
    end_time: datetime
) -> Dict[str, Any]:
    """
    Get campaign metrics for the specified time range.
    
    Args:
        campaign_repo: Campaign repository instance
        start_time: Start time for metrics
        end_time: End time for metrics
        
    Returns:
        Campaign metrics
    """
    # Get campaigns created in the time range
    all_campaigns = await campaign_repo.list_campaigns(
        {"created_at": {"$gte": start_time, "$lte": end_time}},
        0,
        1000
    )
    
    # Count campaigns by status
    status_counts = {}
    type_counts = {}
    
    for campaign in all_campaigns:
        status = campaign.get("status", "unknown")
        campaign_type = campaign.get("type", "unknown")
        
        if status not in status_counts:
            status_counts[status] = 0
        if campaign_type not in type_counts:
            type_counts[campaign_type] = 0
            
        status_counts[status] += 1
        type_counts[campaign_type] += 1
    
    return {
        "total": len(all_campaigns),
        "by_status": status_counts,
        "by_type": type_counts,
        "time_period": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        }
    }

async def get_conversation_metrics(
    conversation_repo: ConversationStateRepository, 
    start_time: datetime, 
    end_time: datetime
) -> Dict[str, Any]:
    """
    Get conversation metrics for the specified time range.
    
    Args:
        conversation_repo: Conversation repository instance
        start_time: Start time for metrics
        end_time: End time for metrics
        
    Returns:
        Conversation metrics
    """
    # Get conversations created in the time range
    all_conversations = await conversation_repo.get_conversation_states(
        {"created_at": {"$gte": start_time, "$lte": end_time}},
        0,
        10000
    )
    
    # Count conversations by status
    status_counts = {}
    stage_counts = {}
    
    for conversation in all_conversations:
        status = conversation.get("status", "unknown")
        stage = conversation.get("current_stage", "unknown")
        
        if status not in status_counts:
            status_counts[status] = 0
        if stage not in stage_counts:
            stage_counts[stage] = 0
            
        status_counts[status] += 1
        stage_counts[stage] += 1
    
    # Get progression metrics
    progression_counts = {}
    for conversation in all_conversations:
        history = conversation.get("history", [])
        if not history:
            continue
            
        for entry in history:
            from_stage = entry.get("from_stage")
            to_stage = entry.get("to_stage")
            
            if from_stage and to_stage:
                key = f"{from_stage}_to_{to_stage}"
                if key not in progression_counts:
                    progression_counts[key] = 0
                    
                progression_counts[key] += 1
    
    return {
        "total": len(all_conversations),
        "by_status": status_counts,
        "by_stage": stage_counts,
        "stage_progressions": progression_counts,
        "time_period": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        }
    }

def get_system_metrics() -> Dict[str, Any]:
    """
    Get system metrics.
    
    Returns:
        System metrics
    """
    metrics_client = get_metrics()
    
    if not metrics_client:
        return {
            "status": "not_available",
            "reason": "Metrics client not initialized"
        }
    
    try:
        # Get memory usage
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        system_metrics = {
            "memory": {
                "rss_mb": memory_info.rss / (1024 * 1024),
                "vms_mb": memory_info.vms / (1024 * 1024)
            },
            "cpu": {
                "percent": process.cpu_percent(interval=0.1)
            },
            "threads": process.num_threads(),
            "open_files": len(process.open_files())
        }
        
        # Add metrics from metrics client if available
        if hasattr(metrics_client, "get_metrics"):
            client_metrics = metrics_client.get_metrics()
            system_metrics["application"] = client_metrics
        
        return system_metrics
        
    except ImportError:
        return {
            "status": "limited",
            "reason": "psutil not available"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        } 