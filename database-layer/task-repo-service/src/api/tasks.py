"""
Task API endpoints for the Task Repository Service.

This module provides the FastAPI router for task management API endpoints.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Path

from ..config.settings import get_settings, Settings
from ..models.task import Task, TaskCreate, TaskUpdate, TaskStatus
from ..repository.task_repository import TaskRepository

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# Dependency to get repository instance
async def get_repository(settings: Settings = Depends(get_settings)) -> TaskRepository:
    """
    Get task repository instance as a FastAPI dependency.
    
    Args:
        settings: Service settings
        
    Returns:
        TaskRepository instance
    """
    repo = TaskRepository(
        mongodb_uri=settings.mongodb_uri,
        database_name=settings.mongodb_database,
        collection_name=settings.mongodb_tasks_collection
    )
    await repo.connect()
    return repo


# API Key security
async def verify_api_key(
    x_api_key: str = Header(None),
    settings: Settings = Depends(get_settings)
):
    """
    Verify API key from header.
    
    Args:
        x_api_key: API key header
        settings: Service settings
        
    Raises:
        HTTPException: If API key is invalid
    """
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


@router.post("/api/v1/tasks", response_model=Dict[str, str], dependencies=[Depends(verify_api_key)])
async def create_task(
    task: TaskCreate,
    repository: TaskRepository = Depends(get_repository)
) -> Dict[str, str]:
    """
    Create a new task.
    
    Args:
        task: Task data to create
        repository: Task repository
        
    Returns:
        Dict with task ID
        
    Raises:
        HTTPException: If task creation fails
    """
    task_id = await repository.create_task(task)
    if task_id:
        return {"task_id": task_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to create task")


@router.get("/api/v1/tasks/{task_id}", response_model=Dict[str, Any], dependencies=[Depends(verify_api_key)])
async def get_task(
    task_id: str = Path(..., description="Task ID (ObjectId or task_id)"),
    repository: TaskRepository = Depends(get_repository)
) -> Dict[str, Any]:
    """
    Get a task by ID.
    
    Args:
        task_id: Task ID (ObjectId or task_id)
        repository: Task repository
        
    Returns:
        Task document
        
    Raises:
        HTTPException: If task not found
    """
    task = await repository.get_task(task_id)
    if task:
        return task
    else:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@router.put("/api/v1/tasks/{task_id}", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def update_task(
    update_data: TaskUpdate,
    task_id: str = Path(..., description="Task ID (ObjectId or task_id)"),
    repository: TaskRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Update a task.
    
    Args:
        update_data: Task data to update
        task_id: Task ID (ObjectId or task_id)
        repository: Task repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If task update fails
    """
    success = await repository.update_task(task_id, update_data)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found or update failed")


@router.delete("/api/v1/tasks/{task_id}", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def delete_task(
    task_id: str = Path(..., description="Task ID (ObjectId or task_id)"),
    repository: TaskRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Delete a task.
    
    Args:
        task_id: Task ID (ObjectId or task_id)
        repository: Task repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If task deletion fails
    """
    success = await repository.delete_task(task_id)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found or deletion failed")


@router.get("/api/v1/tasks", response_model=List[Dict[str, Any]], dependencies=[Depends(verify_api_key)])
async def get_pending_tasks(
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    service_tag: Optional[str] = Query(None, description="Filter by service tag"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of tasks to retrieve"),
    repository: TaskRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings)
) -> List[Dict[str, Any]]:
    """
    Get pending tasks for processing.
    
    Args:
        task_type: Optional task type filter
        tenant_id: Optional tenant ID filter
        service_tag: Optional service tag filter
        limit: Maximum number of tasks to retrieve
        repository: Task repository
        settings: Service settings
        
    Returns:
        List of pending task documents
    """
    tasks = await repository.get_pending_tasks(
        task_type=task_type,
        tenant_id=tenant_id,
        service_tag=service_tag,
        limit=min(limit, settings.default_task_limit)
    )
    return tasks


@router.post("/api/v1/tasks/{task_id}/claim", response_model=Dict[str, Any], dependencies=[Depends(verify_api_key)])
async def claim_task(
    task_id: str = Path(..., description="Task ID (ObjectId or task_id)"),
    processor_id: str = Query(..., description="ID of the processor claiming the task"),
    tenant_id: Optional[str] = Query(None, description="Optional tenant ID for verification"),
    repository: TaskRepository = Depends(get_repository)
) -> Dict[str, Any]:
    """
    Claim a task for processing.
    
    Args:
        task_id: Task ID (ObjectId or task_id)
        processor_id: ID of the processor claiming the task
        tenant_id: Optional tenant ID for verification
        repository: Task repository
        
    Returns:
        Updated task document
        
    Raises:
        HTTPException: If task claim fails
    """
    task = await repository.claim_task(task_id, processor_id, tenant_id)
    if task:
        return task
    else:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found or already claimed")


@router.post("/api/v1/tasks/{task_id}/complete", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def complete_task(
    results: Dict[str, Any],
    task_id: str = Path(..., description="Task ID (ObjectId or task_id)"),
    processor_id: Optional[str] = Query(None, description="Optional processor ID for verification"),
    repository: TaskRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Mark a task as completed with results.
    
    Args:
        results: Task results
        task_id: Task ID (ObjectId or task_id)
        processor_id: Optional processor ID for verification
        repository: Task repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If task completion fails
    """
    success = await repository.mark_task_completed(task_id, results, processor_id)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found or completion failed")


@router.post("/api/v1/tasks/{task_id}/fail", response_model=Dict[str, bool], dependencies=[Depends(verify_api_key)])
async def fail_task(
    error: Dict[str, str],
    task_id: str = Path(..., description="Task ID (ObjectId or task_id)"),
    processor_id: Optional[str] = Query(None, description="Optional processor ID for verification"),
    repository: TaskRepository = Depends(get_repository)
) -> Dict[str, bool]:
    """
    Mark a task as failed with error information.
    
    Args:
        error: Error information (must contain 'message' field)
        task_id: Task ID (ObjectId or task_id)
        processor_id: Optional processor ID for verification
        repository: Task repository
        
    Returns:
        Dict with success status
        
    Raises:
        HTTPException: If task failure marking fails
    """
    if "message" not in error:
        raise HTTPException(status_code=400, detail="Error must contain 'message' field")
        
    success = await repository.mark_task_failed(task_id, error["message"], processor_id)
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found or failure marking failed") 