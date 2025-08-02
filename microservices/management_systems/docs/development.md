# Development Guide

This guide provides information for developers who are working on or extending the Management Systems microservice.

## Development Environment Setup

### Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- Git
- MongoDB (local or container)
- Redis (local or container)

### Local Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd microservices/management_systems
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a local `.env` file:

```bash
cp .env.example .env
```

5. Configure your local environment variables in the `.env` file.

6. Start MongoDB and Redis (using Docker Compose):

```bash
docker-compose up -d mongodb redis
```

7. Run the application:

```bash
uvicorn src.main:app --reload
```

## Project Structure

```
management_systems/
│
├── src/                  # Source code
│   ├── api/              # API routes
│   │   ├── api_router.py     # Main API router
│   │   └── data_router.py    # Data operation endpoints
│   │
│   ├── common/           # Shared utilities
│   │   └── db_client_wrapper.py  # Database client
│   │
│   ├── config/           # Configuration
│   │   └── settings.py   # Application settings
│   │
│   ├── models/           # Data models
│   │   ├── management_system.py  # System models
│   │   └── config_db.py         # Configuration models
│   │
│   ├── plugins/          # Plugin system
│   │   ├── interfaces/   # Plugin interfaces
│   │   └── config_service.py  # Configuration plugin
│   │
│   ├── services/         # Business logic
│   │   ├── management_service.py  # System management
│   │   └── data_service.py       # Data operations
│   │
│   └── main.py           # Application entry point
│
├── alembic/              # Database migrations
├── tests/                # Test files
├── docs/                 # Documentation
└── docker-compose.yml    # Docker configuration
```

## Development Workflow

1. **Create a Feature Branch**:

```bash
git checkout -b feature/your-feature-name
```

2. **Make Changes**: Implement your feature or fix.

3. **Run Tests**:

```bash
pytest
```

4. **Lint Your Code**:

```bash
flake8 src/
```

5. **Submit a Pull Request**: Push your branch and create a PR.

## Adding New API Endpoints

1. Define the endpoint in the appropriate router file:

```python
# src/api/api_router.py
@router.get("/new-endpoint", response_model=YourResponseModel)
async def new_endpoint():
    """Your endpoint documentation."""
    # Implement endpoint logic
    return {"status": "success", "data": ...}
```

2. If needed, create or update models in the `models` directory:

```python
# src/models/your_model.py
from pydantic import BaseModel

class YourResponseModel(BaseModel):
    status: str
    data: Dict[str, Any]
```

## Extending the Configuration System

### Adding a New Configuration Endpoint

1. Define the endpoint in `src/routers/config.py`:

```python
@router.get("/tenants/{tenant_id}/configs/{config_key}/special")
async def special_config_operation(
    tenant_id: str,
    config_key: str,
    token: str = Depends(oauth2_scheme),
    plugin_manager = Depends(get_plugin_manager)
):
    """Special operation on a tenant configuration."""
    config_service = plugin_manager.get_plugin("config_service")
    if not config_service:
        raise HTTPException(status_code=503, detail="Configuration service unavailable")
        
    # Implement your special operation
    result = await config_service.special_operation(tenant_id, config_key)
    return {"result": result}
```

2. Add the new operation to the `ConfigServicePlugin` interface:

```python
# src/plugins/interfaces/config_service_plugin.py
@abstractmethod
async def special_operation(self, tenant_id: str, config_key: str) -> Any:
    """
    Perform a special operation on a configuration.
    
    Args:
        tenant_id: Tenant identifier
        config_key: Configuration key
        
    Returns:
        Result of the special operation
    """
    pass
```

3. Implement the operation in the plugin:

```python
# src/plugins/config_service.py
async def special_operation(self, tenant_id: str, config_key: str) -> Any:
    """Perform a special operation on a configuration."""
    try:
        # Implement your operation
        config = await self.get_tenant_config(tenant_id, config_key)
        if not config:
            return None
            
        # Process the configuration
        result = process_config(config)
        return result
    except Exception as e:
        logger.error(f"Error in special operation for {tenant_id}/{config_key}: {str(e)}")
        return None
```

## Working with Multi-tenancy

When developing for this multi-tenant microservice, follow these guidelines:

1. **Always Include Tenant Context**: Every data operation should include tenant context.

```python
# Good practice:
async def get_tenant_data(tenant_id: str, data_id: str):
    tenant_db = await db_client.get_tenant_db(tenant_id)
    return await tenant_db.collection.find_one({"id": data_id})

# Avoid:
async def get_data(data_id: str):  # Missing tenant context
    return await db.collection.find_one({"id": data_id})
```

2. **Use Middleware for Tenant Extraction**: The tenant middleware extracts the tenant ID from requests.

3. **Test with Multiple Tenants**: Ensure your features work correctly across tenant boundaries.

## Database Operations

### Working with MongoDB

1. **Config Database**:

```python
from ..common.db_client_wrapper import db_client

# Using the config database
await db_client.config_db.collection_name.find_one({"field": "value"})
```

2. **Tenant Database**:

```python
# Get tenant-specific database
tenant_db = await db_client.get_tenant_db(tenant_id)

# Perform operations
await tenant_db.collection_name.insert_one({"field": "value"})
```

### Database Migrations

Alembic is used for database migrations:

1. Create a new migration:

```bash
alembic revision --autogenerate -m "Description of the change"
```

2. Apply migrations:

```bash
alembic upgrade head
```

## Caching

Use the Redis cache for performance optimization:

```python
from ..cache.redis_cache import cache

# Set cache
await cache.set(f"key:{id}", data, ttl=300)  # Cache for 5 minutes

# Get from cache
cached_data = await cache.get(f"key:{id}")
if cached_data:
    return cached_data
    
# Delete from cache
await cache.delete(f"key:{id}")
```

## Error Handling

Follow these error handling practices:

1. **Use Custom Exceptions**:

```python
class YourCustomError(Exception):
    """Custom exception with descriptive message."""
    pass
    
try:
    # Operation that might fail
    if problem_condition:
        raise YourCustomError("Descriptive error message")
except YourCustomError as e:
    # Handle the specific error
    logger.error(f"Custom error occurred: {str(e)}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    # Handle unexpected errors
    logger.error(f"Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

2. **Log Errors Appropriately**: Use proper logging levels.

3. **Return Clear Error Messages**: Give clear information to API consumers.

## Testing

Write tests for your code:

```python
# tests/test_your_feature.py
import pytest
from src.your_module import your_function

def test_your_function():
    result = your_function(test_input)
    assert result == expected_output
    
@pytest.mark.asyncio
async def test_async_function():
    result = await your_async_function(test_input)
    assert result == expected_output
```

Run specific tests:

```bash
pytest tests/test_your_feature.py
```

## Documentation

- Add docstrings to all functions, classes, and modules
- Update API documentation when adding or modifying endpoints
- Create or update architectural documentation for significant changes

## Contribution Guidelines

1. Follow PEP 8 style guidelines
2. Write tests for new features
3. Update documentation
4. Keep pull requests focused on a single feature or fix
5. Get a code review before merging 