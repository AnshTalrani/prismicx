# Client Guide for Agent Microservice

This guide explains how to interact with the Agent microservice as a client application.

## API Endpoints

### Request Processing

#### Process a Single Request

```
POST /api/v1/process
```

**Request Body:**

```json
{
  "text": "Generate an Instagram post about eco-friendly products",
  "purpose_id": "pur_instagram_post_20230415123045_a1b2c3d4",  // Optional: Will be auto-detected if not provided
  "data": {
    "topic": "eco-friendly products",
    "tone": "inspiring",
    "target_audience": "environmentally conscious consumers",
    "key_points": [
      "Our products are made from sustainable materials",
      "We use minimal packaging to reduce waste",
      "For every purchase, we plant a tree"
    ]
  },
  "metadata": {
    "source": "mobile-app",
    "user_id": "user123",
    "locale": "en-US"
  }
}
```

**Response:**

```json
{
  "request_id": "req_api_20230415123045_a1b2c3d4",
  "template_id": "tpl_api_20230414153012_f7g8h9j0",
  "service_type": "GENERATIVE",
  "success": true,
  "status": "completed",
  "post_text": "✨ Attention environmentally conscious consumers! ✨\n\nToday we're spotlighting our amazing eco-friendly products that are changing the game! 🌱\n\n🔹 Our products are made from sustainable materials\n🔹 We use minimal packaging to reduce waste\n🔹 For every purchase, we plant a tree\n\nTag a friend who cares about eco-friendly products and let us know what you think in the comments! 👇",
  "hashtags": ["#EcoFriendly", "#SustainableLiving", "#GreenProducts", "#Eco-friendlyproducts", "#Environmentallyconsciousconsum ers"],
  "image_prompt": "A professional, inspiring product photo featuring eco-friendly products styled for environmentally conscious consumers, with natural lighting, soft shadows, and earthy color palette."
}
```

### Batch Processing

#### Create a Batch

```
POST /api/v1/batch
```

**Request Body:**

```json
{
  "template_id": "tpl_api_20230414153012_f7g8h9j0",
  "items": [
    {
      "id": "item1",
      "data": {
        "topic": "eco-friendly products",
        "tone": "inspiring",
        "target_audience": "environmentally conscious consumers",
        "key_points": [
          "Our products are made from sustainable materials",
          "We use minimal packaging to reduce waste",
          "For every purchase, we plant a tree"
        ]
      }
    },
    {
      "id": "item2",
      "data": {
        "topic": "sustainable fashion",
        "tone": "professional",
        "target_audience": "fashion enthusiasts",
        "key_points": [
          "Ethically sourced materials",
          "Fair trade manufacturing",
          "Recyclable packaging",
          "Carbon-neutral shipping"
        ]
      }
    }
  ],
  "batch_metadata": {
    "priority": "normal",
    "callback_url": "https://example.com/webhook",
    "user_id": "user123"
  }
}
```

**Response:**

```json
{
  "batch_id": "bat_api_20230415123045_e5f6g7h8",
  "status": "processing",
  "total_items": 2,
  "completed_items": 0,
  "failed_items": 0,
  "estimated_completion_time": "2023-01-01T00:01:30Z"
}
```

#### Get Batch Status

```
GET /api/v1/batch/{batch_id}/status
```

**Response:**

```json
{
  "batch_id": "bat_api_20230415123045_e5f6g7h8",
  "status": "completed",
  "total_items": 2,
  "completed_items": 2,
  "failed_items": 0,
  "completion_time": "2023-01-01T00:01:15Z",
  "items": [
    {
      "id": "item1",
      "status": "completed",
      "processing_time": "1.2s"
    },
    {
      "id": "item2",
      "status": "completed",
      "processing_time": "1.5s"
    }
  ]
}
```

#### Get Batch Results

```
GET /api/v1/batch/{batch_id}/results
```

**Response:**

```json
{
  "batch_id": "bat_api_20230415123045_e5f6g7h8",
  "status": "completed",
  "results": [
    {
      "item_id": "item1",
      "status": "completed",
      "post_text": "✨ Attention environmentally conscious consumers! ✨\n\nToday we're spotlighting our amazing eco-friendly products that are changing the game! 🌱\n\n🔹 Our products are made from sustainable materials\n🔹 We use minimal packaging to reduce waste\n🔹 For every purchase, we plant a tree\n\nTag a friend who cares about eco-friendly products and let us know what you think in the comments! 👇",
      "hashtags": ["#EcoFriendly", "#SustainableLiving", "#GreenProducts"],
      "image_prompt": "A professional, inspiring product photo featuring eco-friendly products styled for environmentally conscious consumers..."
    },
    {
      "item_id": "item2",
      "status": "completed",
      "post_text": "Fashion that doesn't cost the Earth 🌏\n\nIntroducing our sustainable fashion collection designed for fashion enthusiasts who care about their impact...",
      "hashtags": ["#SustainableFashion", "#EthicalFashion", "#FashionWithPurpose"],
      "image_prompt": "A professional fashion shoot featuring sustainable clothing items against a minimalist backdrop..."
    }
  ]
}
```

