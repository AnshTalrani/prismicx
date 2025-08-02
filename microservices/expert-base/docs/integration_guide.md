# Expert Base Integration Guide

This guide provides detailed instructions for integrating other microservices with the Expert Base service.

## Overview

The Expert Base microservice provides specialized AI expertise for various platforms and domains. Other services can integrate with Expert Base using different patterns depending on their specific needs.

## Integration Patterns

### 1. Direct API Integration

This is the simplest integration pattern, where services make synchronous API calls to the Expert Base service.

```
┌─────────────────┐      ┌─────────────────┐
│ Your Service    │─────▶│   Expert Base   │
└─────────────────┘      └─────────────────┘
```

**Best for:**
- Real-time content processing
- Immediate feedback and validation
- Simple request-response flows

### 2. Event-Driven Integration

Services communicate through an event bus for asynchronous processing.

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Your Service    │─────▶│  Event Bus      │─────▶│   Expert Base   │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        ▲                                                  │
        └──────────────────────────────────────────────────┘
```

**Best for:**
- Decoupled architecture
- Processing that doesn't require immediate response
- Batch processing workflows

### 3. Worker-Based Processing

Expert Base workers process items from shared storage or queues.

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Your Service    │─────▶│  Shared Queue   │◀────▶│ Expert Base     │
└─────────────────┘      └─────────────────┘      │ Workers         │
                                                  └─────────────────┘
```

**Best for:**
- High-volume processing
- Background tasks
- Job-based workflows

## Direct API Integration

### Setup

1. **Configure Environment**

   Add the following environment variables to your service's configuration:

   ```
   EXPERT_BASE_URL=http://expert-base-service:8000
   EXPERT_BASE_API_KEY=your_api_key
   ```

2. **Create Client**

   Implement an Expert Base client in your service:

   ```python
   import httpx
   import uuid
   from typing import Dict, Any, Optional
   
   class ExpertBaseClient:
       """Client for interacting with the Expert Base microservice"""
       
       def __init__(self, base_url: str, api_key: str):
           self.base_url = base_url
           self.headers = {"Authorization": f"Bearer {api_key}"}
           
       async def process_content(
           self, 
           content: str, 
           expert: str, 
           intent: str, 
           parameters: Optional[Dict[str, Any]] = None,
           metadata: Optional[Dict[str, Any]] = None
       ) -> Dict[str, Any]:
           """Process content using an expert bot"""
           if parameters is None:
               parameters = {}
               
           if metadata is None:
               metadata = {}
               
           request_data = {
               "expert": expert,
               "intent": intent,
               "content": content,
               "parameters": parameters,
               "metadata": metadata,
               "tracking_id": str(uuid.uuid4())
           }
           
           async with httpx.AsyncClient() as client:
               response = await client.post(
                   f"{self.base_url}/api/v1/expert/process",
                   json=request_data,
                   headers=self.headers,
                   timeout=30.0
               )
               
           if response.status_code != 200:
               raise Exception(f"Expert base request failed: {response.text}")
               
           return response.json()
           
       async def get_capabilities(self, expert_id: Optional[str] = None) -> Dict[str, Any]:
           """Get capabilities of experts"""
           url = f"{self.base_url}/api/v1/expert/capabilities"
           if expert_id:
               url = f"{url}?expert_id={expert_id}"
               
           async with httpx.AsyncClient() as client:
               response = await client.get(
                   url,
                   headers=self.headers,
                   timeout=10.0
               )
               
           if response.status_code != 200:
               raise Exception(f"Failed to get capabilities: {response.text}")
               
           return response.json()
   ```

3. **Initialize the Client**

   ```python
   import os
   
   expert_base_client = ExpertBaseClient(
       base_url=os.getenv("EXPERT_BASE_URL"),
       api_key=os.getenv("EXPERT_BASE_API_KEY")
   )
   ```

### Usage Examples

#### Content Generation (Generative Base)

