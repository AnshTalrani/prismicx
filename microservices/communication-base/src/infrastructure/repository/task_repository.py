"""
Task Repository Module

This module provides a repository implementation for task storage and retrieval.
It handles database operations for Tasks, including CRUD operations and advanced queries.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from sqlalchemy import text, exc
from sqlalchemy.engine import Connection

from src.domain.entities.task import Task, TaskStatus, TaskPriority
from src.infrastructure.repository.task_mapper import TaskMapper

logger = logging.getLogger(__name__)

class TaskRepository:
    """
    Repository for Task entity persistence and retrieval.
    
    This class provides methods to create, read, update, and delete tasks in the database,
    as well as search and filter tasks based on various criteria.
    """
    
    def __init__(self, connection: Connection):
        """
        Initialize the repository with a database connection.
        
        Args:
            connection: SQLAlchemy database connection
        """
        self.connection = connection
    
    def create(self, task: Task) -> Task:
        """
        Create a new task in the database.
        
        Args:
            task: Task entity to create
            
        Returns:
            The created Task with database-generated ID
            
        Raises:
            Exception: If task creation fails
        """
        try:
            # Generate UUID if not provided
            if not task.id:
                task.id = str(uuid.uuid4())
            
            # Set creation time if not set
            if not task.created_at:
                task.created_at = datetime.utcnow()
            
            # Set update time
            task.updated_at = datetime.utcnow()
            
            # Convert domain entity to dict for db
            task_dict = TaskMapper.to_api(task)
            
            # Convert tags list to JSON array if present
            tags = task_dict.get("tags")
            if tags is not None:
                task_dict["tags"] = tags
            
            # Insert task into database
            query = text("""
                INSERT INTO tasks (
                    id, tenant_id, type, status, priority, data, 
                    created_at, updated_at, scheduled_for, completed_at,
                    error, retry_count, worker_id, parent_task_id, result, tags
                ) VALUES (
                    :id, :tenant_id, :type, :status, :priority, :data::jsonb, 
                    :created_at, :updated_at, :scheduled_for, :completed_at,
                    :error, :retry_count, :worker_id, :parent_task_id, :result::jsonb, :tags::jsonb
                ) RETURNING *
            """)
            
            result = self.connection.execute(query, task_dict)
            created_task_data = dict(result.fetchone())
            
            logger.info(f"Created task with ID {created_task_data['id']}")
            return TaskMapper.to_domain(created_task_data)
            
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error creating task: {str(e)}")
            raise Exception(f"Failed to create task: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            raise
    
    def get_by_id(self, task_id: str, tenant_id: Optional[str] = None) -> Optional[Task]:
        """
        Get a task by its ID.
        
        Args:
            task_id: ID of the task to retrieve
            tenant_id: Optional tenant ID for multi-tenancy filtering
            
        Returns:
            Task if found, None otherwise
            
        Raises:
            Exception: If database query fails
        """
        try:
            query_params = {"id": task_id}
            
            query = """
                SELECT * FROM tasks 
                WHERE id = :id
            """
            
            # Add tenant filtering if provided
            if tenant_id:
                query += " AND tenant_id = :tenant_id"
                query_params["tenant_id"] = tenant_id
            
            result = self.connection.execute(text(query), query_params)
            row = result.fetchone()
            
            if not row:
                logger.info(f"Task not found with ID {task_id}")
                return None
                
            task_data = dict(row)
            return TaskMapper.to_domain(task_data)
            
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error retrieving task {task_id}: {str(e)}")
            raise Exception(f"Failed to retrieve task: {str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving task {task_id}: {str(e)}")
            raise
    
    def update(self, task: Task) -> Task:
        """
        Update an existing task in the database.
        
        Args:
            task: Task entity with updated values
            
        Returns:
            The updated Task
            
        Raises:
            Exception: If task update fails or task not found
        """
        try:
            # Set update time
            task.updated_at = datetime.utcnow()
            
            # Convert domain entity to dict for db
            task_dict = TaskMapper.to_api(task)
            
            # Update task in database
            query = text("""
                UPDATE tasks SET
                    tenant_id = :tenant_id,
                    type = :type,
                    status = :status,
                    priority = :priority,
                    data = :data::jsonb,
                    updated_at = :updated_at,
                    scheduled_for = :scheduled_for,
                    completed_at = :completed_at,
                    error = :error,
                    retry_count = :retry_count,
                    worker_id = :worker_id,
                    parent_task_id = :parent_task_id,
                    result = :result::jsonb,
                    tags = :tags::jsonb
                WHERE id = :id
                RETURNING *
            """)
            
            result = self.connection.execute(query, task_dict)
            updated_row = result.fetchone()
            
            if not updated_row:
                logger.error(f"Task not found for update: {task.id}")
                raise Exception(f"Task not found for update: {task.id}")
                
            updated_task_data = dict(updated_row)
            logger.info(f"Updated task with ID {updated_task_data['id']}")
            
            return TaskMapper.to_domain(updated_task_data)
            
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error updating task {task.id}: {str(e)}")
            raise Exception(f"Failed to update task: {str(e)}")
        except Exception as e:
            logger.error(f"Error updating task {task.id}: {str(e)}")
            raise
    
    def delete(self, task_id: str, tenant_id: Optional[str] = None) -> bool:
        """
        Delete a task from the database.
        
        Args:
            task_id: ID of the task to delete
            tenant_id: Optional tenant ID for multi-tenancy filtering
            
        Returns:
            True if deletion successful, False if task not found
            
        Raises:
            Exception: If deletion fails
        """
        try:
            query_params = {"id": task_id}
            
            query = """
                DELETE FROM tasks 
                WHERE id = :id
            """
            
            # Add tenant filtering if provided
            if tenant_id:
                query += " AND tenant_id = :tenant_id"
                query_params["tenant_id"] = tenant_id
            
            result = self.connection.execute(text(query), query_params)
            
            if result.rowcount > 0:
                logger.info(f"Deleted task with ID {task_id}")
                return True
            else:
                logger.info(f"Task not found for deletion: {task_id}")
                return False
                
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error deleting task {task_id}: {str(e)}")
            raise Exception(f"Failed to delete task: {str(e)}")
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {str(e)}")
            raise
    
    def find_by_status(
        self, 
        status: TaskStatus, 
        tenant_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """
        Find tasks by status.
        
        Args:
            status: Task status to filter by
            tenant_id: Optional tenant ID for multi-tenancy filtering
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of tasks matching the criteria
            
        Raises:
            Exception: If query fails
        """
        try:
            status_str = TaskMapper._status_to_api.get(status)
            query_params = {
                "status": status_str,
                "limit": limit,
                "offset": offset
            }
            
            query = """
                SELECT * FROM tasks 
                WHERE status = :status
            """
            
            # Add tenant filtering if provided
            if tenant_id:
                query += " AND tenant_id = :tenant_id"
                query_params["tenant_id"] = tenant_id
            
            query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            
            result = self.connection.execute(text(query), query_params)
            
            tasks_data = [dict(row) for row in result]
            return TaskMapper.to_domain_list(tasks_data)
            
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error finding tasks by status {status}: {str(e)}")
            raise Exception(f"Failed to find tasks by status: {str(e)}")
        except Exception as e:
            logger.error(f"Error finding tasks by status {status}: {str(e)}")
            raise
    
    def find_by_type(
        self, 
        task_type: str, 
        tenant_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """
        Find tasks by type.
        
        Args:
            task_type: Task type to filter by
            tenant_id: Optional tenant ID for multi-tenancy filtering
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of tasks matching the criteria
            
        Raises:
            Exception: If query fails
        """
        try:
            query_params = {
                "type": task_type,
                "limit": limit,
                "offset": offset
            }
            
            query = """
                SELECT * FROM tasks 
                WHERE type = :type
            """
            
            # Add tenant filtering if provided
            if tenant_id:
                query += " AND tenant_id = :tenant_id"
                query_params["tenant_id"] = tenant_id
            
            query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            
            result = self.connection.execute(text(query), query_params)
            
            tasks_data = [dict(row) for row in result]
            return TaskMapper.to_domain_list(tasks_data)
            
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error finding tasks by type {task_type}: {str(e)}")
            raise Exception(f"Failed to find tasks by type: {str(e)}")
        except Exception as e:
            logger.error(f"Error finding tasks by type {task_type}: {str(e)}")
            raise
    
    def find_pending_scheduled_tasks(
        self, 
        current_time: datetime,
        tenant_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Task]:
        """
        Find pending scheduled tasks that are due for execution.
        
        Args:
            current_time: Current time to compare against scheduled_for
            tenant_id: Optional tenant ID for multi-tenancy filtering
            limit: Maximum number of results to return
            
        Returns:
            List of scheduled tasks ready for execution
            
        Raises:
            Exception: If query fails
        """
        try:
            query_params = {
                "current_time": current_time.isoformat(),
                "status": TaskMapper._status_to_api.get(TaskStatus.SCHEDULED),
                "limit": limit
            }
            
            query = """
                SELECT * FROM tasks 
                WHERE status = :status
                AND scheduled_for <= :current_time
            """
            
            # Add tenant filtering if provided
            if tenant_id:
                query += " AND tenant_id = :tenant_id"
                query_params["tenant_id"] = tenant_id
            
            query += " ORDER BY priority DESC, scheduled_for ASC LIMIT :limit"
            
            result = self.connection.execute(text(query), query_params)
            
            tasks_data = [dict(row) for row in result]
            return TaskMapper.to_domain_list(tasks_data)
            
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error finding pending scheduled tasks: {str(e)}")
            raise Exception(f"Failed to find pending scheduled tasks: {str(e)}")
        except Exception as e:
            logger.error(f"Error finding pending scheduled tasks: {str(e)}")
            raise
    
    def find_by_tag(
        self, 
        tag: str, 
        tenant_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """
        Find tasks by tag.
        
        Args:
            tag: Tag to search for
            tenant_id: Optional tenant ID for multi-tenancy filtering
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of tasks with the specified tag
            
        Raises:
            Exception: If query fails
        """
        try:
            query_params = {
                "tag": tag,
                "limit": limit,
                "offset": offset
            }
            
            query = """
                SELECT * FROM tasks 
                WHERE tags @> :tag::jsonb
            """
            
            # Add tenant filtering if provided
            if tenant_id:
                query += " AND tenant_id = :tenant_id"
                query_params["tenant_id"] = tenant_id
            
            query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            
            result = self.connection.execute(text(query), query_params)
            
            tasks_data = [dict(row) for row in result]
            return TaskMapper.to_domain_list(tasks_data)
            
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error finding tasks by tag {tag}: {str(e)}")
            raise Exception(f"Failed to find tasks by tag: {str(e)}")
        except Exception as e:
            logger.error(f"Error finding tasks by tag {tag}: {str(e)}")
            raise
    
    def search(
        self,
        filters: Dict[str, Any],
        tenant_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Task], int]:
        """
        Search for tasks based on various filters.
        
        Args:
            filters: Dictionary of filter criteria
            tenant_id: Optional tenant ID for multi-tenancy filtering
            limit: Maximum number of results to return
            offset: Number of results to skip
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            
        Returns:
            Tuple containing (list of matching tasks, total count)
            
        Raises:
            Exception: If search fails
        """
        try:
            query_params = {
                "limit": limit,
                "offset": offset
            }
            
            # Build WHERE clause parts
            where_clauses = []
            
            # Add tenant filtering if provided
            if tenant_id:
                where_clauses.append("tenant_id = :tenant_id")
                query_params["tenant_id"] = tenant_id
            
            # Process filters
            for key, value in filters.items():
                if key == "status" and value:
                    where_clauses.append("status = :status")
                    query_params["status"] = value
                
                elif key == "priority" and value:
                    where_clauses.append("priority = :priority")
                    query_params["priority"] = value
                
                elif key == "type" and value:
                    where_clauses.append("type = :type")
                    query_params["type"] = value
                
                elif key == "worker_id" and value:
                    where_clauses.append("worker_id = :worker_id")
                    query_params["worker_id"] = value
                
                elif key == "parent_task_id" and value:
                    where_clauses.append("parent_task_id = :parent_task_id")
                    query_params["parent_task_id"] = value
                
                elif key == "created_after" and value:
                    where_clauses.append("created_at >= :created_after")
                    query_params["created_after"] = value
                
                elif key == "created_before" and value:
                    where_clauses.append("created_at <= :created_before")
                    query_params["created_before"] = value
                
                elif key == "tag" and value:
                    where_clauses.append("tags @> :tag::jsonb")
                    query_params["tag"] = f'["{value}"]'
            
            # Construct the WHERE clause
            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Validate and sanitize sort parameters
            if sort_by not in ["created_at", "updated_at", "priority", "status", "type"]:
                sort_by = "created_at"
            
            sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"
            
            # Build and execute query
            count_query = f"SELECT COUNT(*) FROM tasks WHERE {where_clause}"
            data_query = f"""
                SELECT * FROM tasks 
                WHERE {where_clause}
                ORDER BY {sort_by} {sort_direction}
                LIMIT :limit OFFSET :offset
            """
            
            # Execute count query
            count_result = self.connection.execute(text(count_query), query_params)
            total_count = count_result.scalar()
            
            # Execute data query
            result = self.connection.execute(text(data_query), query_params)
            
            tasks_data = [dict(row) for row in result]
            tasks = TaskMapper.to_domain_list(tasks_data)
            
            return tasks, total_count
            
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error searching tasks: {str(e)}")
            raise Exception(f"Failed to search tasks: {str(e)}")
        except Exception as e:
            logger.error(f"Error searching tasks: {str(e)}")
            raise 