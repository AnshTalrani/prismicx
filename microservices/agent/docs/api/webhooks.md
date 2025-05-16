# Webhook Documentation

The Agent microservice supports webhooks for asynchronous notifications about requests and batch processing jobs. This document explains how to configure and use webhooks.

## Configuration

You can configure a webhook URL at two levels:

1. **System-wide**: Set in the service configuration
2. **Per-request**: Specified in the request metadata
3. **Per-batch**: Specified in the batch metadata

### Request-level Configuration

```json
{
  "metadata": {
    "webhook_url": "https://example.com/webhooks/agent-notifications",
    "webhook_authentication": {
      "type": "bearer",
      "token": "your_secret_token"
    }
  }
}
```

### Batch-level Configuration

```json
{
  "batch_metadata": {
    "webhook_url": "https://example.com/webhooks/batch-notifications",
    "webhook_authentication": {
      "type": "bearer",
      "token": "your_secret_token"
    }
  }
}
```

## Event Types

The service sends webhook notifications for the following events:

| Event Type | Description |
|------------|-------------|
| `request.created` | A new request has been created |
| `request.started` | Processing of a request has started |
| `request.completed` | A request has been completed successfully |
| `request.failed` | A request has failed |
| `batch.created` | A new batch job has been created |
| `batch.started` | Processing of a batch job has started |
| `batch.progress` | Progress update for a batch job |
| `batch.completed` | A batch job has been completed successfully |
| `batch.failed` | A batch job has failed |

## Payload Structure

### Request Events

```json
{
  "event_type": "request.completed",
  "timestamp": "2023-04-15T12:30:45Z",
  "request": {
    "id": "req_api_20230415123045_a1b2c3d4",
    "status": "COMPLETED",
    "created_at": "2023-04-15T12:30:45Z",
    "completed_at": "2023-04-15T12:31:15Z",
    "template_id": "tpl_api_20230414153012_f7g8h9j0",
    "purpose_id": "pur_instagram_post_20230415123045_a1b2c3d4"
  },
  "result": {
    "success": true,
    "data": {
      // The result data specific to the template
    }
  }
}
```

### Batch Events

```json
{
  "event_type": "batch.progress",
  "timestamp": "2023-04-15T12:35:45Z",
  "batch": {
    "id": "bat_api_20230415123045_e5f6g7h8",
    "status": "PROCESSING",
    "created_at": "2023-04-15T12:30:45Z",
    "progress": {
      "total_items": 100,
      "completed_items": 45,
      "failed_items": 2,
      "completion_percentage": 45,
      "estimated_completion_time": "2023-04-15T12:45:30Z"
    }
  }
}
```

## Security

### Authentication

The service supports the following authentication methods for webhooks:

1. **Bearer Token**: Include your token in the webhook configuration
2. **Basic Auth**: Include username and password in the webhook configuration
3. **HMAC Signatures**: Each webhook includes a signature header

### HMAC Signature Verification

Each webhook request includes an `X-Agent-Signature` header. The signature is computed as:

```
HMAC-SHA256(webhook_secret, request_body)
```

To verify the signature:

1. Compute the HMAC signature of the raw request body using your webhook secret
2. Compare with the value in the `X-Agent-Signature` header
3. If they match, the webhook is authentic

### Example Verification (Python)

```python
import hmac
import hashlib

def verify_webhook(request_body, signature, webhook_secret):
    computed_signature = hmac.new(
        webhook_secret.encode(),
        request_body.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, signature)
```

## Retry Policy

If a webhook delivery fails, the service will retry with the following schedule:

1. Immediate retry
2. After 1 minute
3. After 5 minutes
4. After 15 minutes
5. After 1 hour

After 5 failed attempts, the webhook will be marked as failed, and the event will be logged but not retried.

## Best Practices

1. **Respond quickly**: Your webhook endpoint should acknowledge receipt (HTTP 200) as soon as possible
2. **Process asynchronously**: Handle the actual processing in a background job
3. **Verify signatures**: Always verify the HMAC signature for security
4. **Handle idempotency**: The same webhook may be delivered multiple times due to retries
5. **Log incoming webhooks**: Keep logs of all received webhooks for troubleshooting
6. **Set up monitoring**: Monitor webhook reception to detect failures 