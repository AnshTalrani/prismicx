#!/usr/bin/env python3
"""
Minimal Task Repository Service

A simplified version of the Task Repository Service for standalone testing,
bypassing complex import issues while maintaining core functionality.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Header, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

# In-memory storage for testing (simulating MongoDB)
tasks_storage = {}
task_counter = 1

# Task Status Enum
class TaskStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

# Pydantic Models
class TaskRequest(BaseModel):
    content: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class TaskTemplate(BaseModel):
    service_type: str
    template_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)

class TaskTags(BaseModel):
    service: Optional[str] = None
    source: Optional[str] = None
    category: Optional[str] = None
    custom_tags: Optional[Dict[str, str]] = Field(default_factory=dict)

class TaskCreate(BaseModel):
    task_type: str
    request: TaskRequest
    template: TaskTemplate
    tags: TaskTags = Field(default_factory=TaskTags)
    priority: Optional[int] = 5
    tenant_id: Optional[str] = None
    batch_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[int] = None
    processor_id: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class Task(BaseModel):
    task_id: str
    task_type: str
    status: str = TaskStatus.PENDING
    priority: int = 5
    tenant_id: Optional[str] = None
    processor_id: Optional[str] = None
    batch_id: Optional[str] = None
    request: TaskRequest
    template: TaskTemplate
    tags: TaskTags
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    processing_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Helper functions
def generate_task_id() -> str:
    """Generate a unique task ID."""
    global task_counter
    task_id = f"task_{task_counter}_{int(time.time())}"
    task_counter += 1
    return task_id

def create_task_document(task_data: TaskCreate) -> Task:
    """Create a task document from task creation data."""
    task_id = generate_task_id()
    
    return Task(
        task_id=task_id,
        task_type=task_data.task_type,
        status=TaskStatus.PENDING,
        priority=task_data.priority or 5,
        tenant_id=task_data.tenant_id,
        batch_id=task_data.batch_id,
        request=task_data.request,
        template=task_data.template,
        tags=task_data.tags,
        metadata=task_data.metadata,
        created_at=datetime.utcnow()
    )

# API Key verification
async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key from header."""
    if x_api_key != "dev_api_key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI application lifespan manager."""
    print("🚀 Task Repository Service starting up...")
    
    # Initialize some sample tasks for testing
    sample_tasks = [
        TaskCreate(
            task_type="GENERATIVE",
            request=TaskRequest(
                content={"text": "Sample generative task"},
                metadata={"user_id": "sample_user"}
            ),
            template=TaskTemplate(
                service_type="GENERATIVE",
                parameters={"model": "gpt-4"}
            ),
            tags=TaskTags(service="generative-service", source="sample")
        ),
        TaskCreate(
            task_type="ANALYSIS",
            request=TaskRequest(
                content={"data": "Sample analysis data"},
                metadata={"analysis_type": "sentiment"}
            ),
            template=TaskTemplate(
                service_type="ANALYSIS",
                parameters={"algorithm": "ml-classifier"}
            ),
            tags=TaskTags(service="analysis-service", source="sample")
        )
    ]
    
    for sample_task in sample_tasks:
        task = create_task_document(sample_task)
        tasks_storage[task.task_id] = task
    
    print(f"✅ Initialized with {len(tasks_storage)} sample tasks")
    
    yield
    
    print("🛑 Task Repository Service shutting down...")

# Create FastAPI application
app = FastAPI(
    title="Task Repository Service",
    description="Minimal API for managing tasks in the central task repository",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "task-repo-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "tasks_count": len(tasks_storage),
        "components": {
            "api": "healthy",
            "storage": "healthy",
            "memory": "healthy"
        }
    }

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "service": "Task Repository Service",
        "version": "1.0.0",
        "description": "Centralized task management API",
        "endpoints": {
            "health": "/health",
            "tasks": "/api/v1/tasks",
            "docs": "/docs"
        }
    }

