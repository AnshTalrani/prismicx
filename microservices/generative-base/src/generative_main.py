"""
This module provides the main entry point for the generative-base microservice.

It follows MACH architecture principles:
 - Microservices-based design
 - API-first approach
 - Cloud-native deployment
 - Headless integration

It includes basic error handling and validates environment variables for secure data processing.
"""

import os
import sys
from fastapi import FastAPI, HTTPException, APIRouter
from common.config import Config
from template import Template
from extract_module.handler import ExtractHandler
from common.utils import Utils
from user_details_extraction_module.handler import UserDetailsExtractor
from deep_input_processing_module.strategist import AIStrategist
from deep_input_processing_module.processor import DeepInputProcessor
from high_quality_output_generation_module.handler import OutputGenerator
from expert_base_module.handler import ExpertBaseHandler
import importlib
from processing_pipeline import DataProcessor, BatchPipeline
from typing import Dict

app = FastAPI()

class GenerativeMicroservice:
    """Main microservice handler class"""
    
    def __init__(self):
        self.config = Config()
        self.utils = Utils()
    
    @app.post("/process")
    async def handle_request(self, request: dict):
        """Handle single processing request"""
        try:
            template = self.initialize_template(request)
            self.execute_modules(template)
            return template.generated_output
        except Exception as e:
            self.utils.log_error(str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    def initialize_template(self, request: dict) -> Template:
        """Enhanced template initialization"""
        template = Template(request['purpose_id'])
        template.context = request.get('context', {})
        template.user_details = request.get('user_details', {})
        
        if not template.validate():
            raise ValueError("Invalid template initialization")
            
        return template
    
    def execute_modules(self, template: Template):
        """Full module execution pipeline"""
        try:
            # Extraction Phase
            UserDetailsExtractor(template).extract_user_details()
            ExtractHandler(template).extract_data()
            
            # Processing Phase
            DeepInputProcessor(template).process_input()
            
            # Generation Phase
            OutputGenerator(template).generate_output()
            
            # Expert Review Phase
            ExpertBaseHandler(template).review_content()
            
        except Exception as e:
            self.utils.log_error(f"Processing pipeline failed: {e}")
            raise

    @app.post("/process-sequence")
    async def handle_sequence_batch(self, request: SequenceBatchRequest):
        results = []
        for item in request.batch_items:
            context = item.copy()
            for step in request.template.steps:
                processor = getattr(
                    importlib.import_module(f"src.{step.class_name.lower()}"),
                    step.class_name
                )()
                method = getattr(processor, step.method_name)
                context = method(context, **step.parameters)
            results.append(context)
        return results

class ExecutionEngine:
    def load_template(self, template: dict):
        self.pipeline = DataProcessor()
        for step in template["steps"]:
            self.pipeline.add_step(
                step["class_name"],
                step["method_name"],
                step["parameters"]
            )
    
    def process_item(self, item):
        return self.pipeline.execute(item)

def main():
    """Updated main function with FastAPI integration"""
    from common.config import Config
    Config()  # Validate config on startup
    
    service = GenerativeMicroservice()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main() 

router = APIRouter()

@router.post("/process-batch-chain")
async def handle_batch_chain(request: BatchRequest):
    processor = BatchPipeline(request.template)
    return {
        "results": [
            processor.process_item(item)
            for item in request.batch_items
        ]
    }

@app.post("/execute")
async def execute_operation(request: ExecutionRequest):
    try:
        processor = getattr(sys.modules[__name__], request.operation)
        return processor(request.inputs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 