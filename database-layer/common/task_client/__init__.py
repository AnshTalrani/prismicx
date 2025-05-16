"""
Task Repository Client Package

This package provides client functions for interacting with the Task Repository Service.
"""

from .client import (
    create_task,
    get_pending_tasks,
    claim_task,
    complete_task,
    fail_task,
    get_task,
    update_task_status
)

__all__ = [
    "create_task",
    "get_pending_tasks",
    "claim_task",
    "complete_task",
    "fail_task",
    "get_task",
    "update_task_status"
]