# Create task endpoint
@app.post("/api/v1/tasks", status_code=201, tags=["tasks"])
async def create_task(
    task_data: TaskCreate,
    api_key: str = Header(None, alias="X-API-Key")
):
    """Create a new task."""
    await verify_api_key(api_key)
    
    try:
        task = create_task_document(task_data)
        tasks_storage[task.task_id] = task
        
        return {
            "task_id": task.task_id,
            "status": "created",
            "message": "Task created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

# Get task by ID endpoint
@app.get("/api/v1/tasks/{task_id}", tags=["tasks"])
async def get_task(
    task_id: str = Path(..., description="Task ID"),
    api_key: str = Header(None, alias="X-API-Key")
):
    """Get a task by ID."""
    await verify_api_key(api_key)
    
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks_storage[task_id]
    return task.model_dump()

# Update task endpoint
@app.put("/api/v1/tasks/{task_id}", tags=["tasks"])
async def update_task(
    update_data: TaskUpdate,
    task_id: str = Path(..., description="Task ID"),
    api_key: str = Header(None, alias="X-API-Key")
):
    """Update a task."""
    await verify_api_key(api_key)
    
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks_storage[task_id]
    
    # Update fields
    if update_data.status:
        task.status = update_data.status
    if update_data.priority is not None:
        task.priority = update_data.priority
    if update_data.processor_id:
        task.processor_id = update_data.processor_id
    if update_data.results:
        task.results = update_data.results
    if update_data.error:
        task.error = update_data.error
    if update_data.metadata:
        task.metadata.update(update_data.metadata)
    
    task.updated_at = datetime.utcnow()
    
    return {"success": True, "message": "Task updated successfully"}

# Delete task endpoint
@app.delete("/api/v1/tasks/{task_id}", tags=["tasks"])
async def delete_task(
    task_id: str = Path(..., description="Task ID"),
    api_key: str = Header(None, alias="X-API-Key")
):
    """Delete a task."""
    await verify_api_key(api_key)
    
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del tasks_storage[task_id]
    return {"success": True, "message": "Task deleted successfully"}

# Get pending tasks endpoint
@app.get("/api/v1/tasks", tags=["tasks"])
async def get_pending_tasks(
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    service_tag: Optional[str] = Query(None, description="Filter by service tag"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of tasks to retrieve"),
    api_key: str = Header(None, alias="X-API-Key")
):
    """Get pending tasks for processing."""
    await verify_api_key(api_key)
    
    # Filter tasks based on criteria
    filtered_tasks = []
    for task in tasks_storage.values():
        # Apply filters
        if task_type and task.task_type != task_type:
            continue
        if tenant_id and task.tenant_id != tenant_id:
            continue
        if service_tag and task.tags.service != service_tag:
            continue
        
        filtered_tasks.append(task.model_dump())
    
    # Sort by priority and creation time
    filtered_tasks.sort(key=lambda x: (x.get('priority', 5), x.get('created_at')))
    
    # Apply limit
    limited_tasks = filtered_tasks[:limit]
    
    return {
        "tasks": limited_tasks,
        "total": len(filtered_tasks),
        "limit": limit,
        "filters": {
            "task_type": task_type,
            "tenant_id": tenant_id,
            "service_tag": service_tag
        }
    }

# Claim task endpoint
@app.post("/api/v1/tasks/{task_id}/claim", tags=["tasks"])
async def claim_task(
    task_id: str = Path(..., description="Task ID"),
    processor_id: str = Query(..., description="ID of the processor claiming the task"),
    tenant_id: Optional[str] = Query(None, description="Optional tenant ID for verification"),
    api_key: str = Header(None, alias="X-API-Key")
):
    """Claim a task for processing."""
    await verify_api_key(api_key)
    
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks_storage[task_id]
    
    # Check if task is already claimed
    if task.status != TaskStatus.PENDING:
        raise HTTPException(status_code=409, detail=f"Task is already {task.status}")
    
    # Verify tenant if provided
    if tenant_id and task.tenant_id and task.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID mismatch")
    
    # Claim the task
    task.status = TaskStatus.PROCESSING
    task.processor_id = processor_id
    task.processing_started_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    
    return task.model_dump()

# Complete task endpoint
@app.post("/api/v1/tasks/{task_id}/complete", tags=["tasks"])
async def complete_task(
    results: Dict[str, Any],
    task_id: str = Path(..., description="Task ID"),
    processor_id: Optional[str] = Query(None, description="Optional processor ID for verification"),
    api_key: str = Header(None, alias="X-API-Key")
):
    """Mark a task as completed with results."""
    await verify_api_key(api_key)
    
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks_storage[task_id]
    
    # Verify processor if provided
    if processor_id and task.processor_id and task.processor_id != processor_id:
        raise HTTPException(status_code=403, detail="Processor ID mismatch")
    
    # Complete the task
    task.status = TaskStatus.COMPLETED
    task.results = results
    task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    
    return {"success": True, "message": "Task completed successfully"}

# Fail task endpoint
@app.post("/api/v1/tasks/{task_id}/fail", tags=["tasks"])
async def fail_task(
    error: Dict[str, str],
    task_id: str = Path(..., description="Task ID"),
    processor_id: Optional[str] = Query(None, description="Optional processor ID for verification"),
    api_key: str = Header(None, alias="X-API-Key")
):
    """Mark a task as failed with error information."""
    await verify_api_key(api_key)
    
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks_storage[task_id]
    
    # Verify processor if provided
    if processor_id and task.processor_id and task.processor_id != processor_id:
        raise HTTPException(status_code=403, detail="Processor ID mismatch")
    
    # Fail the task
    task.status = TaskStatus.FAILED
    task.error = error.get("error", error.get("message", "Unknown error"))
    task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    
    return {"success": True, "message": "Task marked as failed"}

# Statistics endpoint
@app.get("/api/v1/stats", tags=["stats"])
async def get_stats(
    api_key: str = Header(None, alias="X-API-Key")
):
    """Get task repository statistics."""
    await verify_api_key(api_key)
    
    # Calculate statistics
    total_tasks = len(tasks_storage)
    status_counts = {}
    type_counts = {}
    
    for task in tasks_storage.values():
        # Count by status
        status = task.status
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by type
        task_type = task.task_type
        type_counts[task_type] = type_counts.get(task_type, 0) + 1
    
    return {
        "total_tasks": total_tasks,
        "status_distribution": status_counts,
        "type_distribution": type_counts,
        "timestamp": datetime.utcnow().isoformat()
    }

# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "minimal_task_service:app",
        host="0.0.0.0",
        port=8503,
        reload=True,
        log_level="info"
    )
