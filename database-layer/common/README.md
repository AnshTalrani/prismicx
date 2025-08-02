# Database Layer Common

This package provides common libraries and utilities for interacting with the database layer services in the PrismicX platform.

## Modules

### Task Client

The Task Client module (`task_client`) provides a simple interface for microservices to interact with the Task Repository Service. It allows services to:

- Create tasks
- Retrieve tasks (individual or batches)
- Claim tasks for processing
- Complete tasks with results
- Mark tasks as failed
- Update task status

## Installation

To install this package from source:

```bash
pip install -e path/to/database-layer/common
```

## Usage

```python
from database_layer.common.task_client import create_task, get_task, complete_task

# Create a task
task_data = {
    "task_type": "analysis",
    "priority": 3,
    "request": {
        "content": {"text": "Sample text to analyze"},
        "metadata": {"source": "user-input"}
    }
}
task_id = await create_task(task_data)

# Get a task
task = await get_task(task_id)

# Complete a task
result = {"sentiment": "positive", "entities": ["Sample"]}
success = await complete_task(task_id, result)
``` 