```python
async def generate_instagram_post(topic, tone, target_audience):
    """Generate an Instagram post using expert knowledge"""
    content = f"Create an Instagram post about {topic}."
    
    parameters = {
        "tone": tone,
        "target_audience": target_audience,
        "include_hashtags": True
    }
    
    result = await expert_base_client.process_content(
        content=content,
        expert="instagram",
        intent="generate",
        parameters=parameters
    )
    
    return {
        "post_text": result.get("content"),
        "suggested_hashtags": result.get("metadata", {}).get("hashtags", []),
        "feedback": result.get("feedback", {})
    }
```

#### Content Analysis (Analysis Base)

```python
async def analyze_social_media_performance(performance_data):
    """Get expert analysis of social media performance"""
    # Format performance data as content
    content = format_performance_data(performance_data)
    
    result = await expert_base_client.process_content(
        content=content,
        expert="instagram",
        intent="analyze",
        parameters={
            "analysis_type": "performance",
            "metrics": ["engagement", "reach", "conversion"],
            "timeframe": "monthly"
        }
    )
    
    return {
        "insights": result.get("content"),
        "recommendations": result.get("feedback", {}).get("recommendations", []),
        "key_metrics": result.get("metadata", {}).get("key_metrics", {})
    }
```

#### Content Review (Marketing Base)

```python
async def review_marketing_campaign(campaign_content):
    """Get expert review of marketing campaign content"""
    result = await expert_base_client.process_content(
        content=campaign_content,
        expert="marketing",
        intent="review",
        parameters={
            "strictness": "high",
            "check_brand_alignment": True,
            "evaluate_conversion_potential": True
        }
    )
    
    return {
        "approved": result.get("metadata", {}).get("approved", False),
        "feedback": result.get("feedback", {}),
        "improvement_suggestions": result.get("content")
    }
```

## Event-Driven Integration

For event-driven integration, you'll need a shared message bus. This example uses a simple event bus pattern.

### Setup

1. **Configure Event Bus**

   Add the following to your service's configuration:

   ```
   EVENT_BUS_URL=amqp://rabbitmq:5672/
   EVENT_BUS_EXCHANGE=expert_exchange
   ```

2. **Create Event Publishers and Consumers**

   ```python
   import aio_pika
   import json
   
   class ExpertBaseEventClient:
       """Client for event-based interaction with Expert Base"""
       
       def __init__(self, event_bus_url, exchange_name):
           self.event_bus_url = event_bus_url
           self.exchange_name = exchange_name
           self.connection = None
           self.channel = None
           self.exchange = None
           
       async def connect(self):
           """Connect to the event bus"""
           self.connection = await aio_pika.connect_robust(self.event_bus_url)
           self.channel = await self.connection.channel()
           self.exchange = await self.channel.declare_exchange(
               self.exchange_name,
               aio_pika.ExchangeType.TOPIC
           )
           
       async def publish_expert_request(self, request_data, routing_key="expert.request"):
           """Publish an expert request to the event bus"""
           if not self.exchange:
               await self.connect()
               
           message = aio_pika.Message(
               body=json.dumps(request_data).encode(),
               content_type="application/json",
               correlation_id=request_data.get("tracking_id")
           )
           
           await self.exchange.publish(
               message,
               routing_key=routing_key
           )
           
       async def consume_expert_responses(self, callback, queue_name, routing_key="expert.response.*"):
           """Consume expert responses from the event bus"""
           if not self.channel:
               await self.connect()
               
           queue = await self.channel.declare_queue(queue_name, durable=True)
           await queue.bind(self.exchange, routing_key)
           
           await queue.consume(callback)
   ```

3. **Initialize the Event Client**

   ```python
   import os
   
   expert_event_client = ExpertBaseEventClient(
       event_bus_url=os.getenv("EVENT_BUS_URL"),
       exchange_name=os.getenv("EVENT_BUS_EXCHANGE")
   )
   ```

