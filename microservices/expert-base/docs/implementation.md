# Expert Base Microservice Technical Implementation

This document outlines the technical implementation of the Expert Base microservice, including code examples and implementation patterns.

## Core Components Implementation

### 1. Intent-Based Configuration

The heart of the Expert Base microservice is its intent-based configuration system, which enables different services to use the same expert bots in different ways.

#### Configuration Structure

```python
# Expert Base Configuration Example
expert_registry = {
    "instagram": {
        "core_config": {
            "model_id": "instagram-specialized-llm",
            "base_parameters": {"temperature": 0.7, "max_tokens": 2000},
            "adapters": {"default": "path/to/instagram_adapter"},
            "capabilities": ["generate", "analyze", "review"]
        },
        "modes": {
            "generate": {
                "processor": "content_generation_pipeline",
                "parameters": {"creativity_level": "high", "format_check": True},
                "knowledge_filters": {"domain": "instagram_posts", "content_type": "creation"}
            },
            "analyze": {
                "processor": "content_analysis_pipeline",
                "parameters": {"depth": "comprehensive", "metrics": ["engagement", "conversion"]},
                "knowledge_filters": {"domain": "instagram_metrics", "content_type": "analysis"}
            },
            "review": {
                "processor": "content_review_pipeline",
                "parameters": {"strictness": "balanced", "check_brand_alignment": True},
                "knowledge_filters": {"domain": "instagram_guidelines", "content_type": "standards"}
            }
        }
    },
    # Additional experts follow the same pattern
}
```

### 2. Expert Orchestrator

The Expert Orchestrator is responsible for handling requests, selecting the appropriate expert bot, and coordinating the processing.

```python
class ExpertOrchestrator:
    """Orchestrates the processing of expert requests"""
    
    def __init__(self, expert_registry, processor_factory, knowledge_hub):
        self.expert_registry = expert_registry
        self.processor_factory = processor_factory
        self.knowledge_hub = knowledge_hub
        
    def process_request(self, request: ExpertRequest) -> ExpertResponse:
        """Process a request using the intent-based configuration model"""
        # 1. Validate request and extract key components
        expert_id = request.expert
        intent = request.intent
        user_parameters = request.parameters
        content = request.content
        
        # 2. Verify expert and intent are valid
        if not self.expert_registry.has_expert(expert_id):
            raise ExpertNotFoundException(f"Expert '{expert_id}' not found")
            
        if not self.expert_registry.supports_intent(expert_id, intent):
            raise IntentNotSupportedException(f"Expert '{expert_id}' does not support intent '{intent}'")
        
        # 3. Get expert configuration
        core_config = self.expert_registry.get_core_config(expert_id)
        mode_config = self.expert_registry.get_mode_config(expert_id, intent)
        
        # 4. Merge configurations with user parameters
        working_config = self._merge_configurations(core_config, mode_config, user_parameters)
        
        # 5. Get knowledge context based on configuration
        knowledge_filters = mode_config.get("knowledge_filters", {})
        knowledge_context = self.knowledge_hub.retrieve_knowledge(
            expert_id, intent, content, knowledge_filters
        )
        
        # 6. Get appropriate processor for this intent
        processor_id = mode_config.get("processor")
        processor = self.processor_factory.create_processor(processor_id)
        
        # 7. Process the request with merged configuration and knowledge
        processing_context = {
            "config": working_config,
            "knowledge": knowledge_context,
            "tracking_id": request.tracking_id,
            "metadata": request.metadata
        }
        
        result = processor.process(content, processing_context)
        
        # 8. Return formatted response
        return self._format_response(result, request)
    
    def _merge_configurations(self, core_config, mode_config, user_parameters):
        """Merge different configuration layers with precedence rules"""
        # Parameters precedence: user_parameters > mode_config > core_config
        merged = {**core_config, **mode_config.get("parameters", {})}
        
        # Apply user parameters, but only those allowed by the mode
        allowed_params = mode_config.get("allowed_user_parameters", [])
        if allowed_params:
            for param in allowed_params:
                if param in user_parameters:
                    merged[param] = user_parameters[param]
        else:
            # If no allowed params specified, merge all user parameters
            merged.update(user_parameters)
            
        return merged
        
    def _format_response(self, result, request):
        """Format the processor result into a standard response"""
        return ExpertResponse(
            expert_id=request.expert,
            intent=request.intent,
            content=result.get("content"),
            feedback=result.get("feedback"),
            metadata=result.get("metadata", {}),
            tracking_id=request.tracking_id
        )
```

### 3. Expert Bot Framework

The Expert Bot Framework provides a base class for all expert bots and handles common functionality.

