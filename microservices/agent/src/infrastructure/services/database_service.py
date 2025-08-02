"""Interface for database service."""
from typing import Dict, Any, Optional, List, TypeVar, Generic, Type
from datetime import datetime
from abc import ABC, abstractmethod


T = TypeVar('T')


class IDatabaseService(ABC, Generic[T]):
    """Interface for database service."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass
    
    @abstractmethod
    async def create_table(
        self,
        table_name: str,
        schema: Dict[str, Any]
    ) -> None:
        """
        Create a new table.
        
        Args:
            table_name: Name of the table
            schema: Table schema definition
        """
        pass
    
    @abstractmethod
    async def drop_table(
        self,
        table_name: str
    ) -> None:
        """
        Drop a table.
        
        Args:
            table_name: Name of the table
        """
        pass
    
    @abstractmethod
    async def insert(
        self,
        table_name: str,
        data: Dict[str, Any]
    ) -> str:
        """
        Insert a record into a table.
        
        Args:
            table_name: Name of the table
            data: Record data
            
        Returns:
            ID of inserted record
        """
        pass
    
    @abstractmethod
    async def insert_many(
        self,
        table_name: str,
        data: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Insert multiple records into a table.
        
        Args:
            table_name: Name of the table
            data: List of record data
            
        Returns:
            List of inserted record IDs
        """
        pass
    
    @abstractmethod
    async def get(
        self,
        table_name: str,
        record_id: str,
        model_class: Optional[Type[T]] = None
    ) -> Optional[T]:
        """
        Get a record by ID.
        
        Args:
            table_name: Name of the table
            record_id: Record ID
            model_class: Optional model class to return
            
        Returns:
            Record data or None if not found
        """
        pass
    
    @abstractmethod
    async def update(
        self,
        table_name: str,
        record_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Update a record.
        
        Args:
            table_name: Name of the table
            record_id: Record ID
            data: Updated data
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        table_name: str,
        record_id: str
    ) -> bool:
        """
        Delete a record.
        
        Args:
            table_name: Name of the table
            record_id: Record ID
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def query(
        self,
        table_name: str,
        conditions: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[Dict[str, str]]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        model_class: Optional[Type[T]] = None
    ) -> List[T]:
        """
        Query records from a table.
        
        Args:
            table_name: Name of the table
            conditions: Optional query conditions
            order_by: Optional ordering criteria
            limit: Optional maximum number of records
            offset: Optional offset for pagination
            model_class: Optional model class to return
            
        Returns:
            List of matching records
        """
        pass
    
    @abstractmethod
    async def count(
        self,
        table_name: str,
        conditions: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count records in a table.
        
        Args:
            table_name: Name of the table
            conditions: Optional query conditions
            
        Returns:
            Number of matching records
        """
        pass
    
    @abstractmethod
    async def exists(
        self,
        table_name: str,
        conditions: Dict[str, Any]
    ) -> bool:
        """
        Check if records exist matching conditions.
        
        Args:
            table_name: Name of the table
            conditions: Query conditions
            
        Returns:
            True if records exist, False otherwise
        """
        pass
    
    @abstractmethod
    async def begin_transaction(self) -> None:
        """Begin a database transaction."""
        pass
    
    @abstractmethod
    async def commit_transaction(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    async def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        pass
    
    @abstractmethod
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            List of query results
        """
        pass
    
    @abstractmethod
    async def execute_command(
        self,
        command: str,
        params: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Execute a raw SQL command.
        
        Args:
            command: SQL command string
            params: Optional command parameters
            
        Returns:
            Number of affected rows
        """
        pass 