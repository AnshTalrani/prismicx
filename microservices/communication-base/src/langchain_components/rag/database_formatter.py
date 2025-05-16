"""
Database formatter for converting query results to readable text.
Formats database results for inclusion in RAG documents.
"""

import logging
from typing import Dict, List, Any
import json

from src.config.config_inheritance import ConfigInheritance

class DatabaseFormatter:
    """
    Formats database query results into readable text.
    Provides various formatting options for different result types.
    """
    
    def __init__(self):
        """Initialize the database formatter."""
        self.config_inheritance = ConfigInheritance()
        self.logger = logging.getLogger(__name__)
    
    def format_result(
        self, result: Dict[str, Any], database_name: str, bot_type: str
    ) -> str:
        """
        Format a database result as readable text.
        
        Args:
            result: Query result dictionary
            database_name: Name of the database
            bot_type: Type of bot
            
        Returns:
            Formatted text
        """
        # Get bot configuration
        config = self.config_inheritance.get_config(bot_type)
        
        # Get formatter configuration
        formatter_config = config.get("database_rag.formatters", {}).get(database_name, {})
        
        # Determine format type
        format_type = formatter_config.get("type", "default")
        
        if format_type == "table":
            return self._format_as_table(result, formatter_config)
        elif format_type == "markdown":
            return self._format_as_markdown(result, formatter_config)
        elif format_type == "key_value":
            return self._format_as_key_value(result, formatter_config)
        elif format_type == "custom":
            return self._format_custom(result, formatter_config)
        else:
            return self._format_default(result, formatter_config)
    
    def _format_as_table(self, result: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Format result as a fixed-width ASCII table."""
        # Simple implementation - proper table formatting would use a dedicated library
        lines = []
        
        # Add header
        if config.get("include_header", True):
            header_text = config.get("header_text", "Database Result")
            lines.append(f"# {header_text}\n")
        
        # Get column keys and widths
        keys = list(result.keys())
        col_widths = {k: max(len(k), len(str(result[k]))) for k in keys}
        
        # Create header row
        header = " | ".join(f"{k:{col_widths[k]}}" for k in keys)
        separator = "-+-".join("-" * col_widths[k] for k in keys)
        
        lines.append(header)
        lines.append(separator)
        
        # Create data row
        data_row = " | ".join(f"{str(result[k]):{col_widths[k]}}" for k in keys)
        lines.append(data_row)
        
        return "\n".join(lines)
    
    def _format_as_markdown(self, result: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Format result as Markdown."""
        lines = []
        
        # Add header
        if config.get("include_header", True):
            header_text = config.get("header_text", "Database Result")
            lines.append(f"## {header_text}\n")
        
        # Create markdown table
        if config.get("use_table", True):
            # Header row
            lines.append("| " + " | ".join(result.keys()) + " |")
            
            # Separator
            lines.append("| " + " | ".join(["---"] * len(result.keys())) + " |")
            
            # Data row
            lines.append("| " + " | ".join(str(v) for v in result.values()) + " |")
        else:
            # Format as bullet points
            for k, v in result.items():
                lines.append(f"- **{k}**: {v}")
        
        return "\n".join(lines)
    
    def _format_as_key_value(self, result: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Format result as simple key-value pairs."""
        lines = []
        
        # Add header
        if config.get("include_header", True):
            header_text = config.get("header_text", "Database Result")
            lines.append(f"{header_text}:\n")
        
        # Format as key-value pairs
        separator = config.get("separator", ": ")
        for k, v in result.items():
            # Format based on field settings
            field_format = config.get("field_formats", {}).get(k, {})
            
            # Apply label if configured
            label = field_format.get("label", k)
            
            # Apply value formatting
            if field_format.get("format") == "currency":
                value_str = f"${float(v):.2f}"
            elif field_format.get("format") == "percentage":
                value_str = f"{float(v):.1f}%"
            else:
                value_str = str(v)
            
            lines.append(f"{label}{separator}{value_str}")
        
        return "\n".join(lines)
    
    def _format_custom(self, result: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Format using a custom template specified in config."""
        template = config.get("template", "")
        
        if not template:
            # Fall back to default if no template provided
            return self._format_default(result, config)
        
        # Simple template substitution
        formatted = template
        
        for k, v in result.items():
            placeholder = f"{{{k}}}"
            formatted = formatted.replace(placeholder, str(v))
            
        return formatted
    
    def _format_default(self, result: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Default formatting for results."""
        # Format as JSON-like text
        lines = []
        
        # Add header
        if config.get("include_header", True):
            header_text = config.get("header_text", "Database Result")
            lines.append(f"{header_text}:")
        
        # Format as indented key-value pairs
        for k, v in result.items():
            lines.append(f"  {k}: {v}")
        
        return "\n".join(lines)
    
    def format_results(
        self, results: List[Dict[str, Any]], database_name: str, bot_type: str
    ) -> str:
        """
        Format multiple database results.
        
        Args:
            results: List of query result dictionaries
            database_name: Name of the database
            bot_type: Type of bot
            
        Returns:
            Formatted text
        """
        # Get bot configuration
        config = self.config_inheritance.get_config(bot_type)
        
        # Get collection formatter configuration
        collection_config = config.get("database_rag.collection_formatters", {}).get(database_name, {})
        
        # Format each result
        formatted_results = []
        for result in results:
            formatted_results.append(self.format_result(result, database_name, bot_type))
        
        # Join with appropriate separator
        separator = collection_config.get("separator", "\n\n")
        header = collection_config.get("header", f"Results from {database_name}:")
        
        # Build final output
        output = header + "\n\n"
        output += separator.join(formatted_results)
        
        return output

# Global instance
database_formatter = DatabaseFormatter() 