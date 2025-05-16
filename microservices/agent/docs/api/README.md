# Agent Microservice API Documentation

## Overview

The Agent microservice provides a RESTful API for processing requests, managing templates, and coordinating service execution. This documentation outlines the available endpoints, request/response formats, and usage examples.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API endpoints require authentication using Bearer token:

```
Authorization: Bearer <your_token>
```

## ID Format

The Agent microservice uses standardized ID formats that contain embedded metadata:

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

These IDs provide better traceability and debugging capabilities as they contain information about the source and creation time.

## Endpoints

### Requests

#### Create Request
```http
POST /requests/process
```

**Request Body:**
```json
{
    "template_id": "tpl_api_20230414153012_f7g8h9j0",
    "data": {
        "key": "value"
    },
    "metadata": {
        "priority": "high",
        "tags": ["tag1", "tag2"],
        "request_id": "req_client_20230415122030_a7b9c1d3"
    }
}
```

**Response:**
```json
{
    "id": "req_api_20230415123045_a1b2c3d4",
    "status": "PENDING",
    "created_at": "2024-03-20T12:00:00Z",
    "template_id": "tpl_api_20230414153012_f7g8h9j0",
    "data": {
        "key": "value"
    },
    "metadata": {
        "priority": "high",
        "tags": ["tag1", "tag2"],
        "request_id": "req_client_20230415122030_a7b9c1d3"
    }
}
```

#### Get Request
```http
GET /requests/{request_id}
```

**Response:**
```json
{
    "id": "req_api_20230415123045_a1b2c3d4",
    "status": "COMPLETED",
    "created_at": "2024-03-20T12:00:00Z",
    "completed_at": "2024-03-20T12:01:00Z",
    "template_id": "tpl_api_20230414153012_f7g8h9j0",
    "data": {
        "key": "value"
    },
    "metadata": {
        "priority": "high",
        "tags": ["tag1", "tag2"],
        "request_id": "req_client_20230415122030_a7b9c1d3"
    },
    "result": {
        "output": "processed result"
    }
}
```

#### List Requests
```http
GET /requests
```

**Query Parameters:**
- `status`: Filter by status (PENDING, PROCESSING, COMPLETED, FAILED)
- `template_id`: Filter by template ID
- `start_date`: Filter by creation date (ISO format)
- `end_date`: Filter by creation date (ISO format)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

**Response:**
```json
{
    "items": [
        {
            "id": "req_api_20230415123045_a1b2c3d4",
            "status": "COMPLETED",
            "created_at": "2024-03-20T12:00:00Z",
            "template_id": "tpl_api_20230414153012_f7g8h9j0"
        }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
}
```

### Batch Processing

#### Process Batch
```http
POST /requests/batch
```

**Request Body:**
```json
{
    "source": "management_system",
    "template_id": "etsy_listing",
    "items": [
        {
            "item_id": "item_001",
            "data": {
                "product_name": "Handmade Wooden Bowl",
                "description": "Beautiful handcrafted wooden bowl made from reclaimed oak.",
                "price": 45.99
            },
            "metadata": {
                "priority": "high"
            }
        },
        {
            "item_id": "item_002",
            "data": {
                "product_name": "Ceramic Mug",
                "description": "Hand-painted ceramic mug with unique design.",
                "price": 25.99
            },
            "metadata": {
                "priority": "medium"
            }
        }
    ],
    "batch_metadata": {
        "request_source": "scheduled_task",
        "user_id": "admin"
    }
}
```

**Response:**
```json
{
    "status": "SUCCESS",
    "message": "Batch processing complete. 2 succeeded, 0 failed.",
    "results": [
        {
            "item_id": "item_001",
            "status": "SUCCESS",
            "data": {
                "listing_id": "12345",
                "title": "Handmade Wooden Bowl - Reclaimed Oak"
            }
        },
        {
            "item_id": "item_002",
            "status": "SUCCESS",
            "data": {
                "listing_id": "12346",
                "title": "Ceramic Mug - Hand Painted"
            }
        }
    ],
    "errors": [],
    "batch_id": "bat_api_20230415123045_a1b2c3d4",
    "summary": {
        "total_items": 2,
        "success_count": 2,
        "error_count": 0,
        "success_rate": 1.0,
        "validation": {
            "valid_users": 2,
            "invalid_users": 0
        }
    }
}
```

