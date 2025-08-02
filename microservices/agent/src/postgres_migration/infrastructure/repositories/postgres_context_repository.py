"""
PostgreSQL implementation for multi-tenant context storage.
"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.utils.id_utils import generate_request_id
from src.postgres_migration.config.postgres_config import (
    CONTEXT_TABLE, BATCH_TABLE, REFERENCE_TABLE, DEFAULT_QUERY_LIMIT
)
from src.postgres_migration.infrastructure.repositories.postgres_connection_manager import (
    execute_tenant_aware, fetch_tenant_aware, fetch_one_tenant_aware
)

logger = logging.getLogger(__name__)

class PostgresContextRepository:
    """
    PostgreSQL repository for multi-tenant context storage and retrieval.
    
    Handles CRUD operations for context documents with tenant isolation.
    """
    
    async def save(self, context_id: str, context: Dict[str, Any]) -> bool:
        """
        Save or update a context document.
        
        Args:
            context_id: Unique context identifier
            context: Context data to save
            
        Returns:
            Success status
        """
        try:
            # If status is completed, set completed_at for TTL
            if context.get("status") == "completed" and "completed_at" not in context:
                context["completed_at"] = datetime.utcnow().isoformat()
                
            # Set create_at and updated_at timestamps
            if "created_at" not in context:
                context["created_at"] = datetime.utcnow().isoformat()
            
            context["updated_at"] = datetime.utcnow().isoformat()
            
            # Ensure _id is set correctly
            context_id = context.get("_id", context_id)
            
            # Extract fields
            status = context.get("status", "pending")
            priority = context.get("priority", 5)
            request = json.dumps(context.get("request", {}))
            template = json.dumps(context.get("template", {}))
            results = json.dumps(context.get("results", {}))
            tags = json.dumps(context.get("tags", {}))
            metadata = json.dumps(context.get("metadata", {}))
            parent_id = context.get("parent_id")
            created_at = context.get("created_at")
            updated_at = context.get("updated_at")
            completed_at = context.get("completed_at")
            
            # Prepare upsert query
            query = f"""
            INSERT INTO {CONTEXT_TABLE} (
                id, created_at, updated_at, completed_at, status, priority,
                request, template, results, tags, metadata, parent_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
            )
            ON CONFLICT (id) DO UPDATE SET
                updated_at = $3,
                completed_at = $4,
                status = $5,
                priority = $6,
                request = $7,
                template = $8,
                results = $9,
                tags = $10,
                metadata = $11,
                parent_id = $12
            """
            
            # Execute query
            await execute_tenant_aware(
                query,
                context_id, created_at, updated_at, completed_at, status, priority,
                request, template, results, tags, metadata, parent_id
            )
            
            logger.debug(f"Saved context {context_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving context {context_id}: {str(e)}")
            return False
    
    async def get(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a context document by ID.
        
        Args:
            context_id: Context identifier
            
        Returns:
            Context document or None if not found
        """
        try:
            query = f"""
            SELECT 
                id, created_at, updated_at, completed_at, status, priority,
                request, template, results, tags, metadata, parent_id
            FROM {CONTEXT_TABLE}
            WHERE id = $1
            """
            
            # Execute query and get first result
            row = await fetch_one_tenant_aware(query, context_id)
            
            if row:
                # Convert to context format
                context = {
                    "_id": row["id"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    "status": row["status"],
                    "priority": row["priority"],
                    "request": row["request"],
                    "template": row["template"],
                    "results": row["results"],
                    "tags": row["tags"],
                    "metadata": row["metadata"]
                }
                
                # Add optional fields if present
                if row["parent_id"]:
                    context["parent_id"] = row["parent_id"]
                if row["completed_at"]:
                    context["completed_at"] = row["completed_at"].isoformat()
                
                return context
            
            return None
        except Exception as e:
            logger.error(f"Error getting context {context_id}: {str(e)}")
            return None
    
    async def delete(self, context_id: str) -> bool:
        """
        Delete a context document by ID.
        
        Args:
            context_id: Context identifier
            
        Returns:
            Success status
        """
        try:
            query = f"""
            DELETE FROM {CONTEXT_TABLE}
            WHERE id = $1
            """
            
            # Execute query
            result = await execute_tenant_aware(query, context_id)
            
            # Check if any rows were deleted
            if "DELETE 0" not in result:
                logger.debug(f"Deleted context {context_id}")
                return True
            else:
                logger.warning(f"Context {context_id} not found for deletion")
                return False
        except Exception as e:
            logger.error(f"Error deleting context {context_id}: {str(e)}")
            return False
    
    async def update_field(self, context_id: str, field: str, value: Any) -> bool:
        """
        Update a specific field in a context document.
        
        Args:
            context_id: Context identifier
            field: Field name to update
            value: New value
            
        Returns:
            Success status
        """
        try:
            # If updating status to completed, set completed_at
            completed_at = None
            if field == "status" and value == "completed":
                completed_at = datetime.utcnow().isoformat()
            
            # Handle special cases for JSON fields
            if field in ["request", "template", "results", "tags", "metadata"]:
                # Get current context
                context = await self.get(context_id)
                if not context:
                    logger.warning(f"Context {context_id} not found for field update")
                    return False
                
                # Update the field
                context[field] = value
                
                # Save updated context
                return await self.save(context_id, context)
            
            # For simple fields, use direct update
            query = f"""
            UPDATE {CONTEXT_TABLE}
            SET {field} = $1, updated_at = $2
            """
            
            # Add completed_at update if needed
            params = [value, datetime.utcnow().isoformat()]
            if completed_at:
                query += ", completed_at = $3 WHERE id = $4"
                params.extend([completed_at, context_id])
            else:
                query += " WHERE id = $3"
                params.append(context_id)
            
            # Execute query
            result = await execute_tenant_aware(query, *params)
            
            # Check if any rows were updated
            if "UPDATE 0" not in result:
                logger.debug(f"Updated field {field} for context {context_id}")
                return True
            else:
                logger.warning(f"Context {context_id} not found for field update")
                return False
        except Exception as e:
            logger.error(f"Error updating field {field} for context {context_id}: {str(e)}")
            return False
    
    async def find_by_status(self, status: str, limit: int = DEFAULT_QUERY_LIMIT) -> List[Dict[str, Any]]:
        """
        Find contexts by status.
        
        Args:
            status: Status to filter by
            limit: Maximum number of results
            
        Returns:
            List of matching contexts
        """
        try:
            query = f"""
            SELECT 
                id, created_at, updated_at, completed_at, status, priority,
                request, template, results, tags, metadata, parent_id
            FROM {CONTEXT_TABLE}
            WHERE status = $1
            ORDER BY priority ASC, created_at ASC
            LIMIT $2
            """
            
            # Execute query
            rows = await fetch_tenant_aware(query, status, limit)
            
            # Convert rows to context format
            contexts = []
            for row in rows:
                context = {
                    "_id": row["id"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    "status": row["status"],
                    "priority": row["priority"],
                    "request": row["request"],
                    "template": row["template"],
                    "results": row["results"],
                    "tags": row["tags"],
                    "metadata": row["metadata"]
                }
                
                # Add optional fields if present
                if row["parent_id"]:
                    context["parent_id"] = row["parent_id"]
                if row["completed_at"]:
                    context["completed_at"] = row["completed_at"].isoformat()
                
                contexts.append(context)
            
            return contexts
        except Exception as e:
            logger.error(f"Error finding contexts by status {status}: {str(e)}")
            return []
    
    async def find_by_user(self, user_id: str, limit: int = DEFAULT_QUERY_LIMIT) -> List[Dict[str, Any]]:
        """
        Find contexts by user ID.
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            
        Returns:
            List of matching contexts
        """
        try:
            query = f"""
            SELECT 
                id, created_at, updated_at, completed_at, status, priority,
                request, template, results, tags, metadata, parent_id
            FROM {CONTEXT_TABLE}
            WHERE request->>'user_id' = $1
            ORDER BY created_at DESC
            LIMIT $2
            """
            
            # Execute query
            rows = await fetch_tenant_aware(query, user_id, limit)
            
            # Convert rows to context format
            contexts = []
            for row in rows:
                context = {
                    "_id": row["id"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    "status": row["status"],
                    "priority": row["priority"],
                    "request": row["request"],
                    "template": row["template"],
                    "results": row["results"],
                    "tags": row["tags"],
                    "metadata": row["metadata"]
                }
                
                # Add optional fields if present
                if row["parent_id"]:
                    context["parent_id"] = row["parent_id"]
                if row["completed_at"]:
                    context["completed_at"] = row["completed_at"].isoformat()
                
                contexts.append(context)
            
            return contexts
        except Exception as e:
            logger.error(f"Error finding contexts for user {user_id}: {str(e)}")
            return []
    
    async def save_batch_context(self, batch_id: str, context: Dict[str, Any]) -> bool:
        """
        Save or update a batch context document.
        
        Args:
            batch_id: Batch identifier
            context: Batch context data
            
        Returns:
            Success status
        """
        try:
            # Set create_at and updated_at timestamps
            if "created_at" not in context:
                context["created_at"] = datetime.utcnow().isoformat()
            
            context["updated_at"] = datetime.utcnow().isoformat()
            
            # Extract fields
            status = context.get("status", "pending")
            total_items = context.get("total_items", 0)
            completed_items = context.get("completed_items", 0)
            failed_items = context.get("failed_items", 0)
            skipped_items = context.get("skipped_items", 0)
            metadata = json.dumps(context.get("metadata", {}))
            created_at = context.get("created_at")
            updated_at = context.get("updated_at")
            
            # Prepare upsert query
            query = f"""
            INSERT INTO {BATCH_TABLE} (
                id, created_at, updated_at, status,
                total_items, completed_items, failed_items, skipped_items, metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9
            )
            ON CONFLICT (id) DO UPDATE SET
                updated_at = $3,
                status = $4,
                total_items = $5,
                completed_items = $6,
                failed_items = $7,
                skipped_items = $8,
                metadata = $9
            """
            
            # Execute query
            await execute_tenant_aware(
                query,
                batch_id, created_at, updated_at, status,
                total_items, completed_items, failed_items, skipped_items, metadata
            )
            
            logger.debug(f"Saved batch context {batch_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving batch context {batch_id}: {str(e)}")
            return False
    
    async def get_batch_context(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a batch context document by ID.
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Batch context document or None if not found
        """
        try:
            query = f"""
            SELECT 
                id, created_at, updated_at, status,
                total_items, completed_items, failed_items, skipped_items, metadata
            FROM {BATCH_TABLE}
            WHERE id = $1
            """
            
            # Execute query and get first result
            row = await fetch_one_tenant_aware(query, batch_id)
            
            if row:
                # Convert to batch context format
                context = {
                    "_id": row["id"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    "status": row["status"],
                    "total_items": row["total_items"],
                    "completed_items": row["completed_items"],
                    "failed_items": row["failed_items"],
                    "skipped_items": row["skipped_items"],
                    "metadata": row["metadata"]
                }
                
                return context
            
            return None
        except Exception as e:
            logger.error(f"Error getting batch context {batch_id}: {str(e)}")
            return None
    
    async def delete_old_contexts(self, days: int = 30) -> int:
        """
        Delete contexts older than specified number of days.
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of deleted contexts
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = f"""
            DELETE FROM {CONTEXT_TABLE}
            WHERE created_at < $1
            """
            
            # Execute query
            result = await execute_tenant_aware(query, cutoff_date)
            
            # Extract number of deleted rows
            deleted_count = int(result.split(" ")[1]) if result else 0
            
            logger.info(f"Deleted {deleted_count} contexts older than {days} days")
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting old contexts: {str(e)}")
            return 0 