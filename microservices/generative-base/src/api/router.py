"""
API Router Module

This module defines the API routes for the generative base service.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, Body, Header, HTTPException, Query

from ..dependencies import get_db
from ..processing.processing_engine import ProcessingEngine
from ..common.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


def configure_routes(app, processing_engine: ProcessingEngine):
    """
    Configure API routes.
    
    Args:
        app: FastAPI application
        processing_engine: The processing engine
    """
    # Create a closure to pass the processing engine to the route handlers
    def get_processing_engine():
        return processing_engine
    
    # Register routes
    @router.post("/contexts", status_code=201)
    async def create_context(
        context: Dict[str, Any] = Body(...),
        x_batch_id: Optional[str] = Header(None, alias="X-Batch-ID"),
        engine=Depends(get_processing_engine),
        db=Depends(get_db)
    ):
        """
        Create a new context for processing.
        
        Args:
            context: The context to create
            x_batch_id: Optional batch identifier
            engine: Processing engine dependency
            db: Database session dependency
        """
        # Add batch_id to context if provided
        if x_batch_id:
            context["batch_id"] = x_batch_id
            
        # Add created_at timestamp
        from datetime import datetime
        context["created_at"] = datetime.utcnow().isoformat()
        context["status"] = "pending"
        
        # Use the database session
        try:
            # Insert into database
            async with db.begin():
                result = await db.execute(
                    "INSERT INTO contexts (data, status, created_at, batch_id) VALUES (:data, :status, :created_at, :batch_id) RETURNING id",
                    {
                        "data": context,
                        "status": "pending",
                        "created_at": context["created_at"],
                        "batch_id": context.get("batch_id")
                    }
                )
                context_id = await result.scalar()
                
            return {
                "id": context_id,
                "status": "pending",
                "message": "Context created successfully",
                "batch_id": context.get("batch_id")
            }
        except Exception as e:
            logger.error(f"Error creating context: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating context: {str(e)}")
    
    @router.post("/process", status_code=200)
    async def process_context(
        context: Dict[str, Any] = Body(...),
        x_batch_id: Optional[str] = Header(None, alias="X-Batch-ID"),
        engine=Depends(get_processing_engine)
    ):
        """
        Process a context immediately.
        
        Args:
            context: The context to process
            x_batch_id: Optional batch identifier
            engine: Processing engine dependency
        """
        # Add batch_id to context if provided
        if x_batch_id:
            context["batch_id"] = x_batch_id
            
        try:
            # Process the context
            result = await engine.process_context(context)
            return result
        except Exception as e:
            logger.error(f"Error processing context: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing context: {str(e)}")
    
    @router.post("/batch", status_code=200)
    async def process_batch(
        contexts: List[Dict[str, Any]] = Body(...),
        x_batch_id: Optional[str] = Header(None, alias="X-Batch-ID"),
        engine=Depends(get_processing_engine)
    ):
        """
        Process a batch of contexts immediately.
        
        Args:
            contexts: List of contexts to process
            x_batch_id: Optional batch identifier
            engine: Processing engine dependency
        """
        # Add batch_id to all contexts if provided
        if x_batch_id:
            for context in contexts:
                context["batch_id"] = x_batch_id
                
        try:
            # Process the batch
            result = await engine.process_batch(contexts)
            return result
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")
    
    @router.get("/contexts/{context_id}")
    async def get_context(
        context_id: str,
        db=Depends(get_db)
    ):
        """
        Get a context by ID.
        
        Args:
            context_id: The context ID
            db: Database session dependency
        """
        try:
            # Get context from database
            result = await db.fetch_one(
                "SELECT id, data, status, created_at, batch_id FROM contexts WHERE id = :id",
                {"id": context_id}
            )
            
            if not result:
                raise HTTPException(status_code=404, detail=f"Context {context_id} not found")
                
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting context {context_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting context: {str(e)}")
    
    @router.get("/batch/{batch_id}")
    async def get_batch_contexts(
        batch_id: str,
        status: Optional[str] = Query(None),
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        db=Depends(get_db)
    ):
        """
        Get contexts by batch ID.
        
        Args:
            batch_id: The batch ID
            status: Optional status filter
            limit: Maximum number of contexts to return
            offset: Number of contexts to skip
            db: Database session dependency
        """
        try:
            # Build query based on filters
            query = "SELECT id, data, status, created_at, batch_id FROM contexts WHERE batch_id = :batch_id"
            params = {"batch_id": batch_id}
            
            if status:
                query += " AND status = :status"
                params["status"] = status
                
            query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            
            # Get contexts from database
            results = await db.fetch(query, params)
            
            # Get total count
            count_result = await db.fetch_one(
                "SELECT COUNT(*) as count FROM contexts WHERE batch_id = :batch_id" +
                (" AND status = :status" if status else ""),
                {k: v for k, v in params.items() if k != "limit" and k != "offset"}
            )
            
            total_count = count_result["count"] if count_result else 0
            
            return {
                "batch_id": batch_id,
                "total_count": total_count,
                "returned_count": len(results),
                "contexts": results
            }
        except Exception as e:
            logger.error(f"Error getting contexts for batch {batch_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting batch contexts: {str(e)}")
    
    # Add the router to the app
    app.include_router(router, prefix="/api")
    
    return app 