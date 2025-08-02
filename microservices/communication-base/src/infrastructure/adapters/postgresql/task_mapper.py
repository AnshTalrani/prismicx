"""
Task Mapper Module

This module provides mapping functionality between Task domain entities and database models.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, cast

from ....domain.entities.task import Task, TaskStatus, TaskPriority


class TaskMapper:
    """
    Mapper for converting between Task domain entities and database models.
    """
    
    @staticmethod
    def to_entity(db_model: Dict[str, Any]) -> Task:
        """
        Convert a database model to a Task domain entity.
        
        Args:
            db_model: The database model dictionary
            
        Returns:
            A Task domain entity
        """
        # Extract tags from JSON array if present
        tags = []
        if db_model.get("tags") and isinstance(db_model["tags"], str):
            try:
                tags = json.loads(db_model["tags"])
            except json.JSONDecodeError:
                tags = []
        elif db_model.get("tags") and isinstance(db_model["tags"], list):
            tags = db_model["tags"]
            
        # Extract data as dictionary
        data = {}
        if db_model.get("data") and isinstance(db_model["data"], str):
            try:
                data = json.loads(db_model["data"])
            except json.JSONDecodeError:
                data = {}
        elif db_model.get("data") and isinstance(db_model["data"], dict):
            data = db_model["data"]
            
        # Extract result as dictionary
        result = {}
        if db_model.get("result") and isinstance(db_model["result"], str):
            try:
                result = json.loads(db_model["result"])
            except json.JSONDecodeError:
                result = {}
        elif db_model.get("result") and isinstance(db_model["result"], dict):
            result = db_model["result"]
            
        # Create the Task entity
        return Task(
            id=db_model["id"],
            type=db_model["type"],
            status=TaskStatus(db_model["status"]),
            priority=TaskPriority(db_model["priority"]),
            tenant_id=db_model.get("tenant_id"),
            title=db_model.get("title"),
            description=db_model.get("description"),
            data=data,
            result=result,
            error=db_model.get("error"),
            worker_id=db_model.get("worker_id"),
            parent_task_id=db_model.get("parent_task_id"),
            created_at=db_model["created_at"],
            updated_at=db_model["updated_at"],
            scheduled_at=db_model.get("scheduled_at"),
            completed_at=db_model.get("completed_at"),
            failed_at=db_model.get("failed_at"),
            tags=tags
        )
    
    @staticmethod
    def to_db_model(task: Task) -> Dict[str, Any]:
        """
        Convert a Task domain entity to a database model.
        
        Args:
            task: The Task domain entity
            
        Returns:
            A dictionary representing the database model
        """
        db_model = {
            "id": task.id,
            "type": task.type,
            "status": task.status.value,
            "priority": task.priority.value,
            "tenant_id": task.tenant_id,
            "title": task.title,
            "description": task.description,
            "data": json.dumps(task.data) if task.data else None,
            "result": json.dumps(task.result) if task.result else None,
            "error": task.error,
            "worker_id": task.worker_id,
            "parent_task_id": task.parent_task_id,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "scheduled_at": task.scheduled_at,
            "completed_at": task.completed_at,
            "failed_at": task.failed_at,
            "tags": json.dumps(task.tags) if task.tags else None
        }
        
        # Remove None values to avoid overwriting with NULL in partial updates
        return {k: v for k, v in db_model.items() if v is not None} 