#update main.py according to the new workflow of agent microservice, current file is setted up according to old workflow and architecture
# Template Structure Example:
"""
{
  "purpose_id": "etsy_listing",
  "version": "1.2.0",
  "description": "Template for generating Etsy product listings",
  "created_by": "admin@example.com",
  "created_at": "2023-10-01T12:00:00Z",
  "updated_at": "2023-10-05T14:30:00Z",
  "input_schema": {
    "type": "object",
    "properties": {
      "user_id": { "type": "string" },
      "product_name": { "type": "string" },
      "product_description": { "type": "string" }
    },
    "required": ["user_id", "product_name"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "listing_id": { "type": "string" },
      "listing_url": { "type": "string" }
    },
    "required": ["listing_id"]
  },
  "steps": [
    {
      "step_number": 1,
      "microservice": "userdetails",
      "class_name": "UserInsights",
      "method_name": "getBranding",
      "input_mapping": {
        "user_id": "user_id"
      },
      "output_mapping": {
        "brand_style": "brand_style"
      },
      "retry_policy": {
        "attempts": 3,
        "backoff": "exponential",
        "max_delay": "10s"
      },
      "timeout": "5s",
      "allowed_errors": ["TimeoutError"],
      "circuit_breaker": {
        "failure_threshold": 5,
        "cooldown_period": "60s"
      }
    },
    {
      "step_number": 2,
      "microservice": "generative-base",
      "class_name": "ListingGenerator",
      "method_name": "createListing",
      "input_mapping": {
        "brand_style": "brand_style",
        "product_name": "product_name",
        "product_description": "product_description"
      },
      "output_mapping": {
        "listing_draft": "listing_draft"
      },
      "retry_policy": {
        "attempts": 2,
        "backoff": "linear",
        "max_delay": "5s"
      },
      "timeout": "10s",
      "allowed_errors": ["ValidationError"],
      "circuit_breaker": {
        "failure_threshold": 3,
        "cooldown_period": "30s"
      }
    }
  ]
}
"""
import os
from fastapi import FastAPI, HTTPException
from models.template import ExecutionTemplate
from batch_processor import BatchProcessor
from realtime_orchestrator import RealtimeOrchestrator
from context_manager import ContextManager
from microservices.agent.src.error_handling.error_handling import ErrorHandler
from microservices.agent.src.template.template_manager import TemplateManager
from microservices.agent.src.nlp.nlp_processor import PurposeAnalyzer
from microservices.agent.src.request_handler.handler import RequestHandler

app = FastAPI()
batch_processor = BatchProcessor()
realtime_orchestrator = RealtimeOrchestrator()
context_mgr = ContextManager()
error_handler = ErrorHandler()
template_mgr = TemplateManager()
nlp_processor = PurposeAnalyzer()
request_handler = RequestHandler(template_mgr, nlp_processor)

@app.post("/process")
async def handle_request(request_data: dict):
    """Main request processing endpoint"""
    try:
        template = request_handler.handle_request(request_data)
        context = context_mgr.create_context(request_data)
        return await realtime_orchestrator.execute(template, context)
    except Exception as e:
        error_handler.log_error(e)
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/process-batch")
async def handle_batch(batch_request: BatchRequest):
    """Batch processing endpoint"""
    try:
        template = template_mgr.get_template(batch_request.purpose_id)
        return await batch_processor.execute(template, batch_request.data)
    except Exception as e:
        error_handler.log_error(e)
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 80)))