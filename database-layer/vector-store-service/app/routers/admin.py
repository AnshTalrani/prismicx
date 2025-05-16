"""
Administrative endpoints for the vector store service.

These endpoints require admin privileges and are used for
maintenance, monitoring, and system management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Dict, Optional, Any
from pymongo.database import Database
import os
import logging
import shutil
import time
import json

from dependencies import get_mongodb, get_validated_tenant_id
from services.vector_store_service import VectorStoreService, VECTOR_STORE_DIR

router = APIRouter()
logger = logging.getLogger("vector-store-service")

def get_admin_service(db: Database = Depends(get_mongodb)) -> VectorStoreService:
    """Get vector store service instance with system database."""
    return VectorStoreService(db)

@router.post("/rebuild-indexes")
async def rebuild_indexes(
    service: VectorStoreService = Depends(get_admin_service)
):
    """
    Rebuild database indexes.
    
    This endpoint recreates all indexes used by the vector store service.
    """
    try:
        service._ensure_indexes()
        return {
            "status": "success",
            "message": "Database indexes rebuilt successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rebuild indexes: {str(e)}"
        )

@router.post("/clear-tenant-data/{tenant_id}")
async def clear_tenant_data(
    tenant_id: str,
    background_tasks: BackgroundTasks,
    service: VectorStoreService = Depends(get_admin_service)
):
    """
    Clear all vector store data for a specific tenant.
    
    This endpoint removes all vector stores and documents for the specified tenant.
    This is a destructive operation and should be used with caution.
    """
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID is required"
        )
        
    # Define background task to clear data
    def _clear_tenant_data(tenant_id: str):
        # Remove vector store files
        tenant_dir = os.path.join(VECTOR_STORE_DIR, tenant_id)
        if os.path.exists(tenant_dir):
            try:
                shutil.rmtree(tenant_dir)
                logger.info(f"Removed vector store directory for tenant: {tenant_id}")
            except Exception as e:
                logger.error(f"Failed to remove vector store directory: {e}")
        
        # Remove database records
        try:
            db = service.db
            # Remove store metadata
            db.vector_stores.delete_many({"tenant_id": tenant_id})
            # Remove document metadata
            db.vector_documents.delete_many({"metadata.tenant_id": tenant_id})
            logger.info(f"Removed database records for tenant: {tenant_id}")
        except Exception as e:
            logger.error(f"Failed to remove database records: {e}")
    
    # Schedule the task to run in the background
    background_tasks.add_task(_clear_tenant_data, tenant_id)
    
    return {
        "status": "accepted",
        "message": f"Clearing data for tenant {tenant_id} has been scheduled"
    }

@router.get("/stats")
async def get_stats(
    service: VectorStoreService = Depends(get_admin_service)
):
    """
    Get statistics about the vector store service.
    
    Returns information about:
    - Total number of stores
    - Total number of documents
    - Storage usage
    - Tenant usage statistics
    """
    stats = {
        "total_stores": 0,
        "total_documents": 0,
        "storage_bytes": 0,
        "tenants": {},
        "store_types": {},
        "embedding_models": {}
    }
    
    try:
        # Count stores
        stats["total_stores"] = await service.db.vector_stores.count_documents({})
        
        # Count documents
        stats["total_documents"] = await service.db.vector_documents.count_documents({})
        
        # Get tenant stats
        pipeline = [
            {"$group": {
                "_id": "$tenant_id",
                "store_count": {"$sum": 1}
            }}
        ]
        async for result in service.db.vector_stores.aggregate(pipeline):
            tenant_id = result["_id"] or "system"
            stats["tenants"][tenant_id] = {
                "store_count": result["store_count"],
                "document_count": 0
            }
            
        # Get document counts by tenant
        pipeline = [
            {"$group": {
                "_id": "$metadata.tenant_id",
                "doc_count": {"$sum": 1}
            }}
        ]
        async for result in service.db.vector_documents.aggregate(pipeline):
            tenant_id = result["_id"] or "system"
            if tenant_id in stats["tenants"]:
                stats["tenants"][tenant_id]["document_count"] = result["doc_count"]
            else:
                stats["tenants"][tenant_id] = {
                    "store_count": 0,
                    "document_count": result["doc_count"]
                }
                
        # Get store types
        pipeline = [
            {"$group": {
                "_id": "$metadata.store_type",
                "count": {"$sum": 1}
            }}
        ]
        async for result in service.db.vector_stores.aggregate(pipeline):
            stats["store_types"][result["_id"]] = result["count"]
            
        # Get embedding models
        pipeline = [
            {"$group": {
                "_id": "$metadata.embedding_model",
                "count": {"$sum": 1}
            }}
        ]
        async for result in service.db.vector_stores.aggregate(pipeline):
            stats["embedding_models"][result["_id"]] = result["count"]
            
        # Calculate storage usage
        if os.path.exists(VECTOR_STORE_DIR):
            for root, dirs, files in os.walk(VECTOR_STORE_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    stats["storage_bytes"] += os.path.getsize(file_path)
        
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        ) 