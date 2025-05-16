"""
User Insights Router (Sync Version)

API routes for managing user insights with synchronous operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header, Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from ..services.user_insights_service import UserInsightsService
from ..models.user_insight import UserInsight
from ..dependencies import get_mongo_client_sync

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request and response validation
class TopicCreate(BaseModel):
    name: str = Field(..., description="Topic name")
    description: str = Field(..., description="Topic description")

class SubtopicCreate(BaseModel):
    name: str = Field(..., description="Subtopic name")
    content: Dict[str, Any] = Field(..., description="Subtopic content")

class TopicUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Topic name")
    description: Optional[str] = Field(None, description="Topic description")

class SubtopicUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Subtopic name")
    content: Optional[Dict[str, Any]] = Field(None, description="Subtopic content")

class MetadataUpdate(BaseModel):
    metadata: Dict[str, Any] = Field(..., description="Metadata to update")


# Service dependency
def get_insight_service() -> UserInsightsService:
    """
    Get the user insight service.
    
    Returns:
        UserInsightsService instance
    """
    mongo_client = get_mongo_client_sync()
    service = UserInsightsService(mongo_client)
    service.initialize("user_data")
    return service


# Tenant ID extraction from header
def get_tenant_id(x_tenant_id: str = Header(..., description="Tenant identifier")) -> str:
    """
    Extract tenant ID from header.
    
    Args:
        x_tenant_id: Tenant identifier header
    
    Returns:
        Tenant ID
    """
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required")
    return x_tenant_id


# Routes
@router.get("/{user_id}", response_model=Dict[str, Any])
def get_user_insight(
    user_id: str = Path(..., description="User identifier"),
    tenant_id: str = Depends(get_tenant_id),
    insight_service: UserInsightsService = Depends(get_insight_service)
):
    """
    Get a user insight by user ID.
    
    Args:
        user_id: User identifier
        tenant_id: Tenant identifier
        insight_service: UserInsightsService instance
    
    Returns:
        User insight data
    """
    insight = insight_service.get_user_insight(user_id, tenant_id)
    
    if not insight:
        raise HTTPException(status_code=404, detail=f"User insight not found for user {user_id}")
    
    return insight.to_dict()


@router.post("/{user_id}", response_model=Dict[str, Any])
def create_user_insight(
    user_id: str = Path(..., description="User identifier"),
    metadata: Optional[Dict[str, Any]] = None,
    tenant_id: str = Depends(get_tenant_id),
    insight_service: UserInsightsService = Depends(get_insight_service)
):
    """
    Create a new user insight.
    
    Args:
        user_id: User identifier
        metadata: Additional metadata
        tenant_id: Tenant identifier
        insight_service: UserInsightsService instance
    
    Returns:
        Created user insight data
    """
    # Check if insight already exists
    existing = insight_service.get_user_insight(user_id, tenant_id)
    if existing:
        raise HTTPException(status_code=409, detail=f"User insight already exists for user {user_id}")
    
    insight = insight_service.create_user_insight(user_id, tenant_id, metadata)
    
    if not insight:
        raise HTTPException(status_code=500, detail="Failed to create user insight")
        
    return insight.to_dict()


@router.put("/{user_id}/metadata", response_model=Dict[str, Any])
def update_metadata(
    metadata_update: MetadataUpdate,
    user_id: str = Path(..., description="User identifier"),
    tenant_id: str = Depends(get_tenant_id),
    insight_service: UserInsightsService = Depends(get_insight_service)
):
    """
    Update metadata for a user insight.
    
    Args:
        metadata_update: Metadata to update
        user_id: User identifier
        tenant_id: Tenant identifier
        insight_service: UserInsightsService instance
    
    Returns:
        Success status
    """
    success = insight_service.update_metadata(user_id, tenant_id, metadata_update.metadata)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"User insight not found for user {user_id}")
    
    return {"status": "success", "message": f"Updated metadata for user {user_id}"}


@router.post("/{user_id}/topics", response_model=Dict[str, Any])
def add_topic(
    topic_create: TopicCreate,
    user_id: str = Path(..., description="User identifier"),
    tenant_id: str = Depends(get_tenant_id),
    insight_service: UserInsightsService = Depends(get_insight_service)
):
    """
    Add a topic to a user insight.
    
    Args:
        topic_create: Topic data to create
        user_id: User identifier
        tenant_id: Tenant identifier
        insight_service: UserInsightsService instance
    
    Returns:
        Created topic data
    """
    topic = insight_service.add_topic(
        user_id=user_id,
        tenant_id=tenant_id,
        name=topic_create.name,
        description=topic_create.description
    )
    
    if not topic:
        raise HTTPException(status_code=404, detail=f"User insight not found for user {user_id}")
    
    return topic


@router.put("/{user_id}/topics/{topic_id}", response_model=Dict[str, Any])
def update_topic(
    topic_update: TopicUpdate,
    user_id: str = Path(..., description="User identifier"),
    topic_id: str = Path(..., description="Topic identifier"),
    tenant_id: str = Depends(get_tenant_id),
    insight_service: UserInsightsService = Depends(get_insight_service)
):
    """
    Update a topic in a user insight.
    
    Args:
        topic_update: Topic data to update
        user_id: User identifier
        topic_id: Topic identifier
        tenant_id: Tenant identifier
        insight_service: UserInsightsService instance
    
    Returns:
        Success status
    """
    topic_data = {k: v for k, v in topic_update.model_dump().items() if v is not None}
    
    if not topic_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    success = insight_service.update_topic(user_id, tenant_id, topic_id, topic_data)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Topic not found with ID {topic_id} for user {user_id}")
    
    return {"status": "success", "message": f"Updated topic {topic_id} for user {user_id}"}


@router.delete("/{user_id}/topics/{topic_id}")
def delete_topic(
    user_id: str = Path(..., description="User identifier"),
    topic_id: str = Path(..., description="Topic identifier"),
    tenant_id: str = Depends(get_tenant_id),
    insight_service: UserInsightsService = Depends(get_insight_service)
):
    """
    Delete a topic from a user insight.
    
    Args:
        user_id: User identifier
        topic_id: Topic identifier
        tenant_id: Tenant identifier
        insight_service: UserInsightsService instance
    
    Returns:
        Deletion status
    """
    success = insight_service.delete_topic(user_id, tenant_id, topic_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Topic not found with ID {topic_id} for user {user_id}")
    
    return {"status": "success", "message": f"Topic {topic_id} deleted"}


@router.post("/{user_id}/topics/{topic_id}/subtopics", response_model=Dict[str, Any])
def add_subtopic(
    subtopic_create: SubtopicCreate,
    user_id: str = Path(..., description="User identifier"),
    topic_id: str = Path(..., description="Topic identifier"),
    tenant_id: str = Depends(get_tenant_id),
    insight_service: UserInsightsService = Depends(get_insight_service)
):
    """
    Add a subtopic to a topic.
    
    Args:
        subtopic_create: Subtopic data to create
        user_id: User identifier
        topic_id: Topic identifier
        tenant_id: Tenant identifier
        insight_service: UserInsightsService instance
    
    Returns:
        Created subtopic data
    """
    subtopic = insight_service.add_subtopic(
        user_id=user_id,
        tenant_id=tenant_id,
        topic_id=topic_id,
        name=subtopic_create.name,
        content=subtopic_create.content
    )
    
    if not subtopic:
        raise HTTPException(status_code=404, detail=f"Topic not found with ID {topic_id} for user {user_id}")
    
    return subtopic


@router.put("/{user_id}/topics/{topic_id}/subtopics/{subtopic_id}", response_model=Dict[str, Any])
def update_subtopic(
    subtopic_update: SubtopicUpdate,
    user_id: str = Path(..., description="User identifier"),
    topic_id: str = Path(..., description="Topic identifier"),
    subtopic_id: str = Path(..., description="Subtopic identifier"),
    tenant_id: str = Depends(get_tenant_id),
    insight_service: UserInsightsService = Depends(get_insight_service)
):
    """
    Update a subtopic in a topic.
    
    Args:
        subtopic_update: Subtopic data to update
        user_id: User identifier
        topic_id: Topic identifier
        subtopic_id: Subtopic identifier
        tenant_id: Tenant identifier
        insight_service: UserInsightsService instance
    
    Returns:
        Success status
    """
    subtopic_data = {k: v for k, v in subtopic_update.model_dump().items() if v is not None}
    
    if not subtopic_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    success = insight_service.update_subtopic(
        user_id=user_id,
        tenant_id=tenant_id,
        topic_id=topic_id,
        subtopic_id=subtopic_id,
        subtopic_data=subtopic_data
    )
    
    if not success:
        raise HTTPException(
            status_code=404, 
            detail=f"Subtopic not found with ID {subtopic_id} in topic {topic_id} for user {user_id}"
        )
    
    return {"status": "success", "message": f"Updated subtopic {subtopic_id} in topic {topic_id}"}


@router.delete("/{user_id}/topics/{topic_id}/subtopics/{subtopic_id}")
def delete_subtopic(
    user_id: str = Path(..., description="User identifier"),
    topic_id: str = Path(..., description="Topic identifier"),
    subtopic_id: str = Path(..., description="Subtopic identifier"),
    tenant_id: str = Depends(get_tenant_id),
    insight_service: UserInsightsService = Depends(get_insight_service)
):
    """
    Delete a subtopic from a topic.
    
    Args:
        user_id: User identifier
        topic_id: Topic identifier
        subtopic_id: Subtopic identifier
        tenant_id: Tenant identifier
        insight_service: UserInsightsService instance
    
    Returns:
        Deletion status
    """
    success = insight_service.delete_subtopic(user_id, tenant_id, topic_id, subtopic_id)
    
    if not success:
        raise HTTPException(
            status_code=404, 
            detail=f"Subtopic not found with ID {subtopic_id} in topic {topic_id} for user {user_id}"
        )
    
    return {"status": "success", "message": f"Subtopic {subtopic_id} deleted"}


@router.delete("/{user_id}")
def delete_user_insight(
    user_id: str = Path(..., description="User identifier"),
    tenant_id: str = Depends(get_tenant_id),
    insight_service: UserInsightsService = Depends(get_insight_service)
):
    """
    Delete a user insight.
    
    Args:
        user_id: User identifier
        tenant_id: Tenant identifier
        insight_service: UserInsightsService instance
    
    Returns:
        Deletion status
    """
    success = insight_service.delete_user_insight(user_id, tenant_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"User insight not found for user {user_id}")
    
    return {"status": "success", "message": f"User insight deleted for user {user_id}"}


@router.get("/topics/{topic_name}/users", response_model=List[Dict[str, Any]])
def find_users_by_topic(
    topic_name: str = Path(..., description="Topic name"),
    page: int = Query(1, description="Page number"),
    page_size: int = Query(20, description="Page size"),
    tenant_id: str = Depends(get_tenant_id),
    insight_service: UserInsightsService = Depends(get_insight_service)
):
    """
    Find all users with a specific topic.
    
    Args:
        topic_name: Topic name to search for
        page: Page number
        page_size: Page size
        tenant_id: Tenant identifier
        insight_service: UserInsightsService instance
    
    Returns:
        List of users with their topic data
    """
    users = insight_service.find_users_by_topic(
        topic_name=topic_name,
        tenant_id=tenant_id,
        page=page,
        page_size=page_size
    )
    
    return users


@router.get("/topics/{topic_name}/all", response_model=List[Dict[str, Any]])
def get_topic_across_users(
    topic_name: str = Path(..., description="Topic name"),
    tenant_id: str = Depends(get_tenant_id),
    insight_service: UserInsightsService = Depends(get_insight_service)
):
    """
    Get a specific topic across all users.
    
    Args:
        topic_name: Topic name to search for
        tenant_id: Tenant identifier
        insight_service: UserInsightsService instance
    
    Returns:
        List of users with the specified topic
    """
    results = insight_service.get_topic_across_users(topic_name, tenant_id)
    
    return results


@router.get("/tenants", response_model=List[str])
def get_all_tenants(
    insight_service: UserInsightsService = Depends(get_insight_service)
):
    """
    Get all tenant IDs that have user insights.
    
    Args:
        insight_service: UserInsightsService instance
    
    Returns:
        List of tenant IDs
    """
    tenants = insight_service.get_all_tenants()
    
    return tenants


@router.get("/tenant/{tenant_id}/insights", response_model=List[Dict[str, Any]])
def find_all_for_tenant(
    tenant_id: str = Path(..., description="Tenant identifier"),
    page: int = Query(1, description="Page number"),
    page_size: int = Query(100, description="Page size"),
    insight_service: UserInsightsService = Depends(get_insight_service)
):
    """
    Find all UserInsights for a tenant.
    
    Args:
        tenant_id: Tenant identifier
        page: Page number
        page_size: Page size
        insight_service: UserInsightsService instance
    
    Returns:
        List of UserInsight data
    """
    insights = insight_service.find_all_for_tenant(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size
    )
    
    return insights 