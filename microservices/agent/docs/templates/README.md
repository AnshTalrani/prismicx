# Template Management Guide

## Overview

This guide explains the template management system in the Agent microservice. Templates define the structure and validation rules for processing different types of requests, ensuring consistency and reliability in request handling.

## Directory Structure

```
src/
├── domain/
│   └── templates/
│       ├── entities/
│       │   └── template.py        # Template domain entity
│       └── repositories/
│           └── template_repo.py   # Template repository interface
├── application/
│   └── services/
│       └── template_service.py    # Template management service
├── infrastructure/
│   └── templates/
│       ├── repositories/
│       │   └── mongo_template_repo.py  # MongoDB template repository
│       └── validators/
│           └── template_validator.py    # Template validation logic
└── templates/                     # Template JSON files
    ├── etsy/
    │   ├── product_listing.json
    │   └── shop_management.json
    ├── instagram/
    │   ├── post_analysis.json
    │   └── engagement_metrics.json
    └── email/
        ├── campaign_template.json
        └── newsletter_template.json
```

## Template Structure

Templates are defined in JSON format with the following structure:

```json
{
    "name": "Template Name",
    "description": "Template Description",
    "service_type": "GENERATIVE|ANALYSIS|COMMUNICATION",
    "version": "1.0.0",
    "parameters": {
        "required": ["param1", "param2"],
        "optional": ["param3"]
    },
    "config": {
        "timeout": 300,
        "retries": 3,
        "validation_rules": {
            "param1": {
                "type": "string",
                "min_length": 5,
                "max_length": 140
            }
        }
    }
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| name | string | Unique template identifier |
| description | string | Template purpose and usage |
| service_type | enum | Type of service (GENERATIVE, ANALYSIS, COMMUNICATION) |
| version | string | Semantic version (x.y.z) |
| parameters | object | Required and optional parameters |
| config | object | Template configuration |

## Creating a New Template

1. **Create Template File**
   ```bash
   mkdir -p src/templates/<category>
   touch src/templates/<category>/<template_name>.json
   ```

2. **Define Template Content**
   Create the template JSON following the structure above.

3. **Validate Template**
   Use the template validation service:
   ```python
   from infrastructure.templates.validators.template_validator import TemplateValidator
   
   validator = TemplateValidator()
   is_valid, errors = validator.validate_template('src/templates/etsy/product_listing.json')
   if not is_valid:
       print(f"Template validation failed: {errors}")
   ```

4. **Register Template**
   Use the template service to register the template:
   ```python
   from application.services.template_service import TemplateService
   
   template_service = TemplateService()
   template_id = await template_service.register_template(
       template_path='src/templates/etsy/product_listing.json'
   )
   ```

## Example Template: Etsy Product Listing

```json
{
    "name": "Etsy Product Listing",
    "description": "Template for creating Etsy product listings",
    "service_type": "GENERATIVE",
    "version": "1.0.0",
    "parameters": {
        "required": [
            "product_name",
            "product_description",
            "price",
            "category"
        ],
        "optional": [
            "tags",
            "shipping_profile"
        ]
    },
    "config": {
        "timeout": 300,
        "retries": 3,
        "validation_rules": {
            "product_name": {
                "min_length": 5,
                "max_length": 140
            },
            "product_description": {
                "min_length": 50,
                "max_length": 2000
            },
            "price": {
                "min": 0.20,
                "max": 50000
            }
        }
    }
}
```

## Using Templates in Code

### 1. Load Template
```python
template = await template_service.get_template("etsy.product_listing")
```

### 2. Validate Request Against Template
```python
from application.dtos.request_dto import RequestDTO

request_data = {
    "template_id": "etsy.product_listing",
    "data": {
        "product_name": "Handmade Ceramic Mug",
        "product_description": "Beautiful handcrafted ceramic mug...",
        "price": 24.99,
        "category": "Home & Living > Kitchen & Dining"
    }
}

request_dto = RequestDTO.from_dict(request_data)
is_valid = await template_service.validate_request(request_dto)
```

### 3. Process Request Using Template
```python
response = await request_service.process_request(request_dto)
```

## Best Practices

1. **Version Control**
   - Keep templates in version control
   - Use meaningful commit messages
   - Review changes before deployment

2. **Documentation**
   - Document template purpose
   - List all parameters
   - Provide usage examples

3. **Testing**
   - Write unit tests for template validation
   - Test templates in staging environment
   - Validate all parameters
   - Check error handling

4. **Maintenance**
   - Review templates regularly
   - Update documentation
   - Remove unused templates
   - Monitor template usage

## Troubleshooting

### Common Issues

1. **Template Validation Errors**
   - Check JSON syntax
   - Verify required fields
   - Validate parameter constraints
   - Check service type enum values

2. **Registration Issues**
   - Verify template file exists
   - Check file permissions
   - Validate JSON structure
   - Check for duplicate templates

3. **Processing Errors**
   - Check request data format
   - Verify parameter values
   - Check service dependencies
   - Monitor timeout settings

## Support

For template management issues:
1. Check service logs
2. Review validation errors
3. Contact the development team
4. Submit bug reports with examples

## References

- [JSON Schema Documentation](https://json-schema.org/)
- [Template Development Guide](../development/templates.md)
- [API Documentation](../api/README.md)
- [Architecture Overview](../architecture/README.md) 