"""
Utilities for generating and validating standardized IDs.
"""
import uuid
import time
import re
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

# ID format patterns
REQUEST_ID_PATTERN = re.compile(r'^req_([a-zA-Z0-9_]+)_(\d+)_([a-zA-Z0-9]+)$')
BATCH_ID_PATTERN = re.compile(r'^bat_([a-zA-Z0-9_]+)_(\d+)_([a-zA-Z0-9]+)$')

def generate_request_id(source: str = "api") -> str:
    """
    Generate a standardized request ID.
    
    Format: req_{source}_{timestamp}_{random}
    
    Args:
        source: Source identifier (api, bot, batch, etc.)
        
    Returns:
        Standardized request ID
    """
    # Clean source to ensure it's valid for IDs
    clean_source = re.sub(r'[^a-zA-Z0-9_]', '_', source)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = str(uuid.uuid4())[:8]
    return f"req_{clean_source}_{timestamp}_{random_suffix}"

def generate_batch_id(source: str = "batch") -> str:
    """
    Generate a standardized batch ID.
    
    Format: bat_{source}_{timestamp}_{random}
    
    Args:
        source: Source identifier (manual, scheduled, etc.)
        
    Returns:
        Standardized batch ID
    """
    # Clean source to ensure it's valid for IDs
    clean_source = re.sub(r'[^a-zA-Z0-9_]', '_', source)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = str(uuid.uuid4())[:8]
    return f"bat_{clean_source}_{timestamp}_{random_suffix}"

def validate_request_id(id_str: Optional[str]) -> bool:
    """
    Validate if a string is a properly formatted request ID.
    
    Args:
        id_str: ID string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not id_str:
        return False
    
    return bool(REQUEST_ID_PATTERN.match(id_str))

def validate_batch_id(id_str: Optional[str]) -> bool:
    """
    Validate if a string is a properly formatted batch ID.
    
    Args:
        id_str: ID string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not id_str:
        return False
    
    return bool(BATCH_ID_PATTERN.match(id_str))

def extract_id_parts(id_str: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Extract the parts of an ID.
    
    Args:
        id_str: ID string to parse
        
    Returns:
        Tuple of (id_type, source, timestamp, random) or (None, None, None, None) if invalid
    """
    # Check request ID format
    request_match = REQUEST_ID_PATTERN.match(id_str)
    if request_match:
        return ("request", request_match.group(1), request_match.group(2), request_match.group(3))
    
    # Check batch ID format
    batch_match = BATCH_ID_PATTERN.match(id_str)
    if batch_match:
        return ("batch", batch_match.group(1), batch_match.group(2), batch_match.group(3))
    
    # Not a recognized ID format
    return (None, None, None, None)

def extract_timestamp_from_id(id_str: str) -> Optional[str]:
    """
    Extract the timestamp from an ID.
    
    Args:
        id_str: ID string to parse
        
    Returns:
        Timestamp string or None if invalid
    """
    _, _, timestamp, _ = extract_id_parts(id_str)
    return timestamp

def extract_source_from_id(id_str: str) -> Optional[str]:
    """
    Extract the source from an ID.
    
    Args:
        id_str: ID string to parse
        
    Returns:
        Source string or None if invalid
    """
    _, source, _, _ = extract_id_parts(id_str)
    return source

def get_id_metadata(id_str: str) -> Dict[str, Any]:
    """
    Get metadata about an ID.
    
    Args:
        id_str: ID string to analyze
        
    Returns:
        Dictionary with ID metadata
    """
    id_type, source, timestamp, random = extract_id_parts(id_str)
    
    if not id_type:
        return {"valid": False}
    
    return {
        "valid": True,
        "type": id_type,
        "source": source,
        "timestamp": timestamp,
        "random": random
    }

# Aliases for backwards compatibility and test consistency
is_valid_request_id = validate_request_id
is_valid_batch_id = validate_batch_id 