#### Process Batch Asynchronously
```http
POST /requests/async/batch
```

This endpoint accepts the same request body as the synchronous batch processing endpoint but processes the batch in the background.

**Response:**
```json
{
    "status": "PENDING",
    "message": "Batch accepted for processing",
    "results": [],
    "errors": [],
    "batch_id": "bat_api_20230415123045_e5f6g7h8",
    "summary": {
        "total_items": 2,
        "status": "pending"
    }
}
```

### Templates

#### Create Template
```http
POST /templates
```

**Request Body:**
```json
{
    "name": "string",
    "description": "string",
    "service_type": "ANALYSIS",
    "version": "1.0.0",
    "parameters": {
        "required": ["param1", "param2"],
        "optional": ["param3"]
    },
    "config": {
        "timeout": 30,
        "retries": 3
    }
}
```

**Response:**
```json
{
    "id": "tpl_api_20230415123045_a1b2c3d4",
    "name": "string",
    "description": "string",
    "service_type": "ANALYSIS",
    "version": "1.0.0",
    "created_at": "2024-03-20T12:00:00Z",
    "parameters": {
        "required": ["param1", "param2"],
        "optional": ["param3"]
    },
    "config": {
        "timeout": 30,
        "retries": 3
    }
}
```

#### Get Template
```http
GET /templates/{template_id}
```

**Response:**
```json
{
    "id": "tpl_api_20230415123045_a1b2c3d4",
    "name": "string",
    "description": "string",
    "service_type": "ANALYSIS",
    "version": "1.0.0",
    "created_at": "2024-03-20T12:00:00Z",
    "parameters": {
        "required": ["param1", "param2"],
        "optional": ["param3"]
    },
    "config": {
        "timeout": 30,
        "retries": 3
    }
}
```

#### List Templates
```http
GET /templates
```

**Query Parameters:**
- `service_type`: Filter by service type (ANALYSIS, GENERATIVE, COMMUNICATION)
- `version`: Filter by version
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

**Response:**
```json
{
    "items": [
        {
            "id": "tpl_api_20230415123045_b2c3d4e5",
            "name": "string",
            "service_type": "ANALYSIS",
            "version": "1.0.0"
        }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
}
```

### Batch Jobs and Scheduling

The batch jobs and scheduling system is primarily configured through the file system rather than the API. Job configurations are stored in `data/batch/batch_config.json`. For detailed information about batch configuration options, please see the [Batch Configuration Guide](../usage/batch_configuration_guide.md).

The batch scheduler runs automatically when the service starts and processes jobs according to their scheduled times.

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request parameters",
        "details": {
            "field": "error message"
        }
    }
}
```

### 401 Unauthorized
```json
{
    "error": {
        "code": "UNAUTHORIZED",
        "message": "Invalid or missing authentication token"
    }
}
```

### 403 Forbidden
```json
{
    "error": {
        "code": "FORBIDDEN",
        "message": "Insufficient permissions"
    }
}
```

### 404 Not Found
```json
{
    "error": {
        "code": "NOT_FOUND",
        "message": "Resource not found",
        "details": {
            "resource_type": "request",
            "resource_id": "req_api_20230415123045_f7g8h9i0"
        }
    }
}
```

### 500 Internal Server Error
```json
{
    "error": {
        "code": "INTERNAL_ERROR",
        "message": "An unexpected error occurred"
    }
}
```

## Rate Limiting

The API implements rate limiting based on the following rules:
- 100 requests per minute per IP
- 1000 requests per hour per user

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1616239020
```

## Webhooks

The service supports webhooks for asynchronous notifications. See [Webhook Documentation](./webhooks.md) for details. 