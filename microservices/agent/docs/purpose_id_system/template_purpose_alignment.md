# Template-Purpose Alignment System

## Overview

The Template-Purpose Alignment System ensures that execution templates are properly aligned with purposes in the consultancy bot system. This alignment is critical for the correct functioning of the system, as it enables the bot to select and use the right templates for each purpose.

## System Components

The alignment system consists of the following components:

1. **Template Service**: Enhanced to check for alignment between templates and purposes
2. **Notification Service**: Sends notifications when misalignments are detected
3. **Application Service**: Coordinates alignment checks and notifications
4. **API Endpoints**: Provide interfaces for checking and monitoring alignment

![Alignment System Components](architecture/uml/diagrams/alignment_system.png)

## Class Structure

The alignment system includes the following key classes and interfaces:

- **FileTemplateRepository**: Stores templates in a file-based repository
- **FilePurposeRepository**: Stores purposes in a file-based repository with format flexibility
- **LogNotificationService**: Sends and logs alignment notifications
- **TemplateService**: Implements alignment check functionality
- **ApplicationService**: Coordinates alignment checks and notifications
- **Alignment API Router**: Provides HTTP endpoints for alignment operations
- **Service Factory**: Creates and initializes services and repositories

![Alignment System Class Diagram](architecture/uml/diagrams/alignment_system_classes.png)

## Alignment Check Process

The alignment check process identifies three types of misalignment:

1. **Templates without purposes**: Templates that exist but aren't associated with any purpose
2. **Purposes without templates**: Purposes that don't have any templates associated with them
3. **Purposes with missing templates**: Purposes that reference templates that don't exist

![Alignment Check Flow](architecture/uml/sequence_diagrams/alignment_flow.png)

## Automated Alignment Checks

The system performs alignment checks in the following scenarios:

1. **On startup**: When the application starts, an initial alignment check is performed
2. **Periodically**: Alignment checks run at configured intervals (default: once per hour)
3. **On template creation**: When a new template is added, it's checked for alignment
4. **On demand**: The alignment check can be triggered manually through the API

## Notification System

When misalignments are detected, the notification system:

1. **Logs the issues**: All misalignments are logged with appropriate severity
2. **Creates structured notifications**: Notifications include detailed information about the issues
3. **Prioritizes issues**: Different types of misalignments receive different priority levels
4. **Sends alerts**: Configured administrators receive alerts about the misalignments

## Key Methods

### Template Service

- `check_purpose_template_alignment()`: Checks alignment between purposes and templates
- `_find_templates_without_purposes()`: Identifies templates not used by any purpose
- `_find_purposes_without_templates()`: Identifies purposes with no templates
- `_find_purposes_with_missing_templates()`: Identifies purposes referencing non-existent templates

### Notification Service

- `send_alignment_notification()`: Sends notifications about alignment issues
- `_format_alignment_message()`: Formats alignment issues for notification
- `_get_priority_for_alignment_issues()`: Determines notification priority based on issue severity

### Application Service

- `check_and_notify_alignment()`: Coordinates alignment checks and notifications
- `_schedule_alignment_checks()`: Sets up periodic alignment checks
- `_run_periodic_alignment_checks()`: Runs background alignment checks

## Configuration

The alignment system can be configured through:

- **Alignment check interval**: How frequently automatic checks run (default: 3600 seconds)
- **Notification recipients**: Who receives alignment notifications
- **Notification file**: Where notification logs are stored

## Using the Alignment API

To run an alignment check and get the results:

```python
import httpx

async def check_alignment():
    """Run an alignment check and get the results."""
    async with httpx.AsyncClient() as client:
        # Run alignment check
        response = await client.post("/api/alignment/check")
        alignment_results = response.json()
        
        return alignment_results
```

## Running Alignment Tests

The alignment system has comprehensive unit, integration, and functional tests:

```bash
# Run all alignment tests
./scripts/run_all_alignment_tests.sh

# Run just unit tests
./scripts/run_alignment_tests.py --unit-only

# Run just integration tests
./scripts/run_alignment_tests.py --integration-only

# Run functional API tests
./scripts/run_functional_tests.py
```

For detailed information about the test implementation, see [Test Plan Execution](testing/test_plan_execution.md).

## Troubleshooting

Common alignment issues and their solutions:

| Issue | Cause | Solution |
|-------|-------|----------|
| Templates without purposes | New templates were created without assigning them to purposes | Associate the templates with appropriate purposes |
| Purposes without templates | Purposes were created without templates, or all their templates were removed | Add appropriate templates to the purposes |
| Purposes with missing templates | Purposes reference templates that don't exist (may have been deleted) | Either recreate the missing templates or update the purposes to reference existing templates |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/alignment/check | POST | Triggers an alignment check and returns the results |
| /api/alignment/status | GET | Returns the current alignment status with metadata | 