"""
Database RAG component for retrieving structured information from databases.
Connects to various structured data sources for precise information retrieval.
"""

import logging
from typing import Dict, List, Any, Optional
from langchain.schema import Document

from src.config.config_inheritance import ConfigInheritance
from src.langchain_components.rag.database_query_builder import database_query_builder
from src.langchain_components.rag.database_formatter import database_formatter
from src.langchain_components.rag.database_cache_manager import database_cache_manager

class DatabaseRAG:
    """
    Database RAG component for structured information retrieval.
    Connects to databases for retrieving specific structured information.
    """
    
    def __init__(self):
        """Initialize the Database RAG component."""
        self.config_inheritance = ConfigInheritance()
        self.logger = logging.getLogger(__name__)
        self.connections = {}
    
    async def get_relevant_documents(
        self, query: str, bot_type: str, database_name: Optional[str] = None, limit: int = 5
    ) -> List[Document]:
        """
        Get relevant information from databases.
        
        Args:
            query: The search query
            bot_type: The type of bot
            database_name: Optional specific database to query
            limit: Maximum number of results to return
            
        Returns:
            List of documents with database information
        """
        # Get bot configuration
        config = self.config_inheritance.get_config(bot_type)
        
        # Determine databases to query
        if database_name:
            databases = [database_name]
        else:
            databases = config.get("database_rag.databases", [])
        
        # Check if databases exist
        if not databases:
            self.logger.warning(f"No databases configured for {bot_type}")
            return []
        
        # Check cache first if enabled
        if config.get("database_rag.use_cache", True):
            cached_documents = await database_cache_manager.get_cached_documents(query, bot_type, databases)
            if cached_documents:
                self.logger.info(f"Using cached database results for query: {query}")
                return cached_documents[:limit]
        
        # Build SQL queries for each database
        queries = await database_query_builder.build_queries(query, bot_type, databases)
        
        # Execute queries and collect results
        documents = []
        for db_name, db_query in queries.items():
            results = await self._execute_query(db_name, db_query, bot_type)
            
            if not results:
                continue
                
            # Convert results to documents
            for result in results:
                # Format the result as a document
                content = database_formatter.format_result(result, db_name, bot_type)
                
                if content:
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": "database",
                            "database": db_name,
                            "query": db_query
                        }
                    )
                    documents.append(doc)
        
        # Cache results if enabled
        if config.get("database_rag.use_cache", True) and documents:
            await database_cache_manager.cache_documents(query, bot_type, databases, documents)
        
        # Return up to limit documents
        return documents[:limit]
    
    async def _execute_query(
        self, database_name: str, query: str, bot_type: str
    ) -> List[Dict[str, Any]]:
        """
        Execute a database query.
        
        Args:
            database_name: The name of the database
            query: The SQL query to execute
            bot_type: The type of bot
            
        Returns:
            List of query results
        """
        # Get database connection or create one
        connection = await self._get_connection(database_name, bot_type)
        if not connection:
            self.logger.error(f"No connection for database {database_name}")
            return []
        
        try:
            # Execute query using connection
            # This is a placeholder - real implementation would use the actual connection
            self.logger.info(f"Executing query on {database_name}: {query}")
            
            # Simulate query execution for now
            # In a real implementation, this would execute the SQL query
            return self._simulate_query_results(database_name, query)
            
        except Exception as e:
            self.logger.error(f"Error executing query on {database_name}: {e}")
            return []
    
    async def _get_connection(self, database_name: str, bot_type: str):
        """
        Get or create a database connection.
        
        Args:
            database_name: The name of the database
            bot_type: The type of bot
            
        Returns:
            Database connection object or None
        """
        # Check if connection already exists
        if database_name in self.connections:
            return self.connections[database_name]
        
        # Get database configuration
        config = self.config_inheritance.get_config(bot_type)
        db_configs = config.get("database_rag.connections", {})
        
        if database_name not in db_configs:
            self.logger.error(f"No configuration for database {database_name}")
            return None
        
        db_config = db_configs[database_name]
        
        try:
            # Create connection based on database type
            db_type = db_config.get("type", "postgresql")
            
            if db_type == "postgresql":
                # Create PostgreSQL connection
                # This is a placeholder - real implementation would create actual connection
                connection = f"postgresql-connection-{database_name}"
                
            elif db_type == "mysql":
                # Create MySQL connection
                connection = f"mysql-connection-{database_name}"
                
            else:
                self.logger.error(f"Unsupported database type: {db_type}")
                return None
            
            # Store connection
            self.connections[database_name] = connection
            return connection
            
        except Exception as e:
            self.logger.error(f"Error creating connection for {database_name}: {e}")
            return None
    
    def _simulate_query_results(self, database_name: str, query: str) -> List[Dict[str, Any]]:
        """
        Simulate query results for development/testing.
        
        Args:
            database_name: The name of the database
            query: The SQL query
            
        Returns:
            Simulated query results
        """
        # This would be replaced with actual query execution in production
        if "product" in query.lower() and "inventory" in database_name.lower():
            return [
                {"product_id": 1, "name": "Product A", "stock": 15, "price": 29.99},
                {"product_id": 2, "name": "Product B", "stock": 8, "price": 49.99},
                {"product_id": 3, "name": "Product C", "stock": 0, "price": 19.99}
            ]
        elif "customer" in query.lower() and "crm" in database_name.lower():
            return [
                {"customer_id": 101, "name": "John Doe", "tier": "Gold", "purchases": 12},
                {"customer_id": 102, "name": "Jane Smith", "tier": "Silver", "purchases": 5}
            ]
        elif "issue" in query.lower() and "support" in database_name.lower():
            return [
                {"issue_id": 501, "title": "Login Problem", "status": "Resolved", "priority": "High"},
                {"issue_id": 502, "title": "Payment Failed", "status": "Open", "priority": "Critical"}
            ]
        else:
            return []
    
    def get_retriever_for_bot(self, bot_type: str):
        """
        Get a specialized retriever for a specific bot type.
        
        Args:
            bot_type: The type of bot
            
        Returns:
            Bot-specific retriever function
        """
        # Get bot configuration
        config = self.config_inheritance.get_config(bot_type)
        
        if bot_type == "consultancy":
            # Consultancy bot focuses on business frameworks and knowledge
            return self._get_consultancy_retriever(config)
        elif bot_type == "sales":
            # Sales bot focuses on product and pricing information
            return self._get_sales_retriever(config)
        elif bot_type == "support":
            # Support bot focuses on troubleshooting information
            return self._get_support_retriever(config)
        else:
            # Default retriever
            return self.get_relevant_documents
    
    def _get_consultancy_retriever(self, config: Dict[str, Any]):
        """Get consultancy-specific retriever focused on business information."""
        async def consultancy_retriever(query: str, bot_type: str, limit: int = 5):
            # Get consultancy-specific databases
            databases = config.get("database_rag.consultancy_databases", [])
            
            # If no consultancy-specific databases, use default databases
            if not databases:
                databases = config.get("database_rag.databases", [])
            
            # Retrieve documents from specified databases
            documents = []
            for database_name in databases:
                docs = await self.get_relevant_documents(query, bot_type, database_name, limit)
                documents.extend(docs)
            
            return documents[:limit]
                
        return consultancy_retriever
    
    def _get_sales_retriever(self, config: Dict[str, Any]):
        """Get sales-specific retriever focused on product information."""
        async def sales_retriever(query: str, bot_type: str, limit: int = 5):
            # Get sales-specific databases
            databases = config.get("database_rag.sales_databases", [])
            
            # If no sales-specific databases, use default databases
            if not databases:
                databases = config.get("database_rag.databases", [])
            
            # Retrieve documents from specified databases
            documents = []
            for database_name in databases:
                docs = await self.get_relevant_documents(query, bot_type, database_name, limit)
                documents.extend(docs)
            
            return documents[:limit]
                
        return sales_retriever
    
    def _get_support_retriever(self, config: Dict[str, Any]):
        """Get support-specific retriever focused on troubleshooting information."""
        async def support_retriever(query: str, bot_type: str, limit: int = 5):
            # Get support-specific databases
            databases = config.get("database_rag.support_databases", [])
            
            # If no support-specific databases, use default databases
            if not databases:
                databases = config.get("database_rag.databases", [])
            
            # Retrieve documents from specified databases
            documents = []
            for database_name in databases:
                docs = await self.get_relevant_documents(query, bot_type, database_name, limit)
                documents.extend(docs)
            
            return documents[:limit]
                
        return support_retriever

# Global instance
database_rag = DatabaseRAG() 