### Template Management

#### Get Template

```
GET /api/v1/templates/{template_id}
```

**Response:**

```json
{
  "id": "tpl_api_20230414153012_f7g8h9j0",
  "version": "1.0",
  "description": "Generates engaging Instagram posts based on topic and brand details",
  "service_type": "GENERATIVE",
  "processing_mode": "realtime",
  "metadata": {
    "tags": ["instagram", "social_media", "post_generation", "marketing"],
    "expected_response_time": "5s",
    "required_fields": ["topic"],
    "optional_fields": ["tone", "target_audience", "key_points"],
    "purpose_id": "instagram_post_creation"
  },
  "created_by": "system",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### List Templates

```
GET /api/v1/templates?service_type=GENERATIVE
```

**Response:**

```json
{
  "templates": [
    {
      "id": "instagram_post_generator",
      "description": "Generates engaging Instagram posts based on topic and brand details",
      "service_type": "GENERATIVE",
      "version": "1.0"
    },
    {
      "id": "twitter_post_generator",
      "description": "Generates concise Twitter posts based on topic and key message",
      "service_type": "GENERATIVE",
      "version": "1.0"
    }
  ],
  "total": 2
}
```

## Client Integration Examples

### Python Example

```python
import requests
import json

# Configuration
BASE_URL = "https://agent-service.example.com/api/v1"
API_KEY = "your_api_key"

def process_request(text, data, metadata=None):
    """Process a single request."""
    url = f"{BASE_URL}/process"
    
    # Add standardized request ID if one wasn't provided in metadata
    if not metadata or "request_id" not in metadata:
        # You can use your own ID generator or the agent will assign one
        metadata = metadata or {}
        # Optional: Generate a client-side request ID for improved traceability
        # metadata["request_id"] = f"client_{timestamp}_{random_suffix}"
    
    payload = {
        "text": text,
        "data": data,
        "metadata": metadata or {}
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Example usage
result = process_request(
    text="Generate an Instagram post about eco-friendly products",
    data={
        "topic": "eco-friendly products",
        "tone": "inspiring",
        "target_audience": "environmentally conscious consumers",
        "key_points": [
            "Our products are made from sustainable materials",
            "We use minimal packaging to reduce waste",
            "For every purchase, we plant a tree"
        ]
    },
    metadata={
        "source": "python-client",
        "user_id": "user123"
    }
)

print(json.dumps(result, indent=2))
```

### JavaScript Example

```javascript
async function processRequest(text, data, metadata = {}) {
  const url = 'https://agent-service.example.com/api/v1/process';
  
  // Add standardized request ID if one wasn't provided in metadata
  if (!metadata.request_id) {
    // You can use your own ID generator or the agent will assign one
    // Optional: Generate a client-side request ID for improved traceability
    // metadata.request_id = `client_${timestamp}_${randomSuffix}`;
  }
  
  const payload = {
    text,
    data,
    metadata
  };
  
  const headers = {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  };
  
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload)
  });
  
  return response.json();
}

// Example usage
processRequest(
  'Generate an Instagram post about eco-friendly products',
  {
    topic: 'eco-friendly products',
    tone: 'inspiring',
    target_audience: 'environmentally conscious consumers',
    key_points: [
      'Our products are made from sustainable materials',
      'We use minimal packaging to reduce waste',
      'For every purchase, we plant a tree'
    ]
  },
  {
    source: 'javascript-client',
    user_id: 'user123'
  }
)
.then(result => console.log(result))
.catch(error => console.error(error));
```

## Best Practices

1. **Always Include Metadata**: Provide useful metadata like `source` and `user_id` to help with debugging and analytics.
2. **Handle Errors Gracefully**: The service will return appropriate HTTP status codes and error messages. Ensure your client handles these properly.
3. **Use Batch Processing for Multiple Items**: Instead of making multiple individual requests, use batch processing for better performance.
4. **Include Purpose ID When Known**: If you know the purpose ID, include it to bypass automatic detection for faster processing.
5. **Specify Required Fields**: Always include all required fields as specified in the template's metadata.

## Error Handling

The service uses standard HTTP status codes:

- **200 OK**: Request succeeded
- **400 Bad Request**: Invalid input parameters
- **401 Unauthorized**: Invalid or missing API key
- **404 Not Found**: Resource not found (e.g., template ID)
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server-side error

Error responses include detailed information:

```json
{
  "error": {
    "code": "invalid_parameter",
    "message": "Required field 'topic' is missing",
    "details": {
      "field": "data.topic",
      "reason": "required"
    },
    "request_id": "req_api_20230415123045_a1b2c3d4"
  }
}
```

Always include the `request_id` when reporting issues to the support team. The standardized format includes information about the source and timestamp of the request. 