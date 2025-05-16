# ID Utilities and Standardized ID Format

## Overview

The agent microservice uses standardized ID formats for various entities like requests, batches, and contexts. This document outlines the ID generation utilities, formats, and best practices.

## ID Utilities

ID generation and validation utilities are provided in the `src/utils/id_utils.py` module. This centralized approach ensures consistent ID formats throughout the system and provides additional metadata in the IDs themselves.

### Key Functions

- `generate_request_id(source)`: Generates standardized request IDs
- `generate_batch_id(source)`: Generates standardized batch IDs
- `is_valid_request_id(id_str)`: Validates request ID format
- `is_valid_batch_id(id_str)`: Validates batch ID format
- `extract_timestamp_from_id(id_str)`: Extracts timestamp from an ID
- `extract_source_from_id(id_str)`: Extracts source information from an ID
- `get_id_metadata(id_str)`: Gets comprehensive metadata from an ID

## ID Formats

### Request IDs

Format: `req_{source}_{timestamp}_{random}`

Example: `req_api_20230415123045_a1b2c3d4`

Components:
- Prefix: `req_` (identifies as a request ID)
- Source: Identifies the component that generated the ID (e.g., `api`, `bot_session123`, `repository`)
- Timestamp: Format `YYYYMMDDHHmmSS` for precise creation time tracking
- Random suffix: Ensures uniqueness even with identical sources and timestamps

### Batch IDs

Format: `bat_{source}_{timestamp}_{random}`

Example: `bat_scheduled_job_20230415123045_e5f6g7h8`

Components:
- Prefix: `bat_` (identifies as a batch ID)
- Source: Identifies the batch source/type (e.g., `api`, `scheduled_job`, `manual`)
- Timestamp: Format `YYYYMMDDHHmmSS` for precise creation time tracking
- Random suffix: Ensures uniqueness even with identical sources and timestamps

## Benefits of Standardized IDs

1. **Self-contained metadata**: IDs contain source and timestamp information
2. **Improved traceability**: Source information helps trace request origins
3. **Temporal information**: Timestamp in ID enables time-based analysis without database lookups
4. **Consistent format**: All system components use the same ID format
5. **Validation**: Easy validation of ID format correctness
6. **Debugging**: Easier to identify and trace issues across system components

## Usage Examples

### Generating IDs

```python
from src.utils.id_utils import generate_request_id, generate_batch_id

# Generate request ID from API endpoint
request_id = generate_request_id(source="api")

# Generate request ID from bot handler
request_id = generate_request_id(source=f"bot_{session_id}")

# Generate batch ID for scheduled job
batch_id = generate_batch_id(source="scheduled_job")
```

### Extracting Information from IDs

```python
from src.utils.id_utils import extract_timestamp_from_id, extract_source_from_id, get_id_metadata

# Extract creation time
timestamp = extract_timestamp_from_id(request_id)  # "20230415123045"

# Extract source
source = extract_source_from_id(request_id)  # "api"

# Get complete metadata
metadata = get_id_metadata(request_id)
# {
#   "valid": True,
#   "type": "request",
#   "source": "api",
#   "timestamp": "20230415123045",
#   "random": "a1b2c3d4"
# }
```

## Implementation in Different Components

- **API Controllers**: Generate request IDs with source="api" or source="api_async"
- **Bot Handlers**: Generate request IDs with source="bot_{session_id}"
- **Batch Processor**: Generate batch IDs with source based on batch type
- **Repositories**: Generate request IDs with source="repository" when needed
- **Clients**: Use request IDs from context or generate new ones with appropriate source

## Migration from Legacy IDs

The system previously used random UUIDs for identification. All components have been updated to use the new standardized ID format. Legacy components have been removed from the codebase. 