```python
class BaseExpertBot:
    """Base class for all expert bots"""
    
    def __init__(self, config):
        self.config = config
        self.model = self._load_model(config)
        
    def _load_model(self, config):
        """Load the appropriate LLM model with adapters"""
        model_id = config.get("model_id")
        adapter_path = config.get("adapters", {}).get("default")
        # Load model with appropriate adapter
        return ModelFactory.load_model(model_id, adapter_path)
    
    def process(self, content, context):
        """Process content in the appropriate mode"""
        intent = context.get("intent")
        if intent == "generate":
            return self.generate(content, context)
        elif intent == "analyze":
            return self.analyze(content, context)
        elif intent == "review":
            return self.review(content, context)
        else:
            raise UnsupportedIntentException(f"Intent '{intent}' not supported")
    
    # Intent-specific methods to be implemented by subclasses
    def generate(self, content, context):
        raise NotImplementedError
        
    def analyze(self, content, context):
        raise NotImplementedError
        
    def review(self, content, context):
        raise NotImplementedError
```

### 4. Knowledge Hub

The Knowledge Hub manages the retrieval of domain-specific knowledge for expert bots.

```python
class KnowledgeHub:
    """Manages knowledge retrieval across different domains"""
    
    def __init__(self, vector_db_client):
        self.vector_db = vector_db_client
        
    def retrieve_knowledge(self, expert_id, intent, content, filters=None):
        """Retrieve relevant knowledge for a specific expert, intent and content"""
        # Create combined filters
        combined_filters = {
            "expert_id": expert_id,
            "intent": intent
        }
        
        if filters:
            combined_filters.update(filters)
            
        # Generate embedding for the content
        content_embedding = self._generate_embedding(content)
        
        # Retrieve relevant knowledge
        results = self.vector_db.query(
            embedding=content_embedding,
            filters=combined_filters,
            limit=10  # Can be configurable
        )
        
        # Format results
        formatted_results = self._format_results(results)
        
        return formatted_results
    
    def _generate_embedding(self, content):
        """Generate embedding for the given content"""
        # Implementation using the chosen embedding model
        pass
        
    def _format_results(self, results):
        """Format retrieved results into a usable knowledge context"""
        # Implementation to structure the knowledge context
        pass
```

### 5. API Layer

The API Layer exposes endpoints for processing requests and discovering capabilities.

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

app = FastAPI(title="Expert Base API")

# Request and response models
class ExpertRequest(BaseModel):
    expert: str
    intent: str
    content: str
    parameters: Optional[Dict[str, Any]] = {}
    metadata: Optional[Dict[str, Any]] = {}
    tracking_id: Optional[str] = None

class ExpertResponse(BaseModel):
    expert_id: str
    intent: str
    content: Optional[str] = None
    feedback: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}
    tracking_id: Optional[str] = None

# Dependency for getting the orchestrator
def get_orchestrator():
    # This would be initialized with configuration from environment/files
    return expert_orchestrator