### Usage Examples

```python
# Publishing a request
async def request_expert_analysis(content_id, content):
    tracking_id = str(uuid.uuid4())
    
    request_data = {
        "expert": "instagram",
        "intent": "analyze",
        "content": content,
        "parameters": {
            "analysis_type": "performance"
        },
        "metadata": {
            "content_id": content_id,
            "service": "analysis-base"
        },
        "tracking_id": tracking_id
    }
    
    await expert_event_client.publish_expert_request(request_data)
    return tracking_id

# Consuming responses
async def handle_expert_response(message):
    async with message.process():
        response_data = json.loads(message.body.decode())
        
        # Extract tracking ID and content ID
        tracking_id = response_data.get("tracking_id")
        content_id = response_data.get("metadata", {}).get("content_id")
        
        # Process the response
        if content_id:
            await store_expert_analysis(content_id, response_data)

# Setup consumer
async def setup_expert_response_consumer():
    await expert_event_client.consume_expert_responses(
        callback=handle_expert_response,
        queue_name="analysis-base-responses",
        routing_key="expert.response.analysis"
    )
```

## Worker-Based Integration

For worker-based integration, you'll need a shared queue system. This example uses a job queue pattern.

### Setup

1. **Configure Job Queue**

   Add the following to your service's configuration:

   ```
   JOB_QUEUE_URL=redis://redis:6379/0
   JOB_QUEUE_NAME=expert_jobs
   ```

2. **Create Job Producers and Consumers**

   ```python
   import redis
   import json
   from typing import Dict, Any, Optional, Callable
   
   class ExpertBaseJobClient:
       """Client for job-based interaction with Expert Base"""
       
       def __init__(self, redis_url, queue_name):
           self.redis_url = redis_url
           self.queue_name = queue_name
           self.redis_client = redis.Redis.from_url(redis_url)
           
       async def enqueue_expert_job(self, job_data):
           """Add a job to the expert job queue"""
           job_id = job_data.get("tracking_id", str(uuid.uuid4()))
           
           # Store the job data
           self.redis_client.set(
               f"job:{job_id}",
               json.dumps(job_data),
               ex=86400  # 24 hour expiry
           )
           
           # Add to the processing queue
           self.redis_client.lpush(self.queue_name, job_id)
           
           return job_id
           
       async def get_job_result(self, job_id):
           """Get the result of a job"""
           result_key = f"result:{job_id}"
           
           # Check if result exists
           if not self.redis_client.exists(result_key):
               return None
               
           # Get and parse result
           result_data = self.redis_client.get(result_key)
           return json.loads(result_data)
           
       async def process_jobs(self, processor: Callable, batch_size=10):
           """Process jobs from the queue"""
           while True:
               # Get batch of jobs
               job_ids = self.redis_client.rpop(self.queue_name, batch_size)
               
               if not job_ids:
                   # No jobs, wait before checking again
                   await asyncio.sleep(1)
                   continue
                   
               for job_id in job_ids:
                   # Get job data
                   job_key = f"job:{job_id.decode()}"
                   job_data = self.redis_client.get(job_key)
                   
                   if job_data:
                       # Process job
                       job_data = json.loads(job_data)
                       result = await processor(job_data)
                       
                       # Store result
                       result_key = f"result:{job_id.decode()}"
                       self.redis_client.set(
                           result_key,
                           json.dumps(result),
                           ex=86400  # 24 hour expiry
                       )
   ```

3. **Initialize the Job Client**

   ```python
   import os
   
   expert_job_client = ExpertBaseJobClient(
       redis_url=os.getenv("JOB_QUEUE_URL"),
       queue_name=os.getenv("JOB_QUEUE_NAME")
   )
   ```

### Usage Examples

