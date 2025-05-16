"""
Database query builder for constructing SQL queries from natural language.
Translates user questions to database queries for structured information retrieval.
"""

import logging
from typing import Dict, List, Any
import re

from src.config.config_inheritance import ConfigInheritance
from src.models.llm.model_registry import ModelRegistry

class DatabaseQueryBuilder:
    """
    Builds SQL queries from natural language questions.
    Uses LLMs and configuration to generate safe, relevant queries.
    """
    
    def __init__(self):
        """Initialize the database query builder."""
        self.config_inheritance = ConfigInheritance()
        self.model_registry = ModelRegistry()
        self.logger = logging.getLogger(__name__)
    
    async def build_queries(
        self, query: str, bot_type: str, databases: List[str]
    ) -> Dict[str, str]:
        """
        Build SQL queries for multiple databases.
        
        Args:
            query: The natural language query
            bot_type: The type of bot
            databases: List of database names to query
            
        Returns:
            Dictionary mapping database names to SQL queries
        """
        config = self.config_inheritance.get_config(bot_type)
        
        # Get query builder method from config
        builder_method = config.get("database_rag.query_builder_method", "template")
        
        # Build queries for each database
        result = {}
        for database_name in databases:
            # Get database schema and config
            db_schema = self._get_database_schema(database_name, bot_type)
            
            if not db_schema:
                self.logger.warning(f"No schema found for database {database_name}")
                continue
                
            # Build query based on method
            if builder_method == "llm":
                sql_query = await self._build_llm_query(query, database_name, db_schema, bot_type)
            elif builder_method == "template":
                sql_query = self._build_template_query(query, database_name, db_schema, bot_type)
            else:
                self.logger.warning(f"Unknown query builder method: {builder_method}")
                sql_query = self._build_template_query(query, database_name, db_schema, bot_type)
            
            # Validate query for safety
            if self._validate_query(sql_query, database_name, bot_type):
                result[database_name] = sql_query
        
        return result
    
    async def _build_llm_query(
        self, query: str, database_name: str, db_schema: Dict[str, Any], bot_type: str
    ) -> str:
        """
        Build SQL query using LLM.
        
        Args:
            query: The natural language query
            database_name: The name of the database
            db_schema: Database schema information
            bot_type: The type of bot
            
        Returns:
            SQL query string
        """
        config = self.config_inheritance.get_config(bot_type)
        
        # Get LLM model from config
        model_name = config.get("database_rag.query_model", "default_nlp_model")
        llm = self.model_registry.get_model(model_name, bot_type)
        
        if not llm:
            self.logger.error(f"No model found for query building, falling back to template")
            return self._build_template_query(query, database_name, db_schema, bot_type)
        
        try:
            # Format schema information
            schema_str = self._format_schema_for_prompt(db_schema)
            
            # Build prompt
            prompt = f"""
            You are an expert SQL query builder. I have a database named '{database_name}' with the following schema:
            
            {schema_str}
            
            Please write a SQL query to answer this question: "{query}"
            
            The query should:
            1. Be simple and efficient
            2. Use only tables and columns defined in the schema
            3. Only include SELECT statements (no INSERT, UPDATE, DELETE, etc.)
            4. Include a LIMIT clause for safety
            
            Return only the SQL query, nothing else.
            """
            
            # Get response from LLM
            response = await llm.ainvoke(prompt)
            sql_query = response.content.strip()
            
            # Extract just the SQL if it's embedded in markdown or other text
            if "```sql" in sql_query:
                sql_query = re.search(r"```sql\n(.*?)\n```", sql_query, re.DOTALL)
                if sql_query:
                    sql_query = sql_query.group(1).strip()
            elif "```" in sql_query:
                sql_query = re.search(r"```\n(.*?)\n```", sql_query, re.DOTALL)
                if sql_query:
                    sql_query = sql_query.group(1).strip()
            
            # Add LIMIT if not present
            if "limit" not in sql_query.lower():
                sql_query = sql_query.rstrip(";") + " LIMIT 5;"
            
            return sql_query
            
        except Exception as e:
            self.logger.error(f"Error building LLM query: {e}")
            return self._build_template_query(query, database_name, db_schema, bot_type)
    
    def _build_template_query(
        self, query: str, database_name: str, db_schema: Dict[str, Any], bot_type: str
    ) -> str:
        """
        Build SQL query using templates.
        
        Args:
            query: The natural language query
            database_name: The name of the database
            db_schema: Database schema information
            bot_type: The type of bot
            
        Returns:
            SQL query string
        """
        # Default to a simple safe query that returns a limited set of results
        main_table = next(iter(db_schema["tables"]), None)
        
        if not main_table:
            return "SELECT 1 LIMIT 0;"  # Empty query
        
        table_name = main_table.get("name", "")
        columns = main_table.get("columns", [])
        
        if not table_name or not columns:
            return "SELECT 1 LIMIT 0;"  # Empty query
        
        # Get column names
        column_names = [col.get("name", "") for col in columns if col.get("name")]
        
        if not column_names:
            return "SELECT 1 LIMIT 0;"  # Empty query
        
        # Simple query that selects all columns from the main table
        sql_query = f"SELECT {', '.join(column_names)} FROM {table_name} LIMIT 5;"
        
        # Try to add a WHERE clause based on keywords in the query
        if self._should_add_where_clause(query, column_names, table_name):
            for col in column_names:
                if col.lower() in query.lower():
                    # Look for potential values
                    for word in query.split():
                        # Simple heuristic: If word is numeric, use equality
                        if word.isdigit():
                            sql_query = f"SELECT {', '.join(column_names)} FROM {table_name} WHERE {col} = {word} LIMIT 5;"
                            break
                        # If word is a string and matches certain patterns, use LIKE
                        elif len(word) > 3 and word.isalpha() and word.lower() not in ["from", "where", "like", "and", "or"]:
                            sql_query = f"SELECT {', '.join(column_names)} FROM {table_name} WHERE {col} LIKE '%{word}%' LIMIT 5;"
                            break
        
        return sql_query
    
    def _should_add_where_clause(self, query: str, column_names: List[str], table_name: str) -> bool:
        """Determine if a WHERE clause should be added to the query."""
        # If query contains specific column names or filtering words
        lower_query = query.lower()
        filter_words = ["where", "filter", "find", "search", "specific", "particular"]
        
        for word in filter_words:
            if word in lower_query:
                return True
                
        for col in column_names:
            if col.lower() in lower_query:
                return True
                
        return False
    
    def _format_schema_for_prompt(self, db_schema: Dict[str, Any]) -> str:
        """Format database schema information for inclusion in prompts."""
        result = ""
        
        for table in db_schema.get("tables", []):
            table_name = table.get("name", "")
            result += f"Table: {table_name}\n"
            result += "Columns:\n"
            
            for column in table.get("columns", []):
                col_name = column.get("name", "")
                col_type = column.get("type", "")
                result += f"  - {col_name} ({col_type})\n"
            
            result += "\n"
        
        return result
    
    def _get_database_schema(self, database_name: str, bot_type: str) -> Dict[str, Any]:
        """
        Get database schema information from configuration.
        
        Args:
            database_name: The name of the database
            bot_type: The type of bot
            
        Returns:
            Database schema dictionary
        """
        config = self.config_inheritance.get_config(bot_type)
        db_schemas = config.get("database_rag.schemas", {})
        
        if database_name not in db_schemas:
            self.logger.warning(f"No schema defined for database {database_name}")
            
            # Return a minimal default schema
            return {
                "tables": [
                    {
                        "name": "unknown_table",
                        "columns": [
                            {"name": "id", "type": "INTEGER"},
                            {"name": "name", "type": "TEXT"},
                            {"name": "description", "type": "TEXT"}
                        ]
                    }
                ]
            }
        
        return db_schemas[database_name]
    
    def _validate_query(self, query: str, database_name: str, bot_type: str) -> bool:
        """
        Validate a SQL query for safety.
        
        Args:
            query: The SQL query to validate
            database_name: The name of the database
            bot_type: The type of bot
            
        Returns:
            True if valid, False otherwise
        """
        # Simple validation rules
        
        # Must contain SELECT
        if not re.search(r"\bSELECT\b", query, re.IGNORECASE):
            self.logger.warning(f"Query rejected: No SELECT statement")
            return False
        
        # Must not contain dangerous statements
        dangerous_patterns = [
            r"\bDELETE\b", r"\bDROP\b", r"\bTRUNCATE\b", r"\bALTER\b", 
            r"\bCREATE\b", r"\bINSERT\b", r"\bUPDATE\b", r"\bGRANT\b", 
            r"\bREVOKE\b", r"\bCOMMIT\b", r"\bROLLBACK\b", r"\bINTO\s+OUTFILE\b"
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                self.logger.warning(f"Query rejected: Contains dangerous pattern: {pattern}")
                return False
        
        # Should ideally contain a LIMIT clause
        if not re.search(r"\bLIMIT\b", query, re.IGNORECASE):
            self.logger.warning(f"Query missing LIMIT clause, adding default")
            query = query.rstrip(";") + " LIMIT 10;"
        
        return True

# Global instance
database_query_builder = DatabaseQueryBuilder() 