# API Endpoints
@app.post("/api/v1/expert/process", response_model=ExpertResponse)
async def process_expert_request(
    request: ExpertRequest, 
    orchestrator: ExpertOrchestrator = Depends(get_orchestrator)
) -> ExpertResponse:
    """Process a request using the appropriate expert in the specified mode"""
    try:
        return orchestrator.process_request(request)
    except ExpertNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IntentNotSupportedException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log unexpected exceptions
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/expert/capabilities")
async def get_expert_capabilities(
    expert_id: Optional[str] = None,
    orchestrator: ExpertOrchestrator = Depends(get_orchestrator)
):
    """Discover available experts and their capabilities"""
    try:
        return orchestrator.expert_registry.get_capabilities(expert_id)
    except ExpertNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Log unexpected exceptions
        logger.error(f"Error getting capabilities: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Integration Examples

### 1. Generative Base Integration

```python
# In Generative Base microservice
class ExpertBaseClient:
    """Client for interacting with the Expert Base microservice"""
    
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
        
    async def review_content(self, content, expert="instagram", intent="review", parameters=None):
        """Send content to expert base for review"""
        if parameters is None:
            parameters = {}
            
        request_data = {
            "expert": expert,
            "intent": intent,
            "content": content,
            "parameters": parameters,
            "tracking_id": str(uuid.uuid4())
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/expert/process",
                json=request_data,
                headers=self.headers
            )
            
        if response.status_code != 200:
            raise Exception(f"Expert base request failed: {response.text}")
            
        return response.json()
```

### 2. Analysis Base Integration

```python
# In Analysis Base microservice
class ExpertInsightGenerator:
    """Generates expert insights for analysis results"""
    
    def __init__(self, expert_client):
        self.expert_client = expert_client
        
    async def generate_insights(self, analysis_results, domain="instagram"):
        """Generate expert insights from analysis results"""
        # Format analysis results as content for expert
        content = self._format_analysis_results(analysis_results)
        
        # Request expert analysis
        expert_response = await self.expert_client.process_content(
            content=content,
            expert=domain,
            intent="analyze",
            parameters={
                "analysis_type": analysis_results.get("type"),
                "depth": "comprehensive",
                "format": "structured"
            }
        )
        
        # Extract and format insights
        insights = self._parse_expert_insights(expert_response)
        
        return insights
        
    def _format_analysis_results(self, results):
        """Format analysis results for expert consumption"""
        # Implementation details
        pass
        
    def _parse_expert_insights(self, response):
        """Parse expert response into structured insights"""
        # Implementation details
        pass
```

## Processing Pipelines

The processing pipelines implement different processing modes:

```python
class ContentGenerationPipeline:
    """Pipeline for generating content"""
    
    def __init__(self, model_provider):
        self.model_provider = model_provider
        
    def process(self, content, context):
        """Generate content based on input and context"""
        # Extract configuration
        config = context.get("config", {})
        knowledge = context.get("knowledge", "")
        
        # Construct prompt with knowledge integration
        prompt = self._construct_prompt(content, knowledge, config)
        
        # Generate content
        generation_params = {
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 1000),
            "stop_sequences": config.get("stop_sequences", []),
        }
        
        generated_content = self.model_provider.generate(prompt, generation_params)
        
        # Post-process content
        processed_content = self._post_process(generated_content, config)
        
        return {
            "content": processed_content,
            "metadata": {
                "prompt_tokens": len(prompt),
                "completion_tokens": len(generated_content),
                "generation_params": generation_params
            }
        }
        
    def _construct_prompt(self, content, knowledge, config):
        """Construct generation prompt with knowledge integration"""
        # Implementation details
        pass
        
    def _post_process(self, content, config):
        """Post-process generated content"""
        # Implementation details
        pass
```

## Configuration Management

Configuration is loaded from multiple sources and merged according to precedence rules:

```python
class ConfigurationManager:
    """Manages configuration across different sources"""
    
    def __init__(self):
        self.default_config = {}
        self.environment_config = {}
        self.file_config = {}
        self.database_config = {}
        
    def load_configuration(self):
        """Load configuration from all sources"""
        self._load_default_config()
        self._load_environment_config()
        self._load_file_config()
        self._load_database_config()
        
    def get_expert_config(self, expert_id):
        """Get merged configuration for a specific expert"""
        # Start with defaults
        config = self.default_config.get("experts", {}).get(expert_id, {})
        
        # Apply environment overrides
        env_config = self.environment_config.get("experts", {}).get(expert_id, {})
        config = self._merge_configs(config, env_config)
        
        # Apply file overrides
        file_config = self.file_config.get("experts", {}).get(expert_id, {})
        config = self._merge_configs(config, file_config)
        
        # Apply database overrides
        db_config = self.database_config.get("experts", {}).get(expert_id, {})
        config = self._merge_configs(config, db_config)
        
        return config
        
    def _merge_configs(self, base, override):
        """Deep merge of configuration dictionaries"""
        # Implementation details for deep merging
        pass
        
    def _load_default_config(self):
        """Load default configuration"""
        pass
        
    def _load_environment_config(self):
        """Load configuration from environment variables"""
        pass
        
    def _load_file_config(self):
        """Load configuration from files"""
        pass
        
    def _load_database_config(self):
        """Load configuration from database"""
        pass
```

## Error Handling

Comprehensive error handling is implemented to provide clear error messages and appropriate responses:

```python
# Custom exceptions
class ExpertBaseException(Exception):
    """Base exception for all expert base exceptions"""
    pass
    
class ExpertNotFoundException(ExpertBaseException):
    """Exception raised when an expert is not found"""
    pass
    
class IntentNotSupportedException(ExpertBaseException):
    """Exception raised when an intent is not supported by an expert"""
    pass
    
class ProcessingException(ExpertBaseException):
    """Exception raised when processing fails"""
    pass

# Error handler
class ErrorHandler:
    """Handles errors in the expert base microservice"""
    
    def __init__(self, logger):
        self.logger = logger
        
    def handle_error(self, error, request=None):
        """Handle an error and generate an appropriate response"""
        if isinstance(error, ExpertNotFoundException):
            self.logger.warning(f"Expert not found: {error}")
            return {"error": "expert_not_found", "message": str(error)}, 404
            
        elif isinstance(error, IntentNotSupportedException):
            self.logger.warning(f"Intent not supported: {error}")
            return {"error": "intent_not_supported", "message": str(error)}, 400
            
        elif isinstance(error, ProcessingException):
            self.logger.error(f"Processing error: {error}")
            return {"error": "processing_error", "message": str(error)}, 500
            
        else:
            # Unexpected error
            self.logger.error(f"Unexpected error: {error}", exc_info=True)
            return {"error": "internal_error", "message": "An unexpected error occurred"}, 500
``` 