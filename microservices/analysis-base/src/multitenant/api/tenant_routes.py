"""
Tenant Routes Module

This module provides API endpoints for demonstrating multi-tenant functionality.
"""

import logging
import structlog
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Body

from ...database.database import database
from ...auth.middleware import require_permission, require_role, get_current_user
from ..context.tenant_context import get_current_tenant_id
from ..tenant.client import tenant_client

# Configure structured logging
logger = structlog.get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/tenant-aware", tags=["tenant-aware"])


@router.get("/current-tenant")
async def get_current_tenant():
    """Get the current tenant from context."""
    tenant_id = get_current_tenant_id()
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Get tenant info from service
    tenant_info = await tenant_client.get_tenant_info(tenant_id)
    
    return {
        "tenant_id": tenant_id,
        "info": tenant_info
    }


@router.get("/analysis-results")
@require_permission("analysis:read")
async def get_analysis_results(
    limit: int = 10,
    offset: int = 0,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get analysis results for the current tenant.
    Requires the 'analysis:read' permission.
    """
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    try:
        # Use the database with tenant context
        rows = await database.fetch(
            """
            SELECT id, user_id, content, results, created_at, updated_at
            FROM analysis_results
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            tenant_id, limit, offset
        )
        
        # Convert rows to dictionaries
        results = [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "content": row["content"],
                "results": row["results"],
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat()
            }
            for row in rows
        ]
        
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(
            "Failed to fetch analysis results",
            tenant_id=tenant_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching analysis results: {str(e)}"
        )


@router.post("/analysis-results")
@require_permission("analysis:write")
async def create_analysis_result(
    data: Dict[str, Any] = Body(...),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new analysis result for the current tenant.
    Requires the 'analysis:write' permission.
    """
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Validate required fields
    if "content" not in data:
        raise HTTPException(status_code=400, detail="Content is required")
    if "results" not in data:
        raise HTTPException(status_code=400, detail="Results are required")
    
    try:
        # Insert into database using tenant context
        result_id = await database.fetchval(
            """
            INSERT INTO analysis_results (tenant_id, user_id, content, results)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            tenant_id,
            user.get("id"),
            data.get("content"),
            data.get("results")
        )
        
        return {
            "id": result_id,
            "message": "Analysis result created successfully"
        }
    except Exception as e:
        logger.error(
            "Failed to create analysis result",
            tenant_id=tenant_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error creating analysis result: {str(e)}"
        )


@router.post("/tenants/{tenant_id}/schema")
@require_role("admin")
async def create_tenant_schema(
    tenant_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a schema for a tenant.
    Requires the 'admin' role.
    """
    # Check if tenant exists in tenant management service
    tenant_exists = await tenant_client.validate_tenant(tenant_id)
    if not tenant_exists:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Create schema in database
    success = await database.create_tenant_schema(tenant_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to create tenant schema"
        )
    
    return {
        "tenant_id": tenant_id,
        "message": "Tenant schema created successfully"
    }


@router.delete("/tenants/{tenant_id}/schema")
@require_role("admin")
async def delete_tenant_schema(
    tenant_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a schema for a tenant.
    Requires the 'admin' role.
    """
    # Delete schema from database
    success = await database.delete_tenant_schema(tenant_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete tenant schema"
        )
    
    return {
        "tenant_id": tenant_id,
        "message": "Tenant schema deleted successfully"
    } 