```python
# Producing jobs
async def submit_expert_review_job(content_id, content):
    job_data = {
        "expert": "marketing",
        "intent": "review",
        "content": content,
        "parameters": {
            "strictness": "high"
        },
        "metadata": {
            "content_id": content_id,
            "service": "marketing-base"
        },
        "tracking_id": str(uuid.uuid4())
    }
    
    job_id = await expert_job_client.enqueue_expert_job(job_data)
    return job_id

# Checking job results
async def check_expert_review(job_id):
    result = await expert_job_client.get_job_result(job_id)
    
    if result is None:
        return {"status": "pending"}
        
    return {
        "status": "completed",
        "approved": result.get("metadata", {}).get("approved", False),
        "feedback": result.get("feedback", {}),
        "suggestions": result.get("content")
    }

# Processing jobs (Expert Base side)
async def process_expert_job(job_data):
    # Extract job information
    expert = job_data.get("expert")
    intent = job_data.get("intent")
    content = job_data.get("content")
    parameters = job_data.get("parameters", {})
    
    # Process with appropriate expert
    result = await expert_orchestrator.process_request({
        "expert": expert,
        "intent": intent,
        "content": content,
        "parameters": parameters,
        "metadata": job_data.get("metadata", {}),
        "tracking_id": job_data.get("tracking_id")
    })
    
    return result
```

## Additional Integration Considerations

### 1. Error Handling

Implement robust error handling for all integration patterns:

```python
try:
    result = await expert_base_client.process_content(...)
except Exception as e:
    # Log the error
    logger.error(f"Expert Base request failed: {e}")
    
    # Provide fallback behavior
    result = get_fallback_result()
```

### 2. Circuit Breaking

Implement circuit breaking to prevent cascading failures:

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=30)
async def call_expert_base_with_circuit_breaker(content, expert, intent, parameters=None):
    return await expert_base_client.process_content(
        content=content,
        expert=expert,
        intent=intent,
        parameters=parameters
    )
```

### 3. Request Tracking

Track requests across services for observability:

```python
async def process_with_tracking(content, expert, intent, parameters=None):
    tracking_id = str(uuid.uuid4())
    
    # Log the request start
    logger.info(f"Starting expert base request: {tracking_id}")
    
    # Add tracking ID to parameters
    if parameters is None:
        parameters = {}
    
    metadata = {
        "source_service": "your-service-name",
        "correlation_id": get_correlation_id()
    }
    
    # Make the request
    result = await expert_base_client.process_content(
        content=content,
        expert=expert,
        intent=intent,
        parameters=parameters,
        metadata=metadata,
        tracking_id=tracking_id
    )
    
    # Log the request completion
    logger.info(f"Completed expert base request: {tracking_id}")
    
    return result
```

### 4. Caching

Implement caching for frequently used expert responses:

```python
import aiocache

@aiocache.cached(ttl=3600)  # Cache for 1 hour
async def get_cached_expert_response(content_hash, expert, intent, parameters_hash):
    # Convert parameters to a consistent hash
    params_str = json.dumps(parameters, sort_keys=True)
    
    # Make the actual request
    result = await expert_base_client.process_content(
        content=content,
        expert=expert,
        intent=intent,
        parameters=parameters
    )
    
    return result
```

## Service-Specific Integration Examples

### 1. Generative Base Integration

```python
# In generative-base/src/modules/expert_base_module/handler.py

