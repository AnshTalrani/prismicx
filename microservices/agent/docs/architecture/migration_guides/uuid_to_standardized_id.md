# Migration Guide: UUID to Standardized ID Format

This guide explains how to migrate code that uses random UUIDs to the new standardized ID format in the Agent microservice.

## Overview

The Agent microservice has transitioned from using random UUIDs for identification to a standardized ID format that contains embedded metadata. This change provides better traceability, debugging capabilities, and contextual information in the IDs themselves.

## ID Format Specification

### Request IDs
Format: `req_{source}_{timestamp}_{random}`

Example: `req_api_20230415123045_a1b2c3d4`

Components:
- Prefix: `req_` identifies it as a request ID
- Source: Identifies where the request originated (e.g., `api`, `bot_session123`)
- Timestamp: Format `YYYYMMDDHHmmSS` for precise creation time tracking
- Random suffix: Ensures uniqueness

### Batch IDs
Format: `bat_{source}_{timestamp}_{random}`

Example: `bat_scheduled_job_20230415123045_e5f6g7h8`

### Template IDs
Format: `tpl_{source}_{timestamp}_{random}`

Example: `tpl_api_20230414153012_f7g8h9j0`

### Purpose IDs
Format: `pur_{purpose_name}_{timestamp}_{random}`

Example: `pur_instagram_post_20230415123045_a1b2c3d4`

## Migration Steps

### 1. Replace UUID imports

Replace:
```python
import uuid

def generate_id():
    return str(uuid.uuid4())
```

With:
```python
from src.utils.id_utils import generate_request_id, generate_batch_id

def generate_request_id_for_api():
    return generate_request_id(source="api")
    
def generate_batch_id_for_scheduler():
    return generate_batch_id(source="scheduled_job")
```

### 2. Update ID creation in services

Replace:
```python
request_id = str(uuid.uuid4())
```

With:
```python
request_id = generate_request_id(source="api")
```

### 3. Update ID validation logic

Replace:
```python
def is_valid_id(id_str):
    try:
        uuid.UUID(id_str)
        return True
    except ValueError:
        return False
```

With:
```python
from src.utils.id_utils import is_valid_request_id, is_valid_batch_id

def is_valid_id(id_str):
    return is_valid_request_id(id_str) or is_valid_batch_id(id_str)
```

### 4. Extract metadata from standardized IDs

New functionality:
```python
from src.utils.id_utils import extract_metadata_from_id

# Extract useful information from IDs
metadata = extract_metadata_from_id("req_api_20230415123045_a1b2c3d4")
print(f"Source: {metadata['source']}")
print(f"Timestamp: {metadata['timestamp']}")
print(f"Created at: {metadata['created_at']}")  # datetime object
```

### 5. Update tests

- Update test fixtures to use the new ID format
- Add tests for ID utility functions
- Update assertions that validate ID format

### 6. Update documentation

- Update API documentation to reflect the new ID format
- Update client integration guides
- Update examples in tutorials

## Benefits of Migration

- Better traceability: IDs now contain source information
- Temporal context: Creation time is embedded in the ID
- Self-documenting: The prefix indicates the type of resource
- Debugging: Easier to correlate issues with specific sources and times
- Consistent format: Standardized across all microservices

## Common Migration Challenges

### Database Migration

If you store IDs in databases, you may need to:

1. Add a migration script to update existing records
2. Update database schemas if ID lengths have changed
3. Update any foreign key constraints or indexes

### API Compatibility

To maintain compatibility during migration:

1. Accept both formats during a transition period
2. Use feature flags to enable the new format incrementally
3. Implement ID format conversion functions for backward compatibility

## Additional Resources

- [ID Utilities Documentation](/microservices/agent/docs/architecture/id_utilities.md)
- [API Documentation](/microservices/agent/docs/api/README.md) 