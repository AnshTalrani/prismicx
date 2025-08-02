"""
Task Mapper Module

This module provides mapping functions between the old context format
and the new task repository format.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)


class TaskMapper:
    """
    Mapper for converting between context and task models.
    
    This class provides methods to convert between the old MongoDB context
    format and the new task repository format.
    """
    
    @staticmethod
    def context_to_task(context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a context document to a task document.
        
        Args:
            context: Context document from MongoDB.
            
        Returns:
            Task document for the task repository.
        """
        # Extract context ID
        context_id = context.get("_id")
        if isinstance(context_id, str):
            task_id = context_id
        else:
            task_id = str(context_id)
        
        # Map status
        status_map = {
            "pending": "PENDING",
            "processing": "PROCESSING",
            "completed": "COMPLETED",
            "failed": "FAILED",
            "canceled": "CANCELED"
        }
        
        status = status_map.get(context.get("status", "pending"), "PENDING")
        
        # Create task document
        task = {
            "task_id": task_id,
            "task_type": "GENERATIVE",
            "status": status,
            "priority": context.get("metadata", {}).get("priority", 5),
            "tenant_id": context.get("organization_id"),
            "batch_id": context.get("batch_id"),
            "request": {
                "content": context.get("content", {}),
                "metadata": context.get("metadata", {})
            },
            "template": {
                "service_type": context.get("service_type", "default"),
                "template_data": {
                    "template_id": context.get("template_id")
                },
                "parameters": context.get("template_params", {})
            },
            "tags": {
                "service": context.get("service_type", "default"),
                "category": context.get("context_type", "general"),
                "custom_tags": {tag: "true" for tag in context.get("tags", [])}
            },
            "metadata": context.get("metadata", {})
        }
        
        # Add timestamps if available
        if "created_at" in context:
            task["created_at"] = context["created_at"]
        if "updated_at" in context:
            task["updated_at"] = context["updated_at"]
        if "processing_started_at" in context:
            task["processing_started_at"] = context["processing_started_at"]
        if "completed_at" in context:
            task["completed_at"] = context["completed_at"]
        
        # Add results if available
        if "result" in context:
            task["results"] = context["result"]
        
        # Add error if available
        if "error" in context:
            task["error"] = context["error"]
        
        return task
    
    @staticmethod
    def task_to_context(task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a task document to a context document.
        
        Args:
            task: Task document from the task repository.
            
        Returns:
            Context document for MongoDB.
        """
        # Extract task ID
        task_id = task.get("task_id")
        
        # Map status
        status_map = {
            "PENDING": "pending",
            "PROCESSING": "processing",
            "COMPLETED": "completed",
            "FAILED": "failed",
            "CANCELED": "canceled"
        }
        
        status = status_map.get(task.get("status", "PENDING"), "pending")
        
        # Create context document
        context = {
            "_id": task_id,
            "status": status,
            "service_type": task.get("template", {}).get("service_type", "default"),
            "organization_id": task.get("tenant_id"),
            "batch_id": task.get("batch_id"),
            "content": task.get("request", {}).get("content", {}),
            "metadata": task.get("request", {}).get("metadata", {}),
            "template_id": task.get("template", {}).get("template_data", {}).get("template_id"),
            "template_params": task.get("template", {}).get("parameters", {}),
            "context_type": task.get("tags", {}).get("category", "general")
        }
        
        # Extract custom tags
        custom_tags = task.get("tags", {}).get("custom_tags", {})
        context["tags"] = [tag for tag, value in custom_tags.items() if value == "true"]
        
        # Add timestamps if available
        if "created_at" in task:
            context["created_at"] = task["created_at"]
        if "updated_at" in task:
            context["updated_at"] = task["updated_at"]
        if "processing_started_at" in task:
            context["processing_started_at"] = task["processing_started_at"]
        if "completed_at" in task:
            context["completed_at"] = task["completed_at"]
        
        # Add results if available
        if "results" in task:
            context["result"] = task["results"]
        
        # Add error if available
        if "error" in task:
            context["error"] = task["error"]
        
        return context 