class ExpertBaseHandler:
    """Handler for expert base integration"""
    
    def __init__(self):
        self.client = ExpertBaseClient(
            base_url=os.getenv("EXPERT_BASE_URL"),
            api_key=os.getenv("EXPERT_BASE_API_KEY")
        )
        
    async def review_generated_content(self, content, content_type, template_info):
        """Review generated content using the appropriate expert"""
        # Determine expert based on content type
        expert = self._map_content_type_to_expert(content_type)
        
        # Extract relevant parameters from template info
        parameters = {
            "tone": template_info.get("tone", "neutral"),
            "brand": template_info.get("brand"),
            "strictness": template_info.get("expert_strictness", "balanced")
        }
        
        # Send for review
        result = await self.client.process_content(
            content=content,
            expert=expert,
            intent="review",
            parameters=parameters,
            metadata={"template_id": template_info.get("template_id")}
        )
        
        # Process review results
        return {
            "approved": result.get("metadata", {}).get("approved", False),
            "feedback": result.get("feedback", {}),
            "suggestions": result.get("content")
        }
        
    def _map_content_type_to_expert(self, content_type):
        """Map content type to appropriate expert"""
        mapping = {
            "instagram_post": "instagram",
            "twitter_post": "twitter",
            "facebook_post": "facebook",
            "linkedin_post": "linkedin",
            "email_campaign": "email",
            "blog_post": "blog"
        }
        
        return mapping.get(content_type, "general")
```

### 2. Analysis Base Integration

```python
# In analysis-base/src/modules/expert_insights/service.py

class ExpertInsightService:
    """Service for getting expert insights on analysis results"""
    
    def __init__(self):
        self.client = ExpertBaseClient(
            base_url=os.getenv("EXPERT_BASE_URL"),
            api_key=os.getenv("EXPERT_BASE_API_KEY")
        )
        
    async def enhance_analysis(self, analysis_results, domain):
        """Enhance analysis results with expert insights"""
        # Format analysis results for expert consumption
        content = self._format_analysis_results(analysis_results)
        
        # Get expert insights
        result = await self.client.process_content(
            content=content,
            expert=domain,
            intent="analyze",
            parameters={
                "analysis_type": analysis_results.get("type"),
                "metrics": analysis_results.get("metrics", []),
                "timeframe": analysis_results.get("timeframe", "all")
            }
        )
        
        # Merge insights with original analysis
        enhanced_analysis = {
            **analysis_results,
            "expert_insights": result.get("content"),
            "recommendations": result.get("feedback", {}).get("recommendations", []),
            "key_findings": result.get("metadata", {}).get("key_findings", [])
        }
        
        return enhanced_analysis
        
    def _format_analysis_results(self, results):
        """Format analysis results for expert consumption"""
        # Implementation details
        formatted_content = json.dumps(results, indent=2)
        return f"Please analyze the following results:\n\n{formatted_content}"
```

### 3. Marketing Base Integration

```python
# In marketing-base/src/services/expert_review_service.py

class MarketingExpertReviewService:
    """Service for expert review of marketing materials"""
    
    def __init__(self):
        self.client = ExpertBaseClient(
            base_url=os.getenv("EXPERT_BASE_URL"),
            api_key=os.getenv("EXPERT_BASE_API_KEY")
        )
        
    async def review_campaign(self, campaign_data):
        """Review a marketing campaign using expert review"""
        # Extract campaign content and metadata
        content = campaign_data.get("content", "")
        campaign_type = campaign_data.get("type", "general")
        
        # Determine appropriate expert
        expert = self._get_expert_for_campaign(campaign_type)
        
        # Send for review
        result = await self.client.process_content(
            content=content,
            expert=expert,
            intent="review",
            parameters={
                "campaign_type": campaign_type,
                "target_audience": campaign_data.get("target_audience", []),
                "brand_guidelines": campaign_data.get("brand_guidelines", {})
            }
        )
        
        # Update campaign with review results
        campaign_data["review_status"] = "completed"
        campaign_data["approved"] = result.get("metadata", {}).get("approved", False)
        campaign_data["expert_feedback"] = result.get("feedback", {})
        campaign_data["improvement_suggestions"] = result.get("content")
        
        return campaign_data
        
    def _get_expert_for_campaign(self, campaign_type):
        """Get the appropriate expert for a campaign type"""
        mapping = {
            "social_media": "social",
            "email": "email",
            "print": "print",
            "video": "video",
            "podcast": "audio"
        }
        
        return mapping.get(campaign_type, "marketing")
``` 