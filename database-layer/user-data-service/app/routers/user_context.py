"""
User Context Router

Router for user context operations including system users and campaign users.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

from ..services.user_context_service import UserContextService
from ..dependencies import get_user_context_service

# Define Pydantic models
class UserContextBase(BaseModel):
    """Base model for user context data."""
    user_id: Optional[str] = Field(None, description="User identifier (generated if not provided)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional user data")

class SystemUserContext(UserContextBase):
    """Model for system user context data."""
    tenant_id: str = Field(..., description="Tenant identifier")

class CampaignUserContext(UserContextBase):
    """Model for campaign user context data."""
    campaign_id: str = Field(..., description="Campaign identifier")
    ttl_days: Optional[int] = Field(None, description="Custom TTL in days")

class UserContextUpdate(BaseModel):
    """Model for user context updates."""
    metadata: Dict[str, Any] = Field(..., description="Updated metadata")

class MigrationRequest(BaseModel):
    """Model for migration requests."""
    user_id: str = Field(..., description="User identifier")
    campaign_id: str = Field(..., description="Source campaign identifier")
    tenant_id: str = Field(..., description="Target tenant identifier")

class TTLUpdateRequest(BaseModel):
    """Model for TTL update requests."""
    ttl_days: int = Field(..., description="New TTL in days")

# Create router
router = APIRouter(
    prefix="/api/v1/user-context",
    tags=["user-context"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{user_id}")
async def get_user_context(
    user_id: str = Path(..., description="User identifier"),
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for system users"),
    campaign_id: Optional[str] = Query(None, description="Campaign identifier for campaign users"),
    service: UserContextService = Depends(get_user_context_service)
):
    """
    Get user context by user ID.
    
    Prioritizes system users over campaign users.
    """
    if not tenant_id and not campaign_id:
        raise HTTPException(status_code=400, detail="Either tenant_id or campaign_id must be provided")
    
    user_data = await service.get_user_context(user_id, tenant_id, campaign_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user_data

@router.post("/system", status_code=201)
async def create_system_user(
    user_data: SystemUserContext,
    service: UserContextService = Depends(get_user_context_service)
):
    """Create or update a system user."""
    try:
        user_id = await service.save_user_context(
            user_data.dict(exclude_unset=True),
            tenant_id=user_data.tenant_id
        )
        return {"user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaign", status_code=201)
async def create_campaign_user(
    user_data: CampaignUserContext,
    service: UserContextService = Depends(get_user_context_service)
):
    """Create or update a campaign user."""
    try:
        user_id = await service.save_user_context(
            user_data.dict(exclude={"campaign_id", "ttl_days"}),
            campaign_id=user_data.campaign_id,
            ttl_days=user_data.ttl_days
        )
        return {"user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}")
async def update_user_context(
    user_id: str,
    update_data: UserContextUpdate,
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for system users"),
    campaign_id: Optional[str] = Query(None, description="Campaign identifier for campaign users"),
    service: UserContextService = Depends(get_user_context_service)
):
    """Update user context metadata."""
    if not tenant_id and not campaign_id:
        raise HTTPException(status_code=400, detail="Either tenant_id or campaign_id must be provided")
    
    success = await service.update_user_context(
        user_id,
        update_data.dict()["metadata"],
        tenant_id,
        campaign_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found or update failed")
    
    return {"status": "success", "user_id": user_id}

@router.delete("/{user_id}")
async def delete_user_context(
    user_id: str,
    tenant_id: Optional[str] = Query(None, description="Tenant identifier for system users"),
    campaign_id: Optional[str] = Query(None, description="Campaign identifier for campaign users"),
    service: UserContextService = Depends(get_user_context_service)
):
    """Delete user context."""
    if not tenant_id and not campaign_id:
        raise HTTPException(status_code=400, detail="Either tenant_id or campaign_id must be provided")
    
    success = await service.delete_user_context(user_id, tenant_id, campaign_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found or deletion failed")
    
    return {"status": "success", "user_id": user_id}

@router.post("/migrate")
async def migrate_user_to_system(
    migration: MigrationRequest,
    service: UserContextService = Depends(get_user_context_service)
):
    """Migrate a campaign user to system users."""
    success = await service.migrate_to_system(
        migration.user_id,
        migration.campaign_id,
        migration.tenant_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found or migration failed")
    
    return {"status": "success", "user_id": migration.user_id}

@router.get("/campaign/{campaign_id}")
async def get_campaign_users(
    campaign_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    service: UserContextService = Depends(get_user_context_service)
):
    """Get all users for a campaign."""
    users = await service.get_all_campaign_users(campaign_id, page, page_size)
    return {"campaign_id": campaign_id, "users": users, "page": page, "page_size": page_size}

@router.get("/system/{tenant_id}")
async def get_system_users(
    tenant_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    service: UserContextService = Depends(get_user_context_service)
):
    """Get all system users for a tenant."""
    users = await service.get_all_system_users(tenant_id, page, page_size)
    return {"tenant_id": tenant_id, "users": users, "page": page, "page_size": page_size}

@router.put("/campaign/{campaign_id}/user/{user_id}/ttl")
async def update_campaign_user_ttl(
    campaign_id: str,
    user_id: str,
    ttl_request: TTLUpdateRequest,
    service: UserContextService = Depends(get_user_context_service)
):
    """Update the TTL for a campaign user."""
    success = await service.update_campaign_ttl(user_id, campaign_id, ttl_request.ttl_days)
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found or update failed")
    
    return {"status": "success", "user_id": user_id, "campaign_id